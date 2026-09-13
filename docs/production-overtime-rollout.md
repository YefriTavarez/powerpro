# Despliegue de horas extras a Producción

Destino autorizado: `igcaribe.com`, sitio alojado `igcaribe.erpnext.com`, grupo `bench-14655` (`igcaribe-bench`). El sitio parte de PowerPro `094bdb9`; Frappe15.120.1, ERPNext15.121.2 y HRMS15.64.0 se mantienen.

La rama de despliegue integra los commits guardados de Desarrollo hasta `3017e9a` y el historial publicado del lote bancario. El árbol de código de `powerpro/` coincide exactamente con aquel commit de Desarrollo. Las dos modificaciones sin commit del controlador de autorizaciones del VPS quedan fuera y conservaron sus hashes.

## Validación

Las suites Python aisladas de Dietas, horas extras, calendario, jornada real, descanso y nocturnidad pasaron; las12 pruebas que requieren DB se omitieron expresamente en el entorno local. También pasaron las7 pruebas de feriado/descanso combinado,12 del archivo bancario y60 de nómina mixta y reglas dominicanas. Las pruebas UI de conciliación, revisión, calendario, nocturnidad, descanso, incidencias, lote bancario y las10 de Dietas pasaron.

Dos simulaciones de tests estaban desactualizadas: la conciliación ahora consulta también la cobertura de base del feriado, y la vista de pago de Dietas utiliza `frappe.datetime.str_to_user`. Se corrigieron únicamente esos adaptadores de prueba. Los163 archivos Python/JSON modificados pasan revisión sintáctica.

## Activación y comprobación

Instalar código y metadatos no habilita conciliación automática, políticas de pago ni declaraciones salariales. Conservar las opciones existentes; releer los nuevos controles y confirmar que los procesos nuevos permanecen apagados por defecto. Las decisiones del piloto de Desarrollo no son fixtures de Producción. No se copian marcaciones, evidencia documental ni salarios de la muestra durante el deployment.

Antes de actualizar se registraron por REST versiones, ajustes, metadatos y contadores. Frappe Cloud debe completar respaldo, construcción y actualización del sitio sin omitir parches fallidos. Después se verificará el commit instalado, los módulos nuevos, los enlaces opcionales de Dietas, los permisos efectivos y los contadores. Un job de build terminado no prueba actualización del sitio.

## Reversión

Conservar el bench previo `bench-14655-000565-f5v`, PowerPro `094bdb9` y el respaldo anterior al cambio. Ante un fallo, revisar el resultado de recuperación de Frappe Cloud antes de otra operación. Para volver al código anterior, usar el flujo nativo de actualización al bench previo; la retirada del código no borra nuevos campos ni auditorías. Si hubiera que recuperar datos desde respaldo, delimitar las escrituras posteriores y obtener autorización específica para esa restauración. No ejecutar restauraciones ni SQL destructivo automáticamente.

## Trabajo separado

Tras verificar el despliegue se retomará la cancelación nativa de la nómina que el operador identificó como prueba. Primero se releerán sus dependencias para descartar movimientos bancarios externos. La importación definitiva de horas y la resolución del feriado coincidente con descanso conservan su revisión independiente.
