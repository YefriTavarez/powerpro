# Complementos fijos de Employee

La función se instala **deshabilitada** y se configura en **Employee Supplement Settings**. No hay aprobaciones rutinarias nuevas ni cron: el hook `Salary Slip.before_insert` genera y confirma Additional Salaries dentro de la misma transacción del worker normal o mixto de Payroll Entry. Un fallo revierte la generación del worker. Las vistas previas no escriben adicionales.

## Política acordada

Los cuatro Currency de Employee representan importes mensuales completos. Nómina Monthly aplica el 100%; Bimonthly aplica una mitad por quincena. No se prorratea por días pagados, ausencias ni fecha de ingreso. El último período absorbe diferencias de redondeo. Se configura si la segunda quincena empieza el 15 o el 16 y la precisión de pago (2 o 4). Los períodos parciales, semanales, por horas o entre meses se rechazan; no se adivina una fórmula.

## Instalación

En Development autorizado: cargar los cuatro DocTypes `Employee Supplement Mapping`, `Employee Supplement Existing Salary`, `Employee Supplement Revision`, `Employee Supplement Settings` y ejecutar `powerpro.patches.v1.setup_employee_supplements.execute`. La función registra la misma instalación en `patches.txt` para el despliegue normal. No crea Salary Components ni cambia sus impuestos/cuentas, no modifica los cuatro Custom Fields existentes y no activa la función.

La instalación añade:

- Employee: los cuatro importes si faltan y `pp_supplements_effective_from`.
- Salary Slip: snapshot de origen y cobertura `pp_employee_supplements`.
- Additional Salary: clave única, campo de origen, período, importe mensual y clasificación explícita de pagos independientes.
- Historial inmutable de importes por empleado y fecha de vigencia.

## Configuración inicial

1. Definir empresa, moneda, primer período futuro, calendario quincenal y precisión.
2. Mapear los cuatro campos a cuatro componentes distintos, de tipo Earning, pagables y sin `depends_on_payment_days`. No deben existir simultáneamente en la estructura: eso crearía otra fuente del mismo ingreso.
3. Conciliar los Additional Salaries de esos componentes que alcancen la fecha de inicio. `Coverage` identifica el campo fijo que ya cubren. `Independent` identifica un pago separado. No se infiere la intención por igualdad de importe ni por el nombre ORC.
4. Habilitar. Se guardan automáticamente los importes iniciales de los empleados activos. Si ya hay recibos desde esa fecha, se rechaza la activación: se necesita una transición posterior.

Un recurrente existente puede cubrir `incentivo_especial` cuando se clasifica explícitamente como `Coverage`. La conciliación debe realizarse con los documentos del entorno de destino. Los pagos independientes, horas extras y préstamos conservan su origen. Un componente de transporte configurado como deducción no sirve para pagar la asignación; el mapeo requiere un componente de ingreso.

## Uso y cambios

El usuario genera la nómina normalmente. Para cada nuevo recibo se resuelve la revisión vigente, se comprueba la cobertura existente y se crea únicamente el faltante. El Additional Salary confirmado referencia su revisión inmutable y guarda el nombre del Payroll Entry de origen como dato de trazabilidad (sin bloquear la cancelación de la nómina). El recibo guarda su propia asociación, incluso si reutiliza un adicional de una generación previa.

Para cambiar importes, editar Employee e indicar **Cambio de complementos vigente desde**. Solo se admiten fechas presentes/futuras, posteriores a la última revisión y a los períodos ya preparados. Los empleados mensuales requieren el día 1. La actualización registra el nuevo importe; los recibos existentes conservan su snapshot. No se captura el valor actual del empleado de nuevo al recalcular una nómina vieja.

Si existe un recurrente explícitamente asociado, el cambio cierra solo su `to_date` al día anterior a la nueva vigencia. Se conserva el documento confirmado, su importe y el inicio. HRMS no permite editar `to_date` normalmente tras confirmar: esta operación interna usa el permiso acotado `ignore_validate_update_after_submit`, comprueba que no alcance recibos preparados y registra el cierre en la revisión. No se modifica core ni se cancela el documento histórico. Un recurrente que todavía no haya comenzado o una cobertura puntual futura exige conciliación explícita; no se borra ni se deshabilita silenciosamente.

Un pago manual sobre un componente gestionado debe indicar `Independent` si se suma al fijo. Los adicionales automáticos y los documentos asociados no se editan/cancelan directamente. Una cobertura de importe distinto, varias coberturas o un borrador pendiente detienen la generación con el documento concreto.

## Integridad y concurrencia

Se bloquea la fila Employee durante la preparación, revisión de importes y cambios de Additional Salary. La clave única incluye empresa, empleado, campo y fechas reales del recibo, independientemente del Payroll Entry. Se impiden períodos superpuestos. Un adicional cancelado o deshabilitado no se regenera silenciosamente. Los documentos de otros conceptos continúan por sus flujos actuales.

Al cancelar/eliminar un recibo, el adicional automático no se cancela por sí solo: una regeneración del mismo período reutiliza su clave y snapshot de origen. Si se abandona un período definitivamente, requiere un procedimiento de reversión explícito; no se presume que borrar el borrador equivale a revocar el derecho al complemento.

La configuración de moneda, mapeo, inicio, calendario y precisión queda fija una vez iniciado el historial. Pueden agregarse clasificaciones, pero no reinterpretar las existentes. Deshabilitar detiene nuevas generaciones; los recibos preparados continúan validando su cobertura histórica y los cambios del empleado inscrito siguen registrándose.

## Verificación en Development

Desde `sites/`:

```sh
../env/bin/python ../apps/powerpro/scripts/test_employee_supplements_dev.py --site igcaribe.fortabs.com --confirm-development
```

El runner comprueba `developer_mode`, restringe el site, bloquea commits, correos y enqueue, y revierte todas las transacciones. No usar un test runner contra producción.

## Reversión de código

Con la función deshabilitada y sin nóminas automáticas reales creadas, retirar únicamente el bloque de hooks de complementos restaurando el respaldo previo del VPS, retirar la línea de patch y los archivos nuevos. Los metadatos aditivos pueden permanecer inactivos; no borrar columnas con datos. Después de usar la función, conservar los validadores y el historial y deshabilitar solo nuevas generaciones hasta conciliar todos los períodos. No borrar Additional Salaries ni revisiones como rollback.
