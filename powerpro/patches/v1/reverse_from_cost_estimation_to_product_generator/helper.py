# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import json
import frappe


record_data_sample = """
{
    "alto_material": 8,
    "alto_montaje": 8,
    "alto_producto": 5.5,
    "ancho_material": 8,
    "ancho_montaje": 8,
    "ancho_producto": 7.5,
    "back_colors": "Black,Cyan,Magenta,Yellow",
    "cantidad_de_producto": "1",
    "cantidad_de_tintas_retiro": 4,
    "cantidad_de_tintas_tiro": 4,
    "cantidad_montaje": "1",
    "front_colors": "Black,Cyan,Magenta,Yellow",
    "incluye_pegado": true,
    "incluye_troquelado": false,
    "margen_de_utilidad": 30,
    "material": "CABLMUES12-00003",
    "porcentaje_adicional": 5,
    "tecnologia": "Offset",
    "tipo_de_empaque": "Corrugado",
    "tipo_de_producto": "Volante",
    "tipo_pegado": "Especial",
    "cinta_doble_cara_alto_punto": 1,
    "cinta_doble_cara_ancho_punto": 0.5,
    "cinta_doble_cara_cantidad_de_puntos": 3,
    "hex_tinta_seleccionada_tiro_1": "#00FFFF",
    "hex_tinta_seleccionada_tiro_2": "#FF00FF",
    "hex_tinta_seleccionada_tiro_3": "#FFFF00",
    "hex_tinta_seleccionada_tiro_4": "#000000",
    "incluye_utilidad": true,
    "tinta_seleccionada_tiro_1": "Cyan",
    "tinta_seleccionada_tiro_2": "Magenta",
    "tinta_seleccionada_tiro_3": "Yellow",
    "tinta_seleccionada_tiro_4": "Black",
    "tipo_utilidad": "Cinta Doble Cara",
    "incluye_barnizado": true,
    "incluye_relieve": false,
    "tipo_barnizado": "UV (Brillo)",
    "hex_tinta_seleccionada_tiro_5": "#c9102e",
    "tinta_seleccionada_tiro_5": "Pantone 186",
    "hex_tinta_seleccionada_tiro_6": "#001E60",
    "tinta_seleccionada_tiro_6": "Pantone 2757",
    "troquel_en_inventario": true,
    "hex_tinta_seleccionada_tiro_7": "#63666a",
    "tinta_seleccionada_tiro_7": "Pantone Cool Gray 10",
    "alto_elemento_relieve_1": 7.625,
    "ancho_elemento_relieve_1": 2.625,
    "cantidad_de_elementos_en_relieve": 1,
    "tipo_de_relieve": "Estampado",
    "incluye_laminado": false,
    "tipo_de_material_relieve": "Plateado",
    "tipo_laminado": "Mate",
    "hex_tinta_seleccionada_retiro_1": "#00FFFF",
    "hex_tinta_seleccionada_retiro_2": "#FF00FF",
    "hex_tinta_seleccionada_retiro_3": "#FFFF00",
    "hex_tinta_seleccionada_retiro_4": "#000000",
    "tinta_seleccionada_retiro_1": "Cyan",
    "tinta_seleccionada_retiro_2": "Magenta",
    "tinta_seleccionada_retiro_3": "Yellow",
    "tinta_seleccionada_retiro_4": "Black",
    "hex_tinta_seleccionada_tiro_8": "#63666a",
    "tinta_seleccionada_tiro_8": "Pantone Cool Gray 10",
    "alto_elemento_relieve_2": 2.25,
    "alto_elemento_relieve_3": 0.125,
    "ancho_elemento_relieve_2": 22.125,
    "ancho_elemento_relieve_3": 5.125,
    "hex_tinta_seleccionada_retiro_5": "#63666a",
    "tinta_seleccionada_retiro_5": "Pantone Cool Gray 10"
}
"""



def map_record_to_product_generator(record_data):
    """
    Maps the record data from the external system to Product Generator fields
    """
    from frappe.utils import cint, flt, cstr

    SPECIAL_FINISH_MAP = {
        "Bajo Relieve": "Debosado",
        "Relieve": "Embosado",
        "Estampado": "Estampado",
    }

    # print(f"cantidad_de_tintas_tiro {record_data.get('cantidad_de_tintas_tiro', 0)}")

    mapping = {}
    
    mapping['own_made'] = 1
    # Basic product information
    mapping['tipo_producto'] = record_data.get('tipo_de_producto', '')
    mapping['material'] = record_data.get('material', '')
    
    # Product dimensions
    mapping['ancho_producto'] = record_data.get('ancho_producto', 0)
    mapping['alto_producto'] = record_data.get('alto_producto', 0)
    
    # Printing requirements
    has_front_colors = cint(record_data.get('cantidad_de_tintas_tiro', 0)) > 0

    has_back_colors = cint(record_data.get('cantidad_de_tintas_retiro', 0)) > 0
    
    mapping['requiere_impresion'] = bool(record_data.get('technologia', '') != "No Print")
    mapping['tiro'] = bool(has_front_colors)
    mapping['retiro'] = bool(has_back_colors)
    
    # Ink quantities and colors
    if has_front_colors:
        mapping['cantidad_tinta_tiro'] = cint(record_data.get('cantidad_de_tintas_tiro', 0))
        
        # Map front/tiro inks
        for i in range(1, mapping['cantidad_tinta_tiro'] + 1):
            tinta_key = f'tinta_seleccionada_tiro_{i}'
            color_key = f'hex_tinta_seleccionada_tiro_{i}'
            
            if tinta_key in record_data:
                mapping[f'tinta_tiro_{i}'] = record_data[tinta_key]
                if color_key in record_data:
                    mapping[f'tinta_tiro_{i}_color'] = record_data[color_key]

    if has_back_colors:
        mapping['cantidad_tinta_retiro'] = cint(record_data.get('cantidad_de_tintas_retiro', 0))
        
        # Map back/retiro inks
        for i in range(1, mapping['cantidad_tinta_retiro'] + 1):
            tinta_key = f'tinta_seleccionada_retiro_{i}'
            color_key = f'hex_tinta_seleccionada_retiro_{i}'
            
            if tinta_key in record_data:
                mapping[f'tinta_retiro_{i}'] = record_data[tinta_key]
                if color_key in record_data:
                    mapping[f'tinta_retiro_{i}_color'] = record_data[color_key]
    
    # Laminating
    mapping['requiere_laminado'] = bool(record_data.get('incluye_laminado', 0))
    if mapping['requiere_laminado']:
        mapping['tipo_de_laminado'] = record_data.get('tipo_laminado', '')
    
    # Varnishing
    mapping['requiere_barnizado'] = bool(record_data.get('incluye_barnizado', 0))
    if mapping['requiere_barnizado']:
        mapping['tipo_de_barnizado'] = record_data.get('tipo_barnizado', '')
    
    # Special finishing (relieve/embossing)
    mapping['requiere_acabado_especial'] = bool(record_data.get('incluye_relieve', 0))
    if mapping['requiere_acabado_especial']:
        mapping['acabado_especial'] = SPECIAL_FINISH_MAP.get(record_data.get('tipo_de_relieve', ''), '')
        mapping['elementos_acabado_especial'] = cint(record_data.get('cantidad_de_elementos_en_relieve', 0))
        mapping['foil_color'] = cstr(record_data.get('tipo_de_material_relieve', ''))
        
        # Map element dimensions
        for i in range(1, mapping['elementos_acabado_especial'] + 1):
            ancho_key = f'ancho_elemento_relieve_{i}'
            alto_key = f'alto_elemento_relieve_{i}'
            
            if ancho_key in record_data:
                mapping[f'ancho_elemento_{i}'] = record_data[ancho_key]
            if alto_key in record_data:
                mapping[f'alto_elemento_{i}'] = record_data[alto_key]
    
    # Die cutting
    mapping['requiere_troquelado'] = bool(record_data.get('incluye_troquelado', 0))
    
    # Set cutting type based on troquelado
    if mapping['requiere_troquelado']:
        mapping['corte'] = 'Troquelado'
    else:
        mapping['corte'] = 'Refilado'  # Default to straight cut
    
    # Double-sided tape
    has_cinta = bool(record_data.get('incluye_utilidad'))
    
    mapping['requiere_cinta_doble_cara'] = has_cinta
    if has_cinta:
        mapping['puntos_cinta_doble_cara'] = record_data.get('cinta_doble_cara_cantidad_de_puntos', 0)


        mapping['ancho_punto_cinta_doble_cara'] = flt(record_data.get('cinta_doble_cara_ancho_punto', 0))
        mapping['alto_punto_cinta_doble_cara'] = flt(record_data.get('cinta_doble_cara_alto_punto', 0))
    
    # Gluing
    mapping['requiere_pegado'] = bool(record_data.get('incluye_pegado', 0))
    if mapping['requiere_pegado']:
        mapping['tipo_de_pegado'] = record_data.get('tipo_pegado', '')
    
    # Generate item name and description
    # mapping['item_name'] = generate_item_name(record_data, mapping)
    # mapping['description'] = generate_description(record_data, mapping)
    
    return mapping


def generate_item_name(record_data, mapping):
    """
    Generate a descriptive item name based on the product specifications
    """
    parts = []
    
    # Product type
    if tipo := record_data.get('tipo_de_producto'):
        parts.append(tipo)
    
    # Dimensions
    ancho = record_data.get('ancho_producto', 0)
    alto = record_data.get('alto_producto', 0)
    if ancho and alto:
        parts.append(f"{ancho}x{alto}")
    
    # Printing info
    if mapping.get('requiere_impresion'):
        print_parts = []
        if mapping.get('tiro'):
            print_parts.append(f"Tiro {mapping.get('cantidad_tinta_tiro', 0)}T")
        if mapping.get('retiro'):
            print_parts.append(f"Retiro {mapping.get('cantidad_tinta_retiro', 0)}T")
        if print_parts:
            parts.append(" + ".join(print_parts))
    
    # Special finishes
    finishes = []
    if mapping.get('requiere_laminado'):
        finishes.append(f"Lam. {mapping.get('tipo_de_laminado', '')}")
    if mapping.get('requiere_barnizado'):
        finishes.append(f"Barn. {mapping.get('tipo_de_barnizado', '')}")
    if mapping.get('requiere_acabado_especial'):
        finishes.append(f"{mapping.get('acabado_especial', '')}")
    if mapping.get('requiere_troquelado'):
        finishes.append("Troquelado")
    if mapping.get('requiere_pegado'):
        finishes.append("Pegado")
    
    if finishes:
        parts.append(" + ".join(finishes))
    
    return " - ".join(parts)

def generate_description(record_data, mapping):
    """
    Generate a detailed description of the product
    """
    desc_parts = []
    
    # Basic info
    if tipo := record_data.get('tipo_de_producto'):
        desc_parts.append(f"Tipo: {tipo}")
    
    if material := record_data.get('material'):
        desc_parts.append(f"Material: {material}")
    
    # Dimensions
    ancho = record_data.get('ancho_producto', 0)
    alto = record_data.get('alto_producto', 0)
    if ancho and alto:
        desc_parts.append(f"Dimensiones: {ancho} x {alto}")
    
    # Printing details
    if mapping.get('requiere_impresion'):
        if mapping.get('tiro'):
            front_colors = []
            for i in range(1, mapping.get('cantidad_tinta_tiro', 0) + 1):
                if color := mapping.get(f'tinta_tiro_{i}'):
                    front_colors.append(color)
            if front_colors:
                desc_parts.append(f"Tiro: {', '.join(front_colors)}")
        
        if mapping.get('retiro'):
            back_colors = []
            for i in range(1, mapping.get('cantidad_tinta_retiro', 0) + 1):
                if color := mapping.get(f'tinta_retiro_{i}'):
                    back_colors.append(color)
            if back_colors:
                desc_parts.append(f"Retiro: {', '.join(back_colors)}")
    
    # Finishes
    if mapping.get('requiere_laminado'):
        desc_parts.append(f"Laminado: {mapping.get('tipo_de_laminado', '')}")
    
    if mapping.get('requiere_barnizado'):
        desc_parts.append(f"Barnizado: {mapping.get('tipo_de_barnizado', '')}")
    
    if mapping.get('requiere_acabado_especial'):
        elementos = mapping.get('elementos_acabado_especial', 0)
        acabado = mapping.get('acabado_especial', '')
        foil = mapping.get('foil_color', '')
        desc_parts.append(f"Acabado especial: {acabado} ({elementos} elementos) - {foil}")
    
    if mapping.get('requiere_troquelado'):
        desc_parts.append("Incluye troquelado")
    
    if mapping.get('requiere_cinta_doble_cara'):
        puntos = mapping.get('puntos_cinta_doble_cara', 0)
        desc_parts.append(f"Cinta doble cara: {puntos} puntos")
    
    if mapping.get('requiere_pegado'):
        desc_parts.append(f"Pegado: {mapping.get('tipo_de_pegado', '')}")
    
    return ". ".join(desc_parts)

def create_product_generator_from_record(record_data_json):
    """
    Create a Product Generator document from record data
    """
    record_data = json.loads(record_data_json) if isinstance(record_data_json, str) else record_data_json
    
    # Map the data
    mapped_data = map_record_to_product_generator(record_data)
    
    # Create the document
    doc = frappe.get_doc({
        'doctype': 'Product Generator',
        **mapped_data
    })
    
    # Insert and return
    # doc.db_insert()
    return doc

def execute():
    """
    Main execution function - processes the sample record
    """
    try:
        # Parse the sample data
        record_data = json.loads(record_data_sample)
        
        # Create the Product Generator
        doc = create_product_generator_from_record(record_data)
        
        print(f"Created Product Generator: {doc.name}")
        print(f"Item Name: {doc.item_name}")
        print(f"Description: {doc.description}")
        
        return doc
        
    except Exception as e:
        print(f"Error processing record: {str(e)}")
        frappe.log_error(f"Error in reverse_item_to_product_generator: {str(e)}")
        raise

if __name__ == "__main__":
    execute()