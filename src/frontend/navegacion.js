"use strict";
// El enlace al panel solo aparece cuando el servidor habilita la demostración.
fetch('/api/contexto', {cache:'no-store', signal:AbortSignal.timeout(5000)})
  .then(response => response.ok ? response.json() : {})
  .then(data => document.querySelectorAll('[data-demo-nav]').forEach(link => link.hidden = !data.operaciones_demo))
  .catch(() => {});
