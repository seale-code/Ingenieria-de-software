# Evidencia técnica — Base de datos del Sprint 1

**Fecha:** 18 de octubre de 2026.  
**Alcance:** S1-06 / Issue #6 y S1-07 / Issue #3; base SQLite, datos ficticios y consultas de apoyo.  
**Estado:** implementación y pruebas automáticas realizadas; revisión del equipo pendiente.

## Entorno y reproducción

- Python 3.12.14; SQLite 3.53.1; Windows.
- Sin dependencias externas para la implementación o las pruebas.
- Pruebas con bases temporales, sin utilizar datos de usuarios.

```bash
python -m unittest discover -s tests -v
python -m src.database init --demo
python -m src.database stock --sucursal DEMO-NORTE --solo-disponibles
```

En el entorno aislado utilizado se configuraron TEMP/TMP hacia una carpeta local `.test-tmp` debido a restricciones de eliminación de temporales del sistema. No se modificó la lógica de las pruebas para omitir comprobaciones.

## Resultado observado

La suite automatizada pasó: **24 pruebas, 0 fallos y 0 errores**. Los comandos crearon la base y devolvieron `DEMO-A`, `DEMO-NORTE`, cantidad `5` como única fila disponible en Norte.

| Grupo | Comprobaciones |
|---|---|
| Integridad | Stock negativo/fraccionado/nulo rechazado en insert y update; par producto/sucursal único. |
| Relaciones | Producto, sucursal y categoría deben existir; no se eliminan entidades referenciadas. |
| Datos | Códigos y nombres no vacíos, coordenadas dentro de rango y stock por sucursal. |
| Conservación | Repetir init/seed mantiene cantidades editadas; base ajena y versión futura se rechazan sin modificaciones. |
| Transacción | Un error durante seed revierte todas sus inserciones. |
| Consulta | Filtros combinados, cero stock excluido, texto SQL y comodines tratados como datos, mayúsculas Unicode. |
| Comandos | Creación/consulta correctas; base ausente produce error claro sin crear un archivo. |

Las pruebas se escribieron y ejecutaron antes de la implementación correspondiente: primero 10 fallos por ausencia del esquema; después 14 fallos adicionales por ausencia del módulo/comandos. Las correcciones posteriores produjeron una suite completamente verde.



[Código e instrucciones](../../src/database/README.md) · [Pruebas](../../tests/test_database.py)
