from powerpro.dietas.documents import ManagedDietaDocument
from powerpro.dietas.service import validate_direct_request


class SolicituddeDieta(ManagedDietaDocument):
    def validate(self):
        if self.flags.get('dieta_service'):
            return super().validate()
        if self.is_new():
            validate_direct_request(self)
        else:
            super().validate()
