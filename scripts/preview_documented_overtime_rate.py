"""Price an accepted documentary sample without choosing a payroll policy.

Reads private source exports locally. Uses the actual pure cash calculator;
does not connect to Frappe, approve evidence or create payroll documents.
"""
import argparse
import hashlib
import json
import sys
import types
from datetime import datetime, time
from pathlib import Path

if 'powerpro' not in sys.modules:
    package = types.ModuleType('powerpro')
    package.__path__ = [str(Path(__file__).resolve().parents[1] / 'powerpro')]
    sys.modules['powerpro'] = package

from powerpro.payroll_rules.overtime_cash_settlement import calculate_cash_settlement
from powerpro.payroll_rules.overtime_combined_day import cash_kwargs, FIELD, HOURS, SINGLE, ADDITIVE


def preview(salary, plan):
    rows = salary['assignments']
    if len(rows) != 1 or rows[0]['employee'] != plan['employee'] or rows[0]['docstatus'] != 1:
        raise ValueError('One matching submitted source assignment required')
    rate = rows[0]['salary_per_hour']
    scenarios = []
    for window in plan['windows']:
        if window['date'] in plan['excluded_dates'] or window['date'] < rows[0]['from_date']:
            raise ValueError('Excluded or uncovered date')
        # Classification must be supplied from the reviewed DEV calendar; never
        # infer a legal holiday merely from a Saturday/Sunday weekday number.
        classification = window['day_classification']
        hours = window['maximum_hours']
        start, end = (datetime.fromisoformat(window[k]) for k in ('start', 'end'))
        if (start.date() != end.date() or str(start.date()) != window['date']
                or not time(7) <= start.time() < end.time() <= time(21)
                or abs((end-start).total_seconds()/3600 - hours) > .0001):
            raise ValueError('This preview supports only matching daytime documentary windows')
        inputs = []
        if classification == 'Regular Workday':
            for band in (35, 100):
                inputs.append((f'Regular band +{band}%; weekly evidence pending',
                               {f'regular_{band}_hours': hours}))
        elif classification == 'Weekly Rest':
            inputs.append(('Cash election and approved weekly-rest policy required',
                           {'weekly_rest_hours': hours, 'weekly_rest_overtime_percent': 100}))
        elif classification == 'Legal Holiday on Weekly Rest':
            for mode in (SINGLE, ADDITIVE):
                for covered in (0, hours):
                    policy = {FIELD: mode, 'extraordinary_percent': 100, 'weekly_rest_percent': 100}
                    calc = {HOURS: hours, 'holiday_100_hours': hours}
                    inputs.append((f'{mode}; holiday base covered: {covered} hours',
                                   {'holiday_100_hours': hours, 'holiday_base_covered_hours': covered,
                                    **cash_kwargs(policy, calc)}))
        else:
            raise ValueError('Unsupported reviewed classification')
        for label, values in inputs:
            result = calculate_cash_settlement(hourly_rate=rate, **values)
            scenarios.append({'date': window['date'], 'hours': hours, 'classification': classification,
                              'condition': label, 'inputs': values, 'amount': result['total_amount'],
                              'lines': result['lines']})
    return {'employee': plan['employee'], 'currency': rows[0]['currency'], 'hourly_rate': rate,
            'source_assignment': rows[0]['name'], 'approved': False, 'settlement_ready': False,
            'excluded_dates': plan['excluded_dates'], 'scenarios': scenarios,
            'note': 'Conditional calculator outputs, not an employee election, evidence certification or legal determination. No total payable is asserted.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('salary', type=Path); p.add_argument('plan', type=Path)
    args = p.parse_args()
    result = preview(json.loads(args.salary.read_text()), json.loads(args.plan.read_text()))
    result['source_hashes'] = {k: hashlib.sha256(v.read_bytes()).hexdigest()
                               for k, v in [('salary', args.salary), ('plan', args.plan)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
