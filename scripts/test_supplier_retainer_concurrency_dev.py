"""DEV-only, two-session proof of the retainer SQL locking protocol.

Runs the actual service._lock_agreements and service._reserve_claim functions,
remapping their SQL to two nonce-owned InnoDB tables. Minimal document facades
replace only agreement loading and claim insertion. No ERP document, invoice,
fiscal record or naming counter is created or committed. This complements the
rollback-only real-controller suite; it is not a concurrent end-to-end invoice
generation test.

The first session locks one amendment's original agreement, reserves a period,
and commits. The second session uses a different amendment of the same original,
establishes an earlier repeatable-read snapshot, waits for the original's lock,
then must reject the duplicate using the latest committed claim.
"""

import argparse
from datetime import date
from hashlib import sha256
import inspect
import json
import multiprocessing
import os
from pathlib import Path
import re
import sys
import time
from types import SimpleNamespace
from urllib.parse import urlsplit
from uuid import uuid4


SITE = "igcaribe.fortabs.com"
TABLE_PREFIX = "__pp_rt_conc_"
COUNT_TYPES = (
    "Supplier Retainer Agreement", "Supplier Retainer Batch", "Supplier Retainer Claim",
    "Purchase Invoice", "Employee", "Salary Slip", "GL Entry",
)


def checked_tables(tables):
    if set(tables) != {"agreement", "claim"}:
        raise AssertionError("Exactly two isolated tables are required.")
    pattern = re.compile(r"^__pp_rt_conc_[0-9a-f]{20}_(agreement|claim)$")
    if not all(pattern.fullmatch(value) for value in tables.values()):
        raise AssertionError("Refusing a table name outside the nonce-owned namespace.")
    if tables["agreement"].removesuffix("_agreement") != tables["claim"].removesuffix("_claim"):
        raise AssertionError("Both tables must belong to the same test run.")
    return tables


def connect(sites_path):
    import frappe
    os.chdir(sites_path)
    frappe.init(site=SITE, sites_path=str(sites_path))
    configured_host = urlsplit(frappe.conf.get("host_name") or "").hostname
    if configured_host not in (None, SITE):
        frappe.destroy()
        raise RuntimeError("Unexpected configured hostname; refusing DEV concurrency test.")
    frappe.connect()
    frappe.db.sql("SET SESSION innodb_lock_wait_timeout = 10")
    return frappe


class DuplicateRejected(Exception):
    pass


class RoutedDatabase:
    """Fail closed if runtime code tries to access any unapproved SQL table."""

    def __init__(self, db, tables):
        self.db = db
        self.tables = checked_tables(tables)

    def sql(self, statement, values=None, **kwargs):
        mapping = {
            "`tabSupplier Retainer Agreement`": "`" + self.tables["agreement"] + "`",
            "`tabSupplier Retainer Claim`": "`" + self.tables["claim"] + "`",
        }
        if not any(source in statement for source in mapping):
            raise AssertionError("Runtime attempted SQL outside isolated agreement/claim tables.")
        for source, target in mapping.items():
            statement = statement.replace(source, target)
        without_lock = re.sub(r"\bFOR\s+UPDATE\b", "", statement, flags=re.I)
        if not statement.lstrip().upper().startswith("SELECT ") or re.search(r"`tab|\b(?:INSERT|UPDATE|DELETE|DROP|ALTER|CREATE)\b", without_lock, re.I):
            raise AssertionError("Only remapped locking SELECTs are allowed from runtime helpers.")
        return self.db.sql(statement, values, **kwargs)


def document_facade(frappe, tables, role):
    class Claim:
        def __init__(self, values):
            self.__dict__.update(values)
            self.flags = SimpleNamespace(retainer_service=False)

        def insert(self, ignore_permissions=False):
            if not ignore_permissions or not self.flags.retainer_service:
                raise AssertionError("Unexpected claim insertion contract.")
            # Synthetic invoice labels are plain data in this private table.
            self.purchase_invoice = "RT-SYNTHETIC-INVOICE-" + role
            frappe.db.sql(
                "INSERT INTO `" + tables["claim"] + "` "
                "(name,agreement,agreement_identity,period_start,period_end,purchase_invoice,batch) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (self.name, self.agreement, self.agreement_identity, self.period_start,
                 self.period_end, self.purchase_invoice, self.batch),
            )
            return self

    def get_doc(doctype, name=None):
        if isinstance(doctype, dict):
            if doctype.get("doctype") != "Supplier Retainer Claim":
                raise AssertionError("Only isolated claim construction is supported.")
            return Claim(doctype)
        if doctype != "Supplier Retainer Agreement" or name not in {"RT-ROOT", "RT-A", "RT-B"}:
            raise AssertionError("Only isolated agreement reads are supported.")
        rows = frappe.db.sql(
            "SELECT name, amended_from, docstatus FROM `" + tables["agreement"] + "` WHERE name=%s",
            (name,), as_dict=True,
        )
        if len(rows) != 1:
            raise AssertionError("Synthetic agreement is missing.")
        return rows[0]

    def throw(message, *args, **kwargs):
        if "already have invoice" in message:
            raise DuplicateRejected(message)
        raise AssertionError("Unexpected runtime validation: " + str(message))

    return SimpleNamespace(db=RoutedDatabase(frappe.db, tables), get_doc=get_doc, throw=throw)


def worker(role, sites_path, tables, held, contender_started, contender_acquired, results):
    frappe = None
    try:
        checked_tables(tables)
        frappe = connect(sites_path)
        from powerpro.retainers import service
        service.frappe = document_facade(frappe, tables, role)
        service._ = lambda text: text
        row = SimpleNamespace(agreement="RT-" + role, replaces_invoice=None)
        batch = SimpleNamespace(
            name="RT-BATCH-" + role, details=[row],
            period_start=date(2037, 2, 1), period_end=date(2037, 2, 28),
        )
        if role == "B":
            if not held.wait(10):
                raise AssertionError("First session did not acquire its agreement lock.")
            # Establish an older snapshot before A commits; the locking claim
            # read must still see A's committed reservation afterwards.
            if frappe.db.sql("SELECT COUNT(*) FROM `" + tables["claim"] + "`")[0][0] != 0:
                raise AssertionError("Contender must establish its snapshot before the claim commits.")
            contender_started.set()
        started = time.monotonic()
        identities = service._lock_agreements(batch)
        waited = time.monotonic() - started
        if role == "A":
            held.set()
            if not contender_started.wait(10):
                raise AssertionError("Second session did not begin its locking attempt.")
            if contender_acquired.wait(0.8):
                raise AssertionError("Second session acquired the shared original agreement too early.")
        else:
            contender_acquired.set()
        try:
            claim = service._reserve_claim(batch, row, identities[row.agreement])
        except DuplicateRejected:
            frappe.db.rollback()
            results.put({"role": role, "outcome": "duplicate_rejected", "lock_wait_seconds": round(waited, 3)})
        else:
            frappe.db.commit()
            results.put({"role": role, "outcome": "claim_committed", "claim": claim.name, "lock_wait_seconds": round(waited, 3)})
    except BaseException as exc:
        if frappe:
            frappe.db.rollback()
        results.put({"role": role, "outcome": "error", "error": type(exc).__name__ + ": " + str(exc)})
    finally:
        if frappe:
            frappe.destroy()


def counts(frappe):
    return {doctype: frappe.db.count(doctype) for doctype in COUNT_TYPES}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", required=True, choices=[SITE])
    parser.add_argument("--sites-path", required=True)
    parser.add_argument("--confirm-development", required=True, choices=[SITE])
    args = parser.parse_args()
    sites_path = Path(args.sites_path).resolve()
    if not (sites_path / SITE / "site_config.json").is_file():
        parser.error("The exact development site configuration must exist in sites-path.")
    suffix = uuid4().hex[:20]
    tables = checked_tables({kind: TABLE_PREFIX + suffix + "_" + kind for kind in ("agreement", "claim")})
    frappe = connect(sites_path)
    created, processes, reports = [], [], []
    before = counts(frappe)
    summary = {"site": SITE, "scope": "actual locking helpers with isolated tables; not end-to-end invoice generation", "tables": tables, "business_counts_before": before}
    try:
        from powerpro.retainers import service
        summary["tested_source_sha256"] = sha256((inspect.getsource(service._lock_agreements) + inspect.getsource(service._reserve_claim)).encode()).hexdigest()
        # This connection performs DDL only in this fresh nonce namespace.
        frappe.db.rollback()
        frappe.db.sql("CREATE TABLE `" + tables["agreement"] + "` (name varchar(140) PRIMARY KEY, amended_from varchar(140), docstatus int NOT NULL) ENGINE=InnoDB")
        created.append(tables["agreement"])
        frappe.db.sql("CREATE TABLE `" + tables["claim"] + "` (name varchar(64) PRIMARY KEY, agreement varchar(140), agreement_identity varchar(140), period_start date, period_end date, purchase_invoice varchar(140), batch varchar(140), KEY identity_period (agreement_identity,period_start,period_end)) ENGINE=InnoDB")
        created.append(tables["claim"])
        frappe.db.sql("INSERT INTO `" + tables["agreement"] + "` (name,amended_from,docstatus) VALUES (%s,%s,%s),(%s,%s,%s),(%s,%s,%s)", ("RT-ROOT", None, 2, "RT-A", "RT-ROOT", 1, "RT-B", "RT-ROOT", 1))
        frappe.db.commit()
        context = multiprocessing.get_context("spawn")
        held, contender_started, contender_acquired = context.Event(), context.Event(), context.Event()
        results = context.Queue()
        for role in ("A", "B"):
            process = context.Process(target=worker, args=(role, str(sites_path), tables, held, contender_started, contender_acquired, results))
            process.start()
            processes.append(process)
        deadline = time.monotonic() + 25
        for process in processes:
            process.join(max(0, deadline - time.monotonic()))
        if any(process.is_alive() for process in processes):
            raise AssertionError("Concurrency workers exceeded the bounded deadline.")
        for _ in processes:
            reports.append(results.get(timeout=2))
        summary["sessions"] = sorted(reports, key=lambda row: row["role"])
        if {row["role"]: row["outcome"] for row in reports} != {"A": "claim_committed", "B": "duplicate_rejected"}:
            raise AssertionError("Expected exactly one committed claim and one duplicate rejection.")
        if next(row["lock_wait_seconds"] for row in reports if row["role"] == "B") < 0.5:
            raise AssertionError("The contender did not demonstrate waiting on the shared agreement lock.")
        rows = frappe.db.sql("SELECT agreement_identity, COUNT(*) AS n FROM `" + tables["claim"] + "` GROUP BY agreement_identity", as_dict=True)
        if len(rows) != 1 or rows[0].agreement_identity != "RT-ROOT" or rows[0].n != 1:
            raise AssertionError("Expected one durable claim shared across agreement amendments.")
        summary["result"] = "PASS"
    except BaseException as exc:
        summary["result"] = "FAIL"
        summary["error"] = type(exc).__name__ + ": " + str(exc)
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
            process.join(5)
        frappe.db.rollback()
        cleanup_errors = []
        for table in reversed(created):
            try:
                if table not in tables.values():
                    raise AssertionError("Refusing to drop an unowned table.")
                frappe.db.sql("DROP TABLE `" + table + "`")
            except BaseException as exc:
                cleanup_errors.append({"table": table, "error": type(exc).__name__ + ": " + str(exc)})
        summary["cleanup_errors"] = cleanup_errors
        remaining = frappe.db.sql("SELECT table_name FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name IN %(names)s", {"names": tuple(tables.values())})
        summary["remaining_test_tables"] = [row[0] for row in remaining]
        after = counts(frappe)
        summary["business_counts_after"] = after
        if cleanup_errors or remaining or before != after:
            summary["result"] = "FAIL"
            summary.setdefault("error", "Cleanup or before/after business count verification failed.")
        frappe.db.rollback()
        frappe.destroy()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return int(summary.get("result") != "PASS")


if __name__ == "__main__":
    sys.exit(main())
