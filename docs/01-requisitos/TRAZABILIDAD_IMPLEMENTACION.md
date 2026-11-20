# Trazabilidad de implementación v6

[CSV completo](TRAZABILIDAD_IMPLEMENTACION.csv) · [Requisitos](REQUISITOS.md) · [Ejecución de pruebas](../05-pruebas/VALIDACION_V6.md)

Base funcional `53b6ff8`; actualización documental del 20 de noviembre de 2026. Se mantienen los 46 criterios y cinco grupos de la matriz UML. El CSV agrega código, pruebas, resultado de verificación y PR sin modificar las historias originales.

## Lectura

- **Implementado:** existe el comportamiento descrito, con el alcance explícito del criterio.
- **Adaptado:** la implementación corresponde a una adaptación de negocio/entorno que requiere aceptación del equipo.
- **Parcial:** solo una parte del criterio original está disponible.
- **Pendiente:** no se acredita ese comportamiento.

Las referencias a pruebas se expresan como archivo::Clase.método. Su resultado concreto está en los registros de ejecución enlazados en Validación v6. Una prueba que pasa sobre una parte no acredita la aceptación de toda la HU. No se crea un porcentaje global de cumplimiento mezclando estados.

## Resumen por criterio

| Cobertura | Cantidad |
|---|---:|
| Implementado | 14 |
| Adaptado | 10 |
| Parcial | 10 |
| Pendiente | 12 |
| **Total** | **46** |

## Mapa de cobertura

| HU / criterio | Grupo | Cobertura | Alcance de la implementación |
|---|---|---|---|
| HU01 / CA1 | G01 | Implementado | Nombre/marca y disponibilidad por sucursal. |
| HU01 / CA2 | G01 | Pendiente | La consulta pública no ordena sucursales por ubicación del usuario. La asignación sí calcula distancia. |
| HU01 / CA3 | G01 | Implementado | Ausencia de stock y filtrado de disponibles. |
| HU07 / CA1 | G01 | Adaptado | Precios locales y stock por sucursal; no comparación con otras cadenas. |
| HU07 / CA2 | G01 | Implementado | Categorías, orden por precio y ficha. |
| HU07 / CA3 | G01 | Implementado | Agregar al carrito y continuar al pedido. |
| HU13 / CA1 | G01 | Pendiente | No existe servicio de equivalencias/alternativas de medicamentos. Diferida en backlog. |
| HU13 / CA2 | G01 | Pendiente | No existe servicio de equivalencias/alternativas de medicamentos. Diferida en backlog. |
| HU13 / CA3 | G01 | Pendiente | No existe servicio de equivalencias/alternativas de medicamentos. Diferida en backlog. |
| HU04 / CA1 | G02 | Parcial | Carrito disponible; falta cuenta registrada del cliente. |
| HU04 / CA2 | G02 | Implementado | Confirmación transaccional con UUID y cotización. |
| HU04 / CA3 | G02 | Implementado | Dirección/distrito y sucursal confirmados; seguimiento disponible. |
| HU08 / CA1 | G02 | Parcial | Recorridos móviles/teclado probados; falta evaluación con adultos mayores. |
| HU08 / CA2 | G02 | Parcial | Página de ayuda y soporte de operaciones; no asistencia humana conectada al cliente. |
| HU08 / CA3 | G02 | Implementado | Resumen antes de confirmar y código de consulta. |
| HU10 / CA1 | G02 | Pendiente | No hay cuenta/historial de compras del usuario ni acción de repetir compra. |
| HU10 / CA2 | G02 | Pendiente | No hay cuenta/historial de compras del usuario ni acción de repetir compra. |
| HU10 / CA3 | G02 | Parcial | Seguimiento oculta contactos; no existe consulta de historial por cuenta autenticada. |
| HU11 / CA1 | G02 | Pendiente | No existe chat de consulta/respuesta para clientes. Incidencias es un flujo interno de operaciones. |
| HU11 / CA2 | G02 | Parcial | Ayuda enlaza seguimiento; no consulta integrada en conversación de soporte. |
| HU11 / CA3 | G02 | Pendiente | No existe derivación de conversación de cliente a asesor. |
| HU12 / CA1 | G02 | Parcial | Datos de la misma aplicación/base; sin integración de canal físico. |
| HU12 / CA2 | G02 | Pendiente | Persistencia local del carrito no acredita continuidad entre canal físico y digital. |
| HU12 / CA3 | G02 | Parcial | Se ofrece domicilio; no selector de modalidades multicanal. |
| HU02 / CA1 | G03 | Adaptado | Reserva al confirmar pedido de domicilio; no reserva independiente para recojo. |
| HU02 / CA2 | G03 | Adaptado | Solicitud visible en bandeja y contador de pendientes; no aviso externo. |
| HU02 / CA3 | G03 | Adaptado | Vence la asignación sin aceptación; busca alternativa o cancela/libera. No vence por falta de pago una vez aceptada. |
| HU03 / CA1 | G03 | Adaptado | Distancia geográfica al centro del distrito y stock completo. |
| HU03 / CA2 | G03 | Adaptado | Elegibilidad por stock/capacidad y prioridad por distancia; no ETA de ruta. |
| HU03 / CA3 | G03 | Implementado | Otra sucursal conservando código e importes; sin alternativa cancela. |
| HU09 / CA1 | G03 | Adaptado | Pendientes de aceptación y límite en panel; iniciar preparación confirma atención, no integra inventario externo. |
| HU09 / CA2 | G03 | Implementado | Supervisor resuelve vencimiento y evita ciclos de sucursal. |
| HU09 / CA3 | G03 | Implementado | Historial de asignaciones e incidencia con solución. |
| HU05 / CA1 | G04 | Implementado | Estado/historial por código completo. |
| HU05 / CA2 | G04 | Parcial | Actualización por consulta; sin notificación externa automática al cliente. |
| HU05 / CA3 | G04 | Parcial | Estado PREPARADO visible para domicilio; no aviso de recojo ni modalidad de recojo. |
| HU15 / CA1 | G04 | Implementado | Sucursal con el pedido completo. |
| HU15 / CA2 | G04 | Adaptado | Distancia geográfica y capacidad de preparación; no tiempo real de reparto. |
| HU15 / CA3 | G04 | Parcial | Seguimiento web consultable durante reparto; sin push/SMS/correo. |
| HU15 / CA4 | G04 | Implementado | Recepción registra estado y fecha de forma atómica. |
| HU06 / CA1 | G05 | Pendiente | No hay suscripción ni envío de avisos de reposición. Registrar entrada no equivale a notificar. |
| HU06 / CA2 | G05 | Pendiente | No hay suscripción ni envío de avisos de reposición. Registrar entrada no equivale a notificar. |
| HU06 / CA3 | G05 | Pendiente | No hay suscripción ni envío de avisos de reposición. Registrar entrada no equivale a notificar. |
| HU14 / CA1 | G05 | Adaptado | Descuento al iniciar reparto; no integra venta de mostrador ni acreditación de cobro. |
| HU14 / CA2 | G05 | Implementado | Entrada aumenta físico/disponible con motivo y saldo. |
| HU14 / CA3 | G05 | Adaptado | Corrección protegida en panel/servicio; sin atribución a identidad individual de empleado. |

## Decisiones de aceptación

Los diagramas son del sistema objetivo y pueden representar funciones futuras. Las adaptaciones a domicilio, la ubicación por centro de distrito, los avisos por consulta y el acceso de operador compartido se declaran por criterio. La conformidad del agrupamiento de 17 diagramas requiere validación docente; no se considera aprobada por existir este CSV.

La referencia de PR identifica la entrega donde se incorporó el comportamiento; no sustituye el acuerdo del Product Owner o del equipo. Los resultados históricos se conservan en sus informes fechados.
