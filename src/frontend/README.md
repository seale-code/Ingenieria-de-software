# Interfaz integrada — Sprint 1

`index.html`, `styles.css` y `catalogo.js` conectan el diseño S1-04 de Willy
(`docs/04-diseño/Inkafarma_S1-04_demo.html`, conservado) con la API de consulta.
No contienen listas de productos ni stock precargados. Las opciones, resultados y
el detalle se obtienen del backend. Incluye filtros combinados, limpiar, carga,
sin resultados, sin inventario, error y reintento, en móvil y escritorio.

Para ejecutar, seguir [Backend](../backend/README.md) y abrir http://127.0.0.1:5000.
No se necesita npm. No abrir el HTML directamente: necesita la API del mismo origen.
La búsqueda espera 250 ms entre pulsaciones y descarta respuestas anteriores.
El prototipo original conserva sus controles de simulación únicamente en docs.
