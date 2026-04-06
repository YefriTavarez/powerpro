// Source Client Script: HTML Opciones Tinta Renderizar Campos en Generador de Producto - Form
// Site: igcaribe.fortabs.com

frappe.ui.form.on('Product Generator', {
    refresh(frm) {
        cargar_bootstrap_icons(() => {
            evaluar_y_renderizar_controles(frm);
        });
    },

    requiere_impresion(frm) {
        evaluar_y_renderizar_controles(frm);
    },

    tiro(frm) {
        actualizar_estilos_botones(frm);
    },

    retiro(frm) {
        actualizar_estilos_botones(frm);
    }
});

function cargar_bootstrap_icons(callback) {
    if (document.getElementById("bootstrap-icons-cdn")) {
        callback();
        return;
    }

    const link = document.createElement("link");
    link.id = "bootstrap-icons-cdn";
    link.rel = "stylesheet";
    link.href = "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css";
    document.head.appendChild(link);

    link.onload = () => {
        callback();
    };
}

function evaluar_y_renderizar_controles(frm) {
    if (frm.doc.requiere_impresion) {
        if (!frm.doc.tiro) {
            frm.set_value('tiro', 1);
        }
        render_controles(frm);
    } else {
        frm.fields_dict.opciones_tintas.$wrapper.empty();
        frm.set_value("tiro", 0);
        frm.set_value("retiro", 0);
        frm.set_value("cantidad_tinta_tiro", "");
        frm.set_value("cantidad_tinta_retiro", "");
    }
}

function render_controles(frm) {
    const wrapper = frm.fields_dict.opciones_tintas.$wrapper;
    wrapper.empty();

    const controles = [
        { campo: 'tiro', label: 'Tiro', icono: 'bi-file-fill' },
        { campo: 'retiro', label: 'Retiro', icono: 'bi-union' }
    ];

    const html = `
        <style>
            .toggle-container {
                display: flex;
                gap: 12px;
                margin-top: -5px;
                flex-wrap: wrap;
            }
            .toggle-btn {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 4px 12px;
                font-size: 13px;
                border: 1px solid #ccc;
                border-radius: 4px;
                cursor: pointer;
                background-color: #f8f9fa;
                transition: all 0.2s ease;
            }
            .toggle-btn i {
                font-size: 16px;
            }
            .toggle-btn.active {
                background-color: #0069d9;
                color: #fff;
                border-color: #fff;
                font-weight: 600;
            }
            .toggle-btn.active i {
                color: #eaf1f9;
            }
        </style>
        <div class="toggle-container">
            ${controles.map(c => `
                <div class="toggle-btn" data-campo="${c.campo}" id="btn-${c.campo}">
                    <i class="bi ${c.icono}"></i> ${c.label}
                </div>
            `).join('')}
        </div>
    `;

    wrapper.html(html);

    controles.forEach(({ campo }) => {
        wrapper.find(`#btn-${campo}`).on('click', function () {
            if (campo === 'retiro' && !frm.doc.tiro) {
                frappe.show_alert(`Debes activar "Tiro" antes de activar "Retiro".`, 3);
                return;
            }

            if (campo === 'tiro' && frm.doc.requiere_impresion && frm.doc.tiro) {
                frappe.show_alert(`No puedes desactivar "Tiro" porque el producto requiere impresión.`, 3);
                return;
            }

            const nuevo_estado = !frm.doc[campo];

            if (!nuevo_estado) {
                if (campo === 'tiro') {
                    frm.set_value('cantidad_tinta_tiro', '');
                } else if (campo === 'retiro') {
                    frm.set_value('cantidad_tinta_retiro', '');
                }
            }

            frm.set_value(campo, nuevo_estado);
        });
    });

    actualizar_estilos_botones(frm);
}

function actualizar_estilos_botones(frm) {
    ['tiro', 'retiro'].forEach(campo => {
        const btn = frm.fields_dict.opciones_tintas.$wrapper.find(`#btn-${campo}`);
        if (frm.doc[campo]) {
            btn.addClass('active');
        } else {
            btn.removeClass('active');
        }
    });
}
