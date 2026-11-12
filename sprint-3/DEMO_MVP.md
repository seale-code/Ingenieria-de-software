# Ejecutar y demostrar el MVP

## Interfaz en Windows

Desde la raíz de una copia del repositorio con esta propuesta, crea una base nueva de demostración. No uses una base con pedidos del equipo para este guion.

```powershell
python -m pip install -r requirements.txt
python -m src.database init --demo --db .test-tmp/demo-s3.sqlite3
python -m src.database.migrate_josue --db .test-tmp/demo-s3.sqlite3 --hasta 3
python -m src.backend.pedidos_s2_cli --db .test-tmp/demo-s3.sqlite3 init
$env:INKAFARMA_DB = '.test-tmp/demo-s3.sqlite3'
python -m src.backend.app
```

En Bash, reemplaza las dos últimas líneas por `INKAFARMA_DB=.test-tmp/demo-s3.sqlite3 python -m src.backend.app`. Abre http://127.0.0.1:5000 en ese mismo equipo y conserva la terminal abierta. Ctrl+C detiene el servidor. Para repetir con stock inicial, utiliza otro nombre de base; los comandos preservan los pedidos existentes.

La pantalla de seguimiento de los pasos siguientes requiere PR #49 y la ampliación de validación S3-05. PR #49 todavía estaba abierto al revisar esta versión.

## Recorrido visual disponible

1. Buscar «demo a»: disponibilidad inicial de 5 unidades.
2. Consultar stock por sucursal: Norte 5, Sur 0.
3. Entrar a «Crear un pedido». Elegir DEMO-A, cantidad 2, cliente ficticio y referencia Norte.
4. Revisar el resumen y volver a editar para mostrar que no hay confirmación anticipada.
5. Confirmar: mostrar número de pedido, sucursal y estado ASIGNADO.
6. Pulsar «Copiar código de seguimiento» y guardarlo. Si el portapapeles está bloqueado, copiar manualmente el código mostrado.
7. Abrir «Ver seguimiento del pedido»: debe mostrar Asignado e historial. El fragmento del código se elimina de la barra; una recarga permite volver a introducir el código guardado.
8. Volver al catálogo y recargar. DEMO-A debe mostrar 3 unidades; abrir su detalle para comprobarlo.
9. En otro pedido, cantidad 0 impide avanzar; una cantidad superior a lo disponible muestra error sin crear un pedido parcial.

El [recorrido automatizado](../tests/e2e/test_pedido_browser.py) ejecuta catálogo → formulario → confirmación → catálogo y verifica el cambio 5 → 3.

## Demo técnica de integración S3

```bash
python -m scripts.validar_mvp
```

El comando utiliza el cliente HTTP de Flask y una base temporal que elimina al terminar. Muestra JSON con disponibilidad, reintento sin duplicación, repartidor, fechas e historial. No escribe en la base de la interfaz ni utiliza servicios externos.

El comando detecta los módulos disponibles. En la versión ampliada, ejecuta ASIGNADO → EN_PREPARACION → PREPARADO con el servicio de César y consulta la API de Willy para comprobar estado e historial del mismo pedido. La respuesta pública no expone datos personales ni observaciones internas. Si no está instalado el seguimiento de #49, lo indica como pendiente.

La entrega conserva ASIGNADA: registrar una fecha no implementa las transiciones de #22. El resultado se identifica como `VALIDACION_PARCIAL_NO_CIERRE_MVP`; la salida correcta del comando acredita únicamente los componentes comprobados. No existe una bandeja web del personal que avance estados desde esta pantalla del cliente.

## Demostración final pendiente

Al integrar seguimiento (#49) y completar #22, ampliar el guion con bandeja de preparación, salida, entrega confirmada, consulta de historial desde la pantalla del cliente, permisos e incidencia asociada al pedido. Revisar que reserva e inventario se cierren sin doble consumo. Registrar versión demostrada, resultados, participantes y aprobación reales antes de cerrar #17.

Las ubicaciones y nombres son ficticios. Esta ejecución es local y no publica un sitio web.
