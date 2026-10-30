'use strict';
const orderElement = id => document.getElementById(id);
let orderProducts = [];
let orderPoints = [];
let orderLineNumber = 0;
let pendingOrder;
let confirmationId;
let confirming = false;
let uncertain = false;

function textNode(tag, text) {
  const el = document.createElement(tag);
  el.textContent = text;
  return el;
}
function showOrderError(message) {
  const box = orderElement('order-error');
  box.textContent = message;
  box.classList.remove('hidden');
  box.focus();
}
function clearOrderError() { orderElement('order-error').classList.add('hidden'); }
function orderView(view, step) {
  for (const name of ['edit', 'review', 'success']) orderElement(`${name}-view`).classList.toggle('hidden', name !== view);
  for (let number = 1; number <= 3; number++) {
    const el = orderElement(`step-${number}`);
    el.removeAttribute('aria-current');
    if (number === step) el.setAttribute('aria-current', 'step');
  }
}
function addOrderLine(productCode = '', quantity = 1) {
  const line = document.createElement('div');
  line.className = 'order-line';
  const number = ++orderLineNumber;
  const productCell = document.createElement('div');
  const label = textNode('label', 'Producto');
  label.htmlFor = `product-${number}`;
  const select = document.createElement('select');
  select.id = label.htmlFor;
  select.className = 'order-product';
  select.required = true;
  select.add(new Option('Selecciona un producto', ''));
  for (const p of orderProducts) select.add(new Option(p.producto, p.producto_codigo));
  select.value = productCode;
  productCell.append(label, select);
  const amountCell = document.createElement('div');
  const amountLabel = textNode('label', 'Cantidad');
  amountLabel.htmlFor = `quantity-${number}`;
  const input = document.createElement('input');
  Object.assign(input, {id: amountLabel.htmlFor, type: 'number', min: '1', max: '10000', step: '1', required: true, value: String(quantity), className: 'order-quantity'});
  input.inputMode = 'numeric';
  amountCell.append(amountLabel, input);
  const remove = textNode('button', 'Quitar producto');
  remove.type = 'button';
  remove.className = 'order-remove';
  remove.onclick = () => {
    line.remove();
    if (!orderElement('order-lines').children.length) addOrderLine();
  };
  line.append(productCell, amountCell, remove);
  orderElement('order-lines').append(line);
}
async function loadOrderOptions() {
  const message = orderElement('load-message');
  message.classList.remove('hidden');
  message.textContent = 'Cargando productos y puntos de referencia…';
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);
  try {
    const response = await fetch('/api/pedidos/opciones', {cache: 'no-store', signal: controller.signal});
    if (!response.ok) throw new Error();
    const data = await response.json();
    orderProducts = data.productos;
    orderPoints = data.puntos;
    if (!orderProducts.length || !orderPoints.length) {
      message.textContent = 'Aún no hay productos o puntos de referencia para preparar un pedido.';
      return;
    }
    orderElement('reference').replaceChildren(new Option('Selecciona un punto', ''));
    for (const p of orderPoints) orderElement('reference').add(new Option(p.nombre, p.codigo));
    orderElement('order-lines').replaceChildren();
    addOrderLine();
    message.classList.add('hidden');
    orderView('edit', 1);
  } catch {
    message.textContent = 'No pudimos cargar los productos. Comprueba la conexión y vuelve a intentarlo.';
    const retry = textNode('button', 'Reintentar carga');
    retry.type = 'button';
    retry.className = 'order-secondary';
    retry.onclick = loadOrderOptions;
    message.append(document.createElement('br'), retry);
  } finally { clearTimeout(timeout); }
}
function reviewOrder(event) {
  event.preventDefault();
  clearOrderError();
  const items = new Map();
  const lines = orderElement('order-lines').querySelectorAll('.order-line');
  if (!lines.length || lines.length > 100) return showOrderError('El pedido debe contener entre 1 y 100 líneas.');
  for (const line of lines) {
    const code = line.querySelector('select').value;
    const amount = Number(line.querySelector('input').value);
    if (!orderProducts.some(p => p.producto_codigo === code) || !Number.isInteger(amount) || amount < 1 || amount > 10000) return showOrderError('Elige un producto y una cantidad entera entre 1 y 10000.');
    items.set(code, (items.get(code) || 0) + amount);
    if (items.get(code) > 10000) return showOrderError('La cantidad total de un producto no puede superar 10000.');
  }
  const point = orderPoints.find(p => p.codigo === orderElement('reference').value);
  const customer = orderElement('customer').value.trim();
  if (!point || !customer) return showOrderError('Completa el nombre y selecciona el punto de referencia.');
  pendingOrder = {cliente: customer, latitud: point.latitud, longitud: point.longitud, items: [...items].map(([producto_codigo, cantidad]) => ({producto_codigo, cantidad}))};
  confirmationId = crypto.randomUUID();
  uncertain = false;
  orderElement('review-customer').replaceChildren(textNode('dt', 'Nombre'), textNode('dd', customer), textNode('dt', 'Punto de referencia'), textNode('dd', point.nombre));
  const rows = orderElement('review-items');
  rows.replaceChildren();
  for (const item of pendingOrder.items) {
    const row = document.createElement('tr');
    const product = textNode('td', orderProducts.find(p => p.producto_codigo === item.producto_codigo).producto);
    product.append(textNode('small', item.producto_codigo));
    row.append(product, textNode('td', item.cantidad));
    rows.append(row);
  }
  orderElement('review-total').textContent = `${items.size} producto(s) · ${pendingOrder.items.reduce((n, p) => n + p.cantidad, 0)} unidad(es)`;
  orderElement('confirm-progress').textContent = '';
  orderElement('confirm-order').textContent = 'Confirmar pedido';
  orderElement('edit-order').disabled = false;
  orderView('review', 2);
  orderElement('review-view').focus();
}
function showOrderSuccess(pedido) {
  orderView('success', 3);
  orderElement('success-description').textContent = `El pedido #${pedido.pedido_id} está registrado en ${pedido.sucursal_nombre}.`;
  orderElement('success-details').replaceChildren(textNode('dt', 'Número de pedido'), textNode('dd', `#${pedido.pedido_id}`), textNode('dt', 'Sucursal'), textNode('dd', pedido.sucursal_nombre), textNode('dt', 'Estado'), textNode('dd', pedido.estado.replaceAll('_', ' ')));
  orderElement('success-items').replaceChildren(...pedido.items.map(item => textNode('li', `${orderProducts.find(p => p.producto_codigo === item.producto_codigo)?.producto || item.producto_codigo} · ${item.cantidad} unidad(es)`)));
  orderElement('success-view').focus();
}
async function confirmOrder() {
  if (confirming || !pendingOrder) return;
  confirming = true;
  clearOrderError();
  orderElement('confirm-order').disabled = true;
  orderElement('edit-order').disabled = true;
  orderElement('confirm-progress').textContent = 'Comprobando disponibilidad y registrando el pedido…';
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);
  try {
    const response = await fetch('/api/pedidos', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({...pendingOrder, confirmacion_id: confirmationId}), signal: controller.signal});
    if (response.status >= 500) throw new Error();
    const result = await response.json();
    if (!response.ok) {
      uncertain = result.codigo === 'CONFIRMACION_REUTILIZADA';
      orderElement('edit-order').disabled = uncertain;
      orderElement('confirm-progress').textContent = 'El pedido no se confirmó. Revisa los datos y vuelve a intentarlo.';
      showOrderError(result.error || 'No pudimos confirmar el pedido. Revisa los datos.');
      return;
    }
    uncertain = false;
    showOrderSuccess(result.pedido);
  } catch {
    uncertain = true;
    showOrderError('No pudimos comprobar si se registró el pedido. Pulsa «Comprobar confirmación» para recuperar el resultado sin duplicarlo.');
    orderElement('confirm-order').textContent = 'Comprobar confirmación';
    orderElement('confirm-progress').textContent = 'Conservamos el mismo pedido para comprobar su resultado.';
  } finally {
    clearTimeout(timeout);
    confirming = false;
    orderElement('confirm-order').disabled = false;
    orderElement('edit-order').disabled = uncertain;
  }
}
orderElement('order-form').addEventListener('submit', reviewOrder);
orderElement('add-line').onclick = () => {
  if (orderElement('order-lines').children.length < 100) addOrderLine();
  else showOrderError('Puedes incluir hasta 100 líneas en un pedido.');
};
orderElement('edit-order').onclick = () => {
  if (confirming || uncertain) return;
  clearOrderError();
  orderView('edit', 1);
  orderElement('customer').focus();
};
orderElement('confirm-order').onclick = confirmOrder;
orderElement('new-order').onclick = () => {
  clearOrderError();
  orderElement('order-form').reset();
  orderElement('order-lines').replaceChildren();
  addOrderLine();
  pendingOrder = undefined;
  confirmationId = undefined;
  orderView('edit', 1);
  orderElement('customer').focus();
};
loadOrderOptions();
