"use strict";
const trackingForm = document.getElementById('tracking-form');
const trackingCode = document.getElementById('tracking-code');
const trackingMessage = document.getElementById('tracking-message');
const trackingResult = document.getElementById('tracking-result');
const trackingButton = document.getElementById('tracking-button');
const dateFormat = new Intl.DateTimeFormat('es-PE', {dateStyle: 'medium', timeStyle: 'short', timeZone: 'America/Lima'});
function formatDate(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Fecha no disponible' : dateFormat.format(date);
}
async function loadTracking(event) {
  if (event) event.preventDefault();
  trackingResult.hidden = true;
  trackingMessage.textContent = 'Consultando el estado de tu pedido…';
  trackingButton.disabled = true;
  trackingCode.readOnly = true;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);
  try {
    const response = await fetch('/api/seguimiento', {headers: {'X-Codigo-Pedido': trackingCode.value.trim()}, cache: 'no-store', signal: controller.signal});
    const data = await response.json();
    if (!response.ok) {
      trackingMessage.textContent = data.error || 'No pudimos consultar el pedido. Inténtalo de nuevo.';
      return;
    }
    const pedido = data.pedido;
    document.getElementById('tracking-title').textContent = `Pedido #${pedido.numero}`;
    document.getElementById('tracking-state').textContent = pedido.etiqueta;
    document.getElementById('tracking-description').textContent = pedido.mensaje;
    document.getElementById('tracking-branch').textContent = `Sucursal: ${pedido.sucursal}`;
    const history = document.getElementById('tracking-history');
    history.replaceChildren();
    for (const item of pedido.historial) {
      const row = document.createElement('li');
      row.textContent = `${item.etiqueta} · ${formatDate(item.fecha)}`;
      history.append(row);
    }
    if (!pedido.historial.length) {
      const row = document.createElement('li');
      row.textContent = 'Todavía no hay cambios registrados.';
      history.append(row);
    }
    trackingResult.hidden = false;
    trackingMessage.textContent = 'Seguimiento actualizado.';
  } catch {
    trackingMessage.textContent = 'No pudimos conectar con el seguimiento. Comprueba tu conexión y vuelve a consultar.';
  } finally {
    clearTimeout(timeout);
    trackingButton.disabled = false;
    trackingCode.readOnly = false;
  }
}
trackingForm.addEventListener('submit', loadTracking);
// El fragmento permanece en el navegador; no se envía como URL al servidor.
if (location.hash.length > 1) {
  try { trackingCode.value = decodeURIComponent(location.hash.slice(1)); } catch { trackingCode.value = ''; }
  history.replaceState(null, '', '/seguimiento');
  if (trackingCode.value) loadTracking();
}
