import frappe


def execute():
    data = {
        "Gastos de personal": [
            "Sueldos y salarios",
            "Otros gastos de personal"
        ],
        "Gastos por trabajos, suministros y servicios": [
            "Honorarios por servicios profesionales (Personas Morales)",
            "Honorarios por servicios profesionales (Personas Físicas)",
            "Seguridad, mensajería, transporte y otros servicios (Personas Físicas)",
            "Seguridad, mensajería, transporte y otros servicios (Personas Morales)"
        ],
        "Arrendamientos": [
            "De inmuebles (a Personas Físicas)",
            "De inmuebles (a Personas Morales)",
            "Otros arrendamientos"
        ],
        "Gastos de activos fijos": [
            "Reparación",
            "Mantenimiento"
        ],
        "Gastos de representación": [
            "Relaciones públicas",
            "Publicidad",
            "Promociones",
            "Otros gastos de representación"
        ],
        "Gastos financieros": [
            "Por préstamos con bancos",
            "Por préstamos con financieras",
            "Por préstamos con personas físicas",
            "Por préstamos con organismos internacionales",
            "Otros gastos financieros"
        ],
        "Gastos de seguros": [
            "Gastos de seguros"
        ],
        "Gastos por regalías y otros intangibles": [
            "Cesión / uso marca",
            "Transferencia de know-how",
            "Cesión / uso de patente",
            "Otras regalías"
        ]
    }

    for key, values in data.items():
        create_type_of_service_purchased(key)
        for value in values:
            create_detail_type_of_service_purchased(value, key)
            print(f"Created {value} under {key}")


def create_type_of_service_purchased(key):
    doctype = "Type of Service Purchased"

    if frappe.db.exists(doctype, key):
        return

    doc = frappe.new_doc(doctype)
    doc.update({
        "service_purchased": key,
    })
    doc.save()


def create_detail_type_of_service_purchased(key, value):
    doctype = "Details of Service Purchased"

    if frappe.db.exists(doctype, key):
        return

    doc = frappe.new_doc(doctype)
    doc.update({
        "detail_service_purchased": key,
        "service_purchased": value
    })
    doc.save()
