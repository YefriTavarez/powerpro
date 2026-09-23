from frappe.model.document import Document


class EmployeeSupplementSettings(Document):
    def validate(self):
        from powerpro.supplements.service import validate_settings
        validate_settings(self)

    def on_update(self):
        from powerpro.supplements.service import seed_history
        seed_history(self)
