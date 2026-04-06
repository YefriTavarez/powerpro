// Source Client Script: HTML Requiere Opciones en Generador de Producto - Form
// Site: igcaribe.fortabs.com

frappe.ui.form.on('Product Generator', {
    refresh(frm) {
        render_opciones_requiere(frm);
    }
});

function render_opciones_requiere(frm) {
    const opciones = [
        "Impresión",
        "Laminado",
        "Barnizado",
        "Acabado Especial",
        "Troquelado",
        "Cinta Doble Cara",
        "Pegado",
    ];

    const wrapper = frm.fields_dict.html_opciones.$wrapper;
    wrapper.empty();

    let html = /*html*/ `
        <style>
            .opciones-requiere {
                font-family: "Segoe UI", sans-serif;
                margin-bottom: 15px;
            }
            .opciones-requiere h4 {
                font-size: 14px;
                margin-bottom: 10px;
                color: #021e42;
                border-bottom: 1px solid #ccc;
                padding-bottom: 5px;
            }
            .opciones-requiere .proceso-row {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 8px;
                padding: 6px 0;
                border-bottom: 1px dashed #e0e0e0;
            }
            .opciones-requiere .proceso-label {
                flex: 1;
                font-size: 13px;
                color: #333;
            }
            .opciones-requiere .toggle-btn {
                width: 70px;
                height: 25px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                padding: 4px 12px;
                font-size: 16px;
                font-weight: 400;
                border: 1px solid #ccc;
                border-radius: 4px;
                cursor: pointer;
                background-color: #f8f9fa;
                transition: all 0.2s ease;
            }
            .opciones-requiere .toggle-btn.active {
                background-color: #0069d9;
                color: #fff;
                border-color: #fff;
            }
            .opciones-requiere .check {
                font-size: 16px;
                line-height: 1;
                font-weight: 300;
            }
            .opciones-requiere .toggle-btn.active .check {
                color: #ffffff;
            }
            .opciones-requiere .toggle-btn:not(.active) .check {
                color: #000000;
            }
        </style>

        <div class="opciones-requiere">
            <h4>¿Qué procesos requiere este producto?</h4>
            ${opciones.map(proceso => {
                const p = normalizar_proceso(proceso);
                const activo = frm.doc[`requiere_${p}`];
                const contenido = activo
                    ? '<span class="check">✓</span>'
                    : '<span class="check">×</span>';
                return `
                    <div class="proceso-row">
                        <div class="proceso-label">${proceso}</div>
                        <div class="toggle-btn ${activo ? 'active' : ''}" data-proceso="${p}">
                            ${contenido}
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;

    wrapper.html(html);

    wrapper.find('.toggle-btn').on('click', function () {
        const proceso = $(this).data('proceso');
        const fieldname = `requiere_${proceso}`;
        const esta_activo = $(this).hasClass('active');
        const nuevo_estado = !esta_activo;

        $(this).toggleClass('active');
        $(this).html(nuevo_estado
            ? '<span class="check">✓</span>'
            : '<span class="check">×</span>');
        frm.set_value(fieldname, nuevo_estado);

        if (proceso === "impresion" && nuevo_estado) {
            frm.set_value("tiro", 1);
        }
    });
}

// 🔧 Función para convertir “Impresión” → “impresion”
function normalizar_proceso(texto) {
    return texto
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "") // elimina tildes
        .replace(/\s+/g, '_'); // reemplaza espacios por guiones bajos
}
