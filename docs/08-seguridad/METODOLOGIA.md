# Metodología de análisis de seguridad

[Informe](ANALISIS_VULNERABILIDADES.md) · [Plan](PLAN_REMEDIACION.md) · [Evidencias](../06-evidencias/documentacion-seguridad-2026-11-20/README.md).

## Objetivo y alcance autorizado

Evaluar la propuesta Inkafarma en este repositorio, con acceso al código y pruebas controladas en proceso local. La revisión funcional toma el commit `53b6ff85a4904c6c3f1beb6c73ab4601c4b14886`, esquema SQLite v6; las herramientas/documentación agregadas se evalúan en esta rama. El JSON local conserva SHA-256 de las fuentes para identificar exactamente el material probado.

Incluye `src/`, herramientas Python de `scripts/`, inventarios de dependencias de ejecución/pruebas, rutas públicas/operativas de Flask, sesión, CSRF, privacidad, precio, reservas y despacho. Las comprobaciones HTTP usan `Flask.test_client`, sin servidor de red; hay dos bases temporales: controles y un escenario de reservas de tres unidades totales. Las llamadas no generan cobros ni entregas externas.

Fuera de alcance: sistemas o marca comercial de Inkafarma fuera del repositorio, clientes reales, infraestructura desplegada, TLS de un dominio, firewall, sistema operativo, librerías nativas y binarios completos de navegadores, ingeniería social, carga masiva, análisis regulatorio y auditoría completa del historial Git. No se ejecutan instaladores inseguros ni pruebas de intermediario de red.

## Activos y fronteras

| Activo / frontera | Riesgo considerado | Evidencia seleccionada |
|---|---|---|
| Navegador público → compra | Alterar precio, repetir confirmaciones o inmovilizar disponibilidad | C13–C14 y SEC-02. |
| Sesión → panel operativo | Acceso sin sesión, CSRF, privilegio global y falta de atribución | C01–C10, C15, C19, SEC-01 y SEC-03. |
| Código privado → seguimiento | Enumeración por ID y exposición de contacto | C16–C18; no prueba de entropía exhaustiva. |
| Servicios → SQLite | Entradas SQL, estados inválidos y descuento repetido | C11, C20–C22; revisión de las seis alertas B608. |
| Herramienta de pruebas → instalador | Descarga que omite autenticidad TLS | SEC-05; inspección estática, sin ejecutar la descarga. |

## Procedimiento ejecutado

1. Identificar versión, arquitectura, rutas, dependencias instaladas y controles existentes.
2. Ejecutar la validación funcional/documental y conservar sus resultados fechados.
3. Ejecutar Bandit sobre `src scripts`; conservar todas las alertas y revisar el origen de los datos. Una alerta no se convierte automáticamente en vulnerabilidad confirmada.
4. Ejecutar pip-audit sobre dos inventarios completos y fijados para este Linux, separados por ejecución y herramientas de pruebas. Se consulta el servicio PyPI predeterminado; no se resuelve de nuevo un archivo con dependencias flotantes.
5. Ejecutar 23 controles locales y cinco observaciones con datos sintéticos. El script publica únicamente estados HTTP, contadores, booleanos y hashes de fuentes.
6. Contrastar resultados del escáner con código/fuentes primarias; registrar hallazgo, precondición, impacto, recomendación y estado real del retest.

No se afirma cumplimiento completo de ASVS ni WSTG. Se usa una selección de áreas: autenticación, autorización, sesión, entrada/salida, privacidad y lógica de negocio. WSTG-ATHN-03 orienta intentos de acceso; WSTG-SESS-02, atributos de cookies; WSTG-BUSL-05, límites de uso de funciones. Las demás comprobaciones se describen por su escenario concreto, sin atribuirles una cobertura exhaustiva de un control OWASP.

## Reproducción

Desde la raíz del repositorio, en un entorno Python 3.12 limpio:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-test.txt -r requirements-security.txt
python -m scripts.analizar_seguridad --revision 53b6ff85a4904c6c3f1beb6c73ab4601c4b14886 --salida seguridad-local.json
python -m bandit -r src scripts -f json -o bandit.json
python -m pip_audit --no-deps --disable-pip --progress-spinner off -r docs/08-seguridad/inventario-produccion.txt -f json -o dependencias-produccion.json
python -m pip_audit --no-deps --disable-pip --progress-spinner off -r docs/08-seguridad/inventario-pruebas.txt -f json -o dependencias-pruebas.json
python -m scripts.verificar_documentacion
```

En Windows, activar `.venv\Scripts\Activate.ps1`. No se necesita descargar navegadores para estas comprobaciones. Los [manuales](../09-manuales/TECNICO.md) incluyen las pruebas de navegador, que se ejecutaron antes de esta fase.

Bandit devolvió **1 por alertas**, no por un fallo de análisis; `errors` está vacío. pip-audit devolvió 0 en ambos inventarios. El script devuelve 1 si un control esperado falla; las carencias observadas se registran por separado y siguen abiertas aunque su código de salida sea 0. No se silencian alertas con `nosec` ni avisos con `ignore-vuln`.

Los inventarios son la resolución **instalada** al evaluar, no un lock universal ni una garantía de integridad de descarga: las dependencias transitivas de Flask no están fijadas en `requirements.txt` y faltan hashes. En otro sistema/fecha se debe generar la clausura de dependencias del entorno real y auditarla; los archivos conservados permiten repetir la consulta de estas versiones. `requirements-test.txt` incluye producción: su inventario adicional contiene solo las cuatro herramientas que no estaban en el inventario de ejecución.

Para comprobar SEC-05, localizar la instalación con `python -m pip show playwright` y revisar los cinco archivos `playwright/driver/package/bin/reinstall_*_mac.sh` que enumera la evidencia. Comparar el uso de `curl -k` con el aviso original y el cambio de Microsoft. No ejecutar esos scripts para reproducir el hallazgo.

## Criterio de riesgo

Valoración cualitativa propia, **no CVSS**. Probabilidad 1 = exige condiciones poco frecuentes o entorno no usado; 2 = requiere credencial/acción/configuración adicional; 3 = accesible mediante función pública de uso ordinario. Impacto 1 = limitado a una herramienta/acción recuperable; 2 = indisponibilidad acotada o afectación operativa; 3 = exposición de contacto, alteración global o ejecución privilegiada. Producto: 1–3 bajo, 4–6 medio, 7–9 alto.

La tabla del informe valora el escenario explícito de cada hallazgo: publicar compra, distribuir acceso a empleados o ejecutar instaladores macOS. El arranque actual está en `127.0.0.1`; esos escenarios no se presentan como incidentes ocurridos en una plataforma pública. Prioridad P1 = antes de habilitar ese uso; P2 = siguiente incremento antes de ampliarlo. La severidad del escáner se conserva aparte de esta valoración.

## Referencias primarias consultadas el 20 de noviembre de 2026

- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/), referencia de requisitos, sin certificación de nivel.
- [WSTG v4.2 — intentos de acceso](https://wstg.owasp.org/v4.2/4-Web_Application_Security_Testing/04-Authentication_Testing/03-Testing_for_Weak_Lock_Out_Mechanism/).
- [WSTG v4.2 — atributos de cookies](https://wstg.owasp.org/v4.2/4-Web_Application_Security_Testing/06-Session_Management_Testing/02-Testing_for_Cookies_Attributes/).
- [WSTG v4.2 — límites de uso de funciones](https://wstg.owasp.org/v4.2/4-Web_Application_Security_Testing/10-Business_Logic_Testing/05-Test_Number_of_Times_a_Function_Can_Be_Used_Limits/).
- [Flask — consideraciones de seguridad](https://flask.palletsprojects.com/en/stable/web-security/) y [configuración](https://flask.palletsprojects.com/en/stable/config/).
- [Bandit B608](https://bandit.readthedocs.io/en/latest/plugins/b608_hardcoded_sql_expressions.html) y [modelo de seguridad de pip-audit](https://github.com/pypa/pip-audit#security-model).
- [Aviso original de Socket sobre instaladores Playwright](https://github.com/SocketDev/security-research/security/advisories/GHSA-qxm8-4v54-964r), [cambio de Microsoft](https://github.com/microsoft/playwright/pull/37532) y [release v1.56.0](https://github.com/microsoft/playwright/releases/tag/v1.56.0).
