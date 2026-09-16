"""Continuous, equivalent approved policy periods; no database or payroll writes."""
from datetime import timedelta

from powerpro.payroll_rules.overtime import _as_datetime
from powerpro.payroll_rules.overtime_combined_day import FIELD, REST_FIELD, REVIEW
from powerpro.payroll_rules.overtime_pay_policy import FIELDS, VERSION, validate_policy

VERSIONS = 'policy_versions'
METADATA = {'name', 'company', 'valid_from', 'valid_until', 'approval_reference', 'approved_by', 'approved_on'}
RULE_FIELDS = tuple(k for k in FIELDS if k not in METADATA) + (FIELD, REST_FIELD)
TEXT_RULES = {'night_basis', 'premium_combination', 'leave_type', FIELD}
ERROR = 'La ventana debe tener cobertura continua de políticas aprobadas con reglas iguales. Revise vigencias o divida la autorización.'


def _date(value):
    return _as_datetime(str(value)).date()


def rule_signature(policy):
    """Compare every calculation/compensatory rule, including optional defaults."""
    return tuple((policy.get(k) or (REVIEW if k == FIELD else '')) if k in TEXT_RULES
                 else float(policy.get(k) or 0) for k in RULE_FIELDS)


def policy_value(row):
    # Keep the exact old single-version representation and its evidence hash.
    policy = {k: row.get(k) for k in FIELDS}
    if row.get(FIELD) and row[FIELD] != REVIEW:
        policy[FIELD] = row[FIELD]
    if row.get(REST_FIELD):
        policy[REST_FIELD] = int(row[REST_FIELD])
    validate_policy(policy)
    policy['calculator_version'] = VERSION
    return policy


def compose_coverage(rows, company, start, last):
    """Caller supplies only approved revisions, either active or server-pinned.

    `name` remains the first real policy for existing Link fields. Every version
    (with its own original dates/approval) is included in multi-period snapshots.
    The top-level dates describe the combined coverage, not a changed DB record.
    """
    start, last = _date(start), _date(last)
    if not rows or last < start:
        raise ValueError(ERROR)
    ordered = sorted(rows, key=lambda r: (_date(r['valid_from']), r['name']))
    if len({r['name'] for r in ordered}) != len(ordered):
        raise ValueError(ERROR)
    values = [policy_value(r) for r in ordered]
    if any(r['company'] != company or _date(r['valid_until']) < start
           or _date(r['valid_from']) > last for r in ordered):
        raise ValueError(ERROR)
    if _date(ordered[0]['valid_from']) > start or _date(ordered[-1]['valid_until']) < last:
        raise ValueError(ERROR)
    for left, right in zip(ordered, ordered[1:]):
        if (_date(left['valid_until']) + timedelta(days=1) != _date(right['valid_from'])
                or rule_signature(left) != rule_signature(right)):
            raise ValueError(ERROR)
    if len(values) == 1:
        return values[0]
    return {**values[0], 'valid_until': values[-1]['valid_until'], VERSIONS: values}


def policy_names(policy):
    return [p['name'] for p in policy.get(VERSIONS, [policy])]
