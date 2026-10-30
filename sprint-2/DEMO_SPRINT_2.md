# Demostración del Sprint 2

El catálogo y el formulario ya son funcionales. El Sprint 3 añade preparación, entrega y seguimiento; no es necesario esperar a él para demostrar un pedido.

## Ejecutar en Windows (PowerShell)

Desde una copia del repositorio actualizada a main, abre una terminal en la raíz. Usa una base nueva de demostración; no reemplaces una base con pedidos reales.

```powershell
python -m pip install -r requirements.txt
python -m src.database init --demo --db .test-tmp/demo-sprint2.sqlite3
python -m src.database.migrate_josue --db .test-tmp/demo-sprint2.sqlite3 --hasta 2
python -m src.backend.pedidos_s2_cli --db .test-tmp/demo-sprint2.sqlite3 init
$env:INKAFARMA_DB = '.test-tmp/demo-sprint2.sqlite3'
python -m src.backend.app
```

Abre http://127.0.0.1:5000 en el mismo equipo. Mantén la terminal abierta; Ctrl+C detiene el servidor. En Bash, sustituye las dos últimas líneas por `INKAFARMA_DB=.test-tmp/demo-sprint2.sqlite3 python -m src.backend.app`.

## Guion para presentar

1. En el catálogo, busca «demo» y prueba los filtros de categoría y sucursal.
2. Consulta la disponibilidad de un producto.
3. Pulsa «Crear un pedido» o abre http://127.0.0.1:5000/pedido.
4. Selecciona DEMO-A, cantidad 2, un nombre ficticio y la referencia DEMO-NORTE.
5. Revisa el resumen. Vuelve a editar y comprueba que todavía no se ha confirmado.
6. Confirma y muestra el número de pedido, el estado y la sucursal asignada.
7. En otro pedido, prueba cantidad 0: debe impedir avanzar. Prueba una cantidad superior al stock: debe mostrar un error y permitir corregir.

Los pedidos confirmados consumen disponibilidad mediante reservas. Para repetir la demostración desde cero, usa otro nombre de archivo de base de datos.

## Alcance

Se usan datos ficticios y puntos de referencia de demostración. No hay autenticación de clientes, pagos ni seguimiento de entrega en esta pantalla. El repositorio de GitHub contiene el código; no equivale a un sitio publicado. Esta guía ejecuta el servidor localmente.
