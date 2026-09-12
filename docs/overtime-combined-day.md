# Feriado que coincide con descanso semanal

En DGII Payroll Settings, dentro de Reglas de pago por marcaciones, el campo **Feriado y descanso semanal: pago en efectivo** permite mantener revisión, aplicar una vez el recargo mayor o sumar los dos recargos sobre la hora base. Guardar con publicación habilitada crea una versión de reglas para la empresa y vigencia. La elección expresa del empleado y la habilitación de efectivo por descanso semanal siguen siendo necesarias.

En Holiday List, una fila con **Weekly Off** puede marcarse **También es feriado legal**. Esto identifica la coincidencia sin duplicar la fecha. El campo se distribuye como fixture de PowerPro; no se modifica el código de HRMS ni ERPNext. No se marcaron calendarios empresariales existentes.

Con una hora base de RD$100, recargos de feriado y descanso de 100%, y nocturnidad de 15%, la opción de mayor recargo produce RD$215; la suma produce RD$315. Si la base está cubierta por el sueldo, los adicionales son RD$115 y RD$215. El recargo suplementario solo usa las horas de coincidencia, sin duplicar la base ni modificar otras horas de feriado.

## Alcance comprobado

- Prueba pura: opciones, recargo mayor, cobertura parcial, segmentos mixtos, valores inválidos y rechazo de compensatorio sin separación de obligaciones.
- Prueba nativa de Desarrollo: publicación desde Settings, calendario real con la marca de coincidencia, autorización y ajuste retroactivo, elección requerida, Additional Salary, Salary Slip, cancelación y reintento. Comprobación de conteos y configuración restaurados por rollback.
- Regresiones nativas: versiones de reglas, cobertura salarial de feriado y descanso compensatorio retroactivo.

La combinación de pago del feriado y descanso compensatorio sigue pendiente. La selección predeterminada permanece en revisión. No se publicaron políticas empresariales ni se activó un piloto o el procesamiento automático. Las opciones no certifican una interpretación laboral única para todos los regímenes.

## Instalación y reversión

Desarrollo: `/opt/erpnext/igcaribe-bench`, sitio `igcaribe.fortabs.com`; Frappe 15.103.2, ERPNext 15.102.0, HRMS 15.58.5 y PowerPro 1.0.1. Apps instaladas: frappe, erpnext, print_designer, hrms, wiki, powerpro, drive, survey_pro, nubef, quality_traceability.

⚠️ Se recargan únicamente DGII Payroll Settings y Overtime Pay Policy, se instala el Custom Field desde el fixture y se limpia caché. No requiere editar aplicaciones centrales ni ejecutar migrate en este sitio de desarrollo.

✅ Antes de revertir, verificar que no existan políticas nuevas publicadas ni liquidaciones que usen estas opciones. ⚠️ Revertir el commit de este bloque, recargar los dos DocTypes y limpiar caché. El Custom Field puede quedar sin uso; no eliminar sus datos. Si ya hay operaciones reales, conservar la lectura de sus reglas y evidencia antes de retirar funcionalidad. Revertir código no revierte nómina. Archivos de respaldo y manifiestos: `logs/combined-day-20260912/`.
