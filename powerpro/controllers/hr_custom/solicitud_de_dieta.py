"""Creation uses the existing locked, idempotent dieta service."""
from frappe.model.document import Document


class SolicituddeDieta(Document):
    def validate_new_request(self):
        from powerpro.dietas.service import validate_direct_request
        return validate_direct_request(self)
