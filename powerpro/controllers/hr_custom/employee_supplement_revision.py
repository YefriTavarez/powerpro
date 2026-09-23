"""Read the unforgeable authority token kept outside the sandbox."""
from frappe.model.document import Document
from powerpro.supplements.service import internal


class EmployeeSupplementRevision(Document):
    def is_internal_revision(self):
        return internal(self)
