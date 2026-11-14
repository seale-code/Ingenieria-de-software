# Presentación del producto Inkafarma

## Iniciar

```bash
python -m pip install -r requirements.txt
python -m scripts.iniciar_tienda
```

Abre `http://127.0.0.1:5000/`. La terminal muestra la dirección y la clave de acceso a operaciones. Los pedidos y el inventario permanecen guardados al cerrar el servidor.

## Recorrido para presentar

| Paso | Acción | Valor del producto |
|---|---|---|
| Catálogo | Explorar portada, categorías y fichas; buscar una marca y ordenar por precio. | Productos con fotografía, presentación y precio identificados. |
| Carrito | Agregar productos y ajustar las cantidades. | Resumen de productos, envío y total; el carrito se conserva al recargar. |
| Datos de entrega | Completar nombre, celular, dirección y distrito. | Registro de la información que necesita operaciones para atender el pedido. |
| Revisión | Comprobar cantidades, subtotal, envío y total. | El servidor valida los precios y exige una nueva revisión si cambian. |
| Confirmación | Registrar el pedido y guardar el código. | Se reserva stock y se conservan los precios confirmados. |
| Operaciones | Iniciar preparación, marcar preparado, asignar repartidor y registrar salida. | Historial y consumo de stock consistentes, sin repetir descuentos. |
| Entrega | Confirmar recepción y actualizar el seguimiento. | Pedido entregado y cinco estados visibles para el cliente. |
| Soporte | Registrar, revisar y resolver una incidencia. | Problema relacionado con el pedido y resolución conservada. |

El método disponible es pago al recibir. El acceso al panel está en el pie de página y requiere la clave del servidor. El seguimiento por código no muestra dirección, celular ni observaciones internas.

[Pruebas y capturas actuales](../docs/06-evidencias/2026-11-13_tienda-comercial.md) · [Fuentes y reglas del catálogo](../docs/CATALOGO_COMERCIAL.md).
