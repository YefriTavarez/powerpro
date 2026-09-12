# Feriado que coincide con descanso semanal

En DGII Payroll Settings, dentro de Reglas de pago por marcaciones, el campo **Feriado y descanso semanal: pago en efectivo** permite mantener revisión, aplicar una vez el recargo mayor o sumar los dos recargos sobre la hora base. Guardar con publicación habilitada crea una versión de reglas para la empresa y vigencia. La elección expresa del empleado y la habilitación de efectivo por descanso semanal siguen siendo necesarias.

En Holiday List, una fila con **Weekly Off** puede marcarse **También es feriado legal**. Esto identifica la coincidencia sin duplicar la fecha. El campo se distribuye como fixture de PowerPro; no se modifica el código de HRMS ni ERPNext. No se marcaron calendarios empresariales existentes.

Con una hora base de RD$100, recargos de feriado y descanso de 100%, y nocturnidad de 15%, la opción de mayor recargo produce RD$215; la suma produce RD$315. Si la base está cubierta por el sueldo, los adicionales son RD$115 y RD$215. El recargo suplementario solo usa las horas de coincidencia, sin duplicar la base ni modificar otras horas de feriado.

## Alcance comprobado

- Prueba pura: opciones, recargo mayor, cobertura parcial, segmentos mixtos, valores inválidos y rechazo de compensatorio sin separación de obligaciones.
- Prueba nativa de Desarrollo: publicación desde Settings, calendario real con la marca de coincidencia, autorización y ajuste retroactivo, elección requerida, Additional Salary, Salary Slip, cancelación y reintento. Comprobación de conteos y configuración restaurados por rollback.
- Regresiones nativas: versiones de reglas, cobertura salarial de feriado y descanso compensatorio retroactivo.

La opción **Pagar feriado y conceder descanso semanal compensatorio** conserva pago del feriado y nocturnidad y crea el crédito de descanso elegido en una sola transacción. Su cálculo no suma un segundo recargo de descanso en efectivo. La nómina se refleja en **Pago del feriado con descanso compensatorio** y conserva el estado del crédito y la programación del descanso. La elección requiere fecha de nómina. Una ventana que mezcla obligaciones de descanso distintas sigue en revisión. La selección predeterminada permanece en revisión. No se publicaron políticas empresariales ni se activó un piloto o el procesamiento automático. Las opciones no certifican una interpretación laboral única para todos los regímenes.

## Instalación y reversión

Desarrollo: `/opt/erpnext/igcaribe-bench`, sitio `igcaribe.fortabs.com`; Frappe 15.103.2, ERPNext 15.102.0, HRMS 15.58.5 y PowerPro 1.0.1. Apps instaladas: frappe, erpnext, print_designer, hrms, wiki, powerpro, drive, survey_pro, nubef, quality_traceability.

⚠️ Se recargan únicamente DGII Payroll Settings y Overtime Pay Policy, se instala el Custom Field desde el fixture y se limpia caché. No requiere editar aplicaciones centrales ni ejecutar migrate en este sitio de desarrollo.

✅ Antes de revertir, verificar que no existan políticas nuevas publicadas ni liquidaciones que usen estas opciones. ⚠️ Revertir el commit de este bloque, recargar los dos DocTypes y limpiar caché. El Custom Field puede quedar sin uso; no eliminar sus datos. Si ya hay operaciones reales, conservar la lectura de sus reglas y evidencia antes de retirar funcionalidad. Revertir código no revierte nómina. Archivos de respaldo y manifiestos: `logs/combined-day-20260912/`.


## Prueba de pago y descanso simultáneos

`tests/dev_overtime_hybrid.py` cubre ajuste retroactivo, autorización manual y procesamiento automático: fallo después de crear dinero revierte ambas partes; reintento crea ambas una vez; Salary Slip incluye el pago y conserva el crédito; una licencia utilizada bloquea cancelación; cancelar licencia permite cancelar ambas partes y liberar la elección. También prueba la rutina de reversión conjunta usada por la revisión de evidencia. Las vistas previas muestran el dinero junto al crédito. No demuestra todavía aceptación con cuentas reales ni un piloto activo.

Se añade un campo de estado de pago a cada origen, además de la opción en Settings/Policy; la fecha de nómina se captura en la elección. ⚠️ La instalación de este bloque recarga también Overtime Authorization, Retroactive Overtime Adjustment y Overtime Settlement Election. Respaldos del bloque híbrido: `logs/hybrid-day-20260912/`. No revertir su código si existen liquidaciones combinadas activas: deben conservarse los lectores, canceladores y seguimiento de ambas obligaciones.
