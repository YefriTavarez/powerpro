# Matriz de revisión antes del piloto

Desarrollo `igcaribe.fortabs.com`. Decisiones parcialmente confirmadas; no activa reglas ni liquida registros.

## Decisiones confirmadas por el usuario — 12 de septiembre de 2026

Base de nocturnidad: `Clock overlap`. Ante la elección entre el tramo 21:00–07:00 y toda la jornada clasificada nocturna, el usuario respondió: «Solo las horas que estan despues de las 9pm.» Se conserva el límite de las 07:00 de la pregunta y se aplica el recargo únicamente al tiempo efectivamente trabajado en ese tramo. No se extiende a las horas diurnas de la misma jornada. Esta decisión funcional queda registrada; no aprueba las otras combinaciones ni activa el sitio.

Hora extra de banda +35% coincidente con nocturnidad: el usuario confirmó sumar 35% y 15% sobre la misma tarifa base, para un recargo total de 50%. Ejemplo: RD$100 de base + RD$35 extraordinarios + RD$15 nocturnos = RD$150 por esa hora. No aplicar 15% sobre RD$135 ni interpretar toda hora nocturna como extraordinaria. Esta confirmación corresponde a la banda de 35%; no convierte en 35% la banda extraordinaria de 100% ni decide feriados/descanso semanal. No cambia configuración del sitio.

Feriado y nocturnidad: tras revisar los arts. 204–205, el usuario indicó «Entonces tenemos que aplicar eso mismo». Se confirma la suma de 100% y 15% sobre la tarifa normal: RD$215 totales por RD$100/h. Si esa base ya está incluida en el sueldo, el adicional es RD$115; si no lo está, RD$215. Una cobertura parcial reduce únicamente la parte de base ya cubierta. La autorización no decide la coincidencia con descanso semanal ni activa el piloto.

Implementación: en el motor por marcaciones, la acción **Base salarial del feriado** registra las horas cubiertas (también cero) y una referencia salarial. La declaración es una evaluación inmutable, vinculada al origen, empleado, jornada, tarifa y política. Una base mensual por sí sola no demuestra cobertura de estas horas. La declaración no certifica automáticamente el pago ni genera salarios: el operador debe sustentar su referencia y después procesar/revisar la conciliación. Un cambio en la evidencia exige nueva revisión. Las fuentes ya liquidadas no admiten cambiarla directamente.

Esta hoja hace concretas las decisiones pendientes del plan. Los importes se obtuvieron ejecutando los calculadores actuales de PowerPro con una tarifa sintética de RD$100/hora. No son importes de empleados. La coincidencia entre una prueba y el código no constituye validación laboral.

## Referencia y decisiones

El texto consultado del Código distingue 21:00–07:00 y clasifica como nocturna la jornada mixta con al menos tres horas nocturnas (art.149). [Publicación del Ministerio de Trabajo](https://transparencia.mt.gob.do/images/docs/publicaciones/codigo-de-trabajo.pdf).

Los arts.203–205 establecen recargos de horas extraordinarias, nocturnidad y feriado. Los arts.163–165 regulan descanso semanal continuo, elección entre efectivo y descanso compensatorio y coincidencia con días no laborables. Estos artículos deben examinarse conjuntamente para aprobar las combinaciones; no se presenta una suma del software como interpretación legal definitiva. [Gaceta Oficial, arts.203–205, páginas PDF 870–871](https://bibliotecadelcongreso.gob.do/gaceta/Gaceta_oficial_1992.pdf#page=870), [arts.163–165, página PDF 864](https://bibliotecadelcongreso.gob.do/gaceta/Gaceta_oficial_1992.pdf#page=864).

| Decisión | Comportamiento disponible / límite | Evidencia requerida para cerrar |
|---|---|---|
| Base de nocturnidad | Usuario seleccionó `Clock overlap` el 12 de septiembre de 2026: solo horas efectivamente trabajadas entre 21:00 y 07:00. | Selección funcional confirmada. Validar los ejemplos del piloto con esa base; no volver a pedir al usuario la misma selección. |
| Recargos coincidentes | Confirmados: extra35 + noche15 = recargo50; feriado100 + noche15 = recargo115. Base incluida una sola vez, con declaración explícita de cobertura salarial del feriado. | Resolver las restantes coincidencias, incluyendo exceso semanal y feriado con descanso semanal; este último continúa bloqueado. |
| Régimen y semana | El motor necesita evidencia semanal completa; los controles distinguen escenarios con excepciones documentadas. | Empleados/puestos y fechas cubiertos, fundamento de excepciones y calendario laboral aplicable. |
| Descanso | Registra elección, programación y disfrute; no basta crear saldo. | Casos elegibles, duración continua, conversión a días de licencia y fecha de disfrute. No asumir cuatro horas por día como regla general. |
| Marcaciones | Alternancia o IN/OUT estricto; pares o primera/última marca según Shift Type. Conflictos requieren revisión. | Regla de pausas, tolerancias y garantía de sincronización; respaldo admisible para declaraciones completas. |

La búsqueda de vigencia encontró una comunicación de Presidencia del 17 de junio de 2026 que todavía describe acuerdos pendientes en la reforma. Eso no certifica su estado a la fecha del piloto: la validación debe identificar el texto promulgado aplicable y sus efectos, si los hay. [Comunicado de Presidencia](https://www.presidencia.gob.do/noticias/presidente-abinader-reafirma-posicion-del-gobierno-de-mantener-la-cesantia-y-llama-al).

## Aritmética actualmente implementada

Importes adicionales por una hora. El sueldo base ordinario ya cubierto por nómina no se vuelve a sumar. Una hora extra incluye su base una vez. Estos casos suponen que la clasificación, la evidencia y la elección requerida ya fueron validadas.

| Caso | RD$ adicionales |
|---|---:|
| Una hora extra en banda +35% | 135.00 |
| Una hora extra en banda +100% | 200.00 |
| Una hora extra +35% y nocturnidad | 150.00 |
| Una hora extra +100% y nocturnidad | 215.00 |
| Una hora en feriado, base no cubierta por sueldo | 200.00 |
| Una hora en feriado y nocturnidad, base no cubierta | 215.00 |
| Una hora en feriado, base cubierta por sueldo | 100.00 |
| Una hora en feriado y nocturnidad, base cubierta | 115.00 |
| Una hora en feriado y nocturnidad, media hora de base cubierta | 165.00 |
| Una hora en descanso semanal, elección efectivo | 200.00 |
| Una hora en descanso semanal y nocturnidad, elección efectivo | 215.00 |

Feriado coincidente con descanso semanal: **bloqueado** por el servicio común de evidencia; todavía requiere una regla conjunta implementada y aprobada. El calculador aritmético de bajo nivel no sustituye esa validación.

## Diferencia concreta de nocturnidad

Jornada sin pausa que inicia a las 18:00; turno ordinario hasta las 20:00 y prolongación autorizada hasta la salida. Tarifa RD$100/h y banda extra del 35%. La tabla separa el adicional ordinario del importe de horas extras.

| Salida | Regla | Clase | Horas nocturnas de reloj | Adicional ordinario | Horas extras y nocturnidad extra | Total adicional |
|---|---|---|---:|---:|---:|---:|
| 2026-09-21T23:59:00 | Clock overlap | Mixta | 2.9833 | 0.00 | 582.50 | 582.50 |
| 2026-09-21T23:59:00 | Whole nocturnal session | Mixta | 2.9833 | 0.00 | 582.50 | 582.50 |
| 2026-09-22T00:00:00 | Clock overlap | Nocturna | 3.0000 | 0.00 | 585.00 | 585.00 |
| 2026-09-22T00:00:00 | Whole nocturnal session | Nocturna | 3.0000 | 30.00 | 600.00 | 630.00 |
| 2026-09-22T00:01:00 | Clock overlap | Nocturna | 3.0167 | 0.00 | 587.50 | 587.50 |
| 2026-09-22T00:01:00 | Whole nocturnal session | Nocturna | 3.0167 | 30.00 | 602.50 | 632.50 |

A medianoche la diferencia es RD$45: el recargo de toda la jornada añade RD$30 sobre dos horas ordinarias y RD$15 sobre una hora extra anterior a las 21:00. El usuario debe poder revisar esa diferencia antes de aprobar la regla aplicable.

## Registro de aprobación pendiente

Completar responsable y referencia de validación laboral, empresa, vigencia, régimen aplicable, regla nocturna, cada combinación de recargos, reglas de descanso y muestra de empleados/autorizaciones del piloto. Si un caso queda sin resolver, excluirlo expresamente del piloto y mantenerlo pendiente; esa exclusión no completa el objetivo de implementarlo.

No hay ninguna `Overtime Pay Policy` guardada en el sitio al hacer esta revisión. El modo nuevo sigue desactivado. Tampoco se ha decidido cambiar las cuatro autorizaciones inscritas en el modo anterior.

## Reproducir y verificar

✅ Sin sitio ni conexión a base de datos: `python3 scripts/preview_overtime_policy_matrix.py` desde el repositorio. Lee los calculadores puros instalados y devuelve JSON con `approved=false` y `settlement_ready=false`. No modifica configuración, nómina ni licencias.

La prueba nativa `tests/dev_dieta_direct_roles.py` requiere explícitamente Desarrollo. Verifica con las cuentas existentes de Finanzas y Gestión Humana la creación sin convocatoria/autorización, lectura/lista, estados protegidos y duplicados, y revierte sus solicitudes. No prueba autenticación HTTP ni la interfaz de una sesión de usuario.
