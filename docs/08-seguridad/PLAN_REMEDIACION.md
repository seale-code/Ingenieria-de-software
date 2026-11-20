# Plan de remediación y verificación posterior

[Informe](ANALISIS_VULNERABILIDADES.md) · [Registro CSV](HALLAZGOS.csv) · [Metodología](METODOLOGIA.md).

**Estado al 20 de noviembre de 2026:** todos los hallazgos están abiertos. El análisis está ejecutado; las siguientes acciones son trabajo futuro, sin fechas ni responsables personales inventados. El equipo debe asignar personas y estimar esfuerzo en su siguiente planificación. P1 debe completarse antes del uso indicado; P2 antes de ampliar el entorno de pruebas correspondiente.

| ID / prioridad | Acción concreta | Responsable funcional propuesto | Criterio de corrección y retest | Evidencia de cierre actual |
|---|---|---|---|---|
| SEC-01 / P1 | Implementar identidad individual, roles/sucursal y auditoría del actor autenticado | Backend + responsable de operación, por asignar | Dos usuarios de sucursal solo consultan/modifican su ámbito; el central conserva permisos explícitos; acceso cruzado recibe 403; actor no se obtiene del cuerpo; baja/rotación retira acceso según política | Pendiente; sin PR de corrección |
| SEC-02 / P1 | Acordar e implementar verificación de contacto, límites de reserva y expiración total | Producto + backend, por asignar | Prueba acotada N/N+1 según umbral acordado; solicitudes sin verificación no inmovilizan stock indefinidamente; recuperación tras vencimiento; contactos ajenos no permiten bloqueo dirigido; compra legítima, concurrencia e idempotencia conservadas | Pendiente; escenario base [200,200,200,409] |
| SEC-03 / P1 | Añadir control de intentos y observabilidad sin registrar claves | Backend + despliegue, por asignar | Umbral documentado; límite/retardo reproducible entre procesos; recuperación tras ventana; protección frente a bloqueo global; reintentos legítimos funcionan | Pendiente; seis intentos rechazados sin limitación observada |
| SEC-04 / P1 | Definir perfil HTTPS/WSGI, secretos, hosts/orígenes y cabeceras | Despliegue + frontend/backend, por asignar | Cookie Secure/HttpOnly/SameSite sobre HTTPS; TLS y HSTS verificados en el dominio; CSP evaluada y aplicada sin romper compra/panel; secretos fuera del repo; 23 controles y recorrido completo pasan | Pendiente; solo configuración HTTP local inspeccionada |
| SEC-05 / P2 | Actualizar Playwright y navegadores compatibles; revisar instaladores | Responsable de pruebas, por asignar | Versión mantenida con cambio de v1.56.0 o posterior; cinco scripts sin descarga que omita validar TLS; repetir SCA y 44 recorridos; registrar versiones de navegador | Pendiente; dependencia actual 1.51.0 conservada |
| OBS-01 | Configurar secreto de sesión persistente protegido y rotación | Despliegue + backend, por asignar | Sesión funciona entre workers según política; rotación y expiración retiran acceso como se espera; no se publica secreto | Pendiente; otra instancia devuelve 401 |
| OBS-02 | Cambiar validaciones de entrega basadas en assert por fallos explícitos | Documentación/herramientas, por asignar | Datos deliberadamente inválidos detienen la herramienta con y sin `python -O`; no se confunde con prueba de autorización HTTP | Pendiente; no afecta al arranque normal documentado |

## Registro de verificación posterior

Para cerrar un hallazgo se debe agregar una fila con: ID, fecha real, responsable, commit/PR de corrección, entorno, prueba ejecutada, resultado esperado/obtenido, evidencia y riesgo residual. La persona que revise debe poder repetir la prueba. Si la medida depende de un proxy o servicio externo, probar ese despliegue; una opción de Flask en un test local no basta.

| Verificación | Fecha real | Corrección / PR | Resultado | Decisión |
|---|---|---|---|---|
| Línea base del análisis, C01–C23 | 20-11-2026 | Código funcional 53b6ff8; análisis en esta entrega | 23/23 aprobados; hallazgos abiertos registrados | No cierra SEC-01–SEC-05 |
| Retest de remediación | Pendiente de implementación | Pendiente | No ejecutado | Mantener abiertos |

## Relación con Scrum y MoSCoW

Scrum organiza planificación, ejecución, Review y retrospectiva; MoSCoW ayuda a priorizar requisitos. Para un incremento de uso público/multiusuario, SEC-01–SEC-04 se proponen como **Must** de esa liberación y SEC-05 como **Must** antes de usar los instaladores afectados. El equipo debe aceptar esa priorización y reflejarla en el Product Backlog; una propuesta documental no equivale a un acuerdo registrado.

La definición de terminado del incremento de seguridad debe exigir pruebas de abuso/autorización, regresión relevante, evidencias sin secretos y revisión de riesgo residual. No se cierran tareas por la mera existencia del informe o por aprobar las pruebas funcionales anteriores.
