"""Daily sequence contracts and opt-in isolated MariaDB concurrency tests.

The database suite creates and drops only its own randomly named database.
Set POWERPRO_SEQUENCE_TEST_ISOLATED=1 and a test SOCKET or HOST to enable it.
Never point this suite at a production database server.
"""

import ast
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import importlib.util
import os
from pathlib import Path
import sys
import threading
import types
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]


def getdate(value):
    return value if isinstance(value, date) else date.fromisoformat(value)


def fail(message):
    raise ValueError(message)


FRAPPE = types.ModuleType("frappe")
FRAPPE._ = lambda message: message
FRAPPE.throw = fail
UTILS = types.ModuleType("frappe.utils")
UTILS.getdate = getdate
SPEC = importlib.util.spec_from_file_location(
    "bank_sequence_under_test", ROOT / "powerpro/payroll_rules/bank_payment_sequence.py"
)
SEQUENCE = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, {"frappe": FRAPPE, "frappe.utils": UTILS}):
    SPEC.loader.exec_module(SEQUENCE)

# Execute the real controller method without importing the full Frappe stack.
source = ast.parse((ROOT / "powerpro/power_pro/doctype/payroll_bank_batch/payroll_bank_batch.py").read_text())
controller = next(node for node in source.body if isinstance(node, ast.ClassDef))
method = next(node for node in controller.body if getattr(node, "name", "") == "_set_payment_sequence")
namespace = {"frappe": FRAPPE, "_": FRAPPE._, "getdate": getdate}
exec(compile(ast.Module(body=[method], type_ignores=[]), "batch_sequence_contract", "exec"), namespace)


class TestSequenceDocumentContract(unittest.TestCase):
    def apply(self, previous=None, payment_date="2026-09-15", sequence=None):
        self.reserve = Mock(return_value="0000008")
        namespace["reserve_payment_sequence"] = self.reserve
        batch = types.SimpleNamespace(
            payment_date=payment_date, payment_sequence=sequence,
            get_doc_before_save=lambda: previous,
        )
        namespace["_set_payment_sequence"](batch)
        return batch

    def previous(self, **changes):
        values = dict(payment_date=date(2026, 9, 15), payment_sequence="0000003", docstatus=0)
        values.update(changes)
        return types.SimpleNamespace(**values)

    def test_new_draft_replaces_client_supplied_sequence(self):
        batch = self.apply(sequence="9999999")
        self.assertEqual(batch.payment_sequence, "0000008")
        self.reserve.assert_called_once_with("2026-09-15")

    def test_resave_retains_number_without_reserving(self):
        batch = self.apply(self.previous(), sequence="0000003")
        self.assertEqual(batch.payment_sequence, "0000003")
        self.reserve.assert_not_called()

    def test_blank_client_value_restores_existing_number(self):
        self.assertEqual(self.apply(self.previous()).payment_sequence, "0000003")
        self.reserve.assert_not_called()

    def test_date_change_reserves_in_new_date(self):
        self.apply(self.previous(), payment_date="2026-09-16", sequence="0000003")
        self.reserve.assert_called_once_with("2026-09-16")

    def test_manual_edits_rejected(self):
        with self.assertRaisesRegex(ValueError, "automatically"):
            self.apply(self.previous(), sequence="0000009")

    def test_approved_date_and_sequence_are_preserved(self):
        previous = self.previous(docstatus=1)
        self.assertEqual(self.apply(previous, sequence="0000003").payment_sequence, "0000003")
        self.reserve.assert_not_called()
        with self.assertRaisesRegex(ValueError, "after approval"):
            self.apply(previous, payment_date="2026-10-01", sequence="0000003")

    def test_missing_date_does_not_reserve(self):
        self.apply(payment_date=None)
        self.reserve.assert_not_called()


class DatabaseAdapter:
    def __init__(self, connection):
        self.connection = connection

    def sql(self, query, values=()):
        with self.connection.cursor() as cursor:
            cursor.execute(query, values)
            return cursor.fetchall()

    def multisql(self, queries, values=()):
        return self.sql(queries["mariadb"], values)


LOCAL = threading.local()


class DatabaseProxy:
    def __getattr__(self, name):
        return getattr(LOCAL.db, name)


@unittest.skipUnless(os.environ.get("POWERPRO_SEQUENCE_TEST_ISOLATED") == "1", "isolated MariaDB opt-in required")
class TestSequenceMariaDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pymysql
        cls.pymysql = pymysql
        cls.options = dict(user="root", password=os.environ.get("POWERPRO_SEQUENCE_TEST_PASSWORD", ""), autocommit=False)
        if socket := os.environ.get("POWERPRO_SEQUENCE_TEST_SOCKET"):
            cls.options["unix_socket"] = socket
        else:
            cls.options["host"] = os.environ["POWERPRO_SEQUENCE_TEST_HOST"]
            cls.options["port"] = int(os.environ.get("POWERPRO_SEQUENCE_TEST_PORT", "3306"))
        cls.database = "powerpro_sequence_test_" + uuid4().hex
        cls.admin = pymysql.connect(**cls.options)
        with cls.admin.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE `{cls.database}`")
        cls.options["database"] = cls.database
        conn = pymysql.connect(**cls.options)
        db = DatabaseAdapter(conn)
        db.sql("CREATE TABLE `tabSeries` (name VARCHAR(140) PRIMARY KEY, current BIGINT NOT NULL) ENGINE=InnoDB")
        db.sql("CREATE TABLE `tabPayroll Bank Batch` (name VARCHAR(140) PRIMARY KEY, payment_date DATE, payment_sequence VARCHAR(140), docstatus INT) ENGINE=InnoDB")
        conn.close()
        FRAPPE.db = DatabaseProxy()

    @classmethod
    def tearDownClass(cls):
        with cls.admin.cursor() as cursor:
            cursor.execute(f"DROP DATABASE `{cls.database}`")
        cls.admin.close()

    def setUp(self):
        self.conn = self.pymysql.connect(**self.options)
        LOCAL.db = DatabaseAdapter(self.conn)
        LOCAL.db.sql("DELETE FROM `tabSeries`")
        LOCAL.db.sql("DELETE FROM `tabPayroll Bank Batch`")
        self.conn.commit()

    def tearDown(self):
        self.conn.rollback()
        self.conn.close()

    def reserve(self, day="2026-09-15"):
        return SEQUENCE.reserve_payment_sequence(day)

    def test_same_date_and_calendar_resets(self):
        self.assertEqual(self.reserve(), "0000001")
        self.assertEqual(self.reserve(), "0000002")
        for day in ("2026-09-16", "2026-10-01", "2027-01-01"):
            self.assertEqual(self.reserve(day), "0000001")
        self.assertEqual(self.reserve(), "0000003")

    def test_existing_cancelled_batch_seeds_counter(self):
        LOCAL.db.sql("INSERT INTO `tabPayroll Bank Batch` VALUES (%s,%s,%s,%s)", ("legacy", "2026-09-15", "0000042", 2))
        self.assertEqual(self.reserve(), "0000043")

    def test_committed_reservation_is_not_reused_when_batch_is_absent(self):
        self.assertEqual(self.reserve(), "0000001")
        self.conn.commit()
        self.assertEqual(self.reserve(), "0000002")

    def test_failed_transaction_rolls_back_reservation(self):
        self.assertEqual(self.reserve(), "0000001")
        self.conn.rollback()
        self.assertEqual(self.reserve(), "0000001")

    def test_sequence_exhaustion_is_blocked(self):
        LOCAL.db.sql("INSERT INTO `tabSeries` VALUES (%s,%s)", (SEQUENCE.SERIES_PREFIX + "2026-09-15", 9999999))
        with self.assertRaisesRegex(ValueError, "exhausted"):
            self.reserve()

    def test_concurrent_first_reservations_are_unique(self):
        barrier = threading.Barrier(8)

        def reserve_and_commit(_):
            conn = self.pymysql.connect(**self.options)
            LOCAL.db = DatabaseAdapter(conn)
            try:
                barrier.wait(timeout=10)
                number = self.reserve()
                conn.commit()
                return number
            finally:
                conn.rollback()
                conn.close()

        with ThreadPoolExecutor(max_workers=8) as pool:
            numbers = list(pool.map(reserve_and_commit, range(8)))
        self.assertEqual(sorted(numbers), [f"{i:07d}" for i in range(1, 9)])


if __name__ == "__main__":
    unittest.main()
