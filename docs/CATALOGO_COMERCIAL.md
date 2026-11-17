# Catálogo comercial y recorrido de compra

La aplicación utiliza un catálogo local editable con precios en céntimos, fotografías y presentaciones verificadas en páginas públicas de Inkafarma. La referencia inicial se consultó el **13 de noviembre de 2026**. Los precios son una carga inicial; no se consultan en tiempo real durante una compra.

## Datos y fotografías

[productos.json](../src/database/catalogo/productos.json) conserva por producto el SKU, nombre, marca, presentación, precio, precio de lista, límite de unidades, URL de la ficha original, URL de la fotografía y fecha de consulta. Se conserva también la presentación del origen cuando su redacción se normaliza para mostrar unidades legibles.

Los 16 productos abarcan dermocosmética, medicamentos de venta libre, cuidado personal, protección solar y bebés. Las fotos se guardan como WebP en `src/frontend/imagenes/productos/`; la página funciona sin conexiones externas para mostrar el catálogo.

La marca visual se toma del archivo SVG público utilizado en la cabecera de Inkafarma. Las fotografías y marcas de producto mantienen su procedencia y titularidad. La imagen de portada es una creación original para esta propuesta, sin marcas ni envases médicos inventados: utiliza una composición fotográfica de cuidado personal sobre piedra clara con luz natural. No sustituye las fotos de las presentaciones reales.

### Fuentes de la carga

- [Cuidado corporal — Inkafarma](https://inkafarma.pe/lista/cuidado-corporal).
- [Selección de productos — Inkafarma](https://inkafarma.pe/lista/cupon-exclusivo-app).
- [Panadol 500 mg — ficha comercial](https://inkafarma.pe/producto/panadol-500mg-tableta/036723).
- [Vick VapoRub — ficha comercial](https://inkafarma.pe/producto/vick-vaporub-unguento-topico/324070).
- [CeraVe Control de Grasa — ficha comercial](https://inkafarma.pe/producto/crema-en-gel-hidratante-cerave-control-de-grasa/073726).
- Cada entrada del JSON enlaza a su ficha específica.

La presentación de Panadol corresponde a la **caja de 104 tabletas**, cuyo precio de origen es S/ 57.20. No se utiliza el precio fraccionado de S/ 1.10 para vender una caja completa. Las descripciones de la aplicación se limitan a identificar la presentación; no añaden dosis o indicaciones clínicas.

## Precios y confirmación

La migración `005_catalogo_comercial.sql` añade datos comerciales al esquema del equipo:

| Tabla | Finalidad |
|---|---|
| `catalogo_comercial` | Marca, presentación, imagen, precio, precio de lista, fuente y límite de unidades. |
| `pedidos_comerciales` | Cotización aceptada, contacto, dirección, distrito y totales confirmados. |
| `precios_pedido` | Cantidades y precio unitario conservados al confirmar cada línea. |

Los valores monetarios se almacenan como enteros en céntimos. `POST /api/pedidos/cotizacion` agrupa productos repetidos, valida límites y devuelve subtotal, envío, total y una huella de cotización. Los precios enviados por el navegador no determinan el importe.

Al confirmar, el servidor vuelve a cotizar dentro del mismo `BEGIN IMMEDIATE` utilizado para la asignación y reserva. Si cambió el precio, responde `409 PRECIO_ACTUALIZADO` antes de crear el pedido y permite revisar el nuevo importe. Un pedido ya confirmado conserva sus precios: un reintento con el mismo UUID devuelve el mismo pedido, incluso después de modificar el catálogo. Reutilizar la confirmación con otra dirección o contenido se rechaza.

Si falla el guardado de precios, se revierten también el pedido, historial y reservas. Las pruebas incluyen fallos inyectados y confirmaciones concurrentes. Los importes y precios del pedido no se editan ni eliminan mediante cambios directos ordinarios.

## Configuración comercial

- Moneda: PEN.
- Método disponible: pago al recibir. El pedido registra este método y no se marca automáticamente como pagado.
- Envío: S/ 6.90; sin costo desde S/ 149.00. El servidor aplica y devuelve esta regla en la cotización.
- Distritos: Miraflores, San Isidro y Santiago de Surco. Las coordenadas del distrito se resuelven en el servidor para la comparación de distancia.
- Límite por producto: definido en el catálogo y aplicado por servidor; los artículos de la categoría Medicamentos están limitados a dos unidades comerciales por pedido.
- La disponibilidad procede del inventario propio de la aplicación y sus reservas, no de un servicio de inventario externo de Inkafarma. Los centros y cantidades iniciales son configuración operativa de esta propuesta.

## Persistencia y datos de entrega

`python -m scripts.iniciar_tienda` prepara la base persistente de la aplicación, aplica migraciones y carga solamente los registros iniciales que no existen. No reemplaza precios, stock ni pedidos ya operados. Los fixtures `DEMO-*` permanecen reservados para las pruebas y los comandos técnicos anteriores.

El carrito guarda exclusivamente códigos y cantidades en el navegador. Nombre, celular y dirección se envían al confirmar y se consultan en operaciones con sesión autorizada; el seguimiento por código no los devuelve.

La clave del panel representa el acceso operativo compartido de esta versión. Los servicios conservan sus verificaciones de estado y asignación; no se atribuye identidad individual de un trabajador a esa clave. El servidor local no integra un proveedor de pago ni una plataforma logística externa.

## Fotografía de portada

Archivo: `src/frontend/imagenes/cuidado-diario.webp`. Se generó una fotografía horizontal de frascos de cuidado personal sin marcas, sobre piedra marfil y lino, con luz de mañana y tonos verdes. Se mantuvo el original y se convirtió a WebP para servirlo localmente. El prompt de creación está en [portada-prompt.txt](../src/frontend/imagenes/portada-prompt.txt).
