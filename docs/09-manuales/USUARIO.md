# Manual de usuario y operaciones

Versión de aplicación: v6. [Inicio](../../README.md) · [Manual técnico](TECNICO.md).

## Comprar

1. Abrir la tienda y buscar por nombre/marca o elegir categoría. Consultar disponibilidad por sucursal; la disponibilidad ya descuenta reservas activas.
2. Agregar productos al carrito y ajustar cantidades. El carrito conserva productos/cantidades en el navegador; los datos de contacto se completan al confirmar.
3. Continuar al pedido. Completar nombre, celular, dirección y distrito de entrega; revisar productos, subtotal, envío y total en soles.
4. Confirmar. Si cambió el precio, revisar el resumen actualizado. Si falta stock completo o capacidad, corregir la selección; el sistema no registra una compra parcial.
5. Guardar el código privado recibido. El método disponible es pago al recibir; la pantalla de confirmación no acredita un pago electrónico.

La asignación utiliza disponibilidad, capacidad y distancia al centro del distrito. La sucursal mostrada puede cambiar si no puede atender o no acepta a tiempo; el código y los importes confirmados se conservan.

## Seguir el pedido

Abrir Seguimiento e introducir el código completo. Consultar estado, sucursal, historial y cambios de atención. Actualizar para ver avances. El código permite la consulta y debe conservarse privado; no se publican nombre, teléfono o dirección.

Ante una confirmación con respuesta incierta, usar **Comprobar confirmación** para recuperar el mismo pedido. Evitar crear una solicitud diferente hasta comprobar su resultado.

## Acceder a operaciones

Abrir `/operaciones` e introducir la clave que entrega el responsable del servidor. La sesión actual es de operador central: no hay cuentas individuales de empleados. Cerrar sesión al terminar.

### Preparar y entregar

1. Elegir el pedido de la bandeja y comprobar productos/cantidades.
2. Pulsar **Iniciar preparación** antes del límite mostrado. Esa acción acepta la atención y detiene su vencimiento automático.
3. Verificar productos y marcar preparado. Asignar un repartidor activo.
4. Registrar salida solo al iniciar el reparto: fecha, estado y consumo del stock se guardan juntos.
5. Confirmar entrega cuando se recibe el pedido. Repetir la misma salida/recepción no duplica sus efectos.

Una pantalla desactualizada puede ser rechazada si cambió la sucursal: actualizar antes de actuar. El pedido no puede saltar directamente de asignado a preparado ni cancelarse después de salir.

### Si la sucursal no puede atender

En el detalle, abrir **La sucursal no puede atender**, explicar el motivo y buscar otra sucursal. Se libera el origen y reserva un destino con todos los productos y capacidad. Si no existe alternativa, se cancela y libera, dejando la resolución registrada. No se vuelve a sucursales ya intentadas.

Las asignaciones no aceptadas vencen inicialmente a los 15 minutos. El supervisor actúa en el servidor. **Revisar vencimientos** ejecuta una revisión manual del lote pendiente; iniciar preparación a tiempo acepta el pedido, no modifica su precio.

### Inventario

1. Entrar a Inventario, elegir sucursal y buscar el producto.
2. Consultar físico, reservado y disponible (físico − reservado).
3. Para recepción, registrar **Entrada de mercadería**, unidades y motivo/referencia.
4. Para corrección, elegir **Ajuste por conteo físico** e introducir el saldo físico final, no la diferencia. Se comprueba el saldo que estaba viendo y que no sea menor a lo reservado.
5. Consultar el movimiento con saldo anterior, nuevo y motivo. Los registros no se editan; una corrección posterior se registra como otro ajuste.

Si una respuesta de movimiento se pierde, reintentar con los mismos datos en el formulario para conservar la misma clave de operación. Si se informa saldo desactualizado, actualizar antes de realizar un nuevo conteo.

### Incidencias y cancelación

Registrar categoría y descripción en el pedido. Iniciar revisión y, al resolver, indicar la solución. El registro general de una incidencia no cambia automáticamente la sucursal; usar la acción explícita de incapacidad de atención para reasignar. La cancelación requiere confirmación y libera las reservas previas a la salida.

## Recuperación de errores

- Error de conexión: comprobar conexión/servidor y actualizar; no asumir éxito sin comprobar el estado.
- Sesión vencida: volver a iniciar sesión con la clave del servidor.
- Falta de stock/capacidad: ajustar cantidades o productos; las líneas no se dividen entre sucursales.
- Código no encontrado: verificar que se pegó completo, sin reemplazarlo por el número del pedido.

Los datos de catálogo y existencia corresponden a esta propuesta. El servicio no tramita recetas ni recomienda equivalencias de medicamentos.
