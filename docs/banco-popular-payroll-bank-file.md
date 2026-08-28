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
3. Completar fecha, secuencia de siete dígitos y descripción del pago.
4. Guardar y usar **Cargar pagos sometidos**.
5. Corregir todo registro bloqueado y volver a cargar el lote.
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
- Cada línea contiene exactamente 320 bytes en Windows-1252 y termina en CRLF.
- El archivo generado es privado e inmutable para el lote aprobado.

## Reversión

Antes de entregar el TXT al banco, se puede cancelar el lote y crear una
enmienda con una secuencia nueva. La cancelación conserva el archivo privado y
su huella como evidencia. Si el banco ya recibió o procesó el archivo, no se
debe asumir que cancelar el lote revierte el pago: la corrección debe acordarse
con el banco y manejarse como una operación separada.

Para retirar la funcionalidad del sitio, revertir el cambio de PowerPro y
ejecutar la migración aprobada. Los lotes y archivos privados existentes deben
conservarse o eliminarse solo conforme a la política de retención de nómina.
