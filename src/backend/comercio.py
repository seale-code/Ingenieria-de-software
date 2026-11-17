"""Precios en céntimos, cotización verificable y datos de entrega privados."""
import hashlib
import json
import re

ENVIO_CENTIMOS = 690
ENVIO_GRATIS_DESDE = 14900
DISTRITOS = {
    'MIRAFLORES': ('Miraflores', -12.1211, -77.0294),
    'SAN-ISIDRO': ('San Isidro', -12.0972, -77.0363),
    'SURCO': ('Santiago de Surco', -12.1343, -76.9868),
}


class DatosComercialesInvalidos(ValueError):
    pass


class ConfirmacionComercialReutilizada(ValueError):
    pass


class CotizacionActualizada(ValueError):
    pass


def disponible(db):
    return db.execute('PRAGMA user_version').fetchone()[0] >= 5


def metadatos(db):
    if not disponible(db):
        return {}
    return {r['producto_codigo']: dict(r) for r in db.execute('''SELECT p.codigo AS producto_codigo,
        c.marca,c.presentacion,c.descripcion,c.imagen,c.orden,c.precio_centimos,c.precio_lista_centimos,c.maximo
        FROM catalogo_comercial c JOIN productos p ON p.id=c.producto_id''')}


def agrupar_items(items):
    if not isinstance(items,list) or not 1 <= len(items) <= 100:
        raise DatosComercialesInvalidos('Agrega entre 1 y 100 productos al pedido.')
    agrupados = {}
    for item in items:
        if not isinstance(item,dict):
            raise DatosComercialesInvalidos('Revisa los productos del carrito.')
        codigo, cantidad = item.get('producto_codigo'),item.get('cantidad')
        if not isinstance(codigo,str) or not 1 <= len(codigo) <= 80 or isinstance(cantidad,bool) or not isinstance(cantidad,int) or not 1 <= cantidad <= 10000:
            raise DatosComercialesInvalidos('Revisa el producto y su cantidad.')
        codigo=codigo.strip()
        agrupados[codigo]=agrupados.get(codigo,0)+cantidad
    return sorted(agrupados.items())


def cotizar(db, items):
    if not disponible(db):
        raise DatosComercialesInvalidos('El catálogo comercial no está disponible.')
    lineas=[]
    for codigo,cantidad in agrupar_items(items):
        fila=db.execute('''SELECT p.id,p.codigo,p.nombre,c.* FROM productos p
            JOIN catalogo_comercial c ON c.producto_id=p.id WHERE p.codigo=?''',(codigo,)).fetchone()
        if fila is None:
            raise DatosComercialesInvalidos(f'El producto {codigo} ya no está disponible en el catálogo.')
        if cantidad>fila['maximo']:
            raise DatosComercialesInvalidos(f"El máximo de {fila['nombre']} es {fila['maximo']} por pedido.")
        lineas.append(dict(producto_codigo=codigo,producto=fila['nombre'],marca=fila['marca'],
            presentacion=fila['presentacion'],imagen=fila['imagen'],cantidad=cantidad,maximo=fila['maximo'],
            precio_unitario_centimos=fila['precio_centimos'],subtotal_centimos=fila['precio_centimos']*cantidad))
    subtotal=sum(p['subtotal_centimos'] for p in lineas)
    envio=0 if subtotal>=ENVIO_GRATIS_DESDE else ENVIO_CENTIMOS
    contenido=dict(items=lineas,subtotal_centimos=subtotal,envio_centimos=envio,total_centimos=subtotal+envio,moneda='PEN',
        envio_gratis_desde_centimos=ENVIO_GRATIS_DESDE,metodo_pago='AL_RECIBIR')
    # Incluye importes e identidad de las líneas; el cliente nunca decide el total.
    contenido['cotizacion_id']=hashlib.sha256(json.dumps(contenido,sort_keys=True,ensure_ascii=True).encode()).hexdigest()
    return contenido


def validar_entrega(datos):
    if not isinstance(datos,dict) or set(datos)!={'cotizacion_id','telefono','direccion','distrito'}:
        raise DatosComercialesInvalidos('Completa la cotización y los datos de entrega.')
    token=datos['cotizacion_id']
    if not isinstance(token,str) or not re.fullmatch(r'[0-9a-f]{64}',token):
        raise DatosComercialesInvalidos('Revisa de nuevo el resumen del pedido.')
    telefono,direccion,distrito=datos['telefono'],datos['direccion'],datos['distrito']
    if not isinstance(telefono,str) or not re.fullmatch(r'9[0-9]{8}',telefono):
        raise DatosComercialesInvalidos('Ingresa un celular de 9 dígitos que comience con 9.')
    if not isinstance(direccion,str) or not 8<=len(direccion.strip())<=240:
        raise DatosComercialesInvalidos('Ingresa la dirección completa de entrega (8 a 240 caracteres).')
    if not isinstance(distrito,str) or distrito not in DISTRITOS:
        raise DatosComercialesInvalidos('Selecciona un distrito con cobertura.')
    return dict(cotizacion_id=token,telefono=telefono,direccion=direccion.strip(),distrito=distrito)


def obtener_resumen(db,pedido_id):
    if not disponible(db):
        return None
    fila=db.execute('''SELECT subtotal_centimos,envio_centimos,total_centimos,moneda,metodo_pago
        FROM pedidos_comerciales WHERE pedido_id=?''',(pedido_id,)).fetchone()
    if fila is None:
        return None
    lineas=[dict(r) for r in db.execute('''SELECT p.codigo AS producto_codigo,pp.cantidad,
        pp.precio_unitario_centimos,pp.cantidad*pp.precio_unitario_centimos AS subtotal_centimos
        FROM precios_pedido pp JOIN productos p ON p.id=pp.producto_id
        WHERE pp.pedido_id=? ORDER BY p.codigo''',(pedido_id,))]
    return dict(fila,items=lineas)


def comprobar_reintento(db,pedido_id,comercial):
    if not disponible(db):
        return
    previo=db.execute('SELECT * FROM pedidos_comerciales WHERE pedido_id=?',(pedido_id,)).fetchone()
    if previo is None and comercial is None:
        return
    if previo is None or comercial is None or any(previo[k]!=comercial.get(k) for k in ('cotizacion_id','telefono','direccion','distrito')):
        raise ConfirmacionComercialReutilizada('Esta confirmación ya corresponde a otros datos de entrega.')


def guardar_resumen(db,pedido_id,comercial,cotizacion):
    db.execute('''INSERT INTO pedidos_comerciales(pedido_id,cotizacion_id,telefono,direccion,distrito,
        subtotal_centimos,envio_centimos,total_centimos) VALUES(?,?,?,?,?,?,?,?)''',
        (pedido_id,comercial['cotizacion_id'],comercial['telefono'],comercial['direccion'],comercial['distrito'],
         cotizacion['subtotal_centimos'],cotizacion['envio_centimos'],cotizacion['total_centimos']))
    for item in cotizacion['items']:
        db.execute('''INSERT INTO precios_pedido(pedido_id,producto_id,cantidad,precio_unitario_centimos)
            SELECT ?,id,?,? FROM productos WHERE codigo=?''',
            (pedido_id,item['cantidad'],item['precio_unitario_centimos'],item['producto_codigo']))
