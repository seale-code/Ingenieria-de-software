# Backend — integración del catálogo S1-11

Tarea de integración: [#13](https://github.com/seale-code/Ingenieria-de-software/issues/13).
Reutiliza `catalogo_busqueda.py` de Anderson y las consultas SQLite del equipo.
El filtro de categoría del endpoint se aplica al catálogo completo para conservar
productos sin inventario; `filtro_categorias.py` de César conserva su contrato original.

## Ejecutar desde la raíz del repositorio

Requiere Python 3.10 o superior. Se recomienda un entorno virtual.

```bash
python -m pip install -r requirements.txt
python -m src.database init --demo
python -m src.backend.app
```

Abrir http://127.0.0.1:5000. La pantalla se sirve desde Flask; no abrir el HTML
con file://. SQLite se crea explícitamente con init; el servidor no crea ni
sobrescribe bases. El servidor local no activa debug ni expone escrituras.

Base alternativa (PowerShell):

```powershell
python -m src.database init --demo --db .test-tmp/catalogo.sqlite3
$env:INKAFARMA_DB = '.test-tmp/catalogo.sqlite3'
python -m src.backend.app
```

En bash: `INKAFARMA_DB=.test-tmp/catalogo.sqlite3 python -m src.backend.app`.

## Contrato de consulta

| GET | Parámetros / respuesta |
|---|---|
| `/api/filtros` | `categorias` y `sucursales`: listas de `codigo`, `nombre`. Incluye categorías vacías. |
| `/api/catalogo` | `buscar`, `categoria`, `sucursal`, `solo_disponibles=true\|false`. Retorna `productos` y `total`. |
| `/api/productos/<codigo>/stock` | `stock`: filas de disponibilidad por sucursal registradas. Producto inexistente: 404. |

Los productos incluyen `producto_codigo`, `producto`, `categoria_codigo`, `categoria`
y `cantidad` (suma de inventarios del ámbito consultado). `cantidad: null` significa
sin inventario registrado; `0` significa registro sin unidades. Sucursal seleccionada
restringe a productos con inventario registrado allí; Solo disponibles exige cantidad > 0.
Búsqueda parcial, Unicode sin distinción de mayúsculas, acentos significativos;
apóstrofos, % y _ son literales. Categorías/sucursales se identifican por código.

Error de datos: HTTP 503 con `error` genérico, sin rutas internas. Booleano inválido:
400. La interfaz muestra carga, vacío, error y reintento; cancela respuestas obsoletas
y limita cada consulta a 10 segundos. Las respuestas API usan `Cache-Control: no-store`.
El detalle consulta de nuevo SQLite cada vez que se abre.

```bash
python -m unittest discover -s tests -v
```

Fuera de esta entrega: pedidos, reserva, autenticación y orden por cercanía.
En S2 se deberá distinguir stock físico de stock reservable antes de habilitar compras.
Este servidor es para demostración académica local, no despliegue de producción.
