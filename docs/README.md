# Documentación de Inkafarma

Actualización: **20 de noviembre de 2026**, esquema **v6**, base funcional histórica `53b6ff8` (PR #56 integrado); consolidación DOC-01 sobre `daa9716` (PR #57). Los informes anteriores conservan su fecha y versión.

## Recorrido de lectura

| Documento | Contenido |
|---|---|
| [Alcance y objetivos](01-requisitos/ALCANCE_Y_OBJETIVOS.md) | Problema, objetivos y fronteras de la propuesta. |
| [Requisitos](01-requisitos/REQUISITOS.md) | Funciones, reglas y condiciones de calidad comprobables. |
| [Trazabilidad](01-requisitos/TRAZABILIDAD_IMPLEMENTACION.md) | 46 criterios: HU → diagrama → código → prueba → resultado → PR. |
| [Historias originales](02-historias-usuario/HistoriasdeUsuario-Inkafarma.pdf) | Fuente funcional conservada sin modificar; [historias y cobertura actualizadas](02-historias-usuario/HISTORIAS_ACTUALIZADAS.md). |
| [Casos de uso](03-diagramas/CASOS_DE_USO.md) y [flujo](03-diagramas/FLUJO_PEDIDO.md) | Recorridos y estados de la aplicación. |
| [Datos v6](03-diagramas/MODELO_DATOS.md) y [diccionario](03-diagramas/DICCIONARIO_DATOS_V6.md) | Relaciones, restricciones y campos del esquema. |
| [UML editable](03-diagramas/uml/README.md) | 17 diagramas del sistema objetivo por procesos; incluye funciones futuras. |
| [Scrum](07-scrum/README.md), [MoSCoW](07-scrum/PRIORIZACION.md) y [cierre](07-scrum/ESTADO_CIERRE_SPRINTS.md) | Planificación y evidencia técnica diferenciada de reuniones y aceptación. |
| [Manual de usuario](09-manuales/USUARIO.md) | Compra, seguimiento, operaciones e inventario. |
| [Manual técnico](09-manuales/TECNICO.md) | Instalación, configuración, migración, respaldo y recuperación. |
| [Validación v6](05-pruebas/VALIDACION_V6.md) | Pruebas, recuperación y mediciones locales reproducibles. |
| [Seguridad](08-seguridad/README.md) | Alcance y resultados del análisis de vulnerabilidades de esta entrega. |
| [Gestión de cambios](10-gestion-cambios/README.md) | Procedimiento y solicitud SC-INK-001, pendientes de aprobación y ejecución. |
| [Informe técnico](INFORME_TECNICO.md) | Síntesis de solución, resultados y decisiones. |
| [Estado y decisiones](ESTADO_Y_PENDIENTES.md) | Cobertura real y validaciones del equipo. |

## Producto y versiones

Funcionan catálogo, carrito, cotización, pedidos, preparación, reparto, seguimiento e inventario con Flask, SQLite y HTML/CSS/JavaScript. Se inicia con `python -m scripts.iniciar_tienda`; API e interfaz ya están implementadas.

La [validación de logística del 16 de noviembre](06-evidencias/2026-11-16_logistica-sucursales.md) registra 322 pruebas Python/API y 44 recorridos Chromium sobre la funcionalidad integrada en #56. Consultar [catálogo comercial](CATALOGO_COMERCIAL.md), [reglas logísticas](LOGISTICA_SUCURSALES.md) y el [índice de evidencias](06-evidencias/README.md).

La [validación posterior a la remediación](06-evidencias/remediacion/validacion.md) registra 334 pruebas Python/API/recuperación y 44 recorridos Chromium aprobados localmente el 20 de noviembre. La verificación telefónica previa a la reserva y las cuentas personales de operadores se describen en [remediación](08-seguridad/REMEDIACION.md). Estos resultados no fueron ejecutados de nuevo en DOC-01.

Los documentos iniciales se conservan en [histórico](00-historico/README.md); las copias del [índice](00-historico/estado-anterior-v6/README.txt) y [revisión anteriores](00-historico/estado-anterior-v6/ESTADO_Y_PENDIENTES.txt) preservan su texto. Los enlaces dentro de esas copias corresponden a su ubicación original.

Una prueba aprobada o un merge no acredita por sí solo una Sprint Review, aceptación del Product Owner, validación con usuarios ni aprobación del docente.
