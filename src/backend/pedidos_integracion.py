"""Puente de S2-05: reglas S2-01 y reservas S2-03 dentro de una transacción.

Las funciones reciben una conexión con BEGIN IMMEDIATE adquirido por pedidos_s2.
El stock físico se descuenta al consumir la reserva mediante el trigger de Josué.
"""
from uuid import uuid4

from src.backend.reglas_asignacion import (
    CAPACIDAD_MAXIMA_DEFAULT, ESTADOS_PEDIDO_ACTIVO, asignar_sucursal_pedido,
)


def evaluar_sucursales(db, latitud, longitud, productos):
    estados = sorted(ESTADOS_PEDIDO_ACTIVO)
    placeholders = ','.join('?' for _ in estados)
    sucursales = []
    filas = db.execute(f"""
        SELECT s.*, COALESCE(c.capacidad_maxima, ?) AS capacidad_maxima,
            (SELECT count(*) FROM pedidos p WHERE p.sucursal_id=s.id
             AND p.estado IN ({placeholders})) AS pedidos_activos
        FROM sucursales s LEFT JOIN s2_capacidades c ON c.sucursal_id=s.id
        ORDER BY s.codigo
    """, [CAPACIDAD_MAXIMA_DEFAULT, *estados]).fetchall()
    for fila in filas:
        if fila['capacidad_maxima'] == 0:
            continue  # Configuración explícita: sucursal deshabilitada.
        disponibles = db.execute("""
            SELECT p.codigo, i.cantidad - COALESCE((
                SELECT sum(r.cantidad) FROM reservas_stock r
                WHERE r.producto_id=i.producto_id AND r.sucursal_id=i.sucursal_id
                  AND r.estado='ACTIVA'
            ),0) AS disponible
            FROM inventario i JOIN productos p ON p.id=i.producto_id
            WHERE i.sucursal_id=?
        """, (fila['id'],)).fetchall()
        sucursales.append({**dict(fila), 'stock_disponible': {
            row['codigo']: row['disponible'] for row in disponibles
        }})
    resultado = asignar_sucursal_pedido(sucursales,
        {p['codigo']: p['cantidad'] for p in productos}, latitud, longitud)
    if filas and not sucursales:
        resultado.update(motivo_rechazo='SIN_CAPACIDAD_DISPONIBLE',
                         mensaje='Todas las sucursales están deshabilitadas por capacidad.')
    return resultado


class ConflictoConfirmacion(ValueError):
    """Un identificador de confirmación ya corresponde a otros datos."""


def registrar_integrado(db, cliente, latitud, longitud, productos, confirmacion_id=None):
    codigo_pedido = 'WEB-' + confirmacion_id if confirmacion_id else 'S2-' + uuid4().hex
    if confirmacion_id:
        existente = db.execute('SELECT id FROM pedidos WHERE codigo=?', (codigo_pedido,)).fetchone()
        if existente:
            anterior = obtener_integrado(db, existente['id'])
            items = [dict(producto_codigo=p['codigo'], cantidad=p['cantidad']) for p in productos]
            if (anterior['cliente'] != cliente or anterior['latitud'] != latitud
                or anterior['longitud'] != longitud or items != [
                    dict(producto_codigo=p['producto_codigo'], cantidad=p['cantidad'])
                    for p in anterior['items']]):
                raise ConflictoConfirmacion('Esta confirmación ya se utilizó con otros datos.')
            return dict(pedido_id=anterior['id'], estado=anterior['estado'],
                sucursal_codigo=anterior['sucursal_codigo'], sucursal_nombre=anterior['sucursal_nombre'],
                distancia_km=anterior['distancia_km'], motivo=None, motivo_codigo=None, items=items)

    asignacion = evaluar_sucursales(db, latitud, longitud, productos)
    codigo = asignacion['sucursal_asignada']
    resultado = dict(pedido_id=None, estado='SIN_ASIGNAR', sucursal_codigo=codigo,
        sucursal_nombre=None, distancia_km=None, motivo=asignacion['mensaje'],
        motivo_codigo=asignacion['motivo_rechazo'],
        items=[dict(producto_codigo=p['codigo'], cantidad=p['cantidad']) for p in productos])
    if not asignacion['asignada']:
        # El esquema oficial exige sucursal: no inventar pedidos ni FK inválidas.
        return resultado
    sucursal_id = db.execute('SELECT id FROM sucursales WHERE codigo=?', (codigo,)).fetchone()[0]
    detalle = asignacion['detalle_asignacion']
    cursor = db.execute("INSERT INTO pedidos(codigo,sucursal_id,estado) VALUES (?,?,'ASIGNADO')",
                        (codigo_pedido, sucursal_id))
    pedido_id = cursor.lastrowid
    db.execute('INSERT INTO s2_solicitudes VALUES (?,?,?,?,?)',
               (pedido_id, cliente, latitud, longitud, detalle['distancia_km']))
    for producto in productos:
        db.execute('INSERT INTO detalles_pedido(pedido_id,producto_id,cantidad) VALUES (?,?,?)',
                   (pedido_id, producto['id'], producto['cantidad']))
        db.execute('''INSERT INTO reservas_stock(pedido_id,producto_id,sucursal_id,cantidad)
                      VALUES (?,?,?,?)''',
                   (pedido_id, producto['id'], sucursal_id, producto['cantidad']))
    resultado.update(pedido_id=pedido_id, estado='ASIGNADO', motivo=None,
                     sucursal_nombre=detalle['nombre'], distancia_km=detalle['distancia_km'])
    return resultado


def obtener_integrado(db, pedido_id):
    pedido = db.execute('''
        SELECT p.id, p.codigo, p.estado, p.fecha_creacion AS creado_en,
               m.cliente, m.latitud, m.longitud, m.distancia_km,
               s.codigo AS sucursal_codigo, s.nombre AS sucursal_nombre
        FROM pedidos p JOIN sucursales s ON s.id=p.sucursal_id
        LEFT JOIN s2_solicitudes m ON m.pedido_id=p.id WHERE p.id=?
    ''', (pedido_id,)).fetchone()
    if pedido is None:
        return None
    items = db.execute('''
        SELECT p.codigo AS producto_codigo, d.cantidad,
            CASE WHEN r.estado='ACTIVA' THEN 1 ELSE 0 END AS reservada
        FROM detalles_pedido d JOIN productos p ON p.id=d.producto_id
        LEFT JOIN reservas_stock r ON r.pedido_id=d.pedido_id AND r.producto_id=d.producto_id
        WHERE d.pedido_id=? ORDER BY p.codigo
    ''', (pedido_id,)).fetchall()
    return {**dict(pedido), 'motivo_sin_asignar': None, 'items': [dict(r) for r in items]}
