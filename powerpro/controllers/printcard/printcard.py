# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt


import frappe
from frappe.model.document import Document

from frappe.desk.form.assign_to import add as assign_to, remove as remove_assignee

from powerpro.controllers.printcard import (
    sign_pdf_with_base64,
    generate_pdf_for_printcard,
)

class PrintCard(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.model.document import Document
        from frappe.types import DF

        acabado_especial: DF.Check
        alto_elemento_relieve_1: DF.Float
        alto_elemento_relieve_2: DF.Float
        alto_elemento_relieve_3: DF.Float
        alto_elemento_relieve_4: DF.Float
        alto_elemento_relieve_5: DF.Float
        alto_total_in: DF.Float
        alto_total_mm: DF.Float
        amended_from: DF.Link | None
        ancho_elemento_relieve_1: DF.Float
        ancho_elemento_relieve_2: DF.Float
        ancho_elemento_relieve_3: DF.Float
        ancho_elemento_relieve_4: DF.Float
        ancho_elemento_relieve_5: DF.Float
        ancho_in: DF.Float
        ancho_mm: DF.Float
        ancho_total_in: DF.Float
        ancho_total_mm: DF.Float
        aprobado: DF.Check
        archivo: DF.Attach
        barnizado: DF.Check
        cantidad_de_elementos_en_relieve: DF.Int
        cantidad_de_tintas_retiro: DF.Int
        cantidad_de_tintas_tiro: DF.Int
        cinta_doble_cara: DF.Check
        cliente: DF.Link
        codigo: DF.Data | None
        codigo_arte: DF.Link
        codigo_barra: DF.Check
        corte: DF.Literal["Refilado", "Troquelado"]
        dimension_sku: DF.Data
        dimensiones_empaque_cerrada: DF.Check
        direccion_hilo: DF.Literal["", "No Especificada", "Lado Corto", "Lado Largo"]
        especificaciones: DF.Text | None
        estado: DF.Literal["Borrador", "Pendiente", "Aprobado", "Rechazado", "Reemplazado"]
        laminado: DF.Check
        largo_in: DF.Float
        largo_mm: DF.Float
        material: DF.Link
        no_codigo_barra: DF.Int
        nombre_arte: DF.Data
        pegado: DF.Check
        printcard_file: DF.Attach | None
        printcard_file_signed: DF.Attach | None
        producto: DF.Link
        profundidad_in: DF.Float
        profundidad_mm: DF.Float
        proyecto: DF.Link | None
        puntos_cinta_doble_cara: DF.Literal["1", "2", "3", "4", "5", "6", "7", "8", "9"]
        qr: DF.Check
        razon_rechazo: DF.SmallText | None
        status: DF.Data | None
        tamano_cinta_doble_cara: DF.Data | None
        tinta_seleccionada_retiro_1: DF.Data | None
        tinta_seleccionada_retiro_2: DF.Data | None
        tinta_seleccionada_retiro_3: DF.Data | None
        tinta_seleccionada_retiro_4: DF.Data | None
        tinta_seleccionada_retiro_5: DF.Data | None
        tinta_seleccionada_retiro_6: DF.Data | None
        tinta_seleccionada_retiro_7: DF.Data | None
        tinta_seleccionada_retiro_8: DF.Data | None
        tinta_seleccionada_tiro_1: DF.Data | None
        tinta_seleccionada_tiro_2: DF.Data | None
        tinta_seleccionada_tiro_3: DF.Data | None
        tinta_seleccionada_tiro_4: DF.Data | None
        tinta_seleccionada_tiro_5: DF.Data | None
        tinta_seleccionada_tiro_6: DF.Data | None
        tinta_seleccionada_tiro_7: DF.Data | None
        tinta_seleccionada_tiro_8: DF.Data | None
        tipo_acabado: DF.Literal["", "Relieve", "Bajo Relieve", "Estampado"]
        tipo_barnizado: DF.Literal["", "Base Aceite (Brillo)", "Base Aceite (Mate)", "Base Aceite Combinado (Brillo/Mate)", "Base Agua (Acuoso)", "UV (Brillo)", "UV (Mate)", "UV Combinado (Brillo/Mate)", "UV Selectivo (Brillo)", "UV Selectivo (Mate)"]
        tipo_de_material_relieve: DF.Data | None
        tipo_impresion: DF.Literal["", "Digital", "Offset"]
        tipo_laminado: DF.Literal["", "Brillo", "Mate", "Soft-Touch"]
        tipo_pegado: DF.Literal["", "Cuatro (4) Puntos", "Especial", "Fondo Autom\u00e1tico", "Lineal", "Seis (6) Puntos"]
        tipo_producto: DF.Link
        usuario_cliente_aprobaciones: DF.Link | None
        usuarios_asignados: DF.TableMultiSelect[Document]
        version: DF.Int
        version_arte_cliente: DF.Int
        version_arte_interna: DF.Int
    # end: auto-generated types
    def before_insert(self):
        self.set_version()

    def before_save(self):
        self.update_arte_status()
        self.update_arte_fields()
        self.update_arte_changes()
        self.save_arte()
    
    def on_update(self):
        self.sign_pdf_if_approved()
        self.check_for_changes_on_usuarios_asignados()

    def after_insert(self):
        self.update_change_log()
        self.save_arte()
    
    def on_trash(self):
        self.revert_art_on_printcard_trash()

    def set_version(self):
        query = f"""
            Select Max(version)
            From `tabPrintCard`
            Where codigo_arte={self.codigo_arte!r}
            And version_arte_interna = {self.version_arte_interna}
        """

        result = frappe.db.sql(query)

        self.version = result[0][0] or 0

        if not frappe.utils.cint(self.version):
            self.version = 0

        # ensure an integer value
        version = frappe.utils.cint(self.version)

        self.version = version + 1

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
            # arte.archivo_actual = ""

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

                
                # estado = frappe.db.get_value("PrintCard", {
                #     "codigo_arte": self.codigo_arte,
                #     "version": arte.version_actual
                # }, "estado") or "Pendiente"

                arte.estado = arte.estado if arte.estado not in {"Reemplazado"} else "Pendiente"
                # arte.ultima_version_aprobada = frappe.db.get_value("PrintCard", {
                #     "codigo_arte": self.codigo_arte,
                #     "estado": "Aprobado",
                #     "name": ["!=", self.name]
                # }, "Max(version)") or 0

                res = frappe.db.sql(f"""
                    Select
                        Max(
                            Concat_Ws(
                                ".",
                                IfNull(version_arte_interna, 0),
                                IfNull(version, 0)
                            )
                        ) As version
                    From
                        `tabPrintCard`
                    Where
                        codigo_arte = {self.codigo_arte!r}
                        And name != {self.name!r}
                        And estado = 'Aprobado'
                """)

                if res:
                    arte.ultima_version_aprobada = res[0][0]

                # Fetch the second latest PrintCard
                second_latest_printcard = frappe.db.sql("""
                    SELECT name, estado
                    FROM `tabPrintCard`
                    WHERE codigo_arte = %s
                    AND name != %s
                    ORDER BY version_arte_interna DESC, version DESC
                    LIMIT 1 OFFSET 1
                """, (self.codigo_arte, self.name), as_dict=True)

                if second_latest_printcard:
                    second_latest_name = second_latest_printcard[0].get("name")
                    second_latest_estado = second_latest_printcard[0].get("estado")

                    # Handle the "Reemplazado" state
                    if second_latest_estado == "Reemplazado":
                        arte.estado = "Aprobado"
                        arte.ultima_version_aprobada = frappe.db.get_value(
                            "PrintCard",
                            {"name": second_latest_name},
                            "version_arte_interna"
                        )
                        arte.archivo_printcard_aprobado = frappe.db.get_value(
                            "PrintCard",
                            {"name": second_latest_name},
                            "archivo"
                        )
                        arte.producto_aprobado = frappe.db.get_value(
                            "PrintCard",
                            {"name": second_latest_name},
                            "producto"
                        )
                        arte.versión_interna_del_aprobada = frappe.db.get_value(
                            "PrintCard",
                            {"name": second_latest_name},
                            "version_arte_cliente"
                        )

                        
                        frappe.db.set_value("PrintCard", second_latest_name, "estado", "Aprobado")

                    # Update the "Last Submitted Info Section"
                    arte.version_actual = frappe.db.get_value(
                        "PrintCard",
                        {"name": second_latest_name},
                        "version"
                    )
                    arte.archivo_actual = frappe.db.get_value(
                        "PrintCard",
                        {"name": second_latest_name},
                        "archivo"
                    )
                    arte.estado = second_latest_estado

                arte.flags.ignore_permissions = True
                arte.flags.ignore_mandatory = True
                arte.save()

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

    def check_for_changes_on_usuarios_asignados(self):
        # we need to compare the current state of the list usuarios_asignados with the previous state
        # to determine if we need to update the arte. We add as Assignees the users that are not in the previous state
        # and remove the users that are not in the current state.
        db_doc = self.get_doc_before_save()

        if not db_doc:
            return

        current_users = {d.user for d in self.usuarios_asignados}
        previous_users = {d.user for d in db_doc.usuarios_asignados}

        users_to_add = current_users - previous_users

        for user in users_to_add:
            self.add_assignee_to_arte(user)

        users_to_remove = previous_users - current_users

        for user in users_to_remove:
            self.remove_assignee_from_arte(user)

    def add_assignee_to_arte(self, user: str):
        if not frappe.flags.in_install:
            frappe.flags.in_install = True
                
            assign_to(
                {
                    "assign_to": [user],
                    "doctype": self.doctype,
                    "name": self.name,
                    "description": f"PrintCard #{self.name} has been assigned to you.",
                },
                ignore_permissions=True,
            )

            frappe.flags.in_install = False

    def remove_assignee_from_arte(self, user: str):
        # remove_assignee(
        #     {
        #         "assign_to": [user],
        #         "doctype": self.doctype,
        #         "name": self.name,
        #     },
        #     ignore_permissions=True,
        # )

        if not frappe.flags.in_install:
            frappe.flags.in_install = True

            remove_assignee(
                self.doctype,
                self.name,
                user,
                ignore_permissions=True,
            )

            frappe.flags.in_install = False

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
                        IfNull(version_arte_interna, 0),
                        IfNull(version, 0)
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

    def update_arte_fields(self):
        if not self.is_latest_version():
            return # don't update the arte if it's not the latest version

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
