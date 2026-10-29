# S2-04 — Registro de pedidos y asignación de sucursal

**Proyecto:** Inkafarma — Ingeniería de Software (UPCH)  
**Sprint:** 2  
**Responsable:** Anderson Delerna  
**Issue:** [#18 — Registrar pedidos y asignar sucursal](https://github.com/seale-code/Ingenieria-de-software/issues/18)  
**Estado de esta entrega:** implementación local y pruebas verificadas; integración y revisión de equipo pendientes.

## 1. Qué desarrollé

Implementé el módulo backend que recibe un pedido, valida los productos y sus cantidades, identifica sucursales con stock y capacidad suficiente, calcula la distancia hasta el cliente y registra el resultado en SQLite. Cuando una sucursal puede atenderlo, guardo el pedido y descuento el stock de forma atómica. También dejo registrada una reserva para poder auditar qué cantidades se comprometieron. Si ninguna sucursal califica, conservo la solicitud en el estado `SIN_ASIGNAR` y devuelvo el motivo sin descontar productos.

Lo programé en **Python 3.10+ con biblioteca estándar y SQLite**, reutilizando `src.database.database` y las tablas de productos, sucursales e inventario del Sprint 1. No agregué Flask ni pantallas porque no forman parte de mi actividad S2-04 y en el repositorio el servidor HTTP todavía aparece como propuesta.

## 2. Archivos de mi actividad

| Archivo | Función |
|---|---|
| `src/backend/pedidos_s2.py` | Validar solicitudes, registrar pedidos, asignar sucursales y consultar pedidos. |
| `src/backend/asignacion_sucursal.py` | Calcular la distancia Haversine y ordenar las sucursales elegibles. |
| `src/backend/pedidos_s2_schema.sql` | Crear las tablas aisladas de pedidos, detalles, capacidades y reservas. |
| `src/backend/pedidos_s2_cli.py` | Mostrar el funcionamiento del backend desde la terminal. |
| `tests/test_pedidos_s2.py` | Ejecutar 20 pruebas automatizadas. |
| `sprint-2/S2-04_Anderson_Delerna.md` | Documentar el alcance, funcionamiento, decisiones y resultados. |
| `sprint-2/S2-04_evidencia_pruebas.txt` | Conservar la evidencia técnica de la ejecución local. |

## 3. Requisitos previos

Ejecutar desde la **raíz del repositorio** `seale-code/Ingenieria-de-software`, después de colocar los archivos en las rutas indicadas. Debe existir la base de datos del Sprint 1:

```bash
python -m src.database init --demo
```

Este comando carga datos **ficticios** de prueba. No ejecutar `init --demo` contra una base de producción; este proyecto es académico.

## 4. Preparación de mi módulo

```bash
python -m src.backend.pedidos_s2_cli init
python -m src.backend.pedidos_s2_cli capacidad --sucursal DEMO-NORTE --max-pedidos 3
python -m src.backend.pedidos_s2_cli capacidad --sucursal DEMO-SUR --max-pedidos 3
```

La capacidad se define explícitamente: no asigno pedidos a sucursales que no tengan una capacidad configurada. En este ejemplo, cada sucursal admite 3 pedidos activos como máximo.

También puedo usar `--db data/otra-demo.sqlite3` **antes** del subcomando para trabajar con otra base ya creada, por ejemplo `python -m src.backend.pedidos_s2_cli --db data/otra-demo.sqlite3 init`.

## 5. Demostración: registrar y consultar

**Caso A — Pedido que sí puede asignarse:**

```bash
python -m src.backend.pedidos_s2_cli registrar --cliente "Cliente demo" --lat -12.0 --lon -77.05 --item DEMO-A:2
```

Resultado esperado al iniciar con la demo: estado `ASIGNADO`, sucursal `DEMO-NORTE`, inventario de DEMO-A en Norte de 5 a 3 y una reserva de 2 unidades.

**Caso B — Producto sin disponibilidad:**

```bash
python -m src.backend.pedidos_s2_cli registrar --cliente "Cliente demo" --lat -12.0 --lon -77.05 --item DEMO-C:1
```

Resultado esperado: pedido persistido con `SIN_ASIGNAR`, sin sucursal ni reservas, e indicación de falta de stock y/o capacidad.

**Caso C — Consultar un pedido creado:**

```bash
python -m src.backend.pedidos_s2_cli consultar --pedido 1
```

Devuelve cliente, estado, sucursal asignada, fecha y productos registrados. El ID puede ser distinto si la base contiene pedidos anteriores.

**Probar todos los casos:**

```bash
python -m unittest tests.test_pedidos_s2 -v
```

Si `tests/` no se reconoce como paquete, usar:

```bash
python -m unittest discover -s tests -p "test_pedidos_s2.py" -v
```

## 6. Reglas de asignación utilizadas

1. Valido nombres, coordenadas y cantidades enteras positivas. Agrupo productos repetidos para no subestimar la cantidad total.
2. Verifico que todos los productos existan en el catálogo del Sprint 1.
3. Solo considero sucursales con **stock suficiente para TODOS** los productos y **capacidad libre**.
4. Entre las elegibles, escojo la de **menor distancia geográfica Haversine**; en caso de empate, priorizo la que tiene **más capacidad libre** y luego el **código alfabéticamente menor**.
5. Registro pedido, detalles, descuento de inventario y reserva en **una sola transacción**. `BEGIN IMMEDIATE` impide que dos solicitudes simultáneas reserven la misma unidad disponible.
6. Si ninguna califica, registro el pedido como `SIN_ASIGNAR`, sin descuento ni reserva.

**Importante — decisión pendiente del equipo:** Estas reglas de priorización son una **propuesta técnica** para hacer verificable mi trabajo, **no una regla oficial ya acordada**. La tarea S2-01 (#9, Cesar Milla) tiene a cargo confirmar prioridades/pesos, criterios de capacidad y desempates. Ajustaré `asignacion_sucursal.py` cuando el equipo apruebe el contrato.

**Distancia:** Haversine mide kilómetros en línea recta, no distancia por carretera ni tiempo de reparto.

## 7. Integración con el trabajo de mis compañeros

- **S2-01 — Cesar:** debe validar las reglas de asignación antes de integrar a `main`.
- **S2-03 — Josue:** su tarea define el esquema definitivo de pedidos y reservas. Para no sobrescribir ni modificar el esquema original del Sprint 1, **esta entrega crea tablas temporales de integración con el prefijo `s2_`** (`s2_pedidos`, `s2_pedido_detalles`, `s2_reservas`, `s2_capacidades`) y conserva `PRAGMA user_version = 1`. Antes de fusionar con el trabajo de S2-03, acordaremos el mapeo o sustituiremos este esquema provisional por el oficial.
- **S2-05 — Sebastian:** podrá llamar a `registrar_pedido()` y `obtener_pedido()` desde la futura API o interfaz para las pruebas de integración.

**Límite deliberado:** Mi módulo no implementa pagos, direcciones postales, autenticación, una API Flask, cancelación ni seguimiento de entrega. Si en S3 se implementa cancelación, deberá devolver el stock y liberar las reservas en la misma transacción. El módulo no debe exponerse como endpoint público sin controles de autorización y protección de datos.

## 8. Evidencia de pruebas

Diseñé 20 pruebas automáticas para cubrir pedidos correctos, stock insuficiente, pedidos con varios productos, capacidad máxima, datos inválidos, productos inexistentes, agrupación de duplicados, persistencia, rollback por error, inicialización repetida, concurrencia y desempates. Se ejecutaron correctamente en un entorno local basado en el contrato/esquema público del Sprint 1; **la suite todavía debe repetirse en un clon actualizado del repositorio real antes de solicitar el merge**. La salida de la ejecución está en `sprint-2/S2-04_evidencia_pruebas.txt`.

## 9. Lista de verificación para el issue #18

- [x] Implementé validación y persistencia de pedidos.
- [x] Implementé selección por disponibilidad, distancia y capacidad (reglas provisionales).
- [x] Implementé respuesta cuando ninguna sucursal es elegible.
- [x] Agregué pruebas unitarias y de integración local.
- [x] Preparé evidencia y documentación técnica.
- [ ] Verificar pruebas con el repositorio real actualizado.
- [ ] Acordar las reglas finales con Cesar (S2-01).
- [ ] Coordinar esquema definitivo de base de datos con Josue (S2-03).
- [ ] Abrir Pull Request y recibir revisión de otro compañero.

No marco como terminada la revisión o integración del equipo porque requieren acciones en GitHub aún no realizadas.
