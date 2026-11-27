# Solicitud de cambio SC-INK-001

Adaptación académica del formato FOR-PYP-001-010 (referencia PRO-PYP-006).

| Campo | Valor |
|---|---|
| Proyecto | Inkafarma — Sistema de Gestión de Pedidos entre Sucursales |
| Issue | [#62](https://github.com/seale-code/Ingenieria-de-software/issues/62) |
| Tipo | Cambio menor de interfaz y accesibilidad |
| Solicitante | Pendiente de identificar formalmente |
| Fecha de solicitud | Pendiente de confirmar |
| Estado | Aprobado; implementado localmente, en validación |
| Componente | Catálogo: `src/frontend/index.html` y `src/frontend/tienda.css` |
| Situación inicial | Botón con lupa y `aria-label="Buscar"`, sin texto visible. |
| Cambio solicitado | Mostrar «Buscar producto» como texto visible y nombre accesible coherente, conservando la lupa y el comportamiento de envío. |
| Justificación | Clarificar la acción para el usuario sin alterar la búsqueda. |
| Exclusiones | API, lógica JavaScript, base de datos, seguridad y reglas de pedidos. |
| Prioridad propuesta | Baja |
| Estimación | Pendiente de registrar por el responsable |

## Decisión
- [x] Aprobado
- [ ] Rechazado

Aprobador: `josue456cris`. Fecha: 27/11/2026. Impacto: bajo. Condiciones: verificar búsqueda, accesibilidad y adaptación móvil antes de integrar en main. Referencia: comentario en el [Issue #62](https://github.com/seale-code/Ingenieria-de-software/issues/62) y [captura de aprobación](evidencias/05-aprobacion-solicitud.png).

La aprobación documentada ocurrió después de la implementación local y de la regresión inicial, desviándose del orden previsto. No constituye aprobación del PR ni autorización retroactiva registrada antes de implementar.

## Criterios
Texto exacto visible; nombre accesible coherente; búsqueda y filtros conservados; sin cortes ni superposiciones en escritorio y móvil. El requisito de decisión previa no se cumplió en el orden documentado; registrar la desviación y solicitar revisión antes de integrar.
