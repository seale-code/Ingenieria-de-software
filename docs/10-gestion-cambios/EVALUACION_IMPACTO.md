# Evaluación de impacto — SC-INK-001

## Revisión de la línea base v6
En `src/frontend/index.html`, el formulario `.header-search` usa `role="search"`, campo `#search` y botón `type="submit"` con `aria-label="Buscar"` e icono SVG. El campo ya tenía etiqueta accesible «Buscar producto». La revisión inicial identificó la búsqueda con `load()` y el evento submit en `src/frontend/catalogo.js`.

| Área | Impacto previsto | Impacto observado / medida |
|---|---|---|
| HTML | Bajo | Texto visible y nombre accesible actualizados; se conserva formulario y lupa. |
| CSS | Bajo | Ajuste de alineación, ancho, colores, espaciado y estilos para pantallas pequeñas. |
| JavaScript / API | Ninguno previsto | Sin cambios locales detectados en estos archivos; regresión del catálogo satisfactoria. |
| SQLite / seguridad | Ninguno previsto | Sin cambios locales detectados en esquema, permisos o controles; no implica auditoría integral. |
| Pruebas | Regresión del catálogo | 8 de 8 pruebas satisfactorias, 27/11/2026. |
| Documentación | Capturas y registro | Evidencias de antes, después, responsive, pruebas y aprobación. |

Riesgos: texto recortado en móvil, reducción del campo de búsqueda, desajuste del nombre accesible y selectores dependientes del texto. Mitigación: revisar tamaños, teclado y nombre accesible; ejecutar regresión. La regresión pasó; falta confirmación específica de VC-02 a VC-05.

Recursos: desarrollador, revisor, navegador Chromium, Playwright y entorno local Python. Esfuerzo: pendiente de registrar. Decisión del aprobador: impacto bajo, aprobado el 27/11/2026, condicionado a validación antes de integrar.

Reversión: si el cambio ya fue integrado y falla, preparar PR de reversión del commit específico previa autorización; no revertir otros cambios de v6. Si aún no se integró, corregir en su rama.
