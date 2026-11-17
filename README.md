<div align="center">

# Inkafarma

### Salud, cuidado personal y bienestar en un mismo lugar

Catálogo visual, carrito, pedidos y gestión de entregas.

</div>

## Iniciar la aplicación

Desde la raíz del repositorio, con Python 3.10 o superior:

```bash
python -m pip install -r requirements.txt
python -m scripts.iniciar_tienda
```

Abre **http://127.0.0.1:5000/**. La terminal muestra la dirección y la clave de acceso al panel de operaciones. El catálogo inicial incluye 16 productos con fotografía, marca, presentación y precio en soles.

Los pedidos, precios confirmados e inventario se conservan en `data/inkafarma-comercial.sqlite3`. Reiniciar la aplicación no restaura el stock ni reemplaza los precios operados. Puedes elegir otra ruta o puerto:

```bash
python -m scripts.iniciar_tienda --port 5001 --db data/mi-tienda.sqlite3
```

Para utilizar una clave propia en operaciones, configura `INKAFARMA_OPERATIONS_KEY` en el entorno del servidor. No publiques claves en el repositorio.

## Recorrido del producto

1. **Explora:** busca por producto o marca, elige categoría, ordena por precio y consulta stock por sucursal.
2. **Arma tu pedido:** agrega productos al carrito, ajusta cantidades y consulta subtotal, envío y total.
3. **Confirma:** completa tus datos de entrega y revisa el importe calculado por el servidor. El método disponible es pago al recibir.
4. **Sigue la entrega:** conserva tu código y consulta preparación, salida y entrega.
5. **Gestiona:** el panel de operaciones permite preparar, asignar repartidor, confirmar entrega y atender incidencias.

La aplicación asigna una sucursal según disponibilidad, distancia y capacidad. Las reservas evitan sobreventa; el consumo se registra una vez al salir el pedido. Los importes confirmados quedan guardados aunque el precio del catálogo cambie después.

## Arquitectura

| Capa | Tecnología | Ubicación |
|---|---|---|
| Interfaz | HTML, CSS y JavaScript | [src/frontend](src/frontend/README.md) |
| Servicios y API | Python y Flask | [src/backend](src/backend/README.md) |
| Persistencia | SQLite, migraciones incrementales | [src/database](src/database/README.md) |
| Verificación | unittest y Playwright | [tests](tests/README.md) |

## Pruebas

```bash
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
python -m playwright install chromium-headless-shell
python -m unittest discover -s tests/e2e -v
```

Las pruebas usan bases temporales independientes de los datos de la aplicación.

## Documentación

[Catálogo, fuentes y reglas comerciales](docs/CATALOGO_COMERCIAL.md) · [Resultados y capturas](docs/06-evidencias/2026-11-13_tienda-comercial.md) · [Modelos UML](docs/03-diagramas/uml/README.md) · [Índice del proyecto](docs/README.md) · [Project Inkafarma](https://github.com/users/seale-code/projects/1)
