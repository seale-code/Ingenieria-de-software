"""Entradas y conteos físicos autorizados, idempotentes y auditables (HU14)."""
from src.backend.logistica import (
    ErrorLogistica, autorizar_sucursal, exigir_esquema, solicitud_uuid, texto_motivo,
)
from src.database.database import DEFAULT_DATABASE, connect_database


def registrar_movimiento(producto_codigo, sucursal_codigo, tipo, cantidad, motivo, solicitud_id,
                         rol='ADMINISTRADOR', actor_id=None, db_path=DEFAULT_DATABASE, *, cantidad_esperada=None):
    """ENTRADA suma unidades; AJUSTE establece el conteo y exige el saldo visto.

    El trigger del movimiento aplica el inventario dentro de esta transacción.
    Los reintentos conservan el resultado original aunque el saldo haya cambiado.
    """
    if not isinstance(producto_codigo, str) or not producto_codigo.strip():
        raise ErrorLogistica('Selecciona un producto.')
    if not isinstance(sucursal_codigo, str) or not sucursal_codigo.strip():
        raise ErrorLogistica('Selecciona una sucursal.')
    if tipo not in ('ENTRADA', 'AJUSTE'):
        raise ErrorLogistica('El tipo debe ser ENTRADA o AJUSTE.')
    minimo = 1 if tipo == 'ENTRADA' else 0
    if isinstance(cantidad, bool) or not isinstance(cantidad, int) or not minimo <= cantidad <= 1_000_000_000:
        raise ErrorLogistica(f'La cantidad debe ser un entero entre {minimo} y 1000000000.')
    if tipo == 'AJUSTE' and (isinstance(cantidad_esperada, bool) or not isinstance(cantidad_esperada, int)
                            or cantidad_esperada < 0):
        raise ErrorLogistica('El ajuste requiere el saldo físico que estás revisando.')
    if tipo == 'ENTRADA' and cantidad_esperada is not None:
        raise ErrorLogistica('Una entrada no requiere un conteo anterior.')
    motivo = texto_motivo(motivo)
    solicitud_id = solicitud_uuid(solicitud_id)
    with connect_database(db_path) as db:
        exigir_esquema(db)
        db.execute('BEGIN IMMEDIATE')
        producto = db.execute('SELECT id FROM productos WHERE codigo=?', (producto_codigo,)).fetchone()
        sucursal = db.execute('SELECT id FROM sucursales WHERE codigo=?', (sucursal_codigo,)).fetchone()
        if producto is None or sucursal is None:
            raise LookupError('No existe el producto o la sucursal.')
        autorizar_sucursal(rol, actor_id, sucursal['id'])
        anterior = db.execute('SELECT * FROM movimientos_inventario WHERE solicitud_id=?', (solicitud_id,)).fetchone()
        if anterior:
            valor = anterior['variacion'] if tipo == 'ENTRADA' else anterior['cantidad_nueva']
            if (anterior['producto_id'] != producto['id'] or anterior['sucursal_id'] != sucursal['id']
                or anterior['tipo'] != tipo or valor != cantidad or anterior['motivo'] != motivo
                or anterior['actor_rol'] != rol or anterior['actor_id'] != actor_id
                or (tipo == 'AJUSTE' and anterior['cantidad_anterior'] != cantidad_esperada)):
                raise ErrorLogistica('Esta operación ya se utilizó con otros datos.')
            return dict(anterior, reintento=True)
        db.execute('INSERT INTO inventario(producto_id,sucursal_id,cantidad) VALUES(?,?,0) ON CONFLICT DO NOTHING',
                   (producto['id'], sucursal['id']))
        saldo = db.execute('SELECT cantidad FROM inventario WHERE producto_id=? AND sucursal_id=?',
                           (producto['id'], sucursal['id'])).fetchone()[0]
        if tipo == 'AJUSTE' and cantidad_esperada != saldo:
            raise ErrorLogistica('El inventario cambió. Actualiza el saldo antes de ajustar.')
        nuevo = saldo + cantidad if tipo == 'ENTRADA' else cantidad
        if nuevo > 1_000_000_000:
            raise ErrorLogistica('El saldo resultante supera el límite permitido.')
        if nuevo == saldo:
            raise ErrorLogistica('El conteo coincide con el saldo actual; no hay un ajuste que registrar.')
        reservadas = db.execute("SELECT COALESCE(sum(cantidad),0) FROM reservas_stock WHERE producto_id=? AND sucursal_id=? AND estado='ACTIVA'",
                                (producto['id'], sucursal['id'])).fetchone()[0]
        if nuevo < reservadas:
            raise ErrorLogistica(f'El saldo no puede ser menor a las {reservadas} unidades reservadas. Resuelve esos pedidos primero.')
        cursor = db.execute('''INSERT INTO movimientos_inventario(producto_id,sucursal_id,tipo,cantidad_anterior,
            cantidad_nueva,variacion,motivo,solicitud_id,actor_rol,actor_id) VALUES(?,?,?,?,?,?,?,?,?,?)''',
            (producto['id'], sucursal['id'], tipo, saldo, nuevo, nuevo-saldo, motivo, solicitud_id, rol, actor_id))
        return dict(db.execute('SELECT * FROM movimientos_inventario WHERE id=?', (cursor.lastrowid,)).fetchone(), reintento=False)


def consultar_inventario(db_path=DEFAULT_DATABASE):
    with connect_database(db_path, read_only=True) as db:
        exigir_esquema(db)
        db.execute('BEGIN')
        existencias = db.execute("""SELECT p.codigo AS producto_codigo,p.nombre AS producto_nombre,
            s.codigo AS sucursal_codigo,s.nombre AS sucursal_nombre,i.cantidad AS fisico,
            COALESCE((SELECT sum(r.cantidad) FROM reservas_stock r WHERE r.producto_id=i.producto_id
                AND r.sucursal_id=i.sucursal_id AND r.estado='ACTIVA'),0) AS reservado
            FROM inventario i JOIN productos p ON p.id=i.producto_id JOIN sucursales s ON s.id=i.sucursal_id
            ORDER BY s.nombre,p.nombre""").fetchall()
        movimientos = db.execute("""SELECT m.*,p.codigo AS producto_codigo,p.nombre AS producto_nombre,
            s.codigo AS sucursal_codigo,s.nombre AS sucursal_nombre FROM movimientos_inventario m
            JOIN productos p ON p.id=m.producto_id JOIN sucursales s ON s.id=m.sucursal_id
            ORDER BY m.id DESC LIMIT 100""").fetchall()
        return dict(existencias=[dict(f, disponible=f['fisico']-f['reservado']) for f in existencias],
                    movimientos=[dict(f) for f in movimientos])
