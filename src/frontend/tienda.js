"use strict";
(() => {
  const key = 'inkafarma.carrito.v1';
  const money = value => new Intl.NumberFormat('es-PE',{style:'currency',currency:'PEN'}).format(value / 100);
  const el = (tag,text,cls) => { const n=document.createElement(tag); if(text!==undefined)n.textContent=text; if(cls)n.className=cls; return n; };
  let cart=[], quoteSequence=0, toastTimer;
  const cache=new Map();
  try {
    const saved=JSON.parse(localStorage.getItem(key)||'[]');
    if(Array.isArray(saved))cart=saved.filter(i=>typeof i?.producto_codigo==='string'&&i.producto_codigo.length<=80&&Number.isInteger(i.cantidad)&&i.cantidad>0&&i.cantidad<=10000).slice(0,100);
  } catch { cart=[]; }
  function count(){ document.querySelectorAll('[data-cart-count]').forEach(n=>n.textContent=cart.reduce((sum,i)=>sum+i.cantidad,0)); }
  function save(){ try{localStorage.setItem(key,JSON.stringify(cart));}catch{} count();window.dispatchEvent(new Event('carrito-cambiado')); }
  function toast(text){ const n=document.getElementById('cart-toast');if(!n)return;n.textContent=text;n.hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>n.hidden=true,3200); }
  function add(p,amount=1){
    cache.set(p.producto_codigo,p);
    const old=cart.find(i=>i.producto_codigo===p.producto_codigo);
    const total=(old?.cantidad||0)+amount;
    if(total>(p.maximo||10000)){toast(`Puedes añadir hasta ${p.maximo||10000} unidades de este producto.`);return false;}
    if(old)old.cantidad=total;else cart.push({producto_codigo:p.producto_codigo,cantidad:amount});
    save();toast('Producto añadido a tu carrito.');return true;
  }
  function update(code,amount){ if(amount<=0)cart=cart.filter(i=>i.producto_codigo!==code);else{const i=cart.find(i=>i.producto_codigo===code);if(i)i.cantidad=amount;}save();renderCart(); }
  function clear(){cart=[];save();}
  async function quote(items){
    try{
      const response=await fetch('/api/pedidos/cotizacion',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({items}),cache:'no-store',signal:AbortSignal.timeout(10000)});
      const data=await response.json();
      if(!response.ok)throw new Error(data.error||'No pudimos calcular tu pedido.');
      return data.cotizacion;
    }catch(error){
      if(error instanceof TypeError||error instanceof SyntaxError||error.name==='TimeoutError')throw new Error('No pudimos actualizar tu pedido. Comprueba la conexión y vuelve a intentarlo.');
      throw error;
    }
  }

  function totals(quote){
    const box=el('dl',undefined,'purchase-totals');
    for(const [label,value] of [['Productos',money(quote.subtotal_centimos)],['Envío',quote.envio_centimos===0?'Sin costo':money(quote.envio_centimos)],['Total',money(quote.total_centimos)]]){box.append(el('dt',label),el('dd',value));}
    return box;
  }
  function renderLines(lines){
    const container=document.getElementById('cart-items');container.replaceChildren();
    for(const item of cart){
      const p=lines.find(l=>l.producto_codigo===item.producto_codigo)||cache.get(item.producto_codigo)||{};
      const row=el('article',undefined,'cart-item');row.dataset.code=item.producto_codigo;
      const image=el('img');image.src=p.imagen||'/assets/imagenes/cuidado-diario.webp';image.alt=p.producto||item.producto_codigo;image.width=80;image.height=90;
      const content=el('div');content.append(el('small',p.marca||'Producto'),el('h3',p.producto||item.producto_codigo),el('p',p.presentacion||''));
      const controls=el('div',undefined,'cart-quantity');
      const minus=el('button','−');minus.type='button';minus.setAttribute('aria-label','Reducir cantidad');minus.onclick=()=>update(item.producto_codigo,item.cantidad-1);
      const plus=el('button','+');plus.type='button';plus.setAttribute('aria-label','Aumentar cantidad');plus.disabled=item.cantidad>=(p.maximo||10000);plus.onclick=()=>update(item.producto_codigo,item.cantidad+1);
      controls.append(minus,el('span',item.cantidad),plus);
      const remove=el('button','Quitar','cart-remove');remove.type='button';remove.onclick=()=>update(item.producto_codigo,0);
      content.append(controls,remove);row.append(image,content,el('strong',p.subtotal_centimos!==undefined?money(p.subtotal_centimos):''));container.append(row);
    }
  }
  async function renderCart(){
    const dialog=document.getElementById('cart-dialog');if(!dialog)return;
    const sequence=++quoteSequence,message=document.getElementById('cart-message'),total=document.getElementById('cart-totals'),checkout=document.getElementById('cart-checkout');
    total.replaceChildren();checkout.hidden=true;renderLines([]);
    if(!cart.length){message.textContent='Tu carrito está esperando tus esenciales.';return;}
    message.textContent='Revisando tu pedido…';
    try{
      const result=await quote(cart);if(sequence!==quoteSequence)return;
      result.items.forEach(p=>cache.set(p.producto_codigo,p));renderLines(result.items);total.append(totals(result));checkout.hidden=false;
      const remaining=result.envio_gratis_desde_centimos-result.subtotal_centimos;
      message.textContent=remaining>0?`Te faltan ${money(remaining)} para obtener envío sin costo.`:'Tu pedido tiene envío sin costo.';
    }catch(error){if(sequence===quoteSequence)message.textContent=error.message||'No pudimos actualizar el carrito. Vuelve a abrirlo para reintentar.';}
  }
  const dialog=document.getElementById('cart-dialog');
  if(dialog){
    document.getElementById('cart-open')?.addEventListener('click',()=>{dialog.showModal();renderCart();});
    document.getElementById('cart-close').onclick=()=>dialog.close();document.getElementById('cart-continue').onclick=()=>dialog.close();
    dialog.addEventListener('click',event=>{if(event.target===dialog&&event.clientX<dialog.getBoundingClientRect().left)dialog.close();});
  }
  window.addEventListener('storage',event=>{if(event.key===key){try{const value=JSON.parse(event.newValue||'[]');cart=Array.isArray(value)?value.filter(i=>typeof i?.producto_codigo==='string'&&Number.isInteger(i.cantidad)&&i.cantidad>0&&i.cantidad<=10000).slice(0,100):[];count();if(dialog?.open)renderCart();}catch{}}});
  window.Tienda={money,add,items:()=>cart.map(i=>({...i})),clear,quote,totals,toast,cache};count();
})();
