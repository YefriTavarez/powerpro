# Muestra documental y marcaciones importadas a Desarrollo

El operador seleccionó una persona y confirmó cuatro ventanas del 13 al 16 de agosto de 2026 en un PDF. Autorizó consultar su API de Producción para descargar las marcaciones. Se descargaron diez, su turno/calendario y los ajustes existentes del período. Los datos personales, exportaciones y credenciales no forman parte del repositorio. Las credenciales se utilizaron en memoria y no se guardaron en los archivos exportados.

## Alcance ejecutado

- Solo GET en `igcaribe.com`; ninguna creación, aprobación o liquidación de Producción.
- Desarrollo confirmado: `/opt/erpnext/igcaribe-bench`, sitio `igcaribe.fortabs.com`, developer_mode=1, sin currentsite.txt. Frappe 15.103.2, ERPNext 15.102.0, HRMS 15.58.5, PowerPro 1.0.1. Orden de apps: frappe, erpnext, print_designer, hrms, wiki, powerpro, drive, survey_pro, nubef, quality_traceability.
- Se importó el registro mínimo del empleado y diez Employee Checkins mediante `Document.insert`, con validaciones nativas. Antes hubo una prueba de rollback y reintento sin duplicados. La importación confirmada también comprobó idempotencia y lectura posterior al commit.
- Se conservaron nombres de origen, tiempo, log_type, turno/ventanas capturadas, offshift y skip_auto_attendance. El campo adicional de acción y creation/modified de Producción permanecen en el archivo fuente; no se fingieron como metadatos nativos de Desarrollo.
- No se modificaron turnos compartidos ni configuración. No se crearon Attendance, autorizaciones, ajustes, salarios, créditos o políticas. Scheduler, Auto Attendance y conciliación permanecieron desactivados.

El importador `scripts/import_overtime_checkin_sample.py` exige sitio DEV explícito, Administrator, hash del paquete, un empleado activo, máximo siete días/200 marcaciones y ausencia de Attendance enlazado. Rechaza colisiones de identidad, datos distintos existentes, cambios por validación de turno y modificaciones de documentos/configuración protegidos. Sin `--apply`, revierte las inserciones y verifica la restauración. Un error antes de commit revierte toda la transacción.

## Defecto reproducido y corrección

La configuración de Producción incluye `custom_hora_salida_viernes=17:00`; HRMS conserva `shift_end=18:00` en los Checkins. El motor exigía igualdad exacta con el horario resuelto y descartaba la jornada del viernes como incompleta, aunque existieran IN/OUT y break completos.

`captured_window_kind` reconoce exclusivamente la pareja exacta turno base/horario especial configurado para viernes. No acepta cualquier diferencia, otro turno, otro día o una excepción ausente. Se usa tanto en la conciliación como en la cobertura semanal. La interpretación guarda final capturado y final de horario sin alterar los originales. Los cargadores incluyen el valor especial en la huella únicamente cuando existe; no agregan claves vacías a las instantáneas anteriores.

La evidencia vigente que cambie por una configuración especial debe pasar la revisión habitual de instantáneas; no se recalculan pagos históricos automáticamente. No se modificó el core de HRMS ni se desplegó esta corrección en Producción.

## Resultado de la muestra

El diagnóstico `scripts/preview_imported_overtime_sample.py` vuelve a leer los registros importados y ejecuta el motor con el contexto DEV y con el contexto archivado de Producción. Prohíbe SQL de escritura, commit, correos y encolado. Los escenarios con sincronización completa son explícitamente hipotéticos y no acreditan una sincronización de dispositivos.

- Con la sincronización real vacía, los cuatro casos esperan.
- Con sincronización completa hipotética y horario de Producción, el jueves obtiene 3.5933 horas dentro de la ventana; la salida es anterior al papel y queda en revisión. Ya existe un ajuste con liquidación creada en Producción: no duplicarlo.
- El viernes obtiene una hora dentro de 17:00–18:00; la salida 27 minutos posterior permanece fuera de autorización y exige revisión. Antes de la corrección, el mismo motor no lograba formar la pareja.
- Sábado tiene solo IN y domingo solo OUT. No se unen como una jornada continua ni se inventan marcas.
- La opción First Check-in and Last Check-out incluye breaks en la duración completa; las entradas previas al turno también permanecen visibles para revisión, sin autorizarlas para pago.
- Producción tiene reglas explícitas de días laborables que Desarrollo no posee. El domingo del período se clasifica como feriado sobre descanso semanal en el contexto archivado. El diagnóstico no cambia silenciosamente la configuración de Desarrollo.

## Validación y comprobantes

Pasaron 7 pruebas específicas del viernes, 14 de evidencia, 19 de semana real, 20 de interpretación de turnos y 27 de calendario. En el VPS pasaron las siete pruebas del viernes y las suites nativas `dev_checkin_overtime.py` y `dev_retroactive_draft.py`, ambas con rollback. Los contadores posteriores incluyen Employee=102 y Employee Checkin=89; Additional Salary=2, Salary Slip=75, AUTH=65, Retro=2, Policy=0 y Run=0 permanecieron intactos.

Paquete fuente, hashes, copia previa del código, recibos y resultados: `logs/obispo-sample-20260912/` en el bench, con acceso privado. El informe para el operador y los originales permanecen fuera del repositorio en el directorio de entrega de esta tarea. Los dos archivos ajenos de Overtime Authorization conservaron sus SHA previos.

## Pendiente y reversión

La selección de empleado/fechas ya está resuelta; no repetir aquella pregunta de alcance. La ampliación semanal fue inicialmente rechazada por la revisión automática de permisos. Posteriormente el usuario la autorizó expresamente y se ejecutó; ese bloqueo quedó resuelto. Falta revisar los intervalos reales y las pausas de las jornadas incompletas antes de certificar recargos o liquidar.

### Ampliación semanal autorizada

Se descargaron 22 Checkins del 10 al 16 de agosto, ningún Attendance enviado y un solo ajuste existente en el período. Las diez marcas anteriores no habían cambiado. Doce marcas nuevas se importaron en Desarrollo y diez se reutilizaron, con el mismo importador, hash del nuevo paquete, prueba de rollback, idempotencia y lectura posterior al commit. No se creó otro Employee. Los contadores de la muestra pasan a 22 Checkins; los globales, a Employee=102 y Employee Checkin=101. Los documentos protegidos y ajustes permanecieron intactos.

La comparación con sincronización completa hipotética da 55:53:32 de lunes a viernes con primera entrada–última salida, y 51:30:54 con cada pareja válida. La diferencia es 4:22:38 de pausas. Son duraciones provisionales de jornada completa, no horas extra a pagar. El lunes guarda IN, IN, OUT, OUT: la alternancia lo interpreta sin modificar los originales; el modo estricto requiere revisión. Sábado y domingo siguen sin una pareja completa y no cuentan como cero. No se certificó la semana ni se activaron procesos.

Se preparó un informe concreto para confirmar si los horarios firmados del fin de semana reflejan el trabajo real y qué pausas contienen, antes de una declaración manual. Confirmar AM/PM no equivale a resolver una discrepancia entre formulario y reloj. El día que ya tiene liquidación en Producción queda excluido de propuestas de pago nuevo. Los comprobantes semanales y el diagnóstico permanecen en el directorio privado de la muestra, fuera de Git.

Para revertir código, revertir el commit correspondiente o restaurar únicamente los archivos del manifiesto desde `code-before.tar`; conservar los dos archivos ajenos. Revertir código no elimina los datos importados. Para retirar la muestra, revisar el recibo y dependencias actuales, eliminar por el ciclo nativo únicamente los Checkins allí creados y luego el Employee si fue creado por la importación y sigue sin dependencias nuevas. Conservar fuente y recibos; no borrar registros que el importador reutilizó ni ejecutar DELETE SQL.

El piloto operativo y la futura carga a Producción siguen pendientes. Las pruebas técnicas y la importación no sustituyen la aceptación de horarios discrepantes ni autorizan repetir una liquidación existente.
