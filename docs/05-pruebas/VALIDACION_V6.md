# Validación de documentación y operación v6

**20 de noviembre de 2026**, base funcional `53b6ff8`. Los cambios de esta fase actualizan documentación y añaden herramientas de respaldo, medición y verificación documental; no cambian el comportamiento del backend/frontend.

## Resultados de esta ejecución

| Verificación | Resultado | Registro |
|---|---|---|
| Python / API / recuperación | **328 pruebas aprobadas**, incluidas 6 nuevas de respaldo/restauración. | [Pruebas Python](../06-evidencias/documentacion-seguridad-2026-11-20/pruebas-python.txt) |
| Chromium | **44 recorridos aprobados** sobre la aplicación v6. | [Pruebas Chromium](../06-evidencias/documentacion-seguridad-2026-11-20/pruebas-chromium.txt) |
| Trazabilidad | 46 criterios; referencias de código, diagramas y métodos comprobadas. | [Matriz](../01-requisitos/TRAZABILIDAD_IMPLEMENTACION.md) |
| Diccionario | 20 tablas generadas desde SQLite temporal v6. | [Diccionario](../03-diagramas/DICCIONARIO_DATOS_V6.md) |
| Rendimiento local | Catálogo p50 **3.33 ms**, p95 **4.351 ms**. | [Medición JSON](../06-evidencias/documentacion-seguridad-2026-11-20/rendimiento.json) |

Los registros con fecha de noviembre anterior conservan sus resultados originales. Las advertencias de persistencia en casos de fallos inyectados son esperadas y se comprueba la reversión/error controlado.

## Recuperación

`tests/test_respaldos.py` utiliza una compra comercial con precios y reservas y una entrada de inventario en base temporal. Copiar y restaurar a una ruta nueva conserva el contenido de todas las tablas y supera integridad/FK. Se comprueba además: destino existente intacto, misma ruta rechazada, origen ausente, base ajena y limpieza del destino propio si falla la validación final.

El programa `scripts.respaldo_base` utiliza SQLite backup y no sobrescribe una base existente. Este ensayo local acredita el mecanismo y la conservación del contenido del fixture; no acredita recuperación frente a pérdida del equipo, ni establece periodicidad/retención aprobadas.

## Medición de laboratorio

- Python 3.12.14, Linux x86_64; base temporal con 16 productos y 3 sucursales.
- Catálogo mediante Flask `test_client` en proceso: 5 calentamientos y 30 muestras; p50 es mediana y p95 rango más cercano, sin red externa.
- Servicio de pedidos: 12 solicitudes, 4 hilos, 12 asignadas; duración de lote **42.276 ms**. Este caso mide el servicio de reserva/asignación, no el checkout comercial completo.
- Copia validada de SQLite: **3.378 ms**, integridad/FK correctas.

Son valores observados en una ejecución pequeña, no un SLA, capacidad máxima, prueba prolongada de carga ni comparación con los sistemas reales de Inkafarma. No se infiere una mejora porcentual sin medición de referencia. Evaluar carga sostenida, despliegue WSGI/red y usuarios destinatarios antes de una afirmación operativa.

## Reproducir

```bash
python -m unittest discover -s tests -v
python -m playwright install chromium-headless-shell
python -m unittest discover -s tests/e2e -v
python -m scripts.medir_rendimiento --muestras 30
python -m scripts.generar_diccionario
python -m scripts.verificar_documentacion
```

Instalar antes `requirements-test.txt`. En esta ejecución el logger `werkzeug` se establece en ERROR para omitir solicitudes rutinarias y conservar el resultado de cada caso. Las bases de pruebas son temporales; no se publican bases ni capturas de pedidos. [Manual de recuperación](../09-manuales/TECNICO.md).
