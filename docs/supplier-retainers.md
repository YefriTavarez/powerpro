# Igualas de proveedores

## Alcance

PowerPro prepara compras periódicas a partir de acuerdos con proveedores. No exige crear Employee, Salary Structure ni Salary Structure Assignment y no cambia Payroll Entry. La factura resultante continúa por la revisión, validación fiscal y pago habituales de ERPNext y las aplicaciones instaladas.

El flujo crea **facturas de compra en borrador**. Validar la liquidación no valida esas facturas ni constituye un pago o una instrucción para emitir comprobantes fiscales.

El espacio de trabajo **Igualas** reúne accesos a acuerdos, liquidaciones y configuración de PowerPro. Está disponible para Accounts User, Accounts Manager y System Manager; cada documento conserva sus propios permisos de acceso.

## Documentos

### Acuerdo de iguala — Supplier Retainer Agreement

Cada acuerdo pertenece a una empresa y un proveedor. Contiene un servicio de compra no inventariable, descripción, moneda, honorario bruto por período, periodicidad, vigencia, cuenta de gasto, centro de costo y plantilla **Purchase Taxes and Charges Template**.

- **Monthly:** mes calendario completo.
- **Bimonthly:** quincenas calendario, del 1 al 15 y del 16 al último día del mes. No significa cada dos meses.
- El honorario es el importe **bruto de cada período**, antes de impuestos y retenciones.
- No se aplica prorrateo automático. Un período parcial no debe facturarse como completo por omisión.
- La clasificación fiscal del proveedor y la plantilla aplicable deben revisarse; cobrar por iguala no define por sí solo el tipo de comprobante.

Los usuarios de Contabilidad pueden preparar acuerdos en borrador. Accounts Manager y System Manager pueden validarlos. Tras validar, las condiciones quedan protegidas. Esos responsables pueden cambiar la selección de plantilla; el cambio se registra en el historial y se utiliza para nuevas facturas, sin recalcular las anteriores.

### Liquidación de igualas — Supplier Retainer Batch

La liquidación selecciona empresa, moneda, periodicidad y una fecha dentro del período. Puede filtrar por proveedor. La fecha de contabilización determina la fecha de las facturas, independientemente del período del servicio.

1. Completar los filtros y pulsar **Acciones > Cargar acuerdos**. El formulario guarda el borrador y carga los acuerdos desde el servidor.
2. Revisar los importes y las plantillas que aparecen en las filas. Quitar los acuerdos que no se desean procesar.
3. Corregir condiciones en el acuerdo de origen y volver a cargar cuando corresponda. Los datos copiados de origen no se editan en la tabla.
4. Validar la liquidación como responsable de Contabilidad. Se genera una factura de compra en borrador por acuerdo y período.
5. Abrir cada factura desde su fila y continuar la revisión de compras.

Cambiar los filtros descarta la selección para que no se procesen filas de otro período. Volver a cargar reemplaza la selección actual y requiere volver a quitar las filas no deseadas.

La generación es atómica: si una factura falla, se revierte el intento completo; no queda una liquidación parcialmente generada.

## Impuestos y retenciones

La plantilla se selecciona en el acuerdo y se copia a la factura con sus filas de impuestos. El módulo no fija porcentajes fiscales en código.

Power-Pro Settings incorpora **Exigir plantilla de impuestos en facturas de igualas**, desactivado por defecto:

- **Desactivado:** la plantilla del acuerdo sirve como valor inicial; Contabilidad puede cambiarla en la factura en borrador durante su revisión.
- **Activado:** la factura debe conservar la selección de plantilla que tenía al generarse. Se compara con la selección guardada en esa factura, no con la plantilla actual del acuerdo.

Cambiar la plantilla del acuerdo afecta a nuevas facturas. No debe modificar el desglose de facturas ya creadas ni alterar documentos históricos. El control de selección de plantilla no sustituye la revisión de los importes ni las validaciones fiscales existentes.

## Protección contra duplicados

La identidad de la facturación es **acuerdo y período**, no únicamente proveedor. Un proveedor puede tener acuerdos para servicios distintos.

Los períodos tienen límites canónicos: escoger otra fecha del mismo mes o quincena no crea un período nuevo. Un registro interno, Supplier Retainer Claim, reserva el acuerdo y período durante la misma transacción de generación y permite controlar intentos simultáneos.

Una factura en borrador, validada o pendiente de pago ocupa su período. Al cancelar una liquidación, sus borradores sin procesamiento fiscal ni adjuntos se descartan y sus reservas se liberan para volver a generar ese período. La liquidación conserva un comentario de auditoría y Frappe conserva las instantáneas en Deleted Document; no se reutilizan sus números de factura. Repetir la generación no debe producir una segunda factura. La identidad del acuerdo se conserva al modificarlo mediante el proceso de enmienda para evitar que una nueva versión vuelva a facturar un período ya utilizado.

Para reemplazar una factura cancelada, se copia su nombre exacto en **Factura cancelada a reemplazar** en la fila. Puede abrirse desde la liquidación anterior. El servidor comprueba que corresponde al mismo acuerdo y período. La referencia anterior y el historial se conservan. El reemplazo no se habilita por una factura impagada o en borrador.

## Permisos y conservación

- Accounts User: consultar y preparar borradores, incluida la plantilla inicial del acuerdo.
- Accounts Manager y System Manager: validar y cancelar, y cambiar la plantilla de un acuerdo validado.
- Supplier Retainer Claim: registro interno, sin creación, edición ni eliminación manual por esos roles.
- Las liquidaciones que generaron facturas se conservan. La cancelación descarta los borradores elegibles en una sola transacción y exige permiso de eliminar Purchase Invoice. Si existe alguna factura sometida, con NCF/procesamiento fiscal o con adjuntos, no se elimina ningún borrador. Las facturas ya canceladas se conservan. Las liquidaciones canceladas no se eliminan, aunque posteriormente se regenere su período.

Los permisos del formulario complementan los controles del servidor; ocultar un botón no basta para proteger la operación.

## Prueba funcional en desarrollo

Usar exclusivamente datos de prueba en el sitio de desarrollo confirmado y las personalizaciones reales de ERPNext, PowerPro y Nubef. No reutilizar personas reales para pruebas que creen facturas. No ejecutar estos casos en producción.

1. Crear un proveedor y un servicio de prueba, y un acuerdo mensual por un importe bruto conocido. Seleccionar una plantilla revisada por Contabilidad.
2. Validar el acuerdo y cargarlo en una liquidación. Verificar límites del período, bruto y contabilidad de la fila.
3. Cargar varios acuerdos, quitar uno y validar. Comprobar una factura en borrador por fila conservada, vínculos correctos y total bruto.
4. Reintentar el mismo acuerdo y período desde otra liquidación y desde dos sesiones simultáneas. Verificar que no aparece una factura adicional.
5. Probar días distintos del mismo mes, cambio de mes, febrero y ambas quincenas. Verificar que no se omiten ni se solapan los límites.
6. Provocar un fallo de validación en una de varias facturas. Verificar que no queda ninguna factura nueva de ese intento y que la liquidación continúa en borrador.
7. Cambiar la plantilla del acuerdo validado con un responsable autorizado. Comprobar historial, factura anterior intacta y nueva factura con la nueva selección. Repetir con Accounts User y verificar rechazo del cambio después de validar.
8. Con la exigencia de plantilla desactivada, revisar una factura en borrador y cambiar su selección. Con la exigencia activada, comprobar que cambiar la selección guardada al generar es rechazado, incluso si después cambió el acuerdo.
9. Cancelar una factura de prueba y comprobar el reemplazo explícito. Rechazar un reemplazo de otro acuerdo, período o una factura no cancelada.
10. Verificar rechazo de servicio inventariable, empresa incompatible, acuerdo no validado, vigencia parcial, importe inválido y modificaciones de los datos copiados en las filas.
11. Abrir las facturas y revisar las validaciones habituales de Nubef sin enviarlas a DGII ni generar pagos durante la prueba del flujo de igualas.

La evidencia de despliegue, resultados de pruebas y validación visual del sitio se registra por separado; esta lista define los casos esperados y no acredita su ejecución.
