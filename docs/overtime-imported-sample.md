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


## Aceptación posterior del respaldo documental

El usuario autorizó continuar usando el PDF firmado como fuente de los horarios pese a las diferencias con los ponches. Esta decisión ya está resuelta y no debe volver a pedirse. Se prepararon tres filas pendientes, excluyendo del pago nuevo la fila con liquidación existente. La suma de sus ventanas declaradas es 14.5 horas; las pausas no constan y las horas netas permanecen sin certificar.

Se guardaron tres adjuntos privados en el Employee de la muestra: imagen de la página pertinente, conciliación legible y paquete estructurado con hash del PDF original, horarios, diferencias y exclusión del ajuste existente. El script `scripts/attach_overtime_documentary_sample.py` utiliza File.insert con permisos nativos y el controlador efectivo de PowerPro. Verifica contenido, privacidad, reintento sin duplicados y contadores protegidos; por defecto revierte. La prueba con rollback y la aplicación con lectura posterior pasaron. No se creó una declaración Manual Full Session ni un Overtime Reconciliation Run.

El preflight encontró una limitación operativa adicional: ajustes habilitados solo para julio, plazo retroactivo vencido, empleado mínimo sin elegibilidad/aprobador y modo de conciliación global apagado. No se eluden esas reglas para crear ajustes. La aceptación del documento no equivale a afirmar que no hubo pausas ni a seleccionar por el empleado pago o descanso. Preparar la configuración específica del piloto y la jornada neta antes de aprobar o liquidar.

Reversión de esta entrega: usar el recibo privado para identificar únicamente los tres File creados, verificar que no tengan usos adicionales y eliminarlos mediante su ciclo nativo; conservar fuente y recibo. Eliminar adjuntos no revierte ni altera Checkins o nómina. El script y esta documentación se revierten con Git, sin tocar las dos modificaciones ajenas.


## Borradores nativos del caso documental

Se resolvieron las dependencias de configuración que impedían guardar el caso de Desarrollo: se conservó el inicio 2026-07-01 y se amplió el límite final hasta 2026-08-16; el plazo de revisión se cambió de 2026-08-31 a 2026-09-19 (siete días desde la ejecución). El empleado importado quedó overtime_eligible=1, con Administrator como aprobador del ensayo. No se amplió ningún rol ni se modificó Producción.

`scripts/stage_documented_overtime_sample.py` consume un plan privado con hash, exige DEV/developer_mode/Administrator, scheduler y motor apagados, fuente aceptada y adjuntos privados idénticos. Cambia mediante save nativo solo los dos campos de período/plazo y la elegibilidad/aprobador del empleado. Inserta hasta tres ajustes Draft de fechas distintas, excluye explícitamente el día ya liquidado, enlaza sus tres respaldos y rechaza colisiones. No modifica ventanas reales, calendario, ponches, política o documentos existentes. Cash y la fecha actual son valores provisionales del formulario, sin constituir elección ni aprobación de pago.

La prueba de rollback y repetición nativa pasó, seguida de aplicación y lectura posterior. Hay tres borradores de 1, 5 y 8.5 horas máximas documentales, sin horas verificadas ni liquidación. El motor y scheduler siguen apagados. Configuración, contadores protegidos y Checkins se verificaron antes y después. Single.save materializa defaults numéricos 0 y claves nulas; el comparador usa metadatos/Decimal para distinguir equivalencia de cambios reales, sin ignorar diferencias de valor.

Pendiente para aprobación: resolver jornada neta/pausas y correspondencia de horario/calendario del piloto. El turno de Desarrollo aún termina a las 18:00 el viernes y clasifica el domingo como Legal Holiday; el contexto archivado de Producción termina a las 17:00 el viernes y ese domingo es feriado sobre descanso semanal. Los borradores conservan esta limitación en su justificación y respaldo. No tomar sus máximos como horas verificadas o calcular pagos con configuración divergente.

Reversión: después de verificar que los tres registros del recibo siguen Draft y sin dependencias, eliminarlos mediante Document.delete. Retirar únicamente los vínculos File de esos borradores, preservando los originales privados del Employee. Restaurar por save los valores previos registrados en el recibo: límite 2026-07-31, plazo 2026-08-31, elegibilidad 0 y aprobador vacío, solo si no hubo cambios posteriores. Un revert de Git no revierte datos. Mantener apagados los procesos automáticos.


## Correspondencia del calendario de Desarrollo

También se resolvió la divergencia del horario: nueve Custom Fields opcionales reproducen los valores archivados del turno seleccionado (control activo, lunes-viernes laborables, sábado/domingo descanso, viernes hasta 17:00). Los otros turnos reciben control desactivado por defecto. El cálculo respeta ese interruptor y utiliza el Holiday List cuando está apagado; instalaciones antiguas con días pero sin interruptor conservan su comportamiento previo.

La función pura `is_scheduled_workday` y su integración en `get_schedule_context` evitan que la mera instalación de metadata con ceros convierta otros turnos en descanso. Pasaron seis pruebas del interruptor, siete de captura del viernes, 27 de calendario, 14 de evidencia y 19 de semana real (73 en total). En el sitio se comparó el calendario completo de 2026 del otro turno antes/después, sin diferencias. Los 101 Checkins permanecieron idénticos; no se modificaron settings ni contadores protegidos en esta fase.

`scripts/configure_dev_overtime_shift.py` exige DEV, fuente con hash, procesos apagados y campos nuevos identificados como propiedad del instalador. Primero genera un recibo de preflight; `--apply` agrega metadata por API nativa, guarda el turno y vuelve a validar los tres borradores. La metadata/DDL no es transaccional; no se presenta como rollback completo. El recibo conserva la definición anterior y las filas a revertir.

Lectura posterior: viernes Regular Workday con fin 17:00; sábado Weekly Rest; domingo Legal Holiday on Weekly Rest. La vista previa nativa sigue Waiting por sincronización incompleta y las marcas faltantes, coherente con su uso documental pendiente. Para liquidar faltan además política aprobada para la fecha y asignación salarial con tarifa vigente en la muestra de Desarrollo. No se presume que la tarifa de un ajuste previo sea una asignación salarial vigente.

Reversión de calendario: restaurar los valores anteriores del turno desde el recibo y refrescar solo los tres Draft. Si se retira metadata, eliminar por ciclo nativo únicamente los nueve Custom Fields creados por esta entrega, después de verificar usos posteriores. No borrar columnas SQL ni tocar campos existentes ajenos. Mantener el código que respeta el interruptor hasta retirar la metadata, para no interpretar los defaults 0 como descansos en todos los turnos. La copia del código previo está en `logs/obispo-sample-20260912/schedule-code-before.tar`.


## Declaración autorizada de fin de semana

El operador indicó asumir íntegros los tramos de sábado/domingo porque no hay registro ni estructura de almuerzo en esos días. Se aceptan 5 y 8.5 horas mediante el servicio nativo `retroactive_draft_review`, no mediante edición de campos calculados. La declaración conserva un objeto `assumption`, deducción de pausa cero, referencia documental y motivo explícito; no afirma verificación por reloj ni crea una regla automática para otros fines de semana.

`scripts/review_documented_overtime_weekend.py` exige un plan privado con hash, dos ventanas exactas de fin de semana, mismo empleado/aprobador, Draft y ausencia de inscripciones activas ajenas. Habilita el motor en Desarrollo con fecha efectiva 2026-08-10 manteniendo scheduler apagado. Usa preview/token/apply nativos, prueba repetición y conserva dos Overtime Reconciliation Run. Los borradores y sus campos económicos permanecen intactos; su vista previa resuelve la declaración manual guardada.

Ensayo con rollback, repetición y aplicación con lectura posterior pasaron: dos revisiones manuales actuales Verified, total13.5h, comparación original Waiting conservada, sin nuevos Checkins, salarios, elecciones ni aprobaciones. No confundir Verified de la declaración manual con marcaciones completas. El viernes no forma parte de la suposición autorizada para fines de semana.

La liquidación sigue separada: la muestra requiere política publicada, tarifa con asignación salarial, evidencia semanal completa y elección expresa del empleado cuando corresponde descanso. No se infiere elección de pago/descanso ni salario a partir de la suposición sobre almuerzo. El tema de las pausas de esas dos fechas está resuelto; no volver a preguntarlo.

Reversión operativa: si se desea detener nueva conciliación, guardar enable_checkin_overtime_reconciliation=0; no borrar los dos historiales auditados. Una corrección de horas requiere nueva revisión trazable con motivo. La fecha efectiva anterior era vacía; conservar el recibo. Un revert de código no elimina auditorías ni revierte configuración.

## Tarifa respaldada y escenarios monetarios

Una consulta REST de solo lectura recuperó la asignación salarial vigente del empleado seleccionado y los atributos mínimos de su estructura. El archivo y los importes permanecen privados, fuera de Git. En Desarrollo se verificaron versiones, metadatos efectivos, hooks, scripts, workflows y las referencias de estructura/cuenta antes de escribir.

`scripts/stage_overtime_sample_rate.py` crea una sola asignación de prueba mediante insert/submit nativos. Exige sitio DEV, developer_mode, Administrator, scheduler apagado, fuente con hash, identidad y vigencia coincidentes, estructura compatible y ausencia de otras asignaciones no identificadas como propias. Compara la tarifa calculada por PowerPro con la fuente y registra un comentario de procedencia. No migra toda la nómina: tabla tributaria, transporte y saldos iniciales quedan expresamente fuera. Si la estructura de Desarrollo exige tabla tributaria, se detiene en lugar de omitir una validación.

Pasaron el ensayo con rollback, la repetición sin duplicados y la aplicación con lectura posterior. Settings, asignaciones preexistentes y contadores de documentos protegidos permanecieron iguales. No se generaron Additional Salary, Salary Slip, elecciones o licencias. La copia no habilita la generación de nómina completa del empleado.

La tarifa cambia la huella de evidencia. El script de revisión del fin de semana ahora permite renovar una declaración idéntica desactualizada mediante la API nativa, conservando la revisión anterior. Sigue rechazando una declaración o motivo distinto. Se verificaron rollback, idempotencia y lectura posterior: ambas jornadas permanecen Verified por declaración manual, con sus intervalos y suposición originales.

`scripts/preview_documented_overtime_rate.py` genera escenarios usando el calculador monetario puro. Requiere clasificación de calendario previamente revisada, tarifa respaldada, fechas no excluidas e intervalos diurnos válidos. Muestra ambas bandas ordinarias y las combinaciones de feriado/descanso y cobertura de base, sin seleccionar una regla ni afirmar un total pagadero. Ocho pruebas del cálculo monetario y siete de combinación de días pasaron.

La revisión actual del viernes sigue Waiting por `sync_incomplete`. Los dos fines de semana aceptados conservan incidencias semanales de sincronización y marcaciones incompletas; una exportación REST no demuestra que el dispositivo haya sincronizado todo. Permanecen pendientes la evidencia semanal, la política aplicable y la elección del empleado. No se publicó una política ni se convirtió el valor provisional Cash del formulario en elección expresa.

Reversión de esta fase: identificar la asignación creada mediante el recibo privado y su comentario con hash; verificar que no tenga Salary Slips ni liquidaciones dependientes y cancelarla mediante su ciclo nativo en DEV. Conservar comentario, fuentes e historiales. La cancelación invalida la tarifa para conciliaciones posteriores; renovar la revisión si se sustituye la asignación. Revertir los scripts con Git no cancela documentos ni borra auditorías. No trasladar esta fixture parcial a Producción.
