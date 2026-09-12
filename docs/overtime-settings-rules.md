# Configurar reglas de pago por marcaciones

En **DGII Payroll Settings → Reglas de pago por marcaciones**, active **Publicar reglas al guardar**, indique empresa y vigencia, ajuste las opciones y guarde. Guardar publica una política con el usuario y momento de aprobación. No crea pagos ni activa el scheduler. La sección aplica al motor por marcaciones, no convierte las convocatorias antiguas de asistencia presumida.

Opciones disponibles:

- **Aplicar el recargo nocturno a toda la jornada nocturna**: apagado aplica al trabajo de 21:00 a 07:00; encendido aplica a toda la jornada evidenciada cuando contiene al menos tres horas nocturnas. Solo extiende el recargo nocturno: las horas ordinarias no reciben automáticamente el recargo de horas extra.
- Porcentajes ordinario, extraordinario/feriado, nocturno y descanso semanal; umbral semanal de horas efectivamente trabajadas. Los recargos se suman sobre la hora base, sin capitalización. Se conservan los mínimos y validaciones del motor.
- **Feriado y descanso semanal: pago en efectivo**: puede dejarlo en revisión, aplicar una sola vez el mayor recargo o sumar ambos recargos sobre la misma hora base. La base se incluye una sola vez y se descuenta únicamente la cobertura salarial documentada. Sigue siendo necesaria la elección del empleado. En Holiday List, marque **También es feriado legal** en la fila de descanso semanal cuando coincidan ambas condiciones; no duplique la fecha.
- Pago por descanso semanal y liquidación de nocturnidad ordinaria junto con una autorización inscrita para liquidación automática. Sus demás requisitos de evidencia, elección y permisos siguen aplicando.
- Descanso compensatorio, tipo de licencia, equivalencia en horas, fracción mínima, duración continua y crédito de descanso semanal. Dejar el crédito semanal en cero mantiene ese caso pendiente de revisión.

Para cambiar una política existente, seleccione la **Versión de partida** vigente y pulse **Cargar reglas de la versión**. Cambie lo necesario y guarde. La nueva versión conserva empresa y fechas y referencia la anterior. Si otro operador publicó mientras editaba, se exige cargar esa versión antes de guardar. Guardar sin cambios no crea otra política. Apagar **Publicar reglas al guardar** detiene la publicación desde este formulario; no cancela una política ya aprobada ni detiene por sí solo el procesamiento de autorizaciones inscritas.

Una nueva vigencia debe ser un período sin superposición. Una autorización que cruza dos políticas sigue requiriendo dividir su ventana. No se cambia silenciosamente la regla a mitad de una jornada.

Las conciliaciones ya guardadas en fuentes enviadas conservan la versión de su instantánea persistida en el servidor. Las evaluaciones nuevas y borradores usan la revisión vigente. Una revisión no invalida por sí sola la nómina anterior; los cambios en marcaciones, tarifa, calendario u otra evidencia continúan sujetos a los controles de vigencia del motor. Las versiones aprobadas son inmutables. Una versión con sucesora aprobada no puede cancelarse.

Al abrir **Revisar evidencia corregida** o declarar la jornada inicial de un ajuste
retroactivo, la vista previa muestra **Reglas utilizadas en esta evaluación**:
versión y vigencia, opción nocturna, porcentajes configurados, horas por categoría,
horas nocturnas de reloj y horas que reciben el recargo. Estas últimas pueden ser
distintas cuando se eligió toda la jornada nocturna. Se separa la nocturnidad
ordinaria de la extraordinaria y no se suman dos veces las horas superpuestas.
También se indica si falta evidencia semanal o cobertura salarial del feriado.
El detalle proviene del resultado evaluado, no de una lectura posterior de las
opciones actuales, y no cambia el token ni la acción de aceptación.

**Comparar cálculo por fecha** conserva la comparación anterior de calendario y
la identifica como referencia. No aplica las políticas versionadas ni representa
por sí sola el importe que liquidará el motor por marcaciones.

## Verificación y límites

La prueba nativa de Configuración cubre publicación mediante `Single.save`, reintento sin duplicado, revisiones sucesivas, editor obsoleto, mínimos, vigencias, empresa, conversión de descanso, denegación a Guest y ausencia de creación financiera. Las pruebas nativas de feriado y nocturnidad ordinaria comprueban que una revisión cambia los cálculos nuevos y preserva las liquidaciones anteriores, incluida su validación en Salary Slip. Todo se revierte al terminar en Desarrollo.

La interfaz real en Desarrollo se verificó sin guardar: apertura de la sección, controles dependientes, valores iniciales y mensaje de carga de versión vacía. La publicación HTTP desde esa sesión y la aceptación con cuentas reales de Finanzas/Gestión Humana no quedan demostradas por esa revisión visual.

El pago en efectivo de feriado coincidente con descanso semanal está cubierto por las opciones anteriores. La opción **Pagar feriado y conceder descanso semanal compensatorio** permite registrar ambas obligaciones juntas para una ventana de coincidencia. Requiere habilitar compensatorio, definir equivalencia, crédito semanal y duración continua, aprobar la elección del empleado con fecha de nómina, y declarar la cobertura salarial del feriado. Este bloque no activa un piloto ni certifica todos los regímenes laborales. Esos puntos siguen dentro del plan general.

## Instalación y reversión en Desarrollo

Target: `/opt/erpnext/igcaribe-bench`, `igcaribe.fortabs.com`, Desarrollo; Frappe 15.103.2, ERPNext 15.102.0, HRMS 15.58.5, PowerPro 1.0.1. Apps: frappe, erpnext, print_designer, hrms, wiki, powerpro, drive, survey_pro, nubef, quality_traceability.

⚠️ Desde `sites`, se recargaron únicamente los DocTypes con `../env/bin/python -m frappe.utils.bench_helper frappe --site igcaribe.fortabs.com reload-doc power_pro doctype overtime_pay_policy` y el mismo comando para `dgii_payroll_settings`. Se ejecutó `clear-cache`; no hubo migrate ni reinicio manual.

✅ Antes de revertir, comprobar que no existen revisiones publicadas ni operaciones en curso. ⚠️ Revertir el commit de esta entrega y recargar esos dos DocTypes. Los campos nuevos pueden permanecer físicamente en la tabla sin uso; no borrar columnas ni registros. Si ya existen revisiones o liquidaciones, conservar el lector de versiones y resolver la transición antes de volver al selector antiguo, que rechaza políticas superpuestas. Un revert de código no revierte nómina. Respaldo y manifiesto de archivos: `logs/policy-settings-20260912/`.
