# Descripción del prototipo móvil — Inkafarma, Issue S1-04

Las siguientes capturas presentan el diseño del catálogo de productos, la aplicación de un filtro por categoría y la consulta de disponibilidad por sucursal. El prototipo utiliza una distribución vertical orientada a dispositivos móviles y una identidad visual basada en tonos verdes. Los productos, las direcciones y las cantidades mostradas son datos demostrativos.

## Figura 1. Vista inicial del catálogo de productos

<img width="379" height="836" alt="Captura de pantalla 2026-10-23 114848" src="https://github.com/user-attachments/assets/eb41c8a3-f58b-47ed-83e1-256834287cfb" />


La pantalla inicial presenta el catálogo y reúne los controles necesarios para localizar productos. En la parte superior se encuentra un campo de búsqueda por nombre o presentación, seguido de los selectores de categoría y sucursal. En esta captura, ambos filtros muestran la opción «todas», lo que representa la vista general del catálogo.

La sección «Productos destacados» contiene tres tarjetas: alcohol medicinal 70°, protector solar FPS 50 y cepillo dental suave. Cada tarjeta identifica el producto, su presentación y su categoría, e incluye la acción «Consultar stock por sucursal». Esta organización permite revisar la información principal antes de acceder al detalle de disponibilidad.

**Aporte al Issue S1-04:** la captura documenta la presentación del catálogo y la ubicación de los controles de búsqueda y filtrado. Por sí sola, no demuestra la ejecución de una búsqueda ni el funcionamiento de los desplegables.

## Figura 2. Catálogo filtrado por categoría

<img width="370" height="685" alt="Captura de pantalla 2026-10-23 114916" src="https://github.com/user-attachments/assets/16d639de-d1ad-455e-be5b-eb9bb691a10f" />


Esta pantalla muestra el resultado de seleccionar la categoría «Cuidado personal», mientras el selector de sucursal permanece en «Todas las sucursales». El catálogo presenta el mensaje «1 producto encontrado» y muestra únicamente la tarjeta de alcohol medicinal 70°, cuya categoría coincide con el filtro seleccionado.

La permanencia de la selección en el control permite reconocer qué criterio está aplicado. Además, el botón «Limpiar filtros» ofrece una acción para restablecer la consulta general. El contador de resultados ayuda a interpretar el efecto del filtrado sobre el listado.

**Aporte al Issue S1-04:** la captura documenta un estado del prototipo en el que la categoría seleccionada y el producto mostrado son coherentes. No evidencia un filtro por sucursal aplicado, puesto que se mantiene la opción de todas las sucursales.

## Figura 3. Detalle de disponibilidad por sucursal

<img width="367" height="779" alt="Captura de pantalla 2026-10-23 114940" src="https://github.com/user-attachments/assets/7e8470b4-262e-4858-ad6c-8028503920f0" />

La vista de detalle identifica el producto «Alcohol medicinal 70°», su categoría «Cuidado personal» y su presentación de 120 ml. El control «Volver al catálogo» permite reconocer la ruta de retorno al listado. A continuación, la sección «Disponibilidad por sucursal» organiza la información de inventario en tarjetas independientes.

| Sucursal | Dirección mostrada | Estado | Cantidad |
| --- | --- | --- | --- |
| Centro | Av. Principal 123 | Disponible | 24 unidades |
| Norte | Av. Los Olivos 456 | Stock bajo | 3 unidades |
| Sur | Av. Central 789 | Sin stock | 0 unidades |

Las etiquetas textuales y las cantidades permiten distinguir entre disponibilidad, stock bajo y ausencia de existencias. El color rojo refuerza el estado «Sin stock», sin depender exclusivamente del color para comunicarlo. La pantalla también incluye el texto «Actualizado hace 2 minutos» y una nota que indica que la disponibilidad puede cambiar; ambos elementos contextualizan la consulta, aunque en el prototipo no acreditan una actualización real del inventario.

**Aporte al Issue S1-04:** la captura documenta la consulta de stock de un producto por sucursal y la representación de tres situaciones de disponibilidad. El umbral que determina la etiqueta «Stock bajo» no se puede establecer a partir de esta imagen.

## Secuencia de uso representada

1. El usuario accede al catálogo general y revisa los productos disponibles en la demostración.
2. Selecciona «Cuidado personal» para reducir el listado a los productos de esa categoría.
3. Accede a «Consultar stock por sucursal» del alcohol medicinal 70° para revisar las cantidades de cada sede.
4. Puede regresar mediante «Volver al catálogo» y continuar la exploración.




## LINK FIGMA:
https://www.figma.com/proto/w2XUu9TxUH9qVmsXpaBas6?node-id=8-45&starting-point-node-id=8%3A45

Las tres capturas ilustran esta secuencia del prototipo. No constituyen evidencia de integración con una base de datos, actualización de inventario en tiempo real ni validación funcional del sistema implementado. Tampoco muestran los estados de carga, catálogo vacío o error, que requieren evidencias adicionales para documentar completamente el alcance del Issue S1-04.

*Fuente de las figuras: capturas del prototipo de Inkafarma proporcionadas para el informe.*
