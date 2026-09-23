# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    settlement = {'currency': doc.currency, 'payroll_date': str(doc.settlement_payroll_date), 'lines': [{'component': 'Horas Nocturnas', 'amount': doc.settlement_amount}]}
    names = doc.create_night_earnings(settlement)
    doc.db_set({'additional_salary': names[0], 'settlement_status': 'Created'})

run(doc)
