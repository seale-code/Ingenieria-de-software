# Manual técnico — esquema v6

[Manual de usuario](USUARIO.md) · [Datos](../03-diagramas/MODELO_DATOS.md) · [Validación](../05-pruebas/VALIDACION_V6.md)

## Instalar e iniciar

Requisitos: Python 3.10 o superior, pip y acceso al repositorio. Desde la carpeta `Ingenieria-de-software`:

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m scripts.iniciar_tienda
```

Abrir `http://127.0.0.1:5000/` y `/operaciones`. La terminal muestra una clave aleatoria si no se configura `INKAFARMA_OPERATIONS_KEY`. Mantenerla privada. El servidor se enlaza a 127.0.0.1, con debug y reloader desactivados; este comando no configura HTTPS o un despliegue público.

La base persistente predeterminada es `data/inkafarma-comercial.sqlite3`. El arranque crea/migra hasta v6, inicializa el módulo de pedidos y agrega solo registros iniciales ausentes. No restablece stock, precios ni pedidos. Los fixtures antiguos `DEMO-*` son exclusivos de pruebas y comandos anteriores.

```bash
python -m scripts.iniciar_tienda --db data/otra-tienda.sqlite3 --port 5001
python -m scripts.iniciar_tienda --reserva-minutos 30
```

El segundo comando cambia el plazo de asignaciones futuras; las ya creadas conservan su límite. Las bases ajenas/versiones no admitidas se rechazan sin recrearlas. Hacer respaldo antes de una migración de una base operada.

## Supervisor de reservas

El arranque recomendado revisa inmediatamente y luego cada 30 s. Debe estar en ejecución para procesar vencimientos; al reiniciar atiende los plazos vencidos persistidos. Una aceptación al iniciar preparación excluye el pedido de los vencimientos automáticos.

Con un servidor WSGI independiente, planificar cada minuto un proceso sobre la misma base:

```bash
python -m scripts.procesar_reservas --db data/inkafarma-comercial.sqlite3
```

Cada lote procesa hasta 100 pedidos. No usar temporizadores del navegador como sustituto del supervisor. La gestión de claves de sesión entre procesos, HTTPS y cuentas individuales debe resolverse antes de un despliegue público; el análisis de seguridad documenta el estado actual.

## Respaldar y restaurar

Usar la API de copia de SQLite, no copiar a ciegas un archivo activo mientras tiene escrituras. Los respaldos contienen información de contacto: restringir acceso, conservarlos fuera de Git y definir retención con el responsable de los datos.

```bash
python -m scripts.respaldo_base crear --origen data/inkafarma-comercial.sqlite3 --destino data/respaldo-2026-11-20.sqlite3
python -m scripts.respaldo_base verificar --origen data/respaldo-2026-11-20.sqlite3
python -m scripts.respaldo_base restaurar --origen data/respaldo-2026-11-20.sqlite3 --destino data/recuperada.sqlite3
python -m scripts.iniciar_tienda --db data/recuperada.sqlite3
```

El destino debe ser nuevo: se rechaza la sobrescritura y la misma ruta. Se validan aplicación/versión, integridad y claves foráneas. Restaurar crea una base nueva; detener el servidor anterior antes de cambiar la operación a la recuperada y conservar el origen hasta validar la recuperación. Los nombres con espacios deben ir entre comillas.

La copia local no equivale a una política completa de recuperación ante pérdida del equipo. La periodicidad, copia externa, retención, responsables y tiempo de recuperación esperado requieren acuerdo operativo.

## Verificar y regenerar documentación

```bash
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
python -m playwright install chromium-headless-shell
python -m unittest discover -s tests/e2e -v
python -m scripts.validar_mvp
python -m scripts.validar_logistica
python -m scripts.medir_rendimiento --muestras 30
python -m scripts.generar_diccionario
python -m scripts.verificar_documentacion
```

Las pruebas y mediciones crean bases temporales, independientes de la base operativa. Los percentiles locales no son un SLA de Internet ni un benchmark de los sistemas reales de Inkafarma.

## Repetir el análisis de seguridad

La [metodología](../08-seguridad/METODOLOGIA.md) detalla inventarios, comandos y límites. Instalar `requirements-security.txt` en el entorno de evaluación y ejecutar `python -m scripts.analizar_seguridad`: utiliza bases temporales y no abre puertos. El [informe](../08-seguridad/ANALISIS_VULNERABILIDADES.md) mantiene cinco hallazgos abiertos y el [plan](../08-seguridad/PLAN_REMEDIACION.md) define sus retests. Un resultado de controles aprobados no cierra esas carencias.
