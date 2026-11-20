# Informe técnico de la propuesta Inkafarma

**Versión funcional v6**, base `53b6ff8`, revisión documental del **20 de noviembre de 2026**. [Índice](README.md) · [Requisitos](01-requisitos/REQUISITOS.md).

## 1. Problema, objetivo y alcance

Coordinar pedidos entre sucursales requiere evitar stock comprometido, asignaciones que no se aceptan y descuentos repetidos. La aplicación relaciona catálogo, pedido, reserva, selección de sucursal, preparación/reparto e inventario con estados e historial verificables. El [alcance](01-requisitos/ALCANCE_Y_OBJETIVOS.md) define objetivos y fronteras sin atribuir mediciones o integración interna con Inkafarma.

## 2. Gestión y requisitos

El trabajo se organiza por incrementos de S1–S3 y ampliaciones integradas mediante PR. Scrum es la referencia de gestión y MoSCoW prioriza los requisitos. Los planes, tareas y resultados están disponibles; las ceremonias, roles Scrum y aceptación se acreditan solo con registros reales. Consultar [estado de cierre](07-scrum/ESTADO_CIERRE_SPRINTS.md).

La [trazabilidad](01-requisitos/TRAZABILIDAD_IMPLEMENTACION.md) conserva 15 HU y 46 criterios: 14 implementados, 10 adaptados, 10 parciales y 12 pendientes. No se mezcla ese resumen en un porcentaje de aprobación ni se equipara representación UML con código implementado.

## 3. Arquitectura y diseño

Cliente HTML/CSS/JavaScript, API Flask y servicios Python, persistencia SQLite. Los módulos funcionales comparten la base y transacciones; el diagrama de componentes no significa un despliegue en microservicios. La compra calcula precios en servidor y mantiene un snapshot inmutable. El panel coordina atención, reparto y soporte; el supervisor procesa vencimientos independientes del navegador.

Los [17 UML](03-diagramas/uml/README.md) son del sistema objetivo y conservan cinco grupos. El [modelo v6](03-diagramas/MODELO_DATOS.md) y [diccionario](03-diagramas/DICCIONARIO_DATOS_V6.md) describen las 20 tablas migradas. La aceptación docente del agrupamiento no consta.

## 4. Reglas que protegen la operación

- Stock disponible calculado a partir del físico y reservas activas; las liberadas se conservan como historial.
- Asignación exige pedido completo/capacidad, prioriza distancia al centro del distrito y no divide sucursales.
- Reasignación libera/evalúa/reserva y registra la solución en una transacción; sin alternativa cancela.
- Preparar acepta la atención; las asignaciones pendientes vencen inicialmente a los 15 minutos.
- Salida de reparto consume una vez y registra un movimiento; recepción conserva coherencia de fecha/estado.
- Entradas/ajustes exigen motivo y UUID; un ajuste valida el saldo visto y protege las reservas.

## 5. Verificación y resultados

La [ejecución actual](05-pruebas/VALIDACION_V6.md) registra 328 pruebas Python/API/recuperación y 44 recorridos Chromium aprobados. Incluye rollback, concurrencia, idempotencia, privacidad, formatos móviles y recuperación a una base nueva. La medición pequeña de laboratorio registra percentiles, muestras y entorno; no se presenta como un SLA ni una mejora de la operación real.

Los manuales de [usuario](09-manuales/USUARIO.md) y [operación técnica](09-manuales/TECNICO.md) permiten reproducir arranque, flujo, inventario, supervisor, copia y restauración sin sobrescribir el origen.

## 6. Seguridad

Los controles y resultados del análisis se documentan en [seguridad](08-seguridad/README.md). Sesión, CSRF y consultas parametrizadas aportan protección, pero las pruebas funcionales no acreditan ausencia de vulnerabilidades. La clave compartida y la configuración de un despliegue público requieren una evaluación contextual. Esta primera fase documental no presenta un pentest ya concluido.

## 7. Decisiones y continuidad

Se mantiene pago al recibir, entrega a domicilio, catálogo/existencias locales y ubicación por distrito. Cuentas individuales, avisos externos, chat, multicanal y equivalencias están diferenciados como cobertura parcial/futura. La aceptación de las adaptaciones, reuniones Scrum y uso con destinatarios requiere evidencia del equipo. Consultar [estado](ESTADO_Y_PENDIENTES.md).

La propuesta demuestra reglas de coordinación con pruebas reproducibles. Los beneficios observados se limitan a esos escenarios; la aceptación del producto y un despliegue real requieren sus validaciones correspondientes.

## 8. Referencias

- [Historias originales](02-historias-usuario/HistoriasdeUsuario-Inkafarma.pdf).
- [Fuentes comerciales](CATALOGO_COMERCIAL.md) y [reglas logísticas](LOGISTICA_SUCURSALES.md).
- [Scrum Guide](https://scrumguides.org/scrum-guide.html).
- [MoSCoW — Agile Business Consortium](https://www.agilebusiness.org/dsdm-project-framework/moscow-prioritisation.html).
- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/) y [WSTG](https://owasp.org/www-project-web-security-testing-guide/).
