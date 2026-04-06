# Source Server Script: Validación de Duplicidad en Generador de Producto
# Script Type: DocType Event
# Reference DocType: Product Generator
# Event Frequency: All
# Site: igcaribe.fortabs.com

def normalize(value):
    if value is None or value == '':
        return ''
    if isinstance(value, bool):
        return '1' if value else '0'
    if isinstance(value, (int, float)):
        return f"{value:.4f}"
    return str(value).strip().lower()

"""
Cuales campos se contemplan como parte del hash?
Cuales campos no cambian el hash por el orden en que aparezcan? Por ejemplo, si se intercambia el color1 con el color2 deberia de seguir siendo el mismo SKU.

ToDo 1: Identificar las dependencias de los campos para luego limpiar al guardar los campos dependientes. Por ejemplo, si se marca el check require_laminado y el usuario introduce el tipo_de_laminado; si el usuario desmarca nuevamente el check require_laminado el sistema debe limpiar el campo tipo_de_laminado.

ToDo 2: identificar los tipos de los campos para que cuando se limpien se reestablezca a un valor que sea congruente con el tipo de campo.


ToDo 1.9: Hay que hacer un arbol de dependencia para establecer que campos dependen de quien.

PS: No hay ningun NO_VALUE_TYPE con depends_on (ni reqd_depends_on). This is a good thing.

Identificar los campos

own_made - no va
tipo_producto
material
descripcion_material - no va

ancho_producto x alto_producto

item_name - no va
description - no va
item_asociado - no va
naming_series - no va
amended_from - no va

tiro
retiro

requiere_impresion
requiere_laminado
requiere_barnizado
requiere_acabado_especial
requiere_troquelado
requiere_cinta_doble_cara
requiere_pegado

cantidad_tinta_tiro
cantidad_tinta_retiro

tinta_tiro_1
tinta_tiro_2
tinta_tiro_3
tinta_tiro_4
tinta_tiro_5
tinta_tiro_6
tinta_tiro_7
tinta_tiro_8

tinta_tiro_1_color
tinta_tiro_2_color
tinta_tiro_3_color
tinta_tiro_4_color
tinta_tiro_5_color
tinta_tiro_6_color
tinta_tiro_7_color
tinta_tiro_8_color

tinta_retiro_1
tinta_retiro_2
tinta_retiro_3
tinta_retiro_4
tinta_retiro_5
tinta_retiro_6
tinta_retiro_7
tinta_retiro_8

tinta_retiro_1_color
tinta_retiro_2_color
tinta_retiro_3_color
tinta_retiro_4_color
tinta_retiro_5_color
tinta_retiro_6_color
tinta_retiro_7_color
tinta_retiro_8_color

corte
texto_laminado - no va
tipo_de_laminado
texto_barnizado - no va
tipo_de_barnizado
texto_pegado - no va
tipo_de_pegado
acabado_especial
elementos_acabado_especial
foil_color


# ponerlo al derecho y al revez. Es decir, duplicarlo y agregarlo a un set
ancho_elemento_1 x alto_elemento_1
ancho_elemento_2 x alto_elemento_2
ancho_elemento_3 x alto_elemento_3
ancho_elemento_4 x alto_elemento_4
ancho_elemento_5 x alto_elemento_5
ancho_elemento_6 x alto_elemento_6

puntos_cinta_doble_cara
ancho_punto_cinta_doble_cara x alto_punto_cinta_doble_cara

product_hash - no va
"""


def generate_hash(doc):
    out = []

    # mandatory fields
    out.append(
        f"tipo_producto: {doc.tipo_producto}"
    )

    out.append(
        f"material: {doc.material}"
    )

    # "dimension_producto" es un campo que representa el tamaño de un producto
    # sin importar el orden en que se especifiquen las dimensiones.
    # Un Producto que tenga una dimension 17 x 23 es el mismo producto si se especifica
    # 23 x 17

    if doc.ancho_producto > doc.alto_producto:
        out.append(
            f"dimension_producto: {doc.ancho_producto} x {doc.alto_producto}"
        )
    else:
        out.append(
            f"dimension_producto: {doc.alto_producto} x {doc.ancho_producto}"
        )

    out.append(
        f"requiere_impresion: {bool(doc.requiere_impresion)}"
    )

    if doc.requiere_impresion:
        out.append(
            f"tiro: {bool(doc.tiro)}"
        )

        if doc.tiro:
            # eval:doc.tiro && doc.requiere_impresion
            out.append(
                f"cantidad_tinta_tiro: {int(doc.cantidad_tinta_tiro)}"
            )

            if count := int(doc.cantidad_tinta_tiro):
                tintas_tiro = list()
                for index in range(1, count + 1):
                    tintas_tiro.append(
                        f"{doc.get(f'tinta_tiro_{index}', default='')}"
                    )

                out.append(
                    f"tintas_tiro: {', '.join( sorted(tintas_tiro) )}"
                )

        out.append(
            f"retiro: {bool(doc.retiro)}"
        )

        if doc.retiro:
            # eval:doc.retiro && doc.requiere_impresion
            out.append(
                f"cantidad_tinta_retiro: {int(doc.cantidad_tinta_retiro)}"
            )

            if count := int(doc.cantidad_tinta_retiro):
                tintas_retiro = list()
                for index in range(1, count + 1):
                    tintas_retiro.append(
                        f"{doc.get(f'tinta_retiro_{index}', default='')}"
                    )

                out.append(
                    f"tintas_retiro: {', '.join( sorted(tintas_retiro) )}"
                )

    out.append(
        f"requiere_laminado: {bool(doc.requiere_laminado)}"
    )

    if doc.requiere_laminado:
        out.append(
            f"tipo_de_laminado: {str(doc.tipo_de_laminado)}"
        )

    out.append(
        f"requiere_barnizado: {bool(doc.requiere_barnizado)}"
    )

    if doc.requiere_barnizado:
        out.append(
            f"tipo_de_barnizado: {str(doc.tipo_de_barnizado)}"
        )

    out.append(
        f"requiere_acabado_especial: {bool(doc.requiere_acabado_especial)}"
    )

    if doc.requiere_acabado_especial:
        out.append(
            f"acabado_especial: {str(doc.acabado_especial)}"
        )

        out.append(
            f"elementos_acabado_especial: {int(doc.elementos_acabado_especial)}"
        )

        if count := int(doc.elementos_acabado_especial):
            dimensions = set()
            for index in range(1, count + 1):
                if doc.get(f'ancho_elemento_{index}') > doc.get(f'alto_elemento_{index}'):
                    dimensions.add(
                        f"{doc.get(f'ancho_elemento_{index}', default=0)} x {doc.get(f'alto_elemento_{index}', default=0)}"
                    )
                else:
                    dimensions.add(
                        f"{doc.get(f'alto_elemento_{index}', default=0)} x {doc.get(f'ancho_elemento_{index}', default=0)}"
                    )
            out.append(
                f"dimension_elementos_acabado_especial: {', '.join( sorted(dimensions) )}"
            )

        if doc.acabado_especial == "Estampado":
            out.append(
                f"foil_color: {str(doc.foil_color)}"
            )

    out.append(
        f"requiere_troquelado: {bool(doc.requiere_troquelado)}"
    )

    # in theory, this is redundant already, but we keep it for consistency
    out.append(
        f"corte: {doc.corte}"
    )

    out.append(
        f"requiere_cinta_doble_cara: {bool(doc.requiere_cinta_doble_cara)}"
    )

    if doc.requiere_cinta_doble_cara:
        out.append(
            f"puntos_cinta_doble_cara: {int(doc.puntos_cinta_doble_cara)}"
        )

        if doc.ancho_punto_cinta_doble_cara > doc.alto_punto_cinta_doble_cara:
            out.append(
                f"dimension_punto_cinta_doble_cara: {doc.ancho_punto_cinta_doble_cara} x {doc.alto_punto_cinta_doble_cara}"
            )
        else:
            out.append(
                f"dimension_punto_cinta_doble_cara: {doc.alto_punto_cinta_doble_cara} x {doc.ancho_punto_cinta_doble_cara}"
            )

    out.append(
        f"requiere_pegado: {bool(doc.requiere_pegado)}"
    )

    if doc.requiere_pegado:
        out.append(
            f"tipo_de_pegado: {str(doc.tipo_de_pegado)}"
        )

    return " | ".join(
        sorted(out)
    )


doc.product_hash = generate_hash(doc)

# print(doc.product_hash)

if name := frappe.db.exists(doc.doctype, {
    "product_hash": doc.product_hash,
    "name": ["!=", doc.name]
}):
    link = frappe.utils.get_link_to_form(doc.doctype, name, f"{_(doc.doctype)} > {name}")
    frappe.throw(f"[{doc.name}] Ya existe un {_(doc.doctype)} con estas mismas especificaciones... favor verifique el '{link}'")
