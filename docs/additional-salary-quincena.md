# Aplicación por quincena de Salario Adicional

## Alcance y activación

Esta actualización es opt-in. La migración crea campos; no configura salarios
existentes, no crea ni recalcula recibos, no valida nóminas y no genera pagos.
Desplegar la revisión de PowerPro y ejecutar la migración normal del sitio antes
de usar los campos. No instalar únicamente los campos mediante un script: sin
la extensión de Salary Slip, HRMS no los interpretaría.

En Salario Adicional, marcar **Es recurrente** (si aún está en borrador), indicar
**Aplicación en Nómina** y **Aplicar desde el Mes** (primer día del mes). Se
conservan las fechas nativas Desde/Hasta y el componente y moneda del registro.
El importe con programación seleccionada es la base mensual, no un nuevo cargo
por cada quincena. El importe completo aplica en una sola nómina mensual
consolidada; en nóminas quincenales se distribuye según la opción seleccionada.
Las reglas existentes del componente, incluido un posible prorrateo por días,
se conservan. El motor distingue el período del recibo; no usa posting_date,
la fecha del equipo ni un día 30 fijo.

| Selección | Primera quincena | Segunda quincena |
|---|---:|---:|
| 50 % en cada quincena | Primera mitad redondeada | Resto del importe mensual |
| 100 % en la primera quincena | Base mensual | 0 |
| 100 % en la segunda quincena | 0 | Base mensual |

Los registros sin selección siguen el comportamiento nativo anterior.
No se trasladan automáticamente importes pendientes de una quincena a otra.
La división respeta el inicio de segunda quincena de Employee Supplement Settings,
con 16 como calendario estándar cuando no se dispone de esa configuración.
Se rechazan períodos parciales o frecuencias incompatibles en vez de cobrar
silenciosamente una cantidad estimada.

## Conservación de lo existente

La extensión se ejecuta en add_additional_salary_components del controlador
actual de Salary Slip. No sustituye la clase de PowerPro ni cambia sus cálculos
mensuales, TSS, ISR, ausencias, complementos, trabajo nocturno o salarios base.
La llamada sucede antes del cálculo de impuestos y es común al cálculo en
memoria, el formulario y la validación. No requiere generar Additional Salary
mensualmente: el recibo conserva el vínculo al único registro recurrente.
Los complementos automáticos y los registros clasificados como Coverage no
pueden reprogramarse por esta vía. Sus mecanismos actuales siguen siendo la
fuente de programación.

La validación impide cambios de programación/importe/vigencia que afecten
períodos con recibos validados dentro de la vigencia afectada. Los cambios y la
validación de nómina usan el bloqueo del empleado con el mismo orden de locks.
No se cancelan recibos, asientos ni documentos para eludir esa protección.
Un cambio posterior a la utilización requiere cerrar la vigencia previa y
registrar una nueva para un período no procesado, según el flujo nativo.

## Pruebas antes de activar producción

Las pruebas unitarias no sustituyen la verificación del sitio instalado.
En un sitio de ensayo representativo, usar el mismo empleado y registro activo
en dos recibos en memoria: 1–15 y 16–último día. Con segunda quincena se debe
obtener 0 y la base mensual respectivamente. Recalcular dos veces, confirmar que
no se repite el vínculo, comprobar el efecto esperado en total_deduction/net_pay,
y verificar previsualización, reporte y formato de impresión del sitio.
Comprobar también un registro puntual, uno sin programación y los complementos
del empleado. No validar recibos reales como prueba.

```sh
python -m unittest powerpro.payroll_rules.test_additional_salary_schedule \
  powerpro.controllers.test_additional_salary_schedule -v
python -m unittest discover -s powerpro/payroll_rules -t . -p 'test_*.py'
node --check powerpro/public/js/additional_salary_schedule.js
```

Las pruebas del controlador simulan lecturas y la frontera con HRMS. No prueban
la base de datos productiva, los permisos de usuarios reales ni los informes
personalizados guardados fuera del repositorio.

La API opcional configure_distribution requiere permiso de escritura y el
modified vigente, conserva la validación normal y no hace cambios de nómina.
El formulario también permite guardar los dos campos con allow_on_submit.
