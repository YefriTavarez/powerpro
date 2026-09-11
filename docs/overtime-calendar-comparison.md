# Comparación de horas extras por fecha

Primera entrega del plan de revisión laboral. Incluye un cálculo segmentado y una
comparación de solo lectura; todavía no sustituye la conciliación usada para liquidar.

## Uso

En una **Overtime Authorization** o **Retroactive Overtime Adjustment** guardada,
abrir **Horas extra → Comparar cálculo por fecha**. En una **Overtime Work Call**,
el mismo botón permite elegir una autorización accesible al usuario.

La tabla compara el motor vigente recalculado con el motor segmentado usando la
misma evidencia. No compara automáticamente contra una liquidación histórica:
esa liquidación pudo utilizar otra tarifa, configuración o evidencia.

Muestra horas por categoría, diferencias y detalle de cada fecha. Si el usuario
puede acceder a la tarifa aplicable —o ya está guardada en la liquidación visible—,
muestra importes ilustrativos. No se muestra un total de efectivo si hay descanso
semanal pendiente de definición. No hay botón de guardar, aprobar, pagar o crear licencias.

## Reglas cubiertas

- Divide intervalos al cambiar de fecha y aplica el calendario de cada fecha.
- Descuenta el turno ordinario de los días regulares, incluida la continuación de
  un turno nocturno anterior cuando corresponde.
- Aplica el máximo autorizado una vez a toda la ventana, en orden cronológico.
- Conserva las pausas observadas y separa los acumulados de semanas distintas.
- Cuenta solapamientos con el horario nocturno con precisión de segundos antes
  del redondeo de presentación.
- Falla si falta cobertura de calendario o hay intervalos inválidos/superpuestos.

## Evidencia y límites

Los documentos sin conciliación usan marcaciones actuales. Las instantáneas con
marcaciones usan las guardadas. Las verificaciones manuales usan sus intervalos
guardados; si sólo existen intervalos ya recortados, se avisa de esa limitación.
La asistencia presumida requiere revisión y no se convierte en evidencia real.

Ventanas de hasta 48 horas, dentro de las dos fechas cubiertas por el lector
actual de marcaciones. La comparación no infiere que un ponche ausente sea ausencia
laboral. Las advertencias de marcaciones se muestran, sin declarar validación.

Se conservan las tasas, bandas semanales y regla de solapamiento nocturno actuales.
Quedan pendientes la clasificación de jornada nocturna completa, la combinación
legal de recargos, el total semanal de todas las fuentes y el flujo completo de
descanso semanal. El calendario de la comparación es el actualmente configurado;
no es una reconstrucción garantizada del calendario histórico.

El resultado incluye versión, huella de entradas, contexto por fecha y origen de
evidencia. No se persiste. Los permisos se comprueban antes de leer evidencia; la
lista de autorizaciones utiliza filtros de permisos y cada comparación vuelve a
comprobar el documento. Los importes requieren acceso a la asignación salarial
efectiva cuando la tarifa no está ya en la liquidación visible.

## Pruebas

```sh
python3 tests/test_overtime_calendar.py
node tests/test_overtime_calendar_ui.cjs
python3 -m unittest discover -s powerpro/payroll_rules -p 'test_overtime*.py'
```

Son pruebas locales, sin base de datos. La verificación en Desarrollo debe comprobar
el endpoint con permisos reales, assets y ausencia de escrituras. No ejecutar jobs
de liquidación ni crear documentos pagables para comprobar esta vista previa.

## Instalación y reversión

Sólo añade módulos Python, un asset JS y un botón en tres formularios; no cambia
esquema, fixtures, configuración de tasas ni métodos del scheduler/liquidación.
Tras desplegar en Desarrollo, limpiar caché del sitio y recargar los formularios.
Las nuevas respuestas se obtienen únicamente al solicitar la comparación.

Para revertir, retirar el commit de esta entrega preservando cambios ajenos, limpiar
caché y recargar. No hay documentos de negocio que revertir por usar la comparación.
