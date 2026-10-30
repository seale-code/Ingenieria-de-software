'use strict';
const $ = id => document.getElementById(id);
const safe = text => String(text).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let sequence = 0;
let active;
let timer;
let filtersReady = false;

async function json(url, signal) {
  const response = await fetch(url, {signal, cache: 'no-store'});
  if (!response.ok) throw new Error('No se pudo completar la consulta');
  return response.json();
}

function status(title, message, action, label) {
  $('products').replaceChildren();
  $('status').classList.remove('hidden');
  $('status').innerHTML = `<h3>${safe(title)}</h3><p>${safe(message)}</p>`;
  if (action) {
    const button = document.createElement('button');
    button.className = 'action';
    button.textContent = label;
    button.onclick = action;
    $('status').append(button);
  }
}

async function detail(button, codigo) {
  const panel = button.nextElementSibling;
  if (button.getAttribute('aria-expanded') === 'true') {
    panel.classList.add('hidden');
    button.setAttribute('aria-expanded', 'false');
    button.textContent = 'Ver stock por sucursal';
    return;
  }
  button.disabled = true;
  panel.classList.remove('hidden');
  panel.textContent = 'Consultando disponibilidad…';
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);
  try {
    const data = await json(`/api/productos/${encodeURIComponent(codigo)}/stock`, controller.signal);
    panel.innerHTML = data.stock.length ? data.stock.map(row => `<div><span>${safe(row.sucursal)}</span><strong>${row.cantidad} unidades${row.cantidad === 0 ? ' · Sin stock' : ''}</strong></div>`).join('') : 'Sin inventario registrado.';
    button.setAttribute('aria-expanded', 'true');
    button.textContent = 'Ocultar disponibilidad';
  } catch {
    panel.textContent = 'No pudimos consultar el stock. Pulsa Reintentar disponibilidad.';
    button.textContent = 'Reintentar disponibilidad';
  } finally {
    clearTimeout(timeout);
    button.disabled = false;
  }
}

function render(data) {
  $('status').classList.add('hidden');
  $('products').replaceChildren();
  $('count').textContent = `${data.total} producto(s) encontrado(s)`;
  if (!data.productos.length) {
    status('No encontramos productos', 'Prueba otro nombre o ajusta los filtros.', clear, 'Limpiar filtros');
    return;
  }
  for (const p of data.productos) {
    const article = document.createElement('article');
    article.className = 'product';
    const available = p.cantidad !== null && p.cantidad > 0;
    const label = p.cantidad === null ? 'Sin inventario registrado' : available ? 'Disponible' : 'Sin stock';
    const amount = p.cantidad === null ? 'Disponibilidad no registrada' : `${p.cantidad} unidades ${$('branch').value ? 'en sucursal seleccionada' : 'en las sucursales registradas'}`;
    article.innerHTML = `<div class="art" aria-hidden="true">✚</div><div class="product-body"><span class="tag">${safe(p.categoria)}</span><h3>${safe(p.producto)}</h3><p class="code">Código: ${safe(p.producto_codigo)}</p><div><span class="pill ${available ? '' : 'off'}">${label}</span></div><div class="bottom"><p class="availability">${amount}</p><button class="action detail-toggle" type="button" aria-expanded="false">Ver stock por sucursal</button><div class="detail hidden" aria-live="polite"></div></div></div>`;
    article.querySelector('button').onclick = event => detail(event.currentTarget, p.producto_codigo);
    $('products').append(article);
  }
}

async function load() {
  clearTimeout(timer);
  const current = ++sequence;
  if (active) active.abort();
  const controller = new AbortController();
  active = controller;
  const timeout = setTimeout(() => controller.abort(), 10000);
  $('products').setAttribute('aria-busy', 'true');
  $('count').textContent = '';
  status('Cargando productos…', 'Estamos consultando el catálogo.');
  try {
    if (!filtersReady) {
      const filters = await json('/api/filtros', controller.signal);
      if (current !== sequence) return;
      for (const [id, rows, label] of [['category', filters.categorias, 'Todas las categorías'], ['branch', filters.sucursales, 'Todas las sucursales']]) {
        $(id).replaceChildren(new Option(label, ''));
        for (const row of rows) $(id).add(new Option(row.nombre, row.codigo));
      }
      filtersReady = true;
    }
    const query = new URLSearchParams({buscar: $('search').value, categoria: $('category').value, sucursal: $('branch').value, solo_disponibles: String($('only-stock').checked)});
    const data = await json(`/api/catalogo?${query}`, controller.signal);
    if (current === sequence) render(data);
  } catch {
    if (current === sequence) status('No pudimos cargar el catálogo', 'Comprueba tu conexión e inténtalo de nuevo.', load, 'Reintentar');
  } finally {
    clearTimeout(timeout);
    if (current === sequence) $('products').setAttribute('aria-busy', 'false');
  }
}

function clear() {
  $('search').value = '';
  $('category').value = '';
  $('branch').value = '';
  $('only-stock').checked = false;
  load();
}
$('search').addEventListener('input', () => {
  // Invalida la petición anterior desde la pulsación, antes del debounce.
  ++sequence;
  if (active) active.abort();
  clearTimeout(timer);
  $('count').textContent = '';
  status('Cargando productos…', 'Estamos consultando el catálogo.');
  timer = setTimeout(load, 250);
});
for (const id of ['category', 'branch', 'only-stock']) $(id).addEventListener('change', load);
$('clear').addEventListener('click', clear);
load();
