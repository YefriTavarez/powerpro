# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    doc.cancel_night_earnings()
    doc.db_set('active_claim', None)

run(doc)
