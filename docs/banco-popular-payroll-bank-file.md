# Archivo de nómina Banco Popular

PowerPro genera el TXT de pago a cuentas del Banco Popular desde un lote
auditable basado en comprobantes de nómina sometidos. La primera versión solo
acepta cuentas del Banco Popular y pagos en pesos dominicanos (DOP).

## Configuración inicial

1. Crear un **Bank File Profile** para la empresa.
2. Registrar exactamente como lo suministró el banco:
   - número de activación;
   - RNC;
   - razón social registrada.
3. Marcar un solo perfil como predeterminado para la empresa.
4. Completar en cada **Employee** el banco, la cuenta, el tipo de cuenta, el
   documento de identidad y su tipo.

El número de activación y los datos bancarios no deben almacenarse en código.

## Flujo operativo

1. Someter la nómina y sus Salary Slips.
2. Desde Payroll Entry, usar **Acciones > Crear lote Banco Popular**.
3. Completar la fecha y descripción del pago. La secuencia se asigna
   automáticamente al guardar: `0000001`, `0000002`, etc., por **fecha de pago**.
   Cada fecha tiene su propio contador, también al cambiar de mes o año.
4. Guardar el borrador, inicialmente sin detalles, y usar **Acciones > Cargar
   pagos sometidos**. La tabla es de solo lectura: no se agregan ni eliminan
   empleados manualmente.
5. Revisar las observaciones de cada registro bloqueado, corregir los datos en
   su registro de origen (Employee o Salary Slip, según corresponda) y volver a
   cargar el lote. No cancelar ni modificar una nómina sometida sin revisar su
   impacto contable. Los datos bancarios incompletos se guardan para revisión,
   pero impiden aprobar el lote y generar el TXT.
6. Someter el lote cuando el resultado sea **Ready**.
7. Usar **Generar TXT privado** y descargar el archivo adjunto.
8. Comparar cantidad, monto total y SHA-256 antes de entregarlo al banco.

La generación no crea Bank Entry, Payment Entry ni Journal Entry, y tampoco
sube el archivo al Banco Popular. La aprobación del banco y la contabilización
continúan siendo pasos operativos separados.

## Controles

- Un lote solo usa Salary Slips sometidos y no retenidos.
- El monto es el `net_pay` guardado en cada Salary Slip.
- El detalle se ordena por nombre del empleado y luego por Salary Slip.
- Una Salary Slip no puede pertenecer a dos lotes activos.
- La secuencia no se puede repetir para el mismo perfil y fecha de pago.
- El contador diario es común a todos los perfiles del sitio y reserva números
  de forma transaccional para evitar duplicados entre guardados simultáneos.
  Continúa después de las secuencias anteriores, incluidos los lotes cancelados.
- Guardar de nuevo o cargar pagos conserva la secuencia. Cambiar la fecha de
  un borrador asigna el siguiente número de la nueva fecha; duplicar o enmendar
  un lote también obtiene un número nuevo. Los números reservados por lotes
  guardados no se reutilizan, incluso si después se eliminan o cancelan.
- La secuencia es de solo lectura. Los lotes aprobados y TXT ya generados
  conservan su fecha y secuencia. Al llegar a `9999999`, se bloquean nuevas
  reservas para esa fecha en lugar de generar un número de ocho dígitos.
- Cada línea contiene exactamente 320 bytes en Windows-1252 y termina en CRLF.
- El archivo generado es privado e inmutable para el lote aprobado.
- Un borrador vacío se guarda como **Pending**; uno con datos bancarios
  incompletos queda **Blocked**. Ninguno puede someterse ni generar archivos.

## Pruebas del flujo de borrador

La suite `powerpro.power_pro.doctype.payroll_bank_batch.test_payroll_bank_batch`
usa persistencia real de Frappe y fuentes de nómina sintéticas, con rollback por
prueba. Ejecutarla solo en un sitio de desarrollo/pruebas. Cubre guardado vacío,
limpieza de filas antiguas completamente vacías, carga con datos incompletos,
bloqueo de aprobación/generación y persistencia del estado **Approved**.

`node --test tests/test_payroll_bank_batch_ui.cjs` verifica los eventos del
formulario con un modelo simulado de Desk; no sustituye una prueba de navegador.

## Reversión

Antes de entregar el TXT al banco, se puede cancelar el lote y crear una
enmienda con una secuencia nueva. La cancelación conserva el archivo privado y
su huella como evidencia. Si el banco ya recibió o procesó el archivo, no se
debe asumir que cancelar el lote revierte el pago: la corrección debe acordarse
con el banco y manejarse como una operación separada.

Para retirar la funcionalidad del sitio, revertir el cambio de PowerPro y
ejecutar la migración aprobada. Los lotes y archivos privados existentes deben
conservarse o eliminarse solo conforme a la política de retención de nómina.
