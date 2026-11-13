# Interfaz web del MVP

- `index.html`, `catalogo.js`, `styles.css`: búsqueda, filtros y disponibilidad efectiva por sucursal. Los productos disponibles enlazan al formulario con el producto preseleccionado.
- `pedido.html`, `pedido.css`, `pedido.js`: elegir, revisar y confirmar; reintento con el mismo UUID ante resultado incierto; código privado y enlace de seguimiento.
- `seguimiento.html`, `seguimiento.css`, `seguimiento.js`: estado, etapas e historial en hora de Lima; consulta manual por código enviado en cabecera, sin datos personales ni observaciones internas.
- `operaciones.html`, `operaciones.css`, `operaciones.js`: sesión del expositor, bandeja, siguiente paso, reparto, cancelación con confirmación e incidencias. Solo funciona cuando el servidor habilita la demostración.
- `navegacion.js`: muestra el acceso al panel cuando está habilitado; no constituye una protección de acceso. El servidor verifica sesión y CSRF.

No requiere npm ni servicios externos. Los datos se consultan al backend; no se mantienen inventarios ficticios en JavaScript. Se conservan los selectores del formulario y catálogo existentes.

Para ejecutarlo: [guía de demostración](../../sprint-3/DEMO_MVP.md). No abrir los HTML directamente: necesitan la API del mismo origen.

Se verificaron carga, vacío, error, recuperación de conexión, texto tratado como contenido, navegación por teclado y vistas de escritorio/móvil. [Evidencias](../../docs/06-evidencias/2026-11-12_mvp-web-integrado.md).
