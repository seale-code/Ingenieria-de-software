'use strict';
const $ = id => document.getElementById(id);
const safe = text => String(text).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let sequence = 0;
let active;
let timer;
let filtersReady = false;
const initialFilters = new URLSearchParams(location.search);
let desiredCategory = initialFilters.get('categoria') || '';
let lastCatalog;
$('search').value = initialFilters.get('buscar') || '';

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
  const products = [...data.productos];
  const sort = $('sort')?.value || 'relevancia';
  products.sort((a,b) => sort === 'nombre' ? a.producto.localeCompare(b.producto,'es') :
    sort === 'menor' ? (a.precio_centimos ?? Infinity)-(b.precio_centimos ?? Infinity) :
    sort === 'mayor' ? (b.precio_centimos ?? -1)-(a.precio_centimos ?? -1) : (a.orden ?? 1000)-(b.orden ?? 1000));
  for (const p of products) {
    window.Tienda?.cache.set(p.producto_codigo,p);
    const article = document.createElement('article'); article.className = 'product';
    const available = p.cantidad !== null && p.cantidad > 0;
    const label = p.cantidad === null ? 'Sin inventario registrado' : available ? 'Disponible' : 'Sin stock';
    const amount = p.cantidad === null ? 'Disponibilidad no registrada' : `${p.cantidad} unidades ${$('branch').value ? 'en sucursal seleccionada' : 'en las sucursales registradas'}`;
    const image = typeof p.imagen === 'string' && p.imagen.startsWith('/assets/') ? p.imagen : '/assets/imagenes/cuidado-diario.webp';
    const priced = Number.isInteger(p.precio_centimos);
    const discount = priced && p.precio_lista_centimos > p.precio_centimos ? Math.round((1-p.precio_centimos/p.precio_lista_centimos)*100) : 0;
    article.innerHTML = `<div class="art">${discount ? `<span class="discount-badge">−${discount}%</span>` : ''}<button class="product-detail" type="button" aria-label="Ver ${safe(p.producto)}"><img src="${safe(image)}" alt="${safe(p.producto)}" width="220" height="190" loading="lazy"></button></div><div class="product-body"><span class="tag">${safe(p.marca || p.categoria)}</span><h3><button type="button" class="product-title">${safe(p.producto)}</button></h3><p class="code">${safe(p.presentacion || p.producto_codigo)}</p>${priced ? `<div class="price-area"><strong>${safe(Tienda.money(p.precio_centimos))}</strong>${discount ? `<del>${safe(Tienda.money(p.precio_lista_centimos))}</del>` : ''}</div>` : ''}<span class="pill ${available ? '' : 'off'}">${label}</span><div class="bottom"><p class="availability">${amount}</p>${priced ? `<button type="button" class="action add-cart" ${available ? '' : 'disabled'}>${available ? 'Agregar al carrito' : 'No disponible'}</button>` : ''}<button class="action detail-toggle" type="button" aria-expanded="false">Ver stock por sucursal</button><div class="detail hidden" aria-live="polite"></div></div></div>`;
    article.querySelector('.detail-toggle').onclick = event => detail(event.currentTarget,p.producto_codigo);
    for (const button of article.querySelectorAll('.product-detail,.product-title')) button.onclick = () => showProduct(p,image);
    if(priced) article.querySelector('.add-cart').onclick = () => Tienda.add(p);
    if(available){
      const order=document.createElement('a');order.className='product-order';order.href='/pedido?producto='+encodeURIComponent(p.producto_codigo);order.textContent=priced?'Comprar ahora':'Pedir este producto →';article.querySelector('.bottom').append(order);
    }
    $('products').append(article);
  }
}
function showProduct(p,image){
  const dialog=$('product-dialog'), content=$('product-content');
  if(!dialog)return;
  content.innerHTML = `<div class="product-detail-grid"><img src="${safe(image)}" alt="${safe(p.producto)}" width="320" height="320"><div><span class="tag">${safe(p.marca||p.categoria)}</span><h2 id="product-title">${safe(p.producto)}</h2><p>${safe(p.presentacion||'')}</p>${Number.isInteger(p.precio_centimos)?`<div class="price-area"><strong>${safe(Tienda.money(p.precio_centimos))}</strong></div>`:''}<p>${safe(p.descripcion||'Consulta la disponibilidad de este producto por sucursal.')}</p><p>Máximo ${p.maximo||10000} unidades por pedido. La disponibilidad se verifica al confirmar.</p></div></div>`;
  if(p.cantidad>0&&Number.isInteger(p.precio_centimos)){
    const button=document.createElement('button');button.type='button';button.className='primary-link';button.textContent='Agregar al carrito';button.onclick=()=>{if(Tienda.add(p))dialog.close();};content.querySelector('.product-detail-grid>div').append(button);
  }
  dialog.showModal();
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
      $('category').value = desiredCategory;
      filtersReady = true;
    }
    const query = new URLSearchParams({buscar: $('search').value, categoria: $('category').value, sucursal: $('branch').value, solo_disponibles: String($('only-stock').checked)});
    const data = await json(`/api/catalogo?${query}`, controller.signal);
    if (current === sequence) { lastCatalog=data; render(data); }
  } catch {
    if (current === sequence) status('No pudimos cargar el catálogo', 'Comprueba tu conexión e inténtalo de nuevo.', load, 'Reintentar');
  } finally {
    clearTimeout(timeout);
    if (current === sequence) $('products').setAttribute('aria-busy', 'false');
  }
}

function clear() {
  $('search').value = '';
  desiredCategory = '';
  if($('sort')) $('sort').value='relevancia';
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
$('search').form?.addEventListener('submit',event=>{event.preventDefault();load();$('catalogo')?.scrollIntoView({block:'start'});});
$('sort')?.addEventListener('change',()=>{if(lastCatalog)render(lastCatalog);});
for(const tile of document.querySelectorAll('[data-category]'))tile.onclick=()=>{desiredCategory=tile.dataset.category;if(filtersReady)$('category').value=desiredCategory;load();$('catalogo')?.scrollIntoView({block:'start'});};
if($('product-close'))$('product-close').onclick=()=>$('product-dialog').close();
load();
