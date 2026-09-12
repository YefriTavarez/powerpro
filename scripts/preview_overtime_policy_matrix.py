"""Print synthetic policy examples from the installed pure calculators.

No Frappe, database, approval, enrollment, payment or leave records are used.
Amounts describe the implemented additive arithmetic, not approved legal scope.
Run from the PowerPro repository: PYTHONPATH=. python scripts/preview_overtime_policy_matrix.py
"""
import json
import sys
import types
from pathlib import Path
# The application initializer installs a Frappe controller hook. Standalone
# examples load the real pure modules without executing that site initializer.
if 'powerpro' not in sys.modules:
    package=types.ModuleType('powerpro')
    package.__path__=[str(Path(__file__).resolve().parents[1]/'powerpro')]
    sys.modules['powerpro']=package
from decimal import Decimal
from datetime import datetime
from powerpro.payroll_rules.overtime_cash_settlement import calculate_cash_settlement
from powerpro.payroll_rules.overtime_pay_policy import classify_night_session


def preview():
    scenarios=[]
    for name,inputs in [
        ('Una hora extra en banda +35%',{'regular_35_hours':1}),
        ('Una hora extra en banda +100%',{'regular_100_hours':1}),
        ('Una hora extra +35% y nocturnidad',{'regular_35_hours':1,'night_hours':1}),
        ('Una hora extra +100% y nocturnidad',{'regular_100_hours':1,'night_hours':1}),
        ('Una hora en feriado',{'holiday_100_hours':1}),
        ('Una hora en feriado y nocturnidad',{'holiday_100_hours':1,'night_hours':1}),
        ('Una hora en descanso semanal, elección efectivo',{'weekly_rest_hours':1,'weekly_rest_overtime_percent':100}),
        ('Una hora en descanso semanal y nocturnidad, elección efectivo',{'weekly_rest_hours':1,'weekly_rest_overtime_percent':100,'night_hours':1}),
    ]:
        result=calculate_cash_settlement(hourly_rate=100,**inputs)
        scenarios.append(dict(case=name,inputs=inputs,additional_amount=result['total_amount'],lines=result['lines']))
    boundaries=[]
    for end in ['2026-09-21T23:59:00','2026-09-22T00:00:00','2026-09-22T00:01:00']:
        for basis in ['Clock overlap','Whole nocturnal session']:
            worked=[dict(start='2026-09-21T18:00:00',end=end)]
            overtime=[dict(start='2026-09-21T20:00:00',end=end)]
            night=classify_night_session(worked,overtime,basis=basis)
            hours=round((datetime.fromisoformat(end)-datetime(2026,9,21,20)).total_seconds()/3600,4)
            extra=calculate_cash_settlement(hourly_rate=100,regular_35_hours=hours,night_hours=night['overtime_premium_hours'])
            ordinary=calculate_cash_settlement(hourly_rate=100,night_hours=night['ordinary_premium_hours'])
            total=Decimal(str(extra['total_amount']))+Decimal(str(ordinary['total_amount']))
            boundaries.append(dict(end=end,basis=basis,classification=night['classification'],
                clock_night_hours=night['clock_night_hours'],ordinary_night_additional=ordinary['total_amount'],
                overtime_additional=extra['total_amount'],combined_additional=float(total)))
    return dict(synthetic=True,approved=False,settlement_ready=False,hourly_rate=100,
        interpretation='Implemented additive-on-base-hour arithmetic only; employee applicability and combined rules require approval.',
        ordinary_base='Ordinary shift base pay is assumed already covered and is not added again in these additional amounts.',
        scenarios=scenarios,night_boundary_comparison=boundaries,
        blocked_cases=['Legal Holiday on Weekly Rest: common evidence builder requires an approved implemented joint rule.'],
        unresolved=['Applicability of either night basis','Holiday/rest concurrent with weekly overtime bands',
            'Which employees and dates follow each working-time regime','Rest election and conversion of continuous rest to native leave days'])


if __name__=='__main__':print(json.dumps(preview(),ensure_ascii=False,indent=2))
