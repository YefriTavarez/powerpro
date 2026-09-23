# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    doc.db_set({'status': 'Cancelled', 'active_authorization': None, 'active_weekly_rest': None})

run(doc)
