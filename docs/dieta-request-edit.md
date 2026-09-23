# Edición de solicitudes de dieta

Una solicitud guardada ofrece **Editar solicitud** para corregir monto y notas.
El solicitante debe conservar su rol de creación y su alcance sobre el empleado;
también puede editar el aprobador asignado o un HR Manager dentro de su alcance.
El empleado beneficiario no puede gestionar su propia solicitud.

Solo se admiten solicitudes Pending / Unpaid, con empleado activo y sin lote de
pago. La identidad, empresa, fecha, moneda, importe por defecto histórico,
aprobación, pago e historial no son campos editables. Los cambios agregan un
evento de auditoría. La API acepta únicamente POST y revalida versión, permisos,
configuración y fuentes vinculadas bajo los mismos bloqueos que el pago.

La escritura genérica de Frappe permanece bloqueada. El formulario deshabilita
Guardar en documentos existentes y utiliza un diálogo con valores recientes del
servidor. En documentos nuevos se conserva la creación normal.

## Alcance del flujo

Las solicitudes vinculadas a una convocatoria continúan por sus diálogos de
gestión y pago. La prueba de integración recorre creación, edición, aprobación
y registro del pago. La vista previa anterior a una edición queda invalidada.

Las solicitudes **sin convocatoria** todavía no tienen acciones independientes
de aprobación y pago. El formulario lo indica expresamente; este arreglo no
inventa una convocatoria ni otorga privilegios de pago al solicitante.

## Despliegue y reversión

Requiere la estructura de HR Custom DocTypes incorporada en PR #73. Frappe 15
omite `doctype_js` para DocTypes personalizados: el diálogo está incluido en el
Client Script versionado `PowerPro HR v1 - Solicitud de Dieta`. Copiar solamente
el módulo Python no actualiza la interfaz. El instalador existente sincroniza
el Client Script durante el despliegue normal y rechaza cambios simultáneos del
propietario y de la versión; no se deben sobrescribir esas personalizaciones.

Una actualización acotada de desarrollo puede sincronizar únicamente ese
Client Script tras comparar su contenido con el código anterior y respaldarlo,
sin modificar permisos, DocTypes, Server Scripts ni documentos de negocio.
Debe invalidarse la caché del DocType y recargarse el navegador después de
conservar cualquier texto todavía no guardado.

Para revertir esa actualización acotada, restaurar juntos el Client Script
respaldado y su archivo fuente, retirar `powerpro/dietas/request_edit.py` si no
existía antes e invalidar la caché de Solicitud de Dieta. Los eventos de auditoría
ya registrados se conservan. No hace falta revertir datos ni asientos.

## Verificación

- `python tests/test_dietas.py`: servicio, permisos, validación, versiones y rollback.
- `node --test tests/test_dietas_ui.cjs tests/test_dieta_request_ui.cjs`: diálogos,
  reintentos, doble clic, navegación y respuestas de interfaz fuera de orden.
- `scripts/test_dietas_dev.py`: suite con Frappe/MariaDB reales, roles y User
  Permissions, Server Scripts, carga del Client Script personalizado y flujo
  vinculado completo. Solo desarrollo; bloquea commits, correo y encolado y
  revierte las fixtures. No es una prueba de carga ni de concurrencia multisesión.

El ensayo de esta corrección pasó 81 pruebas del servicio, 18 de interfaz y 18
de integración en Frappe 15.103.2 / ERPNext 15.102.0. La comparación de 18 tablas
antes/después conservó sus recuentos y hashes de `(name, modified, docstatus)`.
La aprobación/pago independiente sigue siendo trabajo pendiente; estos
resultados no equivalen a una validación en producción.
