# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt


import frappe
from frappe.model.document import Document

from powerpro.controllers.printcard import generate_pdf_for_printcard

class PrintCard(Document):
    def before_save(self):
        self.update_arte_status()
        self.update_arte_fields()
        self.update_arte_changes()
        self.save_arte()

    def _get_arte(self):
        if not hasattr(self, "_arte"):
            _arte = frappe.get_doc("Arte", self.codigo_arte)
            setattr(self, "_arte", _arte)
        
        return getattr(self, "_arte")
    

    @frappe.whitelist()
    def get_lastest_version_of_printcard(self, related_arte: str) -> str:
        """
        Retrieves the latest version of a print card related to a specific arte.

        Args:
            related_arte (str): The identifier of the related arte.

        Returns:
            str: The latest version of the print card in the format "version.version_arte_interna".
                 If no version is found, returns "0.0".
        """
        result = frappe.db.sql(
            f"""
            Select
                Max(
                    Concat_Ws(
                        ".",
                        IfNull(version, 0),
                        IfNull(version_arte_interna, 0)
                    )
                ) As version
            From
                `tabPrintCard`
            Where
                codigo_arte = {related_arte!r}
            """
        )

        if result:
            return result[0][0]

        return "0.0"

    def is_latest_version(self):
        return self.get_lastest_version_of_printcard(self.codigo_arte) == f"{self.version}.{self.version_arte_interna}"

    def mark_as_replaced_previous_printcards(self):
        if self.estado == "Aprobado":
            for name in frappe.get_all("PrintCard", {
                "codigo_arte": self.codigo_arte,
                "estado": [
                    "not in", ["Reemplazado", "Rechazado"],
                ],
                "name": ["!=", self.name],
            }, pluck="name"):
                frappe.db.set_value("PrintCard", name, "estado", "Reemplazado")

    def update_arte_status(self):
        arte = self._get_arte()

        # # Actualizar el estado del Arte si el estado del PrintCard cambia a "Pendiente"
        # if self.estado == "Pendiente":
        #     arte.estado = "Pendiente"
        #     arte.flags.ignore_permissions = True
        #     arte.flags.ignore_mandatory = True
        #     arte.save()

        # Si estamos en la última versión, aplicar lógica existente
        if self.is_latest_version():
            arte.estado = self.estado

            # these fields are only to display the latest info on the approved version
            # in other words, this set of fields are only for the approved version.
            if self.estado == "Aprobado":
                arte.ultima_version_aprobada = self.version_arte_interna
                arte.producto_aprobado = self.producto
                arte.estado_últ_aprobada = self.estado
                arte.versión_interna_del_aprobada = arte.versión_del_cliente

            self.mark_as_replaced_previous_printcards()

            # frappe.msgprint(f"El Arte {arte.name} ha sido actualizada satisfactoriamente.", alert=True)

            db_doc = self.get_doc_before_save()

            if db_doc and db_doc.estado != self.estado:
                # Actualizar tipo de cambio en el Arte
                if self.estado == "Aprobado":
                    for row in arte.cambios:
                        if row.numero_version == self.version_arte_interna \
                            and row.tipo_de_cambio in ("Nueva Versión Pendiente", "Pendiente de Crear PrintCard"):
                            row.tipo_de_cambio = "PrintCard Aprobado"
                            row.db_update()
                            break
                    else:
                        if not arte.cambios:
                            arte.cambios = []

                        size = len(arte.cambios)

                        reversed_arr = []
                        for _ in arte.cambios:
                            reversed_arr.append(None)

                        if arte.cambios:
                            for index, value in enumerate(arte.cambios, start=1):
                                reversed_arr[size - index] = value

                            for row in reversed_arr:
                                if row.printcard == self.name:
                                    row.tipo_de_cambio = "PrintCard Aprobado"
                                    row.db_update()
                                    break

                    # arte.db_set("estado", "Aprobado")
                elif self.estado == "Rechazado":
                    # Revertir a la versión previa si está rechazada
                    # ultima_version_aprobada = frappe.db.get_value("PrintCard", {
                    #     "codigo_arte": self.codigo_arte,
                    #     "estado": "Aprobado",
                    # }, "Max(version)") or 0
                    # arte.db_set("ultima_version_aprobada", ultima_version_aprobada)

                    # Update the status of the changes
                    for row in arte.cambios:
                        if row.printcard == self.name:
                            row.tipo_de_cambio = "PrintCard Rechazado"
                            row.db_update()
                            break

                    for row in arte.cambios:
                        if row.numero_version == frappe.utils.cint(self.version) - 1:
                            row.tipo_de_cambio = "PrintCard Aprobado"
                            row.db_update()
                            break

                    # arte.db_set("estado", "Rechazado")
                if self.estado not in {"Borrador",}:
                # if it's the latest version, the status of the arte should be the same as the printcard
                    arte.db_set("estado", self.estado)

    def update_arte_fields(self):
        arte = self._get_arte()

        # Verificar y actualizar el campo "producto" si hay cambios
        if self.get_doc_before_save().producto != self.producto:
            arte.producto = self.producto

        # Verificar y actualizar el campo "archivo_actual" si hay cambios en "archivo"
        if self.get_doc_before_save().archivo != self.archivo:
            arte.archivo_actual = self.archivo

        # Verificar y actualizar el campo "versión_del_cliente" si hay cambios en "version_arte_cliente"
        if self.get_doc_before_save().version_arte_cliente != self.version_arte_cliente:
            arte.versión_del_cliente = self.version_arte_cliente

    def update_arte_changes(self):
        arte = self._get_arte()

        db_doc = self.get_doc_before_save()

        # PrintCard has been submitted for Approval (from Draft)
        # at this point we should generate the PDF for the PrintCard
        if db_doc.estado == "Borrador" and self.estado == "Pendiente":
            pdf_path = generate_pdf_for_printcard(printcard=self.name, pdf_path=True)

            if pdf_path:
                self.printcard_file = pdf_path

                frappe.msgprint(
                    f"El archivo PDF del PrintCard ha sido generado satisfactoriamente.",
                    alert=True,
                )

        # Handle the "Rechazado" state
        if self.estado == "Rechazado":
            arte.estado = "Rechazado"
            arte.save()

        # ToDo: double check why this is necessary
        if codigo := frappe.db.get_value("Producto del Cliente", {
            "nombre_arte": self.nombre_arte,
        }, ["codigo"]):
            self.codigo = codigo

    def save_arte(self):
        arte = self._get_arte()
        arte.flags.ignore_permissions = True
        arte.flags.ignore_mandatory = True
        arte.save()


    printcard_file_signed: str
    printcard_file: str
    cliente: str
    producto: str
    tipo_producto: str
    nombre_arte: str
    archivo: str
    codigo_arte: str
    proyecto: str
    codigo: str
    estado: str
    status: str
    version_arte_interna: int
    version_arte_cliente: int
    version: int
    material: str
    corte: str
    direccion_hilo: str
    tipo_impresion: str
    dimensiones_empaque_cerrada: bool
    dimension_sku: str
    ancho_total_mm: float
    ancho_total_in: float
    alto_total_mm: float
    alto_total_in: float
    largo_mm: float
    largo_in: float
    ancho_mm: float
    ancho_in: float
    profundidad_mm: float
    profundidad_in: float
    cantidad_de_tintas_tiro: int
    tinta_seleccionada_tiro_1: str
    tinta_seleccionada_tiro_2: str
    tinta_seleccionada_tiro_3: str
    tinta_seleccionada_tiro_4: str
    tinta_seleccionada_tiro_5: str
    tinta_seleccionada_tiro_6: str
    tinta_seleccionada_tiro_7: str
    tinta_seleccionada_tiro_8: str
    cantidad_de_tintas_retiro: int
    tinta_seleccionada_retiro_1: str
    tinta_seleccionada_retiro_2: str
    tinta_seleccionada_retiro_3: str
    tinta_seleccionada_retiro_4: str
    tinta_seleccionada_retiro_5: str
    tinta_seleccionada_retiro_6: str
    tinta_seleccionada_retiro_7: str
    tinta_seleccionada_retiro_8: str
    pegado: bool
    tipo_pegado: str
    cinta_doble_cara: bool
    puntos_cinta_doble_cara: str
    tamano_cinta_doble_cara: str
    laminado: bool
    tipo_laminado: str
    barnizado: bool
    tipo_barnizado: str
    acabado_especial: bool
    tipo_acabado: str
    tipo_de_material_relieve: str
    cantidad_de_elementos_en_relieve: int
    ancho_elemento_relieve_1: float
    ancho_elemento_relieve_2: float
    ancho_elemento_relieve_3: float
    ancho_elemento_relieve_4: float
    ancho_elemento_relieve_5: float
    alto_elemento_relieve_1: float
    alto_elemento_relieve_2: float
    alto_elemento_relieve_3: float
    alto_elemento_relieve_4: float
    alto_elemento_relieve_5: float
    codigo_barra: bool
    no_codigo_barra: int
    qr: bool
    especificaciones: str
    firma_cliente: str
    razon_rechazo: str
    aprobado: bool
