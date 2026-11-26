# Código de Inkafarma

[Proyecto](../README.md) · [Documentación](../docs/README.md)

| Capa | Responsabilidad | Estado v6 |
|---|---|---|
| [Frontend](frontend/README.md) | Catálogo, carrito, checkout, seguimiento y operaciones. | Implementado. |
| [Backend](backend/README.md) | API, asignación, preparación, reparto, soporte e inventario. | Implementado en Flask/Python. |
| [Persistencia](database/README.md) | SQLite, migraciones, reservas, precios e historial. | Implementada hasta v6, con 20 tablas. |

El arranque es `python -m scripts.iniciar_tienda`. Las reglas del producto y su verificación están en [requisitos](../docs/01-requisitos/REQUISITOS.md), [trazabilidad](../docs/01-requisitos/TRAZABILIDAD_IMPLEMENTACION.md) y [validación](../docs/05-pruebas/VALIDACION_V6.md). Los fixtures de pruebas y bases temporales están separados de la base persistente de la aplicación.
