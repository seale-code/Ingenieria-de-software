"use strict";
const ui = id => document.getElementById(id);
const labels = {REGISTRADO:'Registrado', ASIGNADO:'Asignado', EN_PREPARACION:'En preparación', PREPARADO:'Preparado', EN_CAMINO:'En camino', ENTREGADO:'Entregado', CANCELADO:'Cancelado', ABIERTA:'Abierta', EN_REVISION:'En revisión', RESUELTA:'Resuelta'};
const stages = ['ASIGNADO','EN_PREPARACION','PREPARADO','EN_CAMINO','ENTREGADO'];
const dates = new Intl.DateTimeFormat('es-PE', {dateStyle:'medium', timeStyle:'short', timeZone:'America/Lima'});
let branchScope = null;
let csrf = '', orders = [], drivers = [], selected = null, busy = false, detailSequence = 0;
let logisticsEnabled = false, inventory = {existencias:[], movimientos:[]}, movement = null;

function node(tag, text, className) {
  const result = document.createElement(tag);
  if (text !== undefined) result.textContent = text;
  if (className) result.className = className;
  return result;
}
function message(text, error = false) {
  ui('ops-message').textContent = text;
  ui('ops-message').classList.toggle('error', error);
}
function date(value) {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? 'Fecha no disponible' : dates.format(parsed);
}
function badge(state) {
  const result = node('span', labels[state] || state, 'state-badge');
  result.dataset.state = state;
  return result;
}
function lock(value) {
  busy = value;
  document.querySelectorAll('#workspace button, #workspace select, #workspace textarea, #workspace input, #movement-dialog button, #movement-dialog select, #movement-dialog input, #movement-dialog textarea, #session-actions button').forEach(el => el.disabled = value);
}
async function api(path, method = 'GET', body) {
  const response = await fetch(path, {method, cache:'no-store', credentials:'same-origin',
    headers: {'Content-Type':'application/json', 'X-CSRF-Token':csrf},
    body: body === undefined ? undefined : JSON.stringify(body), signal:AbortSignal.timeout(12000)});
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401) showSession(false);
    throw new Error(data.error || 'No pudimos completar la consulta. Actualiza y vuelve a intentarlo.');
  }
  return data;
}
function showSession(authenticated) {
  ui('login-panel').hidden = authenticated;
  ui('workspace').hidden = !authenticated;
  ui('session-actions').hidden = !authenticated;
  if (!authenticated) {
    csrf = ''; orders = []; drivers = []; selected = null; ++detailSequence;
    ui('order-list').replaceChildren(); ui('order-detail').replaceChildren();
    inventory = {existencias:[],movimientos:[]}; movement = null; logisticsEnabled = false;
    ui('inventory-rows').replaceChildren(); ui('inventory-history').replaceChildren();
    ui('movement-dialog').close();
  }
}
function renderInbox() {
  const search = ui('order-search').value.trim().toLocaleLowerCase('es');
  const state = ui('order-state').value;
  const visible = orders.filter(p => (!state || p.estado === state) &&
    `${p.pedido_id} ${p.cliente || ''} ${p.sucursal_nombre}`.toLocaleLowerCase('es').includes(search));
  ui('inbox-count').textContent = `${visible.length}`;
  ui('inbox-empty').hidden = visible.length > 0;
  ui('order-list').replaceChildren(...visible.map(p => {
    const button = node('button', undefined, 'order-row');
    button.type = 'button'; button.dataset.orderId = p.pedido_id;
    button.setAttribute('aria-pressed', String(selected === p.pedido_id));
    const top = node('div', undefined, 'order-row-top');
    top.append(node('strong', `Pedido #${p.pedido_id}`), badge(p.estado));
    button.append(top, node('p', p.cliente || 'Pedido registrado'), node('small', `${p.sucursal_nombre} · ${p.unidades || 0} ud.`));
    button.disabled = busy;
    button.onclick = () => { if (!busy) loadDetail(p.pedido_id).catch(showError); };
    return button;
  }));
}
async function loadInbox() {
  const data = await api('/api/demo/pedidos');
  branchScope = data.sucursal || null;
  orders = data.pedidos; drivers = data.repartidores;
  logisticsEnabled = data.logistica_habilitada;
  ui('tab-inventory').hidden = !logisticsEnabled;
  ui('reservation-notice').hidden = !logisticsEnabled;
  ui('check-expirations').hidden = Boolean(branchScope);
  const pending = data.pendientes_aceptacion || 0;
  ui('pending-acceptance').textContent = `${pending} ${pending === 1 ? 'pedido pendiente' : 'pedidos pendientes'} de aceptación. Los plazos vencidos buscan otra sucursal de forma automática.`;
  for (const [id, key] of [['active','activos'],['delivery','en_camino'],['done','entregados'],['incidents','incidencias']]) {
    ui('metric-' + id).textContent = data.resumen[key];
  }
  renderInbox();
}
function showError(error) {
  message(error instanceof TypeError || error.name === 'TimeoutError' ?
    'No pudimos comprobar el resultado. Pulsa Actualizar antes de repetir una acción.' : error.message, true);
}
async function refresh() {
  if (busy) return;
  lock(true); message('Actualizando operaciones…');
  try {
    await loadInbox();
    if (logisticsEnabled) await loadInventory();
    if (selected !== null) await loadDetail(selected);
    else if (orders.length) await loadDetail(orders[0].pedido_id);
    else {
      ui('order-detail').innerHTML = '<div class="empty-detail"><span aria-hidden="true">▤</span><h2>Todo empieza con un pedido</h2><p>Selecciona uno de la bandeja para ver sus productos y continuar el recorrido.</p><a href="/pedido" class="primary-link">Crear pedido →</a></div>';
    }
    message('Datos actualizados. Fechas en hora de Lima.');
  } catch (error) { showError(error); }
  finally { lock(false); }
}
async function loadDetail(id) {
  const sequence = ++detailSequence;
  selected = id; renderInbox();
  const panel = ui('order-detail');
  panel.setAttribute('aria-busy','true');
  panel.replaceChildren(node('p', `Cargando pedido #${id}…`, 'empty-note'));
  try {
    const data = await api(`/api/demo/pedidos/${id}`);
    if (sequence === detailSequence) renderDetail(data.pedido);
  } finally {
    if (sequence === detailSequence) panel.setAttribute('aria-busy','false');
  }
}
async function perform(path, body, success) {
  if (busy) return false;
  lock(true); message('Guardando el cambio…');
  try {
    const result = await api(path, 'POST', body);
    await loadInbox();
    await loadDetail(selected);
    if (logisticsEnabled) await loadInventory();
    message(typeof success === 'function' ? success(result) : success); return true;
  } catch (error) { showError(error); return false; }
  finally { lock(false); }
}
function actionButton(text, action, order, className = 'action', extra = {}) {
  const button = node('button', text, className); button.type = 'button';
  const generation = order.logistica ? {asignacion_id:order.logistica.asignacion_id} : {};
  button.onclick = () => perform(`/api/demo/pedidos/${order.pedido_id}/acciones`, {accion:action, ...generation, ...extra}, 'Cambio registrado. El seguimiento del cliente ya está actualizado.');
  return button;
}
function renderDetail(p) {
  const panel = ui('order-detail'); panel.replaceChildren();
  const heading = node('div', undefined, 'detail-heading');
  heading.append(node('h2', `Pedido #${p.pedido_id}`), badge(p.estado)); panel.append(heading);
  const meta = node('dl', undefined, 'detail-meta');
  for (const [title, value] of [['Cliente', p.cliente || 'Datos no registrados'], ['Sucursal',p.sucursal_nombre], ['Creado',date(p.fecha_creacion)], ['Repartidor',p.entrega?.repartidor_nombre || 'Pendiente de asignación']]) {
    const group = node('div'); group.append(node('dt',title),node('dd',value)); meta.append(group);
  }
  if(p.comercio){
    for(const [label,value] of [['Dirección',p.comercio.entrega.direccion],['Distrito',p.comercio.entrega.distrito],['Celular',p.comercio.entrega.telefono]]){
      const group=node('div');group.append(node('dt',label),node('dd',value));meta.append(group);
    }
  }
  panel.append(meta);
  if(p.comercio)panel.append(Tienda.totals(p.comercio),node('p','Forma de pago: pago al recibir.','order-help'));
  const progress = node('ol', undefined, 'process-steps'); progress.setAttribute('aria-label','Avance del pedido');
  stages.forEach((state, index) => {
    const li = node('li', labels[state]);
    if (p.estado !== 'CANCELADO' && index <= stages.indexOf(p.estado)) li.classList.add('done');
    if (p.estado === state) { li.classList.add('current'); li.setAttribute('aria-current','step'); }
    progress.append(li);
  }); panel.append(progress);
  const table = node('table', undefined, 'products-table');
  table.innerHTML = '<caption class="sr-only">Productos del pedido</caption><thead><tr><th scope="col">Producto / reserva</th><th scope="col">Cantidad</th></tr></thead><tbody></tbody>';
  for (const item of p.items) {
    const row = node('tr'), name = node('td',item.producto_nombre);
    const reserve = {ACTIVA:'Reserva activa',CONSUMIDA:'Stock consumido',LIBERADA:'Reserva liberada'}[item.estado_reserva] || 'Sin reserva';
    if(item.imagen){const image=node('img');image.src=item.imagen;image.alt='';image.width=42;image.height=48;image.className='ops-product-image';name.prepend(image);}
    name.append(node('small',`${item.producto_codigo} · ${reserve}`)); row.append(name,node('td',item.cantidad)); table.tBodies[0].append(row);
  } panel.append(table, renderNextStep(p));
  if (p.logistica) panel.append(renderLogistics(p));
  const tools = node('div',undefined,'detail-tools');
  const tracking = node('a','Ver seguimiento del cliente','inline-link');
  tracking.href = '/seguimiento#' + encodeURIComponent(p.pedido_codigo); tools.append(tracking);
  if (!branchScope && ['REGISTRADO','ASIGNADO','EN_PREPARACION','PREPARADO'].includes(p.estado) && !p.entrega?.fecha_salida) {
    const cancel = node('button','Cancelar pedido','text-btn'); cancel.type = 'button';
    cancel.onclick = () => {
      if (busy) return;
      const dialog = ui('cancel-dialog'); dialog.returnValue = '';
      dialog.onclose = () => { if (dialog.returnValue === 'yes') perform(`/api/demo/pedidos/${p.pedido_id}/acciones`, {accion:'cancelar'}, 'Pedido cancelado. Las reservas quedaron liberadas.'); };
      dialog.showModal();
    }; tools.append(cancel);
  } panel.append(tools, node('h3','Historial del pedido','subheading'));
  const history = node('ol',undefined,'history-list');
  for (const event of p.historial) {
    const li = node('li'); const time = node('time',date(event.fecha_cambio)); time.dateTime = event.fecha_cambio;
    li.append(node('span',labels[event.estado_nuevo] || event.estado_nuevo), time); history.append(li);
  } panel.append(history);
  if (!branchScope) panel.append(renderIncidents(p));
}
function renderNextStep(p) {
  const section = node('section',undefined,'next-step'); section.append(node('h3','Próximo paso'));
  if (branchScope && !['REGISTRADO','ASIGNADO','EN_PREPARACION'].includes(p.estado)) {
    section.append(node('p','La central coordina el reparto y el seguimiento de este pedido.'));
    return section;
  }
  let text, button;
  if (['REGISTRADO','ASIGNADO'].includes(p.estado)) {
    text = 'La sucursal ya tiene reservados los productos. Comienza la preparación.';
    button = actionButton('Iniciar preparación','preparar',p);
  } else if (p.estado === 'EN_PREPARACION') {
    text = 'Comprueba los productos y cantidades antes de marcar el pedido como listo.';
    button = actionButton('Marcar como preparado','listo',p);
  } else if (p.estado === 'PREPARADO' && !p.entrega) {
    text = 'Elige un repartidor activo para este pedido.';
    const label = node('label','Repartidor'); label.htmlFor = 'driver-select';
    const select = node('select'); select.id = 'driver-select';
    select.append(new Option('Selecciona un repartidor',''));
    drivers.forEach(driver => select.append(new Option(driver.nombre, driver.id)));
    button = node('button','Asignar repartidor','action'); button.type = 'button';
    button.onclick = () => {
      if (!select.value) { message('Selecciona un repartidor activo.',true); select.focus(); return; }
      perform(`/api/demo/pedidos/${p.pedido_id}/acciones`,{accion:'asignar',repartidor_id:Number(select.value)},'Repartidor asignado. Ya puedes registrar la salida.');
    };
    section.append(node('p',text),label,select,button); return section;
  } else if (p.estado === 'PREPARADO') {
    text = 'Al salir se registrará la fecha y se consumirá la reserva una sola vez.';
    button = actionButton('Registrar salida','salir',p);
  } else if (p.estado === 'EN_CAMINO') {
    text = 'Confirma únicamente cuando se haya recibido el pedido.';
    button = actionButton('Confirmar entrega','entregar',p);
  } else {
    text = p.estado === 'ENTREGADO' ? 'Recorrido completado. La entrega y el historial quedaron registrados.' : 'Pedido cancelado. Se conserva su historial y se liberaron las reservas activas.';
  }
  section.append(node('p',text));
  if (p.entrega?.fecha_salida) section.append(node('p',`Salida: ${date(p.entrega.fecha_salida)}`));
  if (p.entrega?.fecha_entrega) section.append(node('p',`Recepción: ${date(p.entrega.fecha_entrega)}`));
  if (button) section.append(button);
  return section;
}
function renderLogistics(p) {
  const section = node('section',undefined,'assignment-area');
  section.append(node('h3','Atención por sucursal','subheading'));
  const control = p.logistica;
  if (['REGISTRADO','ASIGNADO'].includes(p.estado)) {
    section.append(node('p',`Aceptar antes de ${date(control.fecha_limite)} (hora de Lima). Iniciar la preparación confirma la atención.`,'acceptance-deadline'));
  } else if (control.aceptada_en) section.append(node('p',`Atención aceptada: ${date(control.aceptada_en)}.`,'order-help'));
  if (['REGISTRADO','ASIGNADO','EN_PREPARACION'].includes(p.estado) && !p.entrega) {
    const details = node('details'); details.append(node('summary','La sucursal no puede atender'));
    details.append(node('p','Se buscará otra sucursal con todos los productos y capacidad. Si no hay alternativa, se cancelará el pedido y se liberarán sus reservas.','order-help'));
    const form = node('form'); form.id = 'reassignment-form';
    const label = node('label','Motivo de la falta de atención'); label.htmlFor = 'reassignment-reason';
    const input = node('textarea'); input.id = label.htmlFor; input.required = true; input.minLength = 5; input.maxLength = 240;
    const submit = node('button','Buscar otra sucursal','secondary-btn');
    const operationId = crypto.randomUUID();
    form.append(label,input,submit);
    form.onsubmit = event => {
      event.preventDefault();
      perform(`/api/demo/pedidos/${p.pedido_id}/acciones`,{accion:'rechazar',asignacion_id:control.asignacion_id,
        motivo:input.value,solicitud_id:operationId},result => result.resultado.reasignado ?
          `Pedido reasignado a ${result.resultado.sucursal_nombre}. Se conservaron su código y sus importes.` :
          'No hay una sucursal alternativa disponible. Pedido cancelado y reservas liberadas.');
    };
    details.append(form); section.append(details);
  }
  const list = node('ol',undefined,'assignment-history');
  for (const event of control.historial) {
    const item = node('li');
    const text = event.sucursal_origen ? `${event.sucursal_origen} → ${event.sucursal_destino || 'Cancelación sin alternativa'}` : `Asignado a ${event.sucursal_destino}`;
    item.append(node('strong',text),node('small',date(event.fecha)),node('p',event.observacion)); list.append(item);
  }
  section.append(list); return section;
}

async function loadInventory() {
  inventory = await api('/api/demo/inventario');
  const select = ui('inventory-branch'), previous = select.value;
  const branches = new Map(inventory.existencias.map(row => [row.sucursal_codigo,row.sucursal_nombre]));
  select.replaceChildren(...[...branches].map(([code,name]) => new Option(name,code)));
  if (branches.has(previous)) select.value = previous;
  renderInventory();
}
function renderInventory() {
  const branch = ui('inventory-branch').value, search = ui('inventory-search').value.trim().toLocaleLowerCase('es');
  const visible = inventory.existencias.filter(row => row.sucursal_codigo === branch &&
    `${row.producto_nombre} ${row.producto_codigo}`.toLocaleLowerCase('es').includes(search));
  ui('inventory-empty').hidden = visible.length > 0;
  ui('inventory-rows').replaceChildren(...visible.map(row => {
    const tr = node('tr'); tr.dataset.productCode = row.producto_codigo;
    const name = node('td',row.producto_nombre); name.append(node('small',row.producto_codigo));
    const action = node('td'), button = node('button','Registrar movimiento','secondary-btn'); button.type = 'button';
    button.setAttribute('aria-label',`Registrar movimiento de ${row.producto_nombre}`);
    button.onclick = () => openMovement(row); action.append(button);
    tr.append(name,node('td',row.fisico),node('td',row.reservado),node('td',row.disponible),action); return tr;
  }));
  const names = {APERTURA:'Saldo inicial',ENTRADA:'Entrada',AJUSTE:'Ajuste',SALIDA_PEDIDO:'Salida de pedido'};
  const movements = inventory.movimientos.filter(row => row.sucursal_codigo === branch &&
    `${row.producto_nombre} ${row.producto_codigo}`.toLocaleLowerCase('es').includes(search));
  ui('inventory-history').replaceChildren(...movements.map(row => {
    const item = node('li'), top = node('div',undefined,'ledger-heading');
    top.append(node('strong',`${names[row.tipo]} · ${row.variacion > 0 ? '+' : ''}${row.variacion} ud.`),node('small',date(row.fecha)));
    item.append(top,node('p',row.producto_nombre),node('small',`Saldo: ${row.cantidad_anterior} → ${row.cantidad_nueva}${row.pedido_id ? ` · Pedido #${row.pedido_id}` : ''}`),node('p',row.motivo,'ledger-reason')); return item;
  }));
  if (!movements.length) ui('inventory-history').append(node('li','No hay movimientos recientes con estos filtros.','empty-note'));
}
function openMovement(row) {
  if (busy) return;
  movement = {row, id:crypto.randomUUID()};
  ui('movement-form').reset(); ui('movement-message').textContent = '';
  ui('movement-product').textContent = `${row.producto_nombre} · ${row.sucursal_nombre}`;
  ui('movement-balance').textContent = `Físico: ${row.fisico} · Reservado: ${row.reservado} · Disponible: ${row.disponible}`;
  movementType(); ui('movement-dialog').showModal(); ui('movement-quantity').focus();
}
function movementType() {
  const adjustment = ui('movement-type').value === 'AJUSTE';
  ui('movement-quantity-label').textContent = adjustment ? 'Conteo físico final' : 'Unidades recibidas';
  ui('movement-quantity').min = adjustment ? '0' : '1';
}
function switchArea(inventoryArea) {
  if (busy) return;
  ui('orders-view').hidden = inventoryArea; ui('inventory-view').hidden = !inventoryArea;
  ui('tab-orders').setAttribute('aria-pressed', String(!inventoryArea));
  ui('tab-inventory').setAttribute('aria-pressed', String(inventoryArea));
}
ui('tab-orders').onclick = () => switchArea(false);
ui('tab-inventory').onclick = () => switchArea(true);
ui('inventory-branch').onchange = renderInventory; ui('inventory-search').oninput = renderInventory;
ui('movement-type').onchange = movementType;
ui('movement-close').onclick = () => ui('movement-dialog').close();
ui('movement-dialog').addEventListener('cancel', event => { if (busy) event.preventDefault(); });
ui('movement-form').onsubmit = async event => {
  event.preventDefault(); if (busy || !movement) return;
  const row = movement.row, type = ui('movement-type').value;
  const body = {producto_codigo:row.producto_codigo,sucursal_codigo:row.sucursal_codigo,tipo:type,
    cantidad:Number(ui('movement-quantity').value),motivo:ui('movement-reason').value,solicitud_id:movement.id};
  if (type === 'AJUSTE') body.cantidad_esperada = row.fisico;
  lock(true); ui('movement-message').textContent = 'Guardando movimiento…';
  try {
    const result = await api('/api/demo/inventario/movimientos','POST',body);
    await loadInventory(); ui('movement-dialog').close();
    message(result.movimiento.reintento ? 'El movimiento ya estaba registrado; se conserva un único cambio.' : 'Movimiento registrado. El catálogo utiliza el nuevo stock disponible.');
    movement = null; ui('inventory-search').focus();
  } catch (error) {
    ui('movement-message').textContent = error instanceof TypeError || error.name === 'TimeoutError' ?
      'No pudimos comprobar el resultado. Reintenta con los mismos datos para conservar una sola operación.' : error.message;
  } finally { lock(false); }
};
ui('check-expirations').onclick = async () => {
  if (busy) return;
  lock(true);
  try {
    const result = await api('/api/demo/reservas/procesar','POST',{});
    await loadInbox(); if (selected !== null) await loadDetail(selected); await loadInventory();
    message(`${result.procesados} reservas vencidas procesadas. Las asignaciones están actualizadas.`);
  } catch (error) { showError(error); }
  finally { lock(false); }
};
function renderIncidents(p) {
  const section = node('section',undefined,'incident-area'); section.append(node('h3',`Soporte e incidencias (${p.incidencias.length})`,'subheading'));
  const details = node('details'), summary = node('summary','+ Reportar una incidencia'), form = node('form'); form.id = 'incident-form';
  const label = node('label','Tipo de incidencia'); label.htmlFor = 'incident-category';
  const category = node('select'); category.id = 'incident-category';
  for (const [value,text] of [['RETRASO','Retraso'],['PRODUCTO_FALTANTE','Producto faltante'],['PRODUCTO_DANADO','Producto dañado'],['DIRECCION_INCORRECTA','Dirección incorrecta'],['CLIENTE_AUSENTE','Cliente ausente'],['OTRO','Otro']]) category.append(new Option(text,value));
  const descriptionLabel = node('label','Describe lo ocurrido'); descriptionLabel.htmlFor = 'incident-description';
  const description = node('textarea'); description.id = 'incident-description'; description.required = true; description.minLength = 5; description.maxLength = 2000;
  const submit = node('button','Registrar incidencia','secondary-btn');
  form.append(label,category,descriptionLabel,description,submit);
  form.onsubmit = event => { event.preventDefault(); perform(`/api/demo/pedidos/${p.pedido_id}/incidencias`,{categoria:category.value,descripcion:description.value},'Incidencia registrada. Ya puedes iniciar su revisión.'); };
  details.append(summary,form); section.append(details);
  for (const incident of p.incidencias) {
    const card = node('article',undefined,'incident-card'); card.dataset.incidentId = incident.id;
    card.append(node('h4',`Incidencia #${incident.id} · ${incident.categoria.replaceAll('_',' ').toLocaleLowerCase('es')}`),badge(incident.estado),node('p',incident.descripcion),node('small',`Registrada: ${date(incident.fecha_creacion)}`));
    if (incident.estado === 'ABIERTA') {
      const review = node('button','Iniciar revisión','secondary-btn'); review.type = 'button';
      review.onclick = () => perform(`/api/demo/incidencias/${incident.id}/atender`,{estado:'EN_REVISION'},'Incidencia en revisión.'); card.append(node('br'),review);
    } else if (incident.estado === 'EN_REVISION') {
      const resolve = node('form'), label = node('label','Resolución'); label.htmlFor = `resolution-${incident.id}`;
      const input = node('textarea'); input.id = label.htmlFor; input.required = true; input.minLength = 5; input.maxLength = 2000;
      resolve.append(label,input,node('button','Resolver incidencia','secondary-btn'));
      resolve.onsubmit = event => { event.preventDefault(); perform(`/api/demo/incidencias/${incident.id}/atender`,{estado:'RESUELTA',resolucion:input.value},'Incidencia resuelta y documentada.'); }; card.append(resolve);
    } else card.append(node('p',`Resolución: ${incident.resolucion}`));
    section.append(card);
  }
  return section;
}
ui('login-form').onsubmit = async event => {
  event.preventDefault(); ui('login-button').disabled = true;
  try {
    const result = await api('/api/demo/sesion','POST',{...(ui('usuario').value ? {usuario:ui('usuario').value.trim()} : {}),clave:ui('demo-key').value});
    ui('demo-key').value = ''; csrf = result.csrf; showSession(true); await refresh();
  } catch (error) { showError(error); }
  finally { ui('login-button').disabled = false; }
};
ui('logout').onclick = async () => {
  if (busy) return;
  try { await api('/api/demo/sesion','DELETE',{}); showSession(false); message('Sesión cerrada.'); ui('demo-key').focus(); }
  catch (error) { showError(error); }
};
ui('refresh').onclick = refresh;
ui('order-search').oninput = renderInbox; ui('order-state').onchange = renderInbox;
(async () => {
  try {
    const result = await api('/api/demo/sesion'); csrf = result.csrf || ''; showSession(result.autenticado);
    if (result.autenticado) await refresh(); else message('Ingresa tu clave de acceso.');
  } catch (error) { showError(error); }
})();
