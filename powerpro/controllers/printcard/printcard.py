# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt


import frappe
from frappe.model import document


class PrintCard(document.Document):
	def on_update(self):
		...

	def before_insert(self):
		...

	def after_insert(self):
		...

	def validate(self):
		frappe.throw("You can't update a PrintCard")

	def after_delete(self):
		...
	
	def on_trash(self):
		frappe.throw("You can't delete a PrintCard")
	

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
