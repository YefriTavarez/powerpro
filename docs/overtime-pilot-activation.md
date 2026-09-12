# Propuesta de acceso y activación del piloto

Estado: implementación y diagnósticos actualizados; piloto operativo no ejecutado. Sitio exclusivo: `igcaribe.fortabs.com`, Desarrollo. Esta propuesta completa la preparación del piloto; no sustituye la selección de la muestra y su revisión ni acredita que el objetivo completo esté terminado.

## Estado comprobado el 12 de septiembre de 2026

Bench `/opt/erpnext/igcaribe-bench`. Aplicaciones en orden: frappe, erpnext, print_designer, hrms, wiki, powerpro, drive, survey_pro, nubef, quality_traceability. `developer_mode=1`.

Consulta directa de solo lectura: `System Settings.enable_scheduler=0`; `DGII Payroll Settings.enable_checkin_overtime_reconciliation=0`; `checkin_overtime_effective_from` vacío; políticas de pago 0; autorizaciones con `evidence_enrolled=1`: 0. La ejecución puntual del trabajador está documentada en la entrega anterior; no acredita procesamiento recurrente activo.

Las autorizaciones `AUT-HE-2026-00021`, `00022`, `00023` y `00024` están inscritas en el modo anterior, `Queued`, con `evidence_enrolled=0`. No pertenecen al piloto propuesto. Activar el scheduler general puede despertar trabajos ajenos al piloto; queda fuera de esta propuesta.

## Acceso concreto propuesto

| Participante | Situación comprobada | Propuesta para el piloto |
|---|---|---|
| Finanzas | La cuenta existente tiene `Gerente Finanzas` y `System Manager`; puede leer, crear, escribir y enviar autorizaciones. El ámbito de Employee sigue restringido por sus permisos existentes. | Operar los casos seleccionados dentro de ese ámbito, sin ampliar permisos ni asignar roles. La selección del operador y los empleados queda pendiente. |
| Gestión Humana | Su cuenta tiene `Encargado Gestión Humana`; puede crear/leer Dietas, pero no tiene acceso nativo a autorizaciones, políticas ni conciliaciones. | Participar en la revisión funcional de los resultados con Finanzas. Si debe operar directamente, aprobar primero las acciones y el ámbito de empleados; implementar y probar esos permisos antes de usar su sesión. |
| Responsable laboral | Sin responsable ni referencia de aprobación registrados para la matriz. | Validar las reglas y su vigencia con los ejemplos de `overtime-policy-review.md`. |

No se propone asignar `System Manager` a Gestión Humana. El permiso para verificar no equivale a solo consultar: el servicio exige lectura/escritura sobre la fuente y un rol incluido en `overtime_manual_verification_roles`; determinadas acciones pueden producir liquidaciones. Para dar acceso de consulta hay que verificar también Employee, Employee Checkin y las fuentes enlazadas. Para dar acceso operativo deben probarse separadamente conciliación, declaración manual, resolución de incidencias, liquidación y cancelación. No se ampliarán automáticamente los permisos de nómina, políticas o empleados.

## Decisiones necesarias antes de escribir configuración

1. Aplicar las reglas ya resueltas: nocturnidad de reloj 21:00–07:00, recargos aditivos sobre la hora base y cobertura salarial explícita del feriado. Las variantes de jornada nocturna, efectivo en coincidencia feriado/descanso y pago con descanso compensatorio ya son opciones de DGII Payroll Settings. Publicar la configuración para la empresa y vigencia del piloto conserva actor y versión. No volver a solicitar estas decisiones de diseño. Las ventanas que mezclan obligaciones de descanso distintas conservan revisión explícita.
2. Alcance: operador, empleados, autorizaciones nuevas y fechas concretas. Finanzas dentro de su ámbito actual es la opción que requiere menos cambios de acceso.
3. Sesión: autenticación real en Desarrollo para comprobar la interfaz y los permisos del operador. Nunca compartir contraseñas en documentos o mensajes.

Se preparó una muestra histórica concreta de tres fechas mediante el script descrito en `overtime-real-sample.md`. Falta la revisión del operador y delimitar las autorizaciones nuevas del piloto. Las reglas matemáticas confirmadas no se vuelven a tratar como una decisión pendiente. La autenticación efectiva del operador se comprobará durante el recorrido; no fabricar sesiones ni credenciales.

## Secuencia y evidencia de aceptación

| Paso | Acción y alcance | Evidencia necesaria para avanzar |
|---|---|---|
| 1. Diagnóstico ✅ | Leer de nuevo sitio, versiones, apps, configuración efectiva, permisos, personalizaciones, jobs y fuentes seleccionadas. Revisar cualquier cron independiente además del scheduler. | Identidad de Desarrollo y lista exacta de registros; diferencias respecto al estado anterior explicadas. |
| 2. Simulación ✅ | Calcular sin guardar sobre la muestra, incluyendo jornada completa y evidencia semanal. Comparar con la matriz validada. | Tramos, pausas, procedencia de marcaciones, clasificación, importes y discrepancias revisados. Ningún documento financiero creado. |
| 3. Configuración ⚠️ | Registrar la política validada con vigencia y referencia. Activar el modo nuevo y su fecha efectiva solo cuando el alcance esté definido. Mantener scheduler general, monitores y avisos en sus valores anteriores. | Lectura posterior de política y ajustes; inventario de todas las fuentes inscritas antes y después. |
| 4. Conciliación puntual ⚠️ | Inscribir expresamente cada autorización seleccionada mediante el servicio existente. La inscripción individual usa `auto_settle=False`. Procesar desde la sesión del operador, sin ejecutar un barrido global. | Campos reales, instantánea y estado correctos; marcas originales intactas; `evidence_auto_settle=0`; sin nuevos salarios adicionales ni créditos. |
| 5. Liquidación controlada ⚠️ | Sobre casos ya validados, recorrer explícitamente efectivo y descanso. Configurar antes los parámetros y la elección que corresponda. | Un resultado por obligación; referencias rastreables; importe aprobado; crédito, programación y disfrute comprobados donde corresponda. Comprobar cancelación/corrección y efectos dependientes. |
| 6. Automatización delimitada ⚠️ | Preparar ejecución recurrente del modo nuevo después de aprobar la simulación y el recorrido anterior. Identificar mecanismo, usuario, intervalo, registros elegibles y forma de detenerlo. | Una ejecución real con estado terminal y resultado correcto, seguida de reintento sin duplicados. No basta que exista un job o que el trabajador esté disponible. |

El mecanismo recurrente queda por concretar: no instalar un cron ni encender el scheduler general como consecuencia implícita de este documento. El flujo individual usa `powerpro.controllers.checkin_overtime.enroll` y `process_now` a través de sus acciones autorizadas; ambos validan acceso. `process_now` puede liquidar si una autorización tiene `evidence_auto_settle=1`, por lo que hay que comprobar ese valor antes del paso 4.

Muestra mínima: caso coherente, salida de madrugada registrada IN con una entrada posterior, falta de salida, recepción tardía de Checkin, nocturnidad ordinaria y ambas opciones de descanso semanal. Deben incluirse también los cruces y límites de la matriz original y las pruebas de concurrencia/corrección allí exigidas; una muestra pequeña no certifica por sí sola todos esos requisitos.

Una marca ambigua debe quedar para revisión, con motivo visible y sin liquidación automática. Una nueva marcación no debe reemplazar una verificación protegida. Las horas fuera de autorización permanecen visibles para revisión. La ausencia de una salida no acredita el horario de cierre del turno.

## Detención y reversión

- Antes de activar, registrar los valores exactos de configuración y los nombres de política, fuentes y documentos creados por el piloto. No incluir secretos.
- Para detener nuevo procesamiento, volver `DGII Payroll Settings.enable_checkin_overtime_reconciliation` a 0 desde su formulario autorizado. Verificar su lectura posterior y la terminación de cualquier ejecución ya iniciada: cambiar la bandera no revierte ni interrumpe por sí solo una transacción en curso.
- Mantener las autorizaciones, instantáneas y evidencias del piloto. No borrar filas, volver a inscribirlas en el modo presumido ni cambiar las cuatro autorizaciones antiguas.
- Si ya existe Additional Salary, crédito o licencia, usar el procedimiento de cancelación/corrección del módulo y resolver dependencias de nómina o disfrute. Apagar el modo o revertir un commit no revierte esos documentos.
- Si se aprobó un cambio de acceso, revertir únicamente ese cambio identificado, conservando los permisos anteriores. No ejecutar `reset-perms`.
- Los cambios de este documento son solo documentación: su commit puede revertirse sin modificar el sitio.

## Límites y riesgo

La configuración del modo nuevo es global al sitio, aunque el procesamiento exige inscripción explícita. Durante el piloto hay que controlar el inventario completo de inscripciones y los operadores con acceso. La liquidación puede crear documentos económicos o de licencia; la comprobación de acceso no equivale a autorización para todas esas acciones. No hay cambios autorizados aquí sobre `igcaribe.com`, generación masiva de Attendance ni penalizaciones de nómina.

El piloto estará completo cuando exista evidencia real de interfaz, cálculo, revisión, liquidación, descanso y automatización delimitada conforme al plan. El objetivo total requiere además comprobar los restantes criterios de aceptación del plan original; un caso excluido por mezclar obligaciones debe registrarse como limitación, sin inventar tiempo ni cerrar su reclamación.


## Readback posterior a los bloques de configuración y pago combinado

Al verificar el código basado en `237748b` de Desarrollo: no hay políticas publicadas, el modo por marcaciones y la publicación están apagados. Las cuatro autorizaciones anteriores siguen Queued/evidence_enrolled0. System Settings mantiene enable_scheduler0 y el helper del core confirma scheduler_disabled=true; conf.pause_scheduler0 por sí solo no describía ese estado completo.

La prueba nativa de Dietas volvió a pasar con las cuentas existentes de Finanzas (dos empleados elegibles en su alcance) y Gestión Humana (57), sin ampliar roles. Inserción sin ignore_permissions, vínculos de horas extra vacíos, lectura/listado, protección de estados y duplicados; todo revertido. Esto demuestra permisos de servidor, no una sesión HTTP con esas cuentas.

El job puntual `igcaribe.fortabs.com::overtime-dev-probe-73d4ddd66265425ea5616a149185f780` terminó finished/ok=true en worker `88ce6141638340e2890a486a203070e1`. Diez firmas de código/archivo coincidieron, incluidos política, pago híbrido e inclusión en nómina. Ejemplos sintéticos con base salarial cubierta: efectivo115 o215 según opción; pago feriado115 junto al descanso. El diagnóstico prohíbe escrituras SQL, commit, correo y nuevas colas. No crea créditos ni demuestra un piloto financiero en background; las pruebas nativas de esas operaciones permanecen separadas.

La simulación posterior de tres días de julio encontró las 14 marcas excluidas y la sincronización del turno sin completar. Las variantes hipotéticas mantienen los datos originales y no certifican trabajo. Dos días con IN consecutivos quedan en revisión en ambas reglas de dirección. El empleado de la muestra no está en el ámbito actual de Finanzas; revisar con un operador ya autorizado o seleccionar otra muestra, sin ampliar roles automáticamente. Se generó el informe; no se registró aceptación del operador ni se activó el piloto.
