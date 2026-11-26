# Alcance y objetivos

[Documentación](../README.md) · [Requisitos](REQUISITOS.md) · [Cobertura por criterio](TRAZABILIDAD_IMPLEMENTACION.md)

**20 de noviembre de 2026**, esquema v6, base funcional histórica `53b6ff8`; consolidación DOC-01 sobre `daa9716` (PR #57).

## Problema y objetivo general

La coordinación entre sucursales necesita relacionar existencias, reservas, capacidad y avance de la atención. Ofrecer stock comprometido, mantener una asignación sin confirmación o registrar una salida dos veces puede producir pedidos que una sucursal no pueda atender. La propuesta para Inkafarma aborda esos riesgos con reglas verificables y trazabilidad.

El objetivo es implementar una aplicación web que permita comprar productos del catálogo, reservar stock, asignar y reasignar atención, gestionar preparación/reparto y consultar el resultado con inventario e historial consistentes. No se presentan mediciones del funcionamiento interno de Inkafarma ni una integración con sus sistemas comerciales.

## Objetivos específicos

| Objetivo | Comprobación |
|---|---|
| Mostrar catálogo, precios y disponibilidad por sucursal. | Búsqueda por nombre/marca, filtros y pruebas de interfaz. |
| Confirmar cantidades e importes en el servidor. | Cotización en céntimos, revisión ante cambio de precio y snapshot confirmado. |
| Evitar sobreventa y asignaciones sin capacidad. | Reservas transaccionales y escritores concurrentes. |
| Recuperar atención ante falta de aceptación. | Reasignación, historial de intentos y cancelación/liberación sin alternativa. |
| Registrar preparación, salida y recepción sin descuentos repetidos. | Transiciones, fechas e idempotencia del reparto. |
| Mantener inventario verificable. | Entradas, conteos y salidas en un registro inmutable. |
| Entregar resultados reproducibles. | Trazabilidad, pruebas, manuales y análisis de seguridad acotado. |

## Alcance implementado

Web con catálogo de 16 productos de referencia comercial, fotos locales, búsqueda, filtros, carrito, dirección, cotización, confirmación y seguimiento por código privado. El panel permite preparar, asignar repartidor, despachar, confirmar entrega, cancelar antes de salida, gestionar incidencias e inventario.

La asignación exige todos los productos en una sucursal y capacidad disponible. Entre las elegibles prioriza distancia geográfica. La ubicación de entrega es el centro del distrito seleccionado, no una geocodificación de la dirección. Se configuran Miraflores, San Isidro y Santiago de Surco.

Cada asignación pendiente dispone inicialmente de 15 minutos para aceptar al iniciar preparación. El supervisor busca otra sucursal al vencer sin aceptación; si no hay alternativa, cancela y libera. Un pedido aceptado no vence por falta de pago anticipado. El plazo de futuras asignaciones es configurable. Las asignaciones pendientes tienen además un límite total de 45 minutos desde la compra, incluidas las reasignaciones. Antes de confirmar se exige un código telefónico vinculado al pedido; no se reserva sin verificación.

El método disponible es **pago al recibir**: se conservan método e importes; no se ejecuta un cobro electrónico ni se acredita automáticamente el pago.

## Desarrollo incremental

| Etapa | Aporte |
|---|---|
| Sprint 1 | Catálogo, filtros, disponibilidad y modelo inicial. |
| Sprint 2 | Confirmación, reservas, asignación y concurrencia. |
| Sprint 3 | Preparación, reparto, seguimiento, soporte y validación. |
| Ampliaciones #54–#56 | Panel integrado, catálogo/carrito comercial, precios conservados, vencimientos, reasignación e inventario. |

Las integraciones Git acreditan cambios de código, no fechas de reuniones o aceptación de sprints.

## Fronteras y decisiones

- Precios y existencias pertenecen a la base local; las fuentes del catálogo están documentadas. No hay sincronización con inventarios internos de Inkafarma.
- La operación actual es entrega a domicilio. Reserva para recojo, continuidad entre canales, cuentas de clientes y repetición de compras tienen cobertura pendiente o parcial.
- El panel utiliza cuentas personales con permisos diferenciados de central y sucursal; las escrituras se auditan con identidad.
- Los avisos se consultan en bandeja/seguimiento; no hay envío de SMS, correo o push. La verificación del contacto requiere una llamada saliente manual de un operador.
- Recetas, equivalencias de medicamentos, SUNAT y pasarela no forman parte de esta versión.
- Los 17 diagramas agrupados conservan las HU. La conformidad con la exigencia original de un diagrama por HU requiere validación del docente.

Fuente: [HU01–HU15](../02-historias-usuario/HistoriasdeUsuario-Inkafarma.pdf). Las adaptaciones de recojo a entrega y prioridades [MoSCoW](../07-scrum/PRIORIZACION.md) requieren aceptación del equipo/Product Owner. No se atribuyen acuerdos no documentados.

## Consolidación DOC-01

Se conserva el alcance histórico y las 15 historias originales. Ver [revisión de historias](../02-historias-usuario/HISTORIAS_ACTUALIZADAS.md), [Remediación](../08-seguridad/REMEDIACION.md) y [Validación posterior a la remediación](../06-evidencias/remediacion/validacion.md). Los resultados registrados (334 pruebas Python/API/recuperación y 44 recorridos Chromium) son históricos; no se ejecutaron de nuevo en esta consolidación.
