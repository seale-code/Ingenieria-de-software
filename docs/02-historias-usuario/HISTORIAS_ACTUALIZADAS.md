# Historias de usuario — revisión de cobertura DOC-01

Fuente: [PDF original HU01–HU15](HistoriasdeUsuario-Inkafarma.pdf), conservado sin cambios. Base actual `daa9716` (PR #57); matriz histórica v6 basada en `53b6ff8`. Se reproduce el texto de historia y criterios para mantener trazabilidad; los estados por criterio siguen la matriz v6, con notas de remediación; son una evaluación técnica preliminar, no aceptación formal. Las adaptaciones requieren aprobación del equipo.

## HU01 — Consulta de disponibilidad de medicamentos

Como paciente que necesita comprar un medicamento, quiero consultar la disponibilidad en diferentes boticas, para encontrar rápidamente dónde adquirirlo.

- CA1: DADO que el usuario busca un medicamento en la plataforma, CUANDO ingresa el nombre del producto, ENTONCES el sistema debe mostrar las boticas que tienen disponibilidad.
- CA2: DADO que existen varias boticas disponibles, CUANDO se muestran los resultados, ENTONCES deben ordenarse mostrando primero las más cercanas.
- CA3: DADO que un medicamento no tiene stock, CUANDO el usuario realiza la búsqueda, ENTONCES el sistema debe indicar que no está disponible.

**Cobertura técnica por criterio:** CA1: implementado; CA2: pendiente; CA3: implementado.

- CA1: Nombre/marca y disponibilidad por sucursal.
- CA2: La consulta pública no ordena sucursales por ubicación del usuario. La asignación sí calcula distancia.
- CA3: Ausencia de stock y filtrado de disponibles.

## HU02 — Reserva automática del medicamento

Como cliente que encontró un medicamento disponible, quiero reservarlo antes de acudir a la botica, para asegurar que el producto esté disponible cuando llegue.

- CA1: DADO que el medicamento tiene stock disponible, CUANDO el usuario confirma la reserva, ENTONCES el sistema debe bloquear temporalmente el producto.
- CA2: DADO que la reserva fue realizada, CUANDO la botica recibe la solicitud, ENTONCES debe recibir una notificación.
- CA3: DADO que la reserva supera el tiempo permitido, CUANDO no se concreta la compra, ENTONCES el sistema debe liberar nuevamente el stock.

**Cobertura técnica por criterio:** CA1: adaptado; CA2: adaptado; CA3: adaptado.

- CA1: Reserva al confirmar pedido de domicilio después de verificar contacto; no reserva independiente para recojo.
- CA2: Solicitud visible en bandeja y contador de pendientes; no aviso externo.
- CA3: Vence la asignación sin aceptación (15 minutos iniciales; límite total de 45 minutos); alternativa o cancelación/liberación.

## HU03 — Asignación automática de la mejor botica

Como usuario que necesita un medicamento, quiero que el sistema seleccione la mejor botica disponible, para comprar de manera rápida y conveniente.

- CA1: DADO que existen varias boticas con stock, CUANDO el usuario solicita una recomendación, ENTONCES el sistema debe evaluar distancia y disponibilidad.
- CA2: DADO que una botica tiene mayor cercanía y stock, CUANDO se genera la recomendación, ENTONCES debe aparecer como primera opción.
- CA3: DADO que una botica no puede atender el pedido, CUANDO se identifica la restricción, ENTONCES debe asignarse otra alternativa.

**Cobertura técnica por criterio:** CA1: adaptado; CA2: adaptado; CA3: implementado.

- CA1: Distancia geográfica al centro del distrito y stock completo.
- CA2: Elegibilidad por stock/capacidad y prioridad por distancia; no ETA de ruta.
- CA3: Otra sucursal conservando código e importes; sin alternativa cancela.

## HU04 — Compra mediante aplicación móvil

Como usuario con poco tiempo disponible, quiero comprar medicamentos desde una aplicación, para evitar trasladarme innecesariamente.

- CA1: DADO que el usuario tiene una cuenta registrada, CUANDO selecciona un medicamento, ENTONCES debe poder agregarlo al carrito.
- CA2: DADO que el usuario tiene productos seleccionados, CUANDO confirma la compra, ENTONCES debe recibir confirmación del pedido.
- CA3: DADO que la compra fue realizada, CUANDO termina el proceso, ENTONCES debe recibir información de entrega.

**Cobertura técnica por criterio:** CA1: parcial; CA2: implementado; CA3: implementado.

- CA1: Carrito disponible; falta cuenta registrada del cliente.
- CA2: Confirmación transaccional con UUID y cotización, previa verificación telefónica.
- CA3: Dirección/distrito y sucursal confirmados; seguimiento disponible.

## HU05 — Seguimiento del pedido

Como cliente que realizó una compra, quiero conocer el estado de mi pedido, para saber cuándo recibiré mi medicamento.

- CA1: DADO que existe un pedido confirmado, CUANDO el usuario ingresa al sistema, ENTONCES debe visualizar el estado actual.
- CA2: DADO que el pedido cambia de estado, CUANDO ocurre una actualización, ENTONCES el usuario debe recibir una notificación.
- CA3: DADO que el pedido está listo para recoger, CUANDO la botica confirma disponibilidad, ENTONCES debe informarse al cliente.

**Cobertura técnica por criterio:** CA1: implementado; CA2: parcial; CA3: parcial.

- CA1: Estado/historial por código completo.
- CA2: Actualización por consulta; sin notificación externa automática al cliente.
- CA3: Estado PREPARADO visible para domicilio; no aviso de recojo ni modalidad de recojo.

## HU06 — Notificación de disponibilidad

Como paciente que no encuentra un medicamento, quiero recibir una alerta cuando vuelva a estar disponible, para poder comprarlo oportunamente.

- CA1: DADO que un medicamento está agotado, CUANDO el usuario activa una alerta, ENTONCES el sistema debe registrar la solicitud.
- CA2: DADO que llega nuevo stock, CUANDO se actualiza la información, ENTONCES debe enviarse una notificación.
- CA3: DADO que el usuario recibe la alerta, CUANDO ingresa a la plataforma, ENTONCES debe poder realizar la compra.

**Cobertura técnica por criterio:** CA1: pendiente; CA2: pendiente; CA3: pendiente.

- CA1: No hay suscripción ni envío de avisos de reposición. Registrar entrada no equivale a notificar.
- CA2: No hay suscripción ni envío de avisos de reposición. Registrar entrada no equivale a notificar.
- CA3: No hay suscripción ni envío de avisos de reposición. Registrar entrada no equivale a notificar.

## HU07 — Comparación entre boticas

Como comprador, quiero comparar diferentes boticas, para elegir la opción más conveniente.

- CA1: DADO que existen varias opciones, CUANDO el usuario consulta un producto, ENTONCES debe visualizar precios y disponibilidad.
- CA2: DADO que existen diferencias entre establecimientos, CUANDO se muestran resultados, ENTONCES deben estar organizados claramente.
- CA3: DADO que el usuario selecciona una opción, CUANDO confirma, ENTONCES debe iniciar la compra.

**Cobertura técnica por criterio:** CA1: adaptado; CA2: implementado; CA3: implementado.

- CA1: Precios locales y stock por sucursal; no comparación con otras cadenas.
- CA2: Categorías, orden por precio y ficha.
- CA3: Agregar al carrito y continuar al pedido.

## HU08 — Compra para adultos mayores

Como adulto mayor, quiero realizar pedidos de medicamentos de forma sencilla, para obtener mis productos sin dificultades.

- CA1: DADO que el usuario tiene dificultades digitales, CUANDO utiliza la plataforma, ENTONCES debe encontrar opciones simples.
- CA2: DADO que necesita apoyo, CUANDO solicita ayuda, ENTONCES debe contar con asistencia.
- CA3: DADO que completa un pedido, CUANDO confirma, ENTONCES debe recibir una explicación clara.

**Cobertura técnica por criterio:** CA1: parcial; CA2: parcial; CA3: implementado.

- CA1: Recorridos móviles/teclado probados; falta evaluación con adultos mayores.
- CA2: Página de ayuda y soporte de operaciones; no asistencia humana conectada al cliente.
- CA3: Resumen antes de confirmar y código de consulta.

## HU09 — Control de pedidos cancelados

Como administrador de la plataforma, quiero controlar pedidos con riesgo de cancelación, para mejorar la disponibilidad del servicio.

- CA1: DADO que existe un pedido pendiente, CUANDO la botica no confirma stock, ENTONCES debe generarse una alerta.
- CA2: DADO que existe otra botica disponible, CUANDO ocurre una falla, ENTONCES debe reasignarse automáticamente.
- CA3: DADO que el pedido fue solucionado, CUANDO cambia de estado, ENTONCES debe registrarse.

**Cobertura técnica por criterio:** CA1: adaptado; CA2: implementado; CA3: implementado.

- CA1: Bandeja de pendientes con plazos por asignación y total; aceptación al preparar.
- CA2: Supervisor resuelve vencimiento, evita ciclos y respeta límite total de asignaciones pendientes.
- CA3: Historial de asignaciones e incidencia con solución.

## HU10 — Historial de compras

Como usuario frecuente, quiero revisar mis compras anteriores, para repetir pedidos fácilmente.

- CA1: DADO que el usuario realizó compras previas, CUANDO ingresa al historial, ENTONCES debe visualizar sus pedidos.
- CA2: DADO que encuentra un pedido anterior, CUANDO selecciona repetir compra, ENTONCES debe agregar nuevamente los productos.
- CA3: DADO que existen datos registrados, CUANDO consulta, ENTONCES debe proteger la información personal.

**Cobertura técnica por criterio:** CA1: pendiente; CA2: pendiente; CA3: parcial.

- CA1: No hay cuenta/historial de compras del usuario ni acción de repetir compra.
- CA2: No hay cuenta/historial de compras del usuario ni acción de repetir compra.
- CA3: Seguimiento oculta contactos; no existe consulta de historial por cuenta autenticada.

## HU11 — Atención mediante chat de soporte

Como usuario que tiene dudas sobre un medicamento o pedido, quiero recibir orientación mediante un chat de atención, para resolver mis consultas antes de realizar la compra.

- CA1: DADO que el usuario tiene una duda sobre un medicamento, CUANDO ingresa al chat de soporte, ENTONCES debe poder escribir su consulta y recibir respuesta.
- CA2: DADO que el usuario necesita información sobre un pedido, CUANDO solicita ayuda, ENTONCES el sistema debe permitir consultar el estado de la compra.
- CA3: DADO que la consulta requiere atención especializada, CUANDO el sistema identifica la necesidad, ENTONCES debe derivarla a un asesor.

**Cobertura técnica por criterio:** CA1: pendiente; CA2: parcial; CA3: pendiente.

- CA1: No existe chat de consulta/respuesta para clientes. Incidencias es un flujo interno de operaciones.
- CA2: Ayuda enlaza seguimiento; no consulta integrada en conversación de soporte.
- CA3: No existe derivación de conversación de cliente a asesor.

## HU12 — Disponibilidad mediante múltiples canales

Como cliente que utiliza diferentes medios de compra, quiero acceder a la disponibilidad de medicamentos desde canales físicos y digitales, para elegir la opción más conveniente.

- CA1: DADO que el usuario consulta un medicamento, CUANDO utiliza la aplicación o una botica afiliada, ENTONCES debe obtener información actualizada.
- CA2: DADO que el usuario inicia una compra en un canal, CUANDO cambia a otro canal, ENTONCES debe conservar la información del pedido.
- CA3: DADO que existen diferentes puntos de atención, CUANDO busca un producto, ENTONCES debe visualizar todas las opciones disponibles.

**Cobertura técnica por criterio:** CA1: parcial; CA2: pendiente; CA3: parcial.

- CA1: Datos de la misma aplicación/base; sin integración de canal físico.
- CA2: Persistencia local del carrito no acredita continuidad entre canal físico y digital.
- CA3: Se ofrece domicilio; no selector de modalidades multicanal.

## HU13 — Recomendación de productos alternativos

Como paciente que no encuentra un medicamento disponible, quiero recibir alternativas similares, para poder adquirir una opción adecuada.

- CA1: DADO que un medicamento no tiene disponibilidad, CUANDO el usuario realiza la búsqueda, ENTONCES el sistema debe mostrar alternativas existentes.
- CA2: DADO que existen productos equivalentes, CUANDO aparecen las opciones, ENTONCES deben mostrar información básica del producto.
- CA3: DADO que el usuario selecciona una alternativa, CUANDO confirma la compra, ENTONCES debe registrarse como nuevo pedido.

**Cobertura técnica por criterio:** CA1: pendiente; CA2: pendiente; CA3: pendiente.

- CA1: No existe servicio de equivalencias/alternativas de medicamentos. Diferida en backlog.
- CA2: No existe servicio de equivalencias/alternativas de medicamentos. Diferida en backlog.
- CA3: No existe servicio de equivalencias/alternativas de medicamentos. Diferida en backlog.

## HU14 — Gestión de inventario para boticas

Como administrador de una botica, quiero actualizar automáticamente mi inventario, para mantener información correcta de disponibilidad para los clientes.

- CA1: DADO que la botica realiza una venta, CUANDO el producto sale del inventario, ENTONCES el stock debe actualizarse automáticamente.
- CA2: DADO que llega nuevo medicamento al almacén, CUANDO se registra el ingreso, ENTONCES debe aumentar la disponibilidad mostrada.
- CA3: DADO que existe información incorrecta, CUANDO el administrador revisa el sistema, ENTONCES debe poder corregir los datos.

**Cobertura técnica por criterio:** CA1: adaptado; CA2: implementado; CA3: adaptado.

- CA1: Descuento al iniciar reparto; no integra venta de mostrador ni acreditación de cobro.
- CA2: Entrada aumenta físico/disponible con motivo y saldo.
- CA3: Corrección autorizada con cuenta personal y alcance de sede o central; escrituras auditadas.

## HU15 — Entrega rápida de medicamentos

Como usuario que necesita recibir un medicamento rápidamente, quiero que mi pedido sea asignado al establecimiento más adecuado, para recibirlo en el menor tiempo posible.

- CA1: DADO que el usuario solicita entrega a domicilio, CUANDO confirma la compra, ENTONCES el sistema debe seleccionar una botica con disponibilidad.
- CA2: DADO que existen varias boticas cercanas, CUANDO se asigna el pedido, ENTONCES debe considerar distancia y capacidad de atención.
- CA3: DADO que el pedido está en proceso de entrega, CUANDO cambia de estado, ENTONCES el usuario debe recibir una actualización.
- CA4: DADO que el pedido fue entregado, CUANDO finaliza la entrega, ENTONCES debe registrarse la confirmación.

**Cobertura técnica por criterio:** CA1: implementado; CA2: adaptado; CA3: parcial; CA4: implementado.

- CA1: Sucursal con el pedido completo.
- CA2: Distancia geográfica y capacidad de preparación; no tiempo real de reparto.
- CA3: Seguimiento web consultable durante reparto; sin push/SMS/correo.
- CA4: Recepción registra estado y fecha de forma atómica.

## Refinamientos propuestos sin duplicar HU

| HU | Criterios adicionales propuestos para aprobación |
|---|---|
| HU04 | Mostrar cotización del servidor con subtotal, envío y total; conservar importes al confirmar. |
| HU02/HU09 | Verificar contacto antes de reservar; aceptar antes del plazo por asignación y del límite total, reasignar sin ciclos, cancelar sin alternativa y liberar reservas. |
| HU14 | Registrar movimientos, saldos y motivo; impedir conteo inferior a reservas; evitar duplicación por reintento. |
| HU05/HU15 | Consultar cambios de sucursal y estado mediante código privado sin datos internos. |

El acceso operativo se documenta como requisito transversal RNF-03 y control SEC-01; no se crean HU16–HU19 sin acuerdo de alcance. Véase [requisitos](../01-requisitos/REQUISITOS.md) y [evidencia de logística](../06-evidencias/2026-11-16_logistica-sucursales.md).

**Referencia de cobertura:** [matriz v6](../01-requisitos/TRAZABILIDAD_IMPLEMENTACION.md) y [Remediación](../08-seguridad/REMEDIACION.md). Se mantiene la clasificación histórica por criterio hasta DOC-05; las notas anteriores reflejan los controles añadidos. No constituyen aceptación del Product Owner.
