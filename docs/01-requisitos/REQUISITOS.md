# Requisitos de la implementación v6

[Alcance](ALCANCE_Y_OBJETIVOS.md) · [Trazabilidad](TRAZABILIDAD_IMPLEMENTACION.md) · [Estado](../ESTADO_Y_PENDIENTES.md)

**20 de noviembre de 2026.** Se conservan los IDs RF-S1/S2/S3. «Implementado» acredita el comportamiento indicado, no aceptación de toda la HU original.

## Actores y acceso

| Actor de negocio | Acceso disponible |
|---|---|
| Cliente | Catálogo, carrito y confirmación; seguimiento con código privado completo. |
| Personal de sucursal | Preparación/inventario según alcance del servicio. El panel utiliza operador central. |
| Repartidor | Asignación y acciones verificadas en servicios; la web obtiene el actor en el servidor. |
| Administrador / asesor | Gestión y soporte con políticas de servicio; sin cuentas individuales web. |
| Supervisor | Resolución de plazos pendientes vencidos. |

## Requisitos funcionales

| ID | Comportamiento | Fuente | Estado v6 |
|---|---|---|---|
| RF-S1-01 | Buscar por nombre/marca y mostrar resultados o ausencia. | HU01 | Implementado. |
| RF-S1-02 | Combinar categoría, sucursal, búsqueda y disponibles; ordenar catálogo por precio. | S1 / HU07 | Implementado. |
| RF-S1-03 | Consultar disponibilidad efectiva por sucursal. | HU01 / HU14 | Implementado. |
| RF-S1-04 | Ordenar las sucursales del catálogo por cercanía del usuario. | HU01 CA2 | Pendiente en consulta pública; la asignación sí usa distancia. |
| RF-S1-05 | Categorías, productos, sucursales e inventario con integridad. | HU14 | Implementado y ampliado. |
| RF-S2-01 | Cotizar y confirmar productos, cantidades y datos de entrega. | HU04 | Implementado sin cuenta de cliente; CA1 parcial. |
| RF-S2-02 | Reservar con plazo hasta aceptación y mostrar solicitud en bandeja. | HU02 | Adaptado a entrega; no equivale a reserva para recojo sin compra. |
| RF-S2-03 | Asignar con stock completo/capacidad y elegir por distancia. | HU03 / HU15 | Implementado con centro del distrito. |
| RF-S3-01 | ASIGNADO → EN_PREPARACION → PREPARADO. | HU05 / HU15 | Implementado con generación y reservas vigentes. |
| RF-S3-02 | Consultar estado/historial por código sin datos de contacto. | HU05 | Implementado por consulta; sin avisos externos/recojo. |
| RF-S3-03 | Repartidor activo y salida/entrega coherentes con fechas e inventario. | HU15 | Implementado; una entrega por pedido. |
| RF-S3-04 | Registrar/revisar/resolver incidencias. | S3 / HU11 | Operaciones implementado; sin chat del cliente. |
| RF-LOG-01 | Reasignar por incapacidad o falta de aceptación. | HU03 / HU09 | Implementado sin volver a sucursales intentadas. |
| RF-LOG-02 | Cancelar y liberar si no hay alternativa completa. | HU09 | Implementado. |
| RF-INV-01 | Entradas/conteos con saldo, motivo e idempotencia. | HU14 | Implementado; protege reservas y rechaza conteo obsoleto. |
| RF-COM-01 | Conservar precios, dirección e importes ante reintentos/reasignación. | HU04 / HU07 | Implementado en céntimos y snapshots inmutables. |

## Reglas de negocio

1. Un pedido se atiende completo desde una sucursal; no divide líneas entre locales.
2. Disponible = físico − reservas ACTIVA. Liberar no reduce físico; consumir al salir lo reduce una vez.
3. Se conservan reservas liberadas. Solo una reserva ACTIVA o CONSUMIDA por línea.
4. Las escrituras relacionadas se serializan con `BEGIN IMMEDIATE`.
5. Confirmación con UUID; otra solicitud con ese UUID se rechaza. Reasignación y preparación validan la asignación esperada.
6. Plazo inicial de 15 minutos; aceptar al preparar excluye del vencimiento automático.
7. Entrada suma unidades; ajuste establece conteo final y exige el saldo visto por el operador.
8. El servidor calcula precios; el navegador no determina el importe aceptado.
9. La API del panel obtiene roles/actores en el servidor y rechaza esos campos enviados por el cliente.

## Condiciones de calidad

| ID | Condición | Evidencia / criterio |
|---|---|---|
| RNF-01 Integridad | Sin sobre-reserva ni escrituras parciales en escenarios cubiertos. | Concurrencia, rollback, `foreign_key_check` e `integrity_check`. |
| RNF-02 Privacidad | Seguimiento omite nombre, teléfono, dirección, motivos internos y actores. | Pruebas HTTP. |
| RNF-03 Acceso | Sesión para operaciones; JSON/CSRF/origen en escrituras. | Pruebas de acceso y análisis de seguridad; no acredita identidad individual. |
| RNF-04 Recuperación | Copia/restauración conserva estado y existencias. | Recorrido a ruta nueva, sin sobrescribir bases existentes. |
| RNF-05 Rendimiento | Latencias con muestras, percentiles y entorno. | Medición local; sin afirmar SLA ni mejora frente a la operación de Inkafarma. |
| RNF-06 Usabilidad | Escritorio/móvil, errores recuperables y teclado probados. | Chromium; validación con usuarios destinatarios por registrar. |
| RNF-07 Mantenibilidad | HU/diagramas/código/pruebas/resultados/PR enlazados. | Matriz de 46 criterios. |
| RNF-08 Seguridad | Alcance, evidencia, riesgo, remediación y retest. | Informe acotado; pruebas funcionales no equivalen a ausencia de vulnerabilidades. |

Los objetivos de disponibilidad, tiempos de producción, recuperación y retención deben acordarse con quien acepte el producto; no se presentan como compromisos aprobados.

HU06, HU10, HU12 y HU13 permanecen diferidas. HU08/HU11 disponen de apoyos de interfaz/operaciones, sin validación específica de adultos mayores o chat especializado. La matriz describe cada criterio sin convertir una prueba parcial en aceptación de toda la historia.
