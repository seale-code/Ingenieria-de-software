# 6. Repositorio de código — Sprint 02

El código ejecutable está en los directorios originales **`src/` y `tests/`** del repositorio; este directorio **documenta el vínculo**, sin copiar ni duplicar módulos que trabajan juntos.

## Ubicaciones

| Componente | Ruta real | Propósito |
|---|---|---|
| Base de datos | [`src/database/`](../../src/database/) | Esquema, inventario y migraciones. |
| Migración S2 | [`src/database/migrations/002_pedidos_reservas.sql`](../../src/database/migrations/002_pedidos_reservas.sql) | Tablas y restricciones oficiales. |
| Herramienta de migración | [`src/database/migrate_josue.py`](../../src/database/migrate_josue.py) | Evolución incremental y verificación de base. |
| Backend | [`src/backend/`](../../src/backend/) | Registro de pedidos, asignación y puente de integración. |
| Pruebas | [`tests/`](../../tests/) | Tests automatizados y regresión. |

**Trabajo de Josue:** asegurar integridad de pedidos, detalles y reservas sin sobreventa; además corregir el cierre de conexiones en sus migraciones y pruebas.

📄 [Arquitectura, flujo y comandos reproducibles](ARQUITECTURA_Y_FLUJO.md)
