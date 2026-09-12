# Revisión de una muestra real de marcaciones

Herramienta de lectura para el paso de simulación del piloto. No activa reglas,
crea autorizaciones, aprueba asistencia ni calcula salarios de empleados.

## Ejecutar en Desarrollo

✅ Desde `/opt/erpnext/igcaribe-bench/sites`, con la identidad administrativa del
bench, ejecutar `../env/bin/python ../apps/powerpro/scripts/preview_overtime_checkin_sample.py 'NOMBRE DEL EMPLEADO' AAAA-MM-DD AAAA-MM-DD`.
El script exige `igcaribe.fortabs.com`, `developer_mode=1` y Administrator; admite
de una a siete fechas históricas de turnos diurnos. Rechaza asignaciones ambiguas,
turnos que cruzan fecha y muestras excesivas. No es un método HTTP.

El resultado JSON contiene:

- Marcaciones originales y sus identificadores, opciones actuales del turno,
  calendario resuelto, asignaciones y fuentes de horas extras existentes.
- Diagnóstico con las exclusiones y la sincronización actuales, sobre una
  **ventana propuesta sin guardar**. No representa una autorización válida.
- Cuatro comparaciones hipotéticas: alternancia/IN-OUT estricto, combinadas con
  primera-última/cada par. Solo en esas copias se supone que las exclusiones fueron
  revisadas y la sincronización está completa. Las fechas y los IN/OUT se conservan.
- Recargo nocturno por reloj o por jornada nocturna completa, cuando hay
  intervalos interpretables. No se validan bandas semanales ni importes a pagar.
- Hashes de los datos originales releídos y contadores antes/después. Durante la
  consulta se rechazan escrituras SQL, commit, encolado, correo y Error Log.

## Resultado observado en la muestra de julio

La ejecución del 12 de septiembre tomó tres fechas de un empleado con marcaciones
disponibles en Desarrollo: 20, 27 y 31 de julio. Los detalles identificables se
entregan en el informe local de la tarea, fuera del repositorio.

Las 14 marcas de la muestra tienen `skip_auto_attendance=1`. El turno carece de
`last_sync_of_checkin`. Por eso los tres diagnósticos actuales quedan en Waiting
con exclusiones y falta de pares utilizables. **No se corrigieron esas marcas**.

En la comparación hipotética del día 20, primera-última suma 13:47:09; cada par
suma 12:50:19. La diferencia es la pausa de 00:56:50. El tiempo posterior a las
21:00 es 00:42:31. Primera-última además conserva para revisión el tramo temprano
anterior al turno. Estos intervalos son una interpretación condicional, no horas
aprobadas ni una constatación de trabajo continuo.

Los días 27 y 31 tienen cinco marcaciones, incluyendo entradas consecutivas. La
alternancia detecta cantidad impar y la regla estricta detecta IN consecutivos;
ambas requieren revisión. Los intervalos parciales que muestre una variante no
pueden tratarse como una liquidación válida ni como horas cero.

La muestra no demuestra jornada nocturna de tres horas, cruce de medianoche,
feriado, descanso compensatorio o liquidación. Esos casos conservan sus pruebas
controladas y necesitan aceptación operativa dentro del alcance del piloto.

## Próximo paso concreto

Revisar el informe y la razón por la que estas marcaciones están excluidas. No
retirar masivamente exclusiones ni inventar una fecha de sincronización. Si se
usan estos días para revisión histórica, emplear la declaración/revisión de
evidencia existente con respaldo del operador; para el piloto automático, elegir
marcaciones completas, no excluidas, y autorizaciones nuevas con vigencia explícita.
No se activa el scheduler global: existen fuentes inscritas en el modo anterior.

La cuenta de Finanzas consultada no tiene este empleado dentro de su ámbito de
Employee. La muestra puede revisarla un operador ya autorizado; no se ampliaron
roles ni se creó una sesión de esa cuenta. La revisión humana sigue pendiente.

Reversión: el script y esta documentación no cambian el sitio. Revertir su commit
retira la herramienta; no hay documentos empresariales que cancelar.
