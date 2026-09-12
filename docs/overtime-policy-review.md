# Matriz de revisión antes del piloto

Desarrollo `igcaribe.fortabs.com`. Pendiente de aprobación; no activa reglas ni liquida registros.

Esta hoja hace concretas las decisiones pendientes del plan. Los importes se obtuvieron ejecutando los calculadores actuales de PowerPro con una tarifa sintética de RD$100/hora. No son importes de empleados. La coincidencia entre una prueba y el código no constituye validación laboral.

## Referencia y decisiones

El texto consultado del Código distingue 21:00–07:00 y clasifica como nocturna la jornada mixta con al menos tres horas nocturnas (art.149). [Publicación del Ministerio de Trabajo](https://transparencia.mt.gob.do/images/docs/publicaciones/codigo-de-trabajo.pdf).

Los arts.203–205 establecen recargos de horas extraordinarias, nocturnidad y feriado. Los arts.163–165 regulan descanso semanal continuo, elección entre efectivo y descanso compensatorio y coincidencia con días no laborables. Estos artículos deben examinarse conjuntamente para aprobar las combinaciones; no se presenta una suma del software como interpretación legal definitiva. [Gaceta Oficial, arts.203–205, páginas PDF 870–871](https://bibliotecadelcongreso.gob.do/gaceta/Gaceta_oficial_1992.pdf#page=870), [arts.163–165, página PDF 864](https://bibliotecadelcongreso.gob.do/gaceta/Gaceta_oficial_1992.pdf#page=864).

| Decisión | Comportamiento disponible / límite | Evidencia requerida para cerrar |
|---|---|---|
| Base de nocturnidad | `Clock overlap` paga recargo solo en horas de reloj nocturnas. `Whole nocturnal session` lo extiende a la jornada clasificada nocturna. | Selección razonada y ejemplos aprobados por responsable laboral. No seleccionar solo por el menor importe. |
| Recargos coincidentes | Solo está implementada la suma sobre la hora base; el feriado y descanso semanal coincidentes bloquean la liquidación. | Fórmula para cada coincidencia, incluyendo exceso semanal; implementar lo que difiera antes de activar esos casos. |
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
| Una hora en feriado | 200.00 |
| Una hora en feriado y nocturnidad | 215.00 |
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
