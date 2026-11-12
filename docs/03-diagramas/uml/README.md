# Diagramas UML — Inkafarma

Carpeta preparada para cargar y revisar los diagramas antes de integrarlos en main.

## Organización

| Carpeta | Contenido esperado |
|---|---|
| editables/ | Archivo .drawio completo con todas las páginas |
| casos-de-uso/ | 1 modelo general |
| actividades/ | 15 diagramas: uno por HU01–HU15 |
| secuencias/ | 15 diagramas: uno por HU01–HU15 |
| componentes/ | 1 diagrama general |
| colaboracion/ | 15 diagramas: uno por HU01–HU15 |

Total esperado: 47 diagramas. El índice del archivo multipágina no cuenta como diagrama.

## Subir archivos

1. En GitHub, selecciona la rama `docs/diagramas-uml-willy`.
2. Abre esta carpeta y entra a `editables/` para subir el archivo .drawio completo; las demás carpetas sirven para archivos individuales o exportaciones PNG/PDF.
3. Selecciona **Add file → Upload files**, arrastra los archivos y confirma el commit en esta misma rama. Se agregarán al Pull Request abierto automáticamente.
4. Para archivos individuales, usa nombres como `HU01_actividades.drawio`, `HU01_secuencia.drawio` y `HU01_colaboracion.drawio`.
5. Revisa los diagramas y solicita revisión antes de fusionar el PR.

## Validación pendiente

- [ ] Contrastar los modelos con las historias originales del PDF.
- [ ] Validar actores, decisiones, condiciones y mensajes.
- [ ] Distinguir funciones implementadas de propuestas y diferidas.
- [ ] Comprobar apertura en diagrams.net y legibilidad de las exportaciones.
- [ ] Obtener revisión del equipo.

Esta estructura no contiene todavía diagramas aprobados. Los archivos `.gitkeep` permiten conservar las subcarpetas vacías en Git.
