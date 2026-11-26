# Informe de análisis de vulnerabilidades — versión 6

**Seguimiento.** Esta página conserva la línea base del PR #57. La [remediación y las pruebas posteriores](REMEDIACION.md) documentan la versión que la sucede.

**Fecha:** 20 de noviembre de 2026. **Código funcional:** `53b6ff85a4904c6c3f1beb6c73ab4601c4b14886`. **Entorno:** Linux, Python 3.12.14, Flask 3.1.3, SQLite esquema v6. [Metodología](METODOLOGIA.md) · [Evidencias](../06-evidencias/documentacion-seguridad-2026-11-20/README.md) · [Plan de cierre](PLAN_REMEDIACION.md).

## Conclusión ejecutiva

Los escenarios probados conservan integridad de precios/stock, rechazan acceso anónimo al panel, protegen las mutaciones con sesión/CSRF y omiten contactos en el seguimiento. Hay carencias que resolver antes de distribuir la operación entre empleados o publicar la compra: identidad individual, autorización por sucursal, límites de abuso y configuración de despliegue. Se confirmó además código de instaladores macOS que omite la validación TLS en una dependencia de pruebas.

Se registran **cinco hallazgos abiertos y dos observaciones**. No se atribuye explotación remota al arranque local ni se confunde la clave compartida con un acceso anónimo. No se modifica la lógica de producción en esta entrega; las correcciones y sus retests quedan especificados, pendientes de implementación.

## Resultados ejecutados

| Actividad | Resultado | Evidencia / límite |
|---|---|---|
| Regresión funcional Python/API/recuperación | 328 aprobadas | [Validación v6](../05-pruebas/VALIDACION_V6.md); incluye seis pruebas de respaldo agregadas en la fase documental. |
| Navegador Chromium | 44 recorridos aprobados | Misma validación; incluye texto malicioso renderizado como texto. No es cobertura total de XSS. |
| Controles de seguridad locales | 23 aprobados, 0 fallos; cinco observaciones separadas | [JSON local](../06-evidencias/documentacion-seguridad-2026-11-20/seguridad-local.json); no simula TLS ni ejecuta JavaScript. |
| Bandit 1.9.4 — `src scripts` | 37 alertas: 6 medias, 31 bajas; 0 errores del analizador | [Salida original](../06-evidencias/documentacion-seguridad-2026-11-20/bandit.json) y [triaje de cada alerta](../06-evidencias/documentacion-seguridad-2026-11-20/bandit-triaje.csv). No son 37 vulnerabilidades confirmadas. |
| pip-audit 2.10.1 — ejecución | 7 paquetes; 0 avisos reportados | [Inventario](inventario-produccion.txt) y [resultado](../06-evidencias/documentacion-seguridad-2026-11-20/dependencias-produccion.json). Resultado de la fuente PyPI en esta fecha. |
| pip-audit — herramientas de pruebas | 4 paquetes adicionales; 0 avisos reportados | [Inventario](inventario-pruebas.txt) y [resultado](../06-evidencias/documentacion-seguridad-2026-11-20/dependencias-pruebas.json). No cubre automáticamente el driver Node ni navegadores. |
| Inspección adicional Playwright | 5 instaladores macOS incluyen `curl -k` | [Evidencia](../06-evidencias/documentacion-seguridad-2026-11-20/playwright-instaladores.json); ninguno se ejecutó en Linux. |

## Registro de riesgo

Valoración contextual P × I según la [metodología](METODOLOGIA.md); no son puntuaciones CVSS ni prueba de explotación. Los escenarios indicados son precondiciones del riesgo.

| ID | Hallazgo | Escenario valorado | P × I | Riesgo / prioridad | Estado |
|---|---|---|---|---|---|
| SEC-01 | Clave operativa compartida, privilegio global y falta de atribución individual | Acceso distribuido a personal de varias sucursales | 2 × 3 = 6 | Medio / P1 | Abierto |
| SEC-02 | Reservas públicas sin verificar contacto ni limitar nuevas confirmaciones | Compra publicada y producto con pocas unidades | 3 × 2 = 6 | Medio / P1 | Abierto; reproducido localmente |
| SEC-03 | Sin freno de intentos de acceso en la aplicación | Panel expuesto con una clave elegida débil o reutilizada | 2 × 3 = 6 | Medio / P1 | Abierto; no se rompió la clave aleatoria |
| SEC-04 | Cookie sin Secure y ausencia de CSP/HSTS en Flask | Despliegue fuera de loopback sin endurecimiento adicional | 2 × 3 = 6 | Medio / P1 | Abierto; configuración local observada |
| SEC-05 | Instaladores macOS de herramienta de pruebas omiten validación TLS | Ejecutar esos instaladores en una red interceptable | 2 × 3 = 6 | Medio / P2 | Abierto; ruta no ejecutada en el entorno actual |

La igualdad de puntuación no implica la misma exposición. SEC-02 actúa sobre una función pública; SEC-01 requiere acceso autorizado; SEC-05 afecta al equipo que instala navegadores, no a una petición de la API.

## SEC-01 — identidad y mínimo privilegio

**Ubicación:** `src/backend/operaciones_demo.py`, `sesion_demo`, `detalle`, `mover_inventario`, `actuar`. La sesión guarda autorización booleana y CSRF. La API decide roles/actores desde el servidor, pero no los deriva de una identidad personal autenticada. Para movimientos se utiliza el rol administrador predeterminado; para reparto se toma el repartidor asociado al pedido.

**Evidencia:** una segunda sesión con la misma clave obtuvo HTTP 200 en inventario y acceso a las tres sucursales. C02/C15 prueban que una sesión anónima sigue bloqueada. C19 prueba que enviar `rol` o `actor_id` no modifica ese comportamiento.

**Impacto condicionado:** una persona que conoce la clave puede operar globalmente y no existe atribución/revocación por empleado. La validación de rol en servicios internos no equivale a una política de permisos por usuario en HTTP.

**Recomendación:** cuentas individuales, credenciales almacenadas con hash apropiado, relación usuario/rol/sucursal, autorización en cada ruta y auditoría del actor real. Mantener un perfil central explícito para operaciones que lo necesiten. Verificar con dos usuarios de sucursales distintas y uno central; conservar denegaciones anónimas y CSRF.

## SEC-02 — bloqueo temporal de stock por pedidos no verificados

**Ubicación:** `src/backend/pedidos_web.py`, `pedidos_s2.py`, `pedidos_integracion.py`, `logistica.py`. Se valida el formato del contacto y una cotización, pero no su propiedad ni un cupo de nuevas confirmaciones por cliente. UUID/idempotencia evita duplicar una misma confirmación; otro UUID representa otro pedido.

**Reproducción acotada:** en una segunda base temporal se ajustó un producto a una unidad física por cada una de tres sucursales. Un cliente sin sesión hizo cuatro confirmaciones con UUID distintos y el mismo contacto sintético: HTTP **200, 200, 200, 409**. Se observaron tres reservas activas; el físico seguía en tres. No se usó una carga masiva.

**Impacto:** se agota temporalmente la disponibilidad de un producto aunque no exista intención de recibirlo. El supervisor vence inicialmente una asignación no aceptada a los 15 minutos y puede reasignarla; esto limita la permanencia de cada intento, pero no impide crear nuevos pedidos. No se afirma un bloqueo permanente ni una caída de todo el sistema.

**Recomendación:** verificar contacto en el momento adecuado, cupos y límites proporcionales de pedidos/reservas, detección de repetición y expiración total de una reserva. Evitar que un atacante bloquee a otra persona solo por introducir su teléfono. Mantener idempotencia, rollback y atención legítima; verificar agotamiento y recuperación bajo el límite acordado.

## SEC-03 — intentos de acceso sin limitación

**Ubicación:** `src/backend/operaciones_demo.py::sesion_demo`. Seis claves erróneas consecutivas devolvieron 401; la siguiente clave válida devolvió 200. En el código de esa ruta no se encontró retardo, contador de intentos ni desafío por abuso. No se evaluó una protección de proxy porque no existe despliegue público en el alcance.

**Impacto condicionado:** facilita intentos automatizados si se configura una clave débil o reutilizada. La clave generada aleatoriamente por el arranque tiene alta entropía; esta prueba no demuestra que pueda adivinarse. Una defensa de tasa por sí sola no reemplaza credenciales fuertes.

**Recomendación:** limitación con ventana y enfriamiento, registro de intentos sin almacenar claves, protección contra denegación por bloqueo y controles consistentes entre procesos. Probar que el intento N+1 supera la política, se recupera tras la ventana y no bloquea globalmente a usuarios legítimos.

## SEC-04 — configuración antes del despliegue público

**Ubicación:** `src/backend/app.py::create_app` y `scripts/iniciar_tienda.py`. La respuesta local de sesión tiene HttpOnly y SameSite=Strict, pero no Secure; no se emiten CSP ni HSTS. Se mantienen `nosniff`, `no-referrer`, `DENY` y `no-store` para API. El servidor arranca en `127.0.0.1` con depuración desactivada.

**Impacto condicionado:** publicar esa misma configuración sin TLS/cookie Secure debilita la confidencialidad de sesión. Ausencia de CSP reduce defensa adicional si apareciera una inyección; no demuestra una XSS existente. HSTS corresponde a un servicio HTTPS correctamente configurado, no a habilitarlo a ciegas en HTTP local.

**Recomendación:** perfil de producción con WSGI, TLS, orígenes/hosts permitidos, cookie Secure y política de cabeceras compatible con las páginas. Comenzar CSP en modo de reporte, adaptar recursos/estilos según sea necesario y verificar el flujo completo sobre HTTPS. No se afirma que una infraestructura externa carezca de estos controles.

## SEC-05 — descarga de navegadores en herramienta de pruebas

**Ubicación:** `requirements-test.txt`, Playwright Python 1.51.0; driver incluido en `playwright/driver/package/bin/`. Cinco scripts `reinstall_*_mac.sh` contienen instrucciones `curl ... -k ...` para Chrome/Edge. Se conservaron rutas relativas, líneas y SHA-256. Son scripts macOS; las 44 pruebas registradas usaron Chromium en Linux.

**Impacto condicionado:** ejecutar esos instaladores en una red interceptable permite descargar contenido sin autenticar el certificado TLS; algunos pasos instalan con privilegios elevados. **No se ejecutaron ni se sustituyó ninguna descarga**. El hallazgo no significa que un visitante de la tienda pueda ejecutar código por la API.

**Fuente y límite de SCA:** el [aviso original GHSA-qxm8-4v54-964r](https://github.com/SocketDev/security-research/security/advisories/GHSA-qxm8-4v54-964r) documenta este patrón en Playwright npm y remite al cambio incluido en v1.56.0; está relacionado con CVE-2025-59288. La aplicación usa el paquete Python, que incluye el driver: la aplicabilidad se basa en la inspección de los scripts realmente instalados, no en inventar un aviso PyPI que pip-audit no devolvió. No se asigna el CVSS del aviso npm al despliegue de esta aplicación.

**Recomendación:** actualizar la herramienta a una versión mantenida que incluya esa corrección —al menos 1.56.0 para este cambio—, revisar los scripts del artefacto instalado y volver a descargar/verificar navegadores con TLS válido. Repetir los 44 recorridos con la versión seleccionada. Esta entrega conserva la dependencia actual para que el resultado de la evaluación sea revisable; actualización y retest siguen pendientes.

## Revisión de alertas estáticas

Las seis B608 interpolan listas de marcadores `?`, nombres de columnas de una lista interna o cláusulas internas; los valores de usuario se enlazan por separado. La revisión individual no confirmó SQLi en esos puntos. C11 complementa esa revisión en búsqueda, sin demostrar todos los parámetros del sistema seguros. Los 37 registros y su justificación quedan en el CSV, sin ocultar resultados.

Las otras 31 alertas corresponden a herramientas: 21 `assert`, ocho avisos de imports/invocaciones `subprocess` con listas y sin shell, dos imports XML usados para generar/serializar documentos, sin parser de XML externo. Los ejecutables locales deben ser confiables y cualquier futura entrada externa exige reevaluar el uso.

## Observaciones de operación y herramientas

- **OBS-01:** `app.secret_key` se genera por instancia. Una cookie de una instancia, con la misma clave operativa y base, obtuvo 401 en otra. Afecta continuidad entre procesos/reinicios; no es una falsificación de sesión. Antes de usar varios workers, definir secreto persistente protegido y rotación compatibles con la política de sesión.
- **OBS-02:** los `assert` de generadores y smoke checks se omiten con `python -O`. Los comandos documentados no usan optimización. Sustituir validaciones críticas por excepciones explícitas si esas herramientas se convierten en condición obligatoria de entrega.

## Correcciones, retest y riesgo residual

En esta fase se corrigieron documentación y recuperación verificable, no los cinco hallazgos de seguridad de la lógica/configuración. **No hay hallazgos marcados como remediados.** Los 23 controles son la línea base del análisis y no un retest de correcciones inexistentes. El [plan](PLAN_REMEDIACION.md) define evidencia posterior, responsables por asignar y bloqueo de cierre hasta ejecutar sus criterios.

La falta de alertas de dependencias no acredita ausencia de fallos desconocidos, paquetes maliciosos o problemas en componentes nativos. La evaluación no cubre todo ASVS ni todo WSTG. Las reuniones Scrum, validación con destinatarios y aceptación docente tampoco se sustituyen por este informe.
