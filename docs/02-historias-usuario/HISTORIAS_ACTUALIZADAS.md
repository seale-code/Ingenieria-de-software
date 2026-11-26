# Historias de usuario — revisión de cobertura DOC-01

Fuente: [PDF original HU01–HU15](HistoriasdeUsuario-Inkafarma.pdf), conservado sin cambios. Base `53b6ff85a4904c6c3f1beb6c73ab4601c4b14886`. Se reproduce el texto de historia y criterios para mantener trazabilidad; los estados son una evaluación técnica preliminar, no aceptación formal. Las adaptaciones requieren aprobación del equipo.

## HU01 — Consulta de disponibilidad de medicamentos

Como paciente que necesita comprar un medicamento, quiero consultar la disponibilidad en diferentes boticas, para encontrar rápidamente dónde adquirirlo.

- CA1: DADO que el usuario busca un medicamento en la plataforma, CUANDO ingresa el nombre del producto, ENTONCES el sistema debe mostrar las boticas que tienen disponibilidad.
- CA2: DADO que existen varias boticas disponibles, CUANDO se muestran los resultados, ENTONCES deben ordenarse mostrando primero las más cercanas.
- CA3: DADO que un medicamento no tiene stock, CUANDO el usuario realiza la búsqueda, ENTONCES el sistema debe indicar que no está disponible.

**Estado:** Parcial. CA1 y CA3: búsqueda y stock; CA2 pendiente: stock ordenado por código de sucursal, no cercanía.

## HU02 — Reserva automática del medicamento

Como cliente que encontró un medicamento disponible, quiero reservarlo antes de acudir a la botica, para asegurar que el producto esté disponible cuando llegue.

- CA1: DADO que el medicamento tiene stock disponible, CUANDO el usuario confirma la reserva, ENTONCES el sistema debe bloquear temporalmente el producto.
- CA2: DADO que la reserva fue realizada, CUANDO la botica recibe la solicitud, ENTONCES debe recibir una notificación.
- CA3: DADO que la reserva supera el tiempo permitido, CUANDO no se concreta la compra, ENTONCES el sistema debe liberar nuevamente el stock.

**Estado:** Adaptada. CA1: reserva del pedido; CA2: bandeja operativa, no aviso externo; CA3: vence la aceptación, no la compra para recojo.

## HU03 — Asignación automática de la mejor botica

Como usuario que necesita un medicamento, quiero que el sistema seleccione la mejor botica disponible, para comprar de manera rápida y conveniente.

- CA1: DADO que existen varias boticas con stock, CUANDO el usuario solicita una recomendación, ENTONCES el sistema debe evaluar distancia y disponibilidad.
- CA2: DADO que una botica tiene mayor cercanía y stock, CUANDO se genera la recomendación, ENTONCES debe aparecer como primera opción.
- CA3: DADO que una botica no puede atender el pedido, CUANDO se identifica la restricción, ENTONCES debe asignarse otra alternativa.

**Estado:** Adaptada. CA1–CA3: asignación automática y alternativa por stock completo, distancia y capacidad; no lista de recomendaciones al cliente.

## HU04 — Compra mediante aplicación móvil

Como usuario con poco tiempo disponible, quiero comprar medicamentos desde una aplicación, para evitar trasladarme innecesariamente.

- CA1: DADO que el usuario tiene una cuenta registrada, CUANDO selecciona un medicamento, ENTONCES debe poder agregarlo al carrito.
- CA2: DADO que el usuario tiene productos seleccionados, CUANDO confirma la compra, ENTONCES debe recibir confirmación del pedido.
- CA3: DADO que la compra fue realizada, CUANDO termina el proceso, ENTONCES debe recibir información de entrega.

**Estado:** Parcial. CA1: carrito sin cuenta registrada; CA2 y CA3: confirmación e información de entrega web.

## HU05 — Seguimiento del pedido

Como cliente que realizó una compra, quiero conocer el estado de mi pedido, para saber cuándo recibiré mi medicamento.

- CA1: DADO que existe un pedido confirmado, CUANDO el usuario ingresa al sistema, ENTONCES debe visualizar el estado actual.
- CA2: DADO que el pedido cambia de estado, CUANDO ocurre una actualización, ENTONCES el usuario debe recibir una notificación.
- CA3: DADO que el pedido está listo para recoger, CUANDO la botica confirma disponibilidad, ENTONCES debe informarse al cliente.

**Estado:** Parcial. CA1: consulta por código; CA2: actualización manual, sin notificación activa; CA3: recojo no implementado.

## HU06 — Notificación de disponibilidad

Como paciente que no encuentra un medicamento, quiero recibir una alerta cuando vuelva a estar disponible, para poder comprarlo oportunamente.

- CA1: DADO que un medicamento está agotado, CUANDO el usuario activa una alerta, ENTONCES el sistema debe registrar la solicitud.
- CA2: DADO que llega nuevo stock, CUANDO se actualiza la información, ENTONCES debe enviarse una notificación.
- CA3: DADO que el usuario recibe la alerta, CUANDO ingresa a la plataforma, ENTONCES debe poder realizar la compra.

**Estado:** Pendiente. CA1–CA3: no se identificó suscripción ni aviso de reposición.

## HU07 — Comparación entre boticas

Como comprador, quiero comparar diferentes boticas, para elegir la opción más conveniente.

- CA1: DADO que existen varias opciones, CUANDO el usuario consulta un producto, ENTONCES debe visualizar precios y disponibilidad.
- CA2: DADO que existen diferencias entre establecimientos, CUANDO se muestran resultados, ENTONCES deben estar organizados claramente.
- CA3: DADO que el usuario selecciona una opción, CUANDO confirma, ENTONCES debe iniciar la compra.

**Estado:** Parcial. CA1–CA3: precio de catálogo, stock por sucursal y carrito; no comparación de precios diferenciados ni selección de sucursal para compra.

## HU08 — Compra para adultos mayores

Como adulto mayor, quiero realizar pedidos de medicamentos de forma sencilla, para obtener mis productos sin dificultades.

- CA1: DADO que el usuario tiene dificultades digitales, CUANDO utiliza la plataforma, ENTONCES debe encontrar opciones simples.
- CA2: DADO que necesita apoyo, CUANDO solicita ayuda, ENTONCES debe contar con asistencia.
- CA3: DADO que completa un pedido, CUANDO confirma, ENTONCES debe recibir una explicación clara.

**Estado:** Parcial. CA1 y CA3: interfaz y resumen; CA2: preguntas frecuentes, sin asistencia personalizada; falta validación con adultos mayores.

## HU09 — Control de pedidos cancelados

Como administrador de la plataforma, quiero controlar pedidos con riesgo de cancelación, para mejorar la disponibilidad del servicio.

- CA1: DADO que existe un pedido pendiente, CUANDO la botica no confirma stock, ENTONCES debe generarse una alerta.
- CA2: DADO que existe otra botica disponible, CUANDO ocurre una falla, ENTONCES debe reasignarse automáticamente.
- CA3: DADO que el pedido fue solucionado, CUANDO cambia de estado, ENTONCES debe registrarse.

**Estado:** Cobertura técnica. CA1–CA3: bandeja, vencimiento, reasignación e historial de solución; alerta operativa por incidencia, no canal externo.

## HU10 — Historial de compras

Como usuario frecuente, quiero revisar mis compras anteriores, para repetir pedidos fácilmente.

- CA1: DADO que el usuario realizó compras previas, CUANDO ingresa al historial, ENTONCES debe visualizar sus pedidos.
- CA2: DADO que encuentra un pedido anterior, CUANDO selecciona repetir compra, ENTONCES debe agregar nuevamente los productos.
- CA3: DADO que existen datos registrados, CUANDO consulta, ENTONCES debe proteger la información personal.

**Estado:** Pendiente. CA1–CA3: no hay cuenta, historial personal ni repetición de compras; seguimiento individual no sustituye historial.

## HU11 — Atención mediante chat de soporte

Como usuario que tiene dudas sobre un medicamento o pedido, quiero recibir orientación mediante un chat de atención, para resolver mis consultas antes de realizar la compra.

- CA1: DADO que el usuario tiene una duda sobre un medicamento, CUANDO ingresa al chat de soporte, ENTONCES debe poder escribir su consulta y recibir respuesta.
- CA2: DADO que el usuario necesita información sobre un pedido, CUANDO solicita ayuda, ENTONCES el sistema debe permitir consultar el estado de la compra.
- CA3: DADO que la consulta requiere atención especializada, CUANDO el sistema identifica la necesidad, ENTONCES debe derivarla a un asesor.

**Estado:** Parcial. CA2: seguimiento y ayuda básica; CA1 y CA3: sin chat ni derivación a asesor.

## HU12 — Disponibilidad mediante múltiples canales

Como cliente que utiliza diferentes medios de compra, quiero acceder a la disponibilidad de medicamentos desde canales físicos y digitales, para elegir la opción más conveniente.

- CA1: DADO que el usuario consulta un medicamento, CUANDO utiliza la aplicación o una botica afiliada, ENTONCES debe obtener información actualizada.
- CA2: DADO que el usuario inicia una compra en un canal, CUANDO cambia a otro canal, ENTONCES debe conservar la información del pedido.
- CA3: DADO que existen diferentes puntos de atención, CUANDO busca un producto, ENTONCES debe visualizar todas las opciones disponibles.

**Estado:** Diferida. CA1–CA3: no hay integración de canales físicos y digitales.

## HU13 — Recomendación de productos alternativos

Como paciente que no encuentra un medicamento disponible, quiero recibir alternativas similares, para poder adquirir una opción adecuada.

- CA1: DADO que un medicamento no tiene disponibilidad, CUANDO el usuario realiza la búsqueda, ENTONCES el sistema debe mostrar alternativas existentes.
- CA2: DADO que existen productos equivalentes, CUANDO aparecen las opciones, ENTONCES deben mostrar información básica del producto.
- CA3: DADO que el usuario selecciona una alternativa, CUANDO confirma la compra, ENTONCES debe registrarse como nuevo pedido.

**Estado:** Diferida. CA1–CA3: no hay flujo de alternativas de medicamentos; no realizar sustitución automática.

## HU14 — Gestión de inventario para boticas

Como administrador de una botica, quiero actualizar automáticamente mi inventario, para mantener información correcta de disponibilidad para los clientes.

- CA1: DADO que la botica realiza una venta, CUANDO el producto sale del inventario, ENTONCES el stock debe actualizarse automáticamente.
- CA2: DADO que llega nuevo medicamento al almacén, CUANDO se registra el ingreso, ENTONCES debe aumentar la disponibilidad mostrada.
- CA3: DADO que existe información incorrecta, CUANDO el administrador revisa el sistema, ENTONCES debe poder corregir los datos.

**Estado:** Cobertura técnica. CA1–CA3: salida al despacho, ingreso y ajuste autorizado en inventario del prototipo.

## HU15 — Entrega rápida de medicamentos

Como usuario que necesita recibir un medicamento rápidamente, quiero que mi pedido sea asignado al establecimiento más adecuado, para recibirlo en el menor tiempo posible.

- CA1: DADO que el usuario solicita entrega a domicilio, CUANDO confirma la compra, ENTONCES el sistema debe seleccionar una botica con disponibilidad.
- CA2: DADO que existen varias boticas cercanas, CUANDO se asigna el pedido, ENTONCES debe considerar distancia y capacidad de atención.
- CA3: DADO que el pedido está en proceso de entrega, CUANDO cambia de estado, ENTONCES el usuario debe recibir una actualización.
- CA4: DADO que el pedido fue entregado, CUANDO finaliza la entrega, ENTONCES debe registrarse la confirmación.

**Estado:** Parcial. CA1, CA2 y CA4: asignación y confirmación; CA3: estado consultable por código, sin aviso activo; no se mide rapidez.

## Refinamientos propuestos sin duplicar HU

| HU | Criterios adicionales propuestos para aprobación |
|---|---|
| HU04 | Mostrar cotización del servidor con subtotal, envío y total; conservar importes al confirmar. |
| HU02/HU09 | Aceptar antes del plazo, reasignar sin ciclos, cancelar sin alternativa y liberar reservas. |
| HU14 | Registrar movimientos, saldos y motivo; impedir conteo inferior a reservas; evitar duplicación por reintento. |
| HU05/HU15 | Consultar cambios de sucursal y estado mediante código privado sin datos internos. |

El acceso operativo se documenta como requisito transversal RF-EXT-05; no se crean HU16–HU19 sin acuerdo de alcance. Véase [requisitos](../01-requisitos/REQUISITOS.md) y [evidencia de logística](../06-evidencias/2026-11-16_logistica-sucursales.md).
