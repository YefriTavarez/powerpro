# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt


import frappe
from frappe.model.document import Document

from powerpro.controllers.printcard import (
    sign_pdf_with_base64,
    generate_pdf_for_printcard,
)

class PrintCard(Document):
    def before_save(self):
        self.update_arte_status()
        self.update_arte_fields()
        self.update_arte_changes()
        self.save_arte()
    
    def on_update(self):
        self.sign_pdf_if_approved()

    def after_insert(self):
        self.update_change_log()
        self.save_arte()
    
    def on_trash(self):
        self.revert_art_on_printcard_trash()

    def revert_art_on_printcard_trash(self):
        """
        Deletes a PrintCard and updates related fields based on its status.

        This function ensures that when a PrintCard is deleted, the system maintains consistency
        by updating the necessary information in the "Approved Info Section" and 
        "Last Submitted Info Section". The behavior depends on the status of the PrintCard being deleted.

        **Step-by-step logic:**

        1. **Fetch the PrintCard by ID** to determine its current status and position in the sequence.
        
        2. **Check if it's the last submitted PrintCard (most recent one):**
        - If yes, further processing is required.
        - If no, deletion has no impact, and we can exit early.

        3. **Handle deletion based on the status of the PrintCard:**

        - **Case: "Approved" (Last Submitted)**
            1. Retrieve the second latest PrintCard.
            2. If the second latest PrintCard is in "Replaced" status:
                - Revert it back to "Approved".
                - Update the "Approved Info Section" accordingly.
            3. Update the "Last Submitted Info Section" to reflect the second latest PrintCard.

        - **Case: "Rejected" (Last Submitted)**
            1. Only update the "Last Submitted Info Section" to reflect the second latest PrintCard.
            2. No updates needed for "Approved Info Section".

        - **Case: "Pending" (Last Submitted)**
            1. Only update the "Last Submitted Info Section" to reflect the second latest PrintCard.
            2. No updates needed for "Approved Info Section".

        4. **Handle special cases:**
        - If this was the **only PrintCard** in the system, clear the "Last Submitted Info Section".
        - If the user **deleted the second latest and last PrintCard in sequence**, the third last PrintCard 
            will not be reverted, leading to a skipped state. This is expected behavior.

        5. **Perform the deletion operation** and commit changes.

        **Edge Cases Considered:**
        - Deleting a non-latest PrintCard has no effect.
        - Deleting the only existing PrintCard clears the submission sections.
        - The system does not attempt to recover from user-induced inconsistencies when multiple records are deleted.
        """

        count = frappe.db.count("PrintCard", {
            "codigo_arte": self.codigo_arte,
        })

        arte = self._get_arte()

        if count == 1: # if it's the last PrintCard
            # Si es el único PrintCard y se elimina, actualizar el estado a "PrintCard por Crear"
            #
            # Last Submitted Info Section
            arte.estado = "PrintCard por Crear"
            # arte.estado = ""
            # arte.version_actual = ""
            # arte.versión_del_cliente = ""
            # arte.producto = ""
            arte.archivo_actual = ""

            # Last Approved Info Section
            arte.version_actual = None
            arte.estado_últ_aprobada = None
            arte.ultima_version_aprobada = None
            arte.archivo_printcard_aprobado = None
            arte.versión_interna_del_aprobada = None
            arte.producto_aprobado = None
        else:
            # Si no es el único PrintCard y es la última versión, aplicar lógica existente
            if self.is_latest_version():
                arte.archivo_printcard_aprobado = None

                # If the PrintCard being deleted is in Approved state, then...

                # here's some facts. You can't have a newer PrintCard unless you have one that is approved
                # or rejected. When there is a new PrintCard, the previous one is marked as "Reemplazado" only
                # if they're approved. If they're rejected, it will stay as "Rejected"....
                #
                # So, if the last PrintCard is deleted, the second lastest PrintCard should in one of the following
                # states: "Replaced" or "Rejected". If it's "Replaced", the sets of fields for the Approved printcard should be
                # updated accodingly and the set of fields above this set (the one for the last submitted printcard).
                # If it's "Rejected", the set of fields for the last submitted printcard should be updated accordingly.
                # get the state of the second latest printcard and revert 

                
                estado = frappe.db.get_value("PrintCard", {
                    "codigo_arte": self.codigo_arte,
                    "version": arte.version_actual
                }, "estado") or "Pendiente"

                arte.estado = arte.estado if arte.estado not in {"Reemplazado"} else "Pendiente"
                arte.ultima_version_aprobada = frappe.db.get_value("PrintCard", {
                    "codigo_arte": self.codigo_arte,
                    "estado": "Aprobado",
                    "name": ["!=", self.name]
                }, "Max(version)") or 0

                arte.flags.ignore_permissions = True
                arte.flags.ignore_mandatory = True

        # Guardar los cambios en Arte
        arte.flags.ignore_version_validations = True
        arte.save()

        # Desvincular el PrintCard del Arte para que pueda ser eliminado
        for row in arte.cambios:
            if row.printcard == self.name:
                row.printcard = None
                row.tipo_de_cambio = "PrintCard Eliminado"
                frappe.msgprint(f"Fila #{row.idx} desconectada en la tabla de 'Cambios' en el DocType 'Arte'")
                row.db_update()
        else:
            # Si no hay registros relacionados, mostrar alerta
            frappe.msgprint("No se encontró ningún registro asociado en la Tabla de Cambios del Arte", alert=True)

        # Validar y actualizar estado según condiciones adicionales
        if self.is_latest_version():
            arte.archivo_printcard_aprobado = None

            # Validar que arte.version_actual sea mayor a 1 antes de restar
            if frappe.utils.cint(arte.version_actual) > 1:
                arte.version_actual = frappe.utils.cint(arte.version_actual) - 1
            else:
                arte.version_actual = 1  # Garantizar que nunca sea menor a 1

            estado = frappe.db.get_value("PrintCard", {
                "codigo_arte": self.codigo_arte,
                "version": arte.version_actual
            }, "estado") or "Pendiente"

            arte.estado = arte.estado if arte.estado not in {"Reemplazado"} else "Pendiente"
            arte.ultima_version_aprobada = frappe.db.get_value("PrintCard", {
                "codigo_arte": self.codigo_arte,
                "estado": "Aprobado",
                "name": ["!=", self.name]
            }, "Max(version)") or 0

            arte.flags.ignore_permissions = True
            arte.flags.ignore_mandatory = True
            arte.save()

            # Desvincula el PrintCard del Arte para que pueda ser eliminado
            for row in arte.cambios:
                if row.printcard == self.name:
                    row.printcard = None
                    row.tipo_de_cambio = "PrintCard Eliminado"
                    frappe.msgprint(f"Fila #{row.idx} desconectada en la tabla de 'Cambios' en el DocType 'Arte'")
                    row.db_update()
            else:
                frappe.msgprint("No se encontró ningún registro asociado en la Tabla de Cambios del Arte", alert=True)


    def update_change_log(self):
        arte = self._get_arte()

        # cambios_reversed = cambios.reversed()

        # link the printcard with the correct version log in the 'cambios' table
        for row in arte.cambios:
            if row.numero_version == self.version_arte_interna \
                and row.tipo_de_cambio in {"Nueva Versión Pendiente", "Pendiente de Crear PrintCard"}:
                row.printcard = self.name
                row.db_update()
                
                break
        else:
            arte.append("cambios", {
                "arte": self.codigo_arte,
                "printcard": self.name,
                "tipo_de_cambio": "PrintCard Sometido",
                "numero_version": self.version_arte_interna,
                "version_del_cliente": self.version_arte_cliente,
                "notas": "Generado Automaticamente",
                "fecha": frappe.utils.today(),
                "archivo_link": frappe.utils.get_url(self.archivo),
            })

        arte.estado = "Borrador"
        arte.archivo_actual = self.archivo

    def sign_pdf_if_approved(self):
        db_doc = self.get_doc_before_save()

        if not db_doc:
            return # Nothing to do here

        if db_doc.estado != "Aprobado" and self.estado == "Aprobado":
            sign_pdf_with_base64(printcard_id=self.name)

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

        db_doc = self.get_doc_before_save()

        if not db_doc:
            return # Nothing to do here

        # Verificar y actualizar el campo "producto" si hay cambios
        if db_doc.producto != self.producto:
            arte.producto = self.producto

        # Verificar y actualizar el campo "archivo_actual" si hay cambios en "archivo"
        if db_doc.archivo != self.archivo:
            arte.archivo_actual = self.archivo

        # Verificar y actualizar el campo "versión_del_cliente" si hay cambios en "version_arte_cliente"
        if db_doc.version_arte_cliente != self.version_arte_cliente:
            arte.versión_del_cliente = self.version_arte_cliente

    def update_arte_changes(self):
        arte = self._get_arte()

        db_doc = self.get_doc_before_save()

        if not db_doc:
            return # Nothing to do here

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
