Título: [S2-02] Implementar formulario, resumen y confirmación del pedido

El usuario puede elegir productos y cantidades, revisar un resumen editable y
confirmar el pedido contra el servicio integrado. La pantalla muestra errores de
validación, stock insuficiente y conexión, y presenta el ID y la sucursal asignada.
Los reintentos de una confirmación usan el mismo UUID para recuperar el resultado
sin duplicar el pedido; también se protege el caso de solicitudes concurrentes.

Incluye interfaz responsive en `/pedido`, endpoints de opciones/confirmación,
12 pruebas HTTP, 6 recorridos E2E, capturas y guía de ejecución. Validación sobre
el `main` actual (`6cb0ae2`): **147 pruebas Python/API y 6 de navegador OK**,
reejecutadas el 30 de octubre de 2026.

Dependencias: PR #36 y PR #40, ambos ya fusionados en `main`. Usar una base v2/v3
con el módulo S2 inicializado. La entrega cubre formulario/resumen/confirmación con
datos ficticios; no agrega cuentas, pagos, vencimiento de reservas ni notificaciones.
Pendiente revisión de otro integrante.

Closes #20
