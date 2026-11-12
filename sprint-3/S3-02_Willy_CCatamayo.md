# S3-02 — Seguimiento para el cliente

Responsable: Willy CCatamayo. Issue #15.

## Resultado
Pantalla `/seguimiento` con estado actual, sucursal, mensaje explicativo e historial cronológico. Fechas en hora de Lima. Acceso desde el catálogo y desde la confirmación del formulario, que muestra el código privado de consulta. Botón para actualizar y mensajes de carga, código inválido, pedido inexistente y servicio no disponible. No cambia estados ni inventario.

La API `GET /api/seguimiento` recibe `X-Codigo-Pedido`. Usa consultas parametrizadas, lectura consistente de SQLite y `Cache-Control: no-store`. No entrega nombre, ubicación del cliente ni observaciones internas. El código completo permite consultar el pedido: conservarlo privado. No existe autenticación de clientes en este prototipo; para una operación real se requiere autorización vinculada a la cuenta. El código viaja en un fragmento del enlace, se elimina de la barra al cargar y no aparece como parámetro en la URL de la API.

## Ejecutar
Usar el entorno del proyecto e inicializar la base según `src/backend/README.md`. Aplicar la migración a versión 3 (`python -m src.database.migrate_josue --db data/inkafarma.sqlite3`) antes de consultar el historial. Registrar un pedido en `/pedido`, guardar el código y abrir «Ver seguimiento del pedido». Las transiciones siguen siendo responsabilidad de los módulos del equipo.

## Validación realizada
- `python -m unittest discover -s tests -v`: 205 pruebas aprobadas, incluidas 7 nuevas de seguimiento.
- `node --check src/frontend/seguimiento.js` y `node --check src/frontend/pedido.js`: correctos.
- Python 3.13.5 y Flask 3.1.1 disponibles en este entorno; la versión fijada por el proyecto es Flask 3.1.3.
- No se ejecutaron pruebas en navegador: Playwright no está instalado en este entorno.

## Revisión manual pendiente
1. Crear un pedido, abrir su seguimiento y comprobar estado e historial.
2. Cambiar el estado con los módulos del equipo y volver a consultar.
3. Probar código inexistente, desconexión, reintento y vista de 390 px.
4. Otro integrante debe revisar el PR antes de integrar y cerrar #15.

Implementación y pruebas automatizadas listas para revisión; no acredita aceptación del equipo ni cierre del MVP.

## Validación de integración por Sebastian — 12 de noviembre

La ampliación S3-05 comprobó el recorrido real de confirmación a seguimiento, actualización mediante preparación de César, códigos incorrectos, desconexión, reintento, carga y error 503, vista de 390 px y navegación por teclado. Se añadió copia del código en la confirmación, con alternativa manual si falla el portapapeles.

Resultado sobre `9f41300` más la ampliación: 211 pruebas Python/API y 24 recorridos Chromium aprobados (incluidos 9 nuevos de seguimiento). [Evidencia y capturas](../docs/06-evidencias/2026-11-12_seguimiento-validacion-mvp.md). Esta ejecución utiliza Flask 3.1.3 según requirements y Playwright 1.51.0. La ausencia de pruebas de navegador indicada arriba corresponde a la entrega inicial, no a esta ampliación. La aceptación y el merge del PR #49 continúan sujetos a revisión del equipo.
