from frappe.model.document import Document
from powerpro.supplements.service import protect_revision


class EmployeeSupplementRevision(Document):
    def validate(self):
        protect_revision(self)

    def on_trash(self):
        protect_revision(self)
