# Backend — integración del MVP S1/S2/S3

Tarea de integración: [#13](https://github.com/seale-code/Ingenieria-de-software/issues/13).
Reutiliza `catalogo_busqueda.py` de Anderson y las consultas SQLite del equipo.
El filtro de categoría del endpoint se aplica al catálogo completo para conservar
productos sin inventario; `filtro_categorias.py` de César conserva su contrato original.

## Demostración completa

`python -m scripts.demo_web` crea una base temporal v4 con los módulos integrados, datos de ejemplo y clave aleatoria del expositor. Solo escucha en `127.0.0.1`. [Guía](../../sprint-3/DEMO_MVP.md).

`python -m scripts.validar_mvp` comprueba sin navegador el recorrido HTTP completo, soporte y cancelación sobre otra base temporal.

## Ejecutar el catálogo sobre una base propia

Requiere Python 3.10 o superior. Se recomienda un entorno virtual.

```bash
python -m pip install -r requirements.txt
python -m src.database init --demo
python -m src.backend.app
```

Abrir http://127.0.0.1:5000. La pantalla se sirve desde Flask; no abrir el HTML
con file://. SQLite se crea explícitamente con init; el servidor no crea ni
sobrescribe bases. El servidor local no activa debug. El registro público de pedidos requiere las migraciones y el módulo S2; las operaciones internas de demostración permanecen deshabilitadas por defecto.

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

## Pedidos y seguimiento

El módulo S2 debe inicializarse después de migrar la base oficial. `POST /api/pedidos` valida el UUID de confirmación y reserva con `BEGIN IMMEDIATE`; el reintento del mismo contenido devuelve el pedido existente. La disponibilidad HTTP resta las reservas activas; el consumo físico ocurre al iniciar el reparto.

`GET /api/seguimiento` exige `X-Codigo-Pedido`; no acepta el ID numérico como autorización y no devuelve datos personales ni observaciones. La consulta es de solo lectura.

## Panel local del expositor

`operaciones_demo.py` solo habilita sus rutas si se configura `DEMO_KEY` en la fábrica o `INKAFARMA_DEMO_KEY` en el entorno. El comando de demo proporciona automáticamente una clave aleatoria. No guardar claves en el repositorio.

| Ruta | Función |
|---|---|
| `GET/POST/DELETE /api/demo/sesion` | Consultar sesión, entrar con clave y salir. |
| `GET /api/demo/pedidos` | Últimos 100 pedidos, repartidores activos y resumen global. |
| `GET /api/demo/pedidos/<id>` | Productos, entrega, reservas, historial e incidencias. |
| `POST /api/demo/pedidos/<id>/acciones` | Preparar, marcar listo, asignar repartidor, salir, entregar o cancelar. |
| `POST /api/demo/pedidos/<id>/incidencias` | Reportar un problema del pedido. |
| `POST /api/demo/incidencias/<id>/atender` | Revisar y resolver con explicación. |

La cookie de sesión caduca tras dos horas sin uso, es HttpOnly/SameSite=Strict y necesita un token CSRF para escribir. Se comprueban JSON y origen; los roles/actores no se aceptan como campos del cliente. El expositor simula las acciones de los roles y no representa cuentas reales del personal.

`reparto_integrado.avanzar_reparto` combina fecha y transición con los servicios de Anderson dentro de una única transacción. Una falla revierte fecha, estados, historial y consumo; los reintentos y las solicitudes concurrentes del mismo paso no repiten efectos. Los comandos previos de fechas conservan su contrato independiente.

La autenticación de clientes y empleados, cuentas con permisos individuales y despliegue público están fuera del alcance de esta demostración.
Este servidor es para demostración académica local, no despliegue de producción.
