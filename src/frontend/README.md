# Interfaz Inkafarma

La interfaz comparte identidad, navegación, componentes de compra y recursos locales.

| Archivo | Responsabilidad |
|---|---|
| `index.html` + `catalogo.js` | Portada, categorías, búsqueda por nombre/marca, orden de precios, tarjetas, disponibilidad y ficha del producto. |
| `tienda.js` + `tienda.css` | Diseño comercial, carrito persistente, cantidades, cotización y totales. |
| `pedido.html` + `pedido.js` | Datos de entrega, revisión de precios, confirmación y comprobante del pedido. |
| `seguimiento.html` + `seguimiento.js` | Estado y etapas del pedido mediante código privado. |
| `operaciones.html` + `operaciones.js` | Preparación, reparto, datos privados de entrega, importes e incidencias con acceso de operaciones. |
| `ayuda.html` + `privacidad.html` | Información de compra, cobertura y uso de los datos. |
| `imagenes/` | Marca SVG, fotografía de portada y 16 fotografías de producto en WebP. |

`python -m scripts.iniciar_tienda` inicia la aplicación con el catálogo comercial y persistencia. Las fotos y scripts se sirven desde el mismo origen; no se necesita npm ni una conexión externa para renderizar el catálogo.

Los precios del resumen se verifican en servidor antes de confirmar. El navegador guarda en el carrito únicamente códigos y cantidades; no persiste datos de contacto o direcciones.

[Fuentes y reglas del catálogo](../../docs/CATALOGO_COMERCIAL.md) · [Pruebas y capturas](../../docs/06-evidencias/2026-11-13_tienda-comercial.md).
