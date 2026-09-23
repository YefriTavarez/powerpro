"""Atomic history seeding uses employee locks and private authority tokens."""
from frappe.model.document import Document


class EmployeeSupplementSettings(Document):
    def seed_supplement_history(self):
        from powerpro.supplements.service import seed_history
        seed_history(self)
