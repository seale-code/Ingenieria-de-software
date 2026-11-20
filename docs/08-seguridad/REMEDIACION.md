# Remediación de los cinco hallazgos de la tienda

La fábrica pública `src.backend.app:create_app()` y el arranque `python -m scripts.iniciar_tienda` aplican los controles de esta entrega. El [informe inicial](ANALISIS_VULNERABILIDADES.md) conserva la evaluación anterior a los cambios.

| Hallazgo | Corrección | Verificación |
|---|---|---|
| SEC-01 · Identidad y permisos | Cuenta personal con contraseña protegida mediante scrypt. La central coordina las sedes. Cada cuenta de sucursal consulta su bandeja e inventario, prepara o rechaza sus asignaciones y registra movimientos en su sede. Cambiar la cuenta o revocarla invalida sus sesiones. La auditoría de escrituras registra usuario, ruta, acción y respuesta. | Dos cuentas de sedes distintas y una central. Se comprobaron lectura y escritura autorizadas, rechazo cruzado, identidad en auditoría y revocación. |
| SEC-02 · Reservas | El cliente solicita una llamada antes de confirmar. El operador llama al teléfono registrado y comunica un código de ocho dígitos, válido diez minutos, ligado al teléfono y UUID del pedido. Se permiten cinco comprobaciones erróneas por código, seis nuevas solicitudes por origen en diez minutos y dos pedidos activos por celular verificado. El cupo se comprueba dentro de la transacción de reserva. Las asignaciones pendientes de aceptación tienen un plazo total de 45 minutos desde la compra, incluidas las reasignaciones. | Se comprobó la ausencia de reservas sin verificación, vinculación, caducidad, cupo concurrente, reintento del mismo pedido y liberación por el supervisor. |
| SEC-03 · Intentos de acceso | Ventanas de cinco minutos en SQLite compartidas entre procesos. Cinco intentos por usuario y dirección de origen y sesenta por origen. El acceso que supera el límite recibe HTTP 429 con Retry-After. | Dos instancias comparten el límite. Otra cuenta puede acceder antes del tope general. El usuario recupera el acceso al vencer la ventana. |
| SEC-04 · Transporte y sesión | Perfil de producción con host explícito, HTTPS obligatorio, clave de firma persistente, cookie Secure/HttpOnly/SameSite=Strict, HSTS y CSP de mismo origen. En desarrollo se restringe el acceso a loopback. | Se validaron el rechazo de host/HTTP, sesión entre instancias y cabeceras. Gunicorn con dos workers sirvió el catálogo y el acceso por HTTPS en loopback con comprobación del certificado de prueba. |
| SEC-05 · Instaladores | Playwright Python 1.65.2. Los cinco instaladores macOS señalados ahora descargan con validación de certificados. | Inspección de los cinco archivos del driver instalado, auditoría de paquetes y regresión de navegador. |

## Operación de la tienda

Desde la raíz y después de instalar `requirements.txt`, cada persona recibe una cuenta con su propio nombre. El comando pide la contraseña por entrada oculta. Al volver a guardar el usuario se reemplazan su contraseña y permisos y se invalidan sus sesiones previas.

```bash
python -m scripts.operadores guardar ana --sucursal MIRAFLORES
python -m scripts.operadores guardar luis --central
python -m scripts.iniciar_tienda
```

El cliente pulsa **Solicitar llamada** al revisar el pedido. Desde la consola operativa, el personal consulta las solicitudes y atiende una por su UUID. El segundo comando muestra el número de destino y el código una sola vez. La persona que atiende la solicitud **llama al número de destino registrado** y dicta el código durante esa llamada saliente. El cliente lo escribe en la tienda y confirma el pedido. Este circuito requiere una persona disponible para llamar.

```bash
python -m scripts.operadores llamadas
python -m scripts.operadores llamar UUID_DE_LA_SOLICITUD
python -m scripts.operadores revocar ana
```

Para otra base, pasar `--db RUTA` antes del subcomando. Las credenciales y solicitudes se almacenan en la base de la tienda. Las copias de seguridad contienen hashes de contraseñas y datos de contacto, por lo que requieren acceso restringido. La firma local se guarda en un archivo con permisos de propietario junto a la base. En producción se obtiene del gestor de secretos del despliegue.

## Servir con HTTPS

En un servidor Linux, instalar `requirements-produccion.txt`, aprovisionar las cuentas en la base elegida y configurar `INKAFARMA_DB`, `INKAFARMA_PERFIL=produccion`, `INKAFARMA_HOST` con un único nombre de dominio y `INKAFARMA_SESSION_SECRET` con un secreto aleatorio de al menos 32 caracteres, persistente entre workers. Todos los procesos que atiendan verificaciones telefónicas deben usar el mismo secreto. Gunicorn termina TLS directamente en este ejemplo.

```bash
gunicorn --workers 2 --bind 0.0.0.0:8443 --forwarded-allow-ips '' \
  --certfile /run/tls/fullchain.pem --keyfile /run/tls/privkey.pem \
  'src.backend.app:create_app()'
python -m scripts.procesar_reservas --db "$INKAFARMA_DB"
```

Programar el último comando cada minuto junto al servicio WSGI. El arranque local incluye el supervisor. Para publicar, se necesita montar el certificado del dominio y verificar allí el nombre del host, la cadena y las cabeceras. El ensayo HTTPS de esta entrega se hizo en loopback.

## Evidencia y repetición

- [Controles de remediación](../06-evidencias/remediacion/controles.json) y [casos verificables](../../tests/test_remediacion.py).
- [Resultado de auditoría Python](../06-evidencias/remediacion/dependencias.json) y [verificación de instaladores](../06-evidencias/remediacion/instaladores.json).
- [Validación de la entrega](../06-evidencias/remediacion/validacion.md).

```bash
python -m scripts.analizar_seguridad
python -m unittest discover -s tests -v
python -m pip install -r requirements-test.txt
python -m playwright install chromium-headless-shell
python -m unittest discover -s tests/e2e -v
```

Las pruebas históricas conservan sus contratos de S1–S3 en una fábrica de fixtures temporales. La regresión comercial y logística en navegador y los controles nuevos usan la fábrica actual. El informe original y sus inventarios siguen disponibles para comparar el antes y el después.
