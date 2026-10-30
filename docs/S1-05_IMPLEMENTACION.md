# S1-05 — Implementar interfaz inicial

Responsable propuesto: Willy CCatamayo. Trazabilidad: PBI-01; apoyo parcial a PBI-08.
Versión local: S1-05-v1, 29/10/2026. No se ha creado commit ni publicado cambios en GitHub.
Estado: implementado y probado localmente; pendiente de revisión de otro integrante.

## Instalación

Copiar las carpetas de este paquete sobre la raíz del repositorio original (donde están `src`, `tests` y `docs`). Todos los archivos de esta entrega son nuevos; no requiere los cambios del Sprint 2.

Desde esa raíz, con Python 3.10 o superior:

```powershell
python -m src.backend.servidor_s1 --demo --db data/s1-05-demo.sqlite3
```

Abrir http://127.0.0.1:8001. Mantener la terminal abierta. Detener con Ctrl+C.
Si el puerto está ocupado, agregar `--port 8002` y abrir ese puerto.
No abrir el HTML mediante doble clic: necesita el servidor para consultar SQLite.

## Archivos

- `src/frontend/catalogo.html`: pantalla basada en el diseño S1-04.
- `src/frontend/catalogo.css`: diseño adaptable, foco visible y estilos sin dependencias de Internet.
- `src/frontend/catalogo.js`: consulta real, búsqueda parcial sin distinguir mayúsculas, filtros combinados, disponibilidad, carga, error y reintento.
- `src/backend/servidor_s1.py`: adaptador local mínimo de solo lectura para servir la interfaz y consultar la base existente. No modifica los módulos del backend del equipo.
- `tests/test_interfaz_s1_05.py`: pruebas del catálogo y servicio HTTP.
- `docs/06-evidencias/S1-05/`: capturas reales, resultados y huellas de versión.

## Comportamiento

Se combina nombre, categoría, sucursal y solo disponibles. Al seleccionar una sucursal se incluyen productos con registro allí, incluso con cantidad cero si no se activa solo disponibles. Sin sucursal se muestran también productos sin inventario. Un registro ausente no se presenta como cantidad cero. La búsqueda conserva la distinción de acentos.

La consulta del Sprint 1 presenta existencias físicas. No incluye reservas, pedidos ni funciones del Sprint 2. La cercanía, cuentas y asistencia completa de PBI-08 quedan fuera de esta tarea.

Actualizar disponibilidad vuelve a consultar SQLite y conserva los filtros válidos. Un fallo retira los resultados anteriores y ofrece reintentar. No utiliza el simulador de estados del boceto S1-04.

## Revisión para cerrar la tarea

Otro integrante debe ejecutar la demo, revisar los archivos y registrar su nombre, fecha, versión/commit revisado, resultado y observaciones en el Issue o Pull Request. No se marca la tarea cerrada y no se atribuye una revisión inexistente.
