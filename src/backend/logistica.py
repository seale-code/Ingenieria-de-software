"""Aceptación, vencimientos y reasignación atómica entre sucursales (HU02/03/09)."""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from src.backend.soporte_pedidos_s3 import ErrorSoportePedido, PermisoDenegado
from src.database.database import DEFAULT_DATABASE, connect_database


class ErrorLogistica(ErrorSoportePedido):
    """Conflicto de negocio; no altera reservas, asignaciones ni existencias."""


class AsignacionResuelta(ErrorLogistica):
    """El lote leyó una asignación que otra transacción ya atendió."""


def disponible(db):
    return db.execute('PRAGMA user_version').fetchone()[0] >= 6


def exigir_esquema(db):
    if not disponible(db):
        raise ErrorLogistica('Actualiza la base a la versión 6 para gestionar la logística.')


def instante(ahora=None):
    fecha = ahora if ahora is not None else datetime.now(timezone.utc)
    if not isinstance(fecha, datetime) or fecha.tzinfo is None or fecha.utcoffset() is None:
        raise ErrorLogistica('La fecha debe incluir la zona horaria.')
    return fecha.astimezone(timezone.utc)


def fecha_utc(fecha):
    return fecha.isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def identificador(valor, campo):
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        raise ErrorLogistica(f'{campo} debe ser un entero positivo.')
    return valor


def solicitud_uuid(valor):
    if not isinstance(valor, str):
        raise ErrorLogistica('Envía un identificador UUID para la operación.')
    try:
        return str(UUID(valor))
    except (ValueError, AttributeError):
        raise ErrorLogistica('El identificador de la operación no es válido.') from None


def texto_motivo(valor):
    if not isinstance(valor, str) or not 5 <= len(valor.strip()) <= 240:
        raise ErrorLogistica('El motivo debe tener entre 5 y 240 caracteres.')
    return valor.strip()


def autorizar_sucursal(rol, actor_id, sucursal_id):
    if rol == 'ADMINISTRADOR':
        if actor_id is not None:
            identificador(actor_id, 'actor_id')
    elif rol == 'PERSONAL_SUCURSAL':
        identificador(actor_id, 'actor_id')
        if actor_id != sucursal_id:
            raise PermisoDenegado('Solo puedes gestionar tu sucursal.')
    else:
        raise PermisoDenegado('Esta operación requiere administración o personal de la sucursal.')


def configurar_plazo(minutos, db_path=DEFAULT_DATABASE):
    if isinstance(minutos, bool) or not isinstance(minutos, int) or not 1 <= minutos <= 1440:
        raise ErrorLogistica('El plazo debe ser de 1 a 1440 minutos.')
    with connect_database(db_path) as db:
        exigir_esquema(db)
        db.execute('UPDATE politica_reservas SET plazo_minutos=? WHERE id=1', (minutos,))


def nuevo_limite(db, ahora):
    minutos = db.execute('SELECT plazo_minutos FROM politica_reservas WHERE id=1').fetchone()[0]
    return fecha_utc(ahora + timedelta(minutes=minutos))


def comprobar_reservas(db, pedido_id, sucursal_id):
    detalles = db.execute('SELECT count(*) FROM detalles_pedido WHERE pedido_id=?', (pedido_id,)).fetchone()[0]
    activas = db.execute("""SELECT count(*) FROM detalles_pedido d JOIN reservas_stock r
        ON r.pedido_id=d.pedido_id AND r.producto_id=d.producto_id
        WHERE d.pedido_id=? AND r.sucursal_id=? AND r.cantidad=d.cantidad AND r.estado='ACTIVA'""",
        (pedido_id, sucursal_id)).fetchone()[0]
    if not detalles or detalles != activas:
        raise ErrorLogistica('El pedido no tiene todas las reservas activas de su sucursal.')


def aceptar_en_db(db, pedido_id, asignacion_id=None, *, ahora=None):
    """Se ejecuta dentro del BEGIN IMMEDIATE de preparación, nunca por separado."""
    if not disponible(db):
        return
    control = db.execute('SELECT * FROM control_reservas WHERE pedido_id=?', (pedido_id,)).fetchone()
    pedido = db.execute('SELECT sucursal_id FROM pedidos WHERE id=?', (pedido_id,)).fetchone()
    if control is None:
        raise ErrorLogistica('El pedido no tiene una asignación vigente.')
    if asignacion_id is not None:
        identificador(asignacion_id, 'asignacion_id')
        if asignacion_id != control['asignacion_id']:
            raise ErrorLogistica('La sucursal del pedido cambió. Actualiza antes de continuar.')
    fecha = fecha_utc(instante(ahora))
    if control['aceptada_en'] is None and (not control['fecha_limite'] or control['fecha_limite'] <= fecha):
        raise ErrorLogistica('Venció el plazo de aceptación. Actualiza para consultar la reasignación.')
    comprobar_reservas(db, pedido_id, pedido['sucursal_id'])
    if control['aceptada_en'] is None:
        db.execute('UPDATE control_reservas SET aceptada_en=? WHERE pedido_id=?', (fecha, pedido_id))


def obtener_logistica(db, pedido_id):
    if not disponible(db):
        return None
    control = db.execute('SELECT asignacion_id,fecha_limite,aceptada_en FROM control_reservas WHERE pedido_id=?',
                         (pedido_id,)).fetchone()
    if control is None:
        return None
    historial = db.execute("""SELECT h.*,o.nombre AS sucursal_origen,d.nombre AS sucursal_destino
        FROM historial_asignaciones h LEFT JOIN sucursales o ON o.id=h.sucursal_origen_id
        LEFT JOIN sucursales d ON d.id=h.sucursal_destino_id WHERE h.pedido_id=? ORDER BY h.id""",
        (pedido_id,)).fetchall()
    return dict(control, historial=[dict(f) for f in historial])


def _resultado(db, evento, reintento=False):
    pedido = db.execute("""SELECT p.estado,s.codigo AS sucursal_codigo,s.nombre AS sucursal_nombre
        FROM pedidos p JOIN sucursales s ON s.id=p.sucursal_id WHERE p.id=?""", (evento['pedido_id'],)).fetchone()
    return dict(pedido_id=evento['pedido_id'], asignacion_id=evento['id'],
        reasignado=evento['sucursal_destino_id'] is not None, incidencia_id=evento['incidencia_id'],
        estado_nuevo=pedido['estado'], sucursal_codigo=pedido['sucursal_codigo'],
        sucursal_nombre=pedido['sucursal_nombre'], reintento=reintento)


def resolver_falta_atencion(pedido_id, asignacion_id, motivo, solicitud_id, rol='ADMINISTRADOR',
                           actor_id=None, db_path=DEFAULT_DATABASE, *, ahora=None, por_vencimiento=False):
    """Libera, busca alternativa y vuelve a reservar en la misma transacción.

    La generación esperada y el UUID impiden que un reintento rechace también
    la siguiente sucursal. Cada sucursal se intenta una sola vez por pedido.
    """
    identificador(pedido_id, 'pedido_id')
    identificador(asignacion_id, 'asignacion_id')
    motivo = texto_motivo(motivo)
    solicitud_id = solicitud_uuid(solicitud_id)
    reloj = instante(ahora)
    fecha = fecha_utc(reloj)
    causa = 'PLAZO_AGOTADO' if por_vencimiento else 'RECHAZO_SUCURSAL'
    if por_vencimiento and rol != 'SISTEMA':
        raise PermisoDenegado('Solo el proceso de vencimientos aplica esta causa.')
    with connect_database(db_path) as db:
        exigir_esquema(db)
        db.execute('BEGIN IMMEDIATE')
        pedido = db.execute('SELECT * FROM pedidos WHERE id=?', (pedido_id,)).fetchone()
        if pedido is None:
            raise LookupError('No existe ese pedido.')
        anterior = db.execute('SELECT * FROM historial_asignaciones WHERE solicitud_id=?', (solicitud_id,)).fetchone()
        # Un reintento legítimo se autoriza sobre la sucursal original.
        sucursal_autorizada = anterior['sucursal_origen_id'] if anterior else pedido['sucursal_id']
        if rol != 'SISTEMA' or not por_vencimiento:
            autorizar_sucursal(rol, actor_id, sucursal_autorizada)
        if anterior:
            if (anterior['pedido_id'] != pedido_id or anterior['asignacion_anterior_id'] != asignacion_id
                or anterior['observacion'] != motivo or anterior['causa'] != causa
                or anterior['actor_rol'] != rol or anterior['actor_id'] != actor_id):
                raise ErrorLogistica('Esta operación ya se utilizó con otros datos.')
            return _resultado(db, anterior, True)
        control = db.execute('SELECT * FROM control_reservas WHERE pedido_id=?', (pedido_id,)).fetchone()
        if control is None or control['asignacion_id'] != asignacion_id:
            raise AsignacionResuelta('La asignación cambió. Actualiza antes de continuar.')
        if pedido['estado'] not in ('REGISTRADO', 'ASIGNADO', 'EN_PREPARACION'):
            raise AsignacionResuelta('Solo se puede reasignar antes de terminar la preparación.')
        if db.execute('SELECT 1 FROM entregas WHERE pedido_id=?', (pedido_id,)).fetchone():
            raise ErrorLogistica('El pedido ya tiene una entrega asignada.')
        if por_vencimiento and (control['aceptada_en'] is not None or not control['fecha_limite']
                                or control['fecha_limite'] > fecha
                                or pedido['estado'] not in ('REGISTRADO', 'ASIGNADO')):
            raise AsignacionResuelta('La asignación no tiene un plazo pendiente vencido.')
        comprobar_reservas(db, pedido_id, pedido['sucursal_id'])
        coordenadas = db.execute('SELECT latitud,longitud FROM s2_solicitudes WHERE pedido_id=?', (pedido_id,)).fetchone()
        if coordenadas is None:
            raise ErrorLogistica('El pedido no tiene ubicación para evaluar otra sucursal.')
        productos = [dict(f) for f in db.execute("""SELECT p.codigo,d.producto_id AS id,d.cantidad
            FROM detalles_pedido d JOIN productos p ON p.id=d.producto_id WHERE d.pedido_id=?""", (pedido_id,))]
        visitadas = {f[0] for f in db.execute('SELECT sucursal_destino_id FROM historial_asignaciones WHERE pedido_id=?',
                                           (pedido_id,)) if f[0] is not None}
        visitadas.add(pedido['sucursal_id'])
        db.execute("UPDATE reservas_stock SET estado='LIBERADA',fecha_cierre=? WHERE pedido_id=? AND estado='ACTIVA'",
                   (fecha, pedido_id))
        # Importación local para conservar el módulo S2 utilizable sin dependencias circulares.
        from src.backend.pedidos_integracion import evaluar_sucursales
        asignacion = evaluar_sucursales(db, coordenadas['latitud'], coordenadas['longitud'], productos,
                                      excluir_ids=visitadas)
        destino = None
        techo = None
        if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='plazos_compra'").fetchone():
            fila=db.execute('SELECT limite FROM plazos_compra WHERE pedido_id=?',(pedido_id,)).fetchone()
            techo=fila[0] if fila else None
        if asignacion['asignada'] and (techo is None or fecha < techo):
            destino = db.execute('SELECT id FROM sucursales WHERE codigo=?', (asignacion['sucursal_asignada'],)).fetchone()[0]
        categoria = 'RETRASO' if por_vencimiento else 'PRODUCTO_FALTANTE'
        incidencia = db.execute("""INSERT INTO incidencias_pedido(pedido_id,categoria,descripcion,reportado_por_rol,reportado_por_id)
            VALUES(?,?,?,?,?)""", (pedido_id, categoria, motivo,
                'ADMINISTRADOR' if rol == 'SISTEMA' else rol, actor_id)).lastrowid
        evento_id = db.execute("""INSERT INTO historial_asignaciones(pedido_id,sucursal_origen_id,sucursal_destino_id,
            asignacion_anterior_id,causa,observacion,incidencia_id,solicitud_id,actor_rol,actor_id,fecha)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)""", (pedido_id, pedido['sucursal_id'], destino, asignacion_id, causa,
                motivo, incidencia, solicitud_id, rol, actor_id, fecha)).lastrowid
        if destino is not None:
            db.execute("UPDATE pedidos SET sucursal_id=?,estado='ASIGNADO' WHERE id=?", (destino, pedido_id))
            limite = nuevo_limite(db, reloj)
            if techo:
                limite=min(limite,techo)
            for producto in productos:
                db.execute('''INSERT INTO reservas_stock(pedido_id,producto_id,sucursal_id,cantidad,fecha_vencimiento)
                    VALUES(?,?,?,?,?)''', (pedido_id, producto['id'], destino, producto['cantidad'], limite))
            db.execute('UPDATE s2_solicitudes SET distancia_km=? WHERE pedido_id=?',
                       (asignacion['detalle_asignacion']['distancia_km'], pedido_id))
            resolucion = f"Pedido reasignado a {asignacion['detalle_asignacion']['nombre']}; nuevas reservas confirmadas."
        else:
            limite = None
            db.execute("UPDATE pedidos SET estado='CANCELADO' WHERE id=?", (pedido_id,))
            resolucion = 'Ninguna sucursal alternativa puede atender el pedido completo. Pedido cancelado y reservas liberadas.'
        db.execute('UPDATE control_reservas SET asignacion_id=?,fecha_limite=?,aceptada_en=NULL WHERE pedido_id=?',
                   (evento_id, limite, pedido_id))
        db.execute("""UPDATE incidencias_pedido SET estado='EN_REVISION',atendido_por_rol='ADMINISTRADOR',
            fecha_actualizacion=? WHERE id=?""", (fecha, incidencia))
        db.execute("""UPDATE incidencias_pedido SET estado='RESUELTA',resolucion=?,fecha_resolucion=?,
            fecha_actualizacion=? WHERE id=?""", (resolucion, fecha, fecha, incidencia))
        evento = db.execute('SELECT * FROM historial_asignaciones WHERE id=?', (evento_id,)).fetchone()
        return _resultado(db, evento)


def procesar_vencimientos(db_path=DEFAULT_DATABASE, *, ahora=None, limite=100):
    """Lote acotado; cada pedido se revalida y resuelve bajo su bloqueo de escritura."""
    identificador(limite, 'limite')
    if limite > 1000:
        raise ErrorLogistica('El lote no puede superar 1000 pedidos.')
    reloj = instante(ahora)
    with connect_database(db_path, read_only=True) as db:
        exigir_esquema(db)
        filas = db.execute("""SELECT c.pedido_id,c.asignacion_id FROM control_reservas c JOIN pedidos p ON p.id=c.pedido_id
            WHERE c.aceptada_en IS NULL AND c.fecha_limite<=? AND p.estado IN ('REGISTRADO','ASIGNADO')
              AND EXISTS(SELECT 1 FROM reservas_stock r WHERE r.pedido_id=p.id AND r.estado='ACTIVA')
            ORDER BY c.fecha_limite,c.pedido_id LIMIT ?""", (fecha_utc(reloj), limite)).fetchall()
    resultados = []
    from uuid import NAMESPACE_URL, uuid5
    for fila in filas:
        # El mismo vencimiento tiene la misma clave entre procesos/reinicios.
        clave = str(uuid5(NAMESPACE_URL, f"inkafarma:vencimiento:{fila['pedido_id']}:{fila['asignacion_id']}"))
        try:
            resultado = resolver_falta_atencion(fila['pedido_id'], fila['asignacion_id'],
                'La sucursal no aceptó el pedido dentro del plazo de reserva.', clave,
                'SISTEMA', db_path=db_path, ahora=reloj, por_vencimiento=True)
            if not resultado['reintento']:
                resultados.append(resultado)
        except AsignacionResuelta:
            # Otra transacción pudo aceptar/cancelar/reasignar desde la lectura del lote.
            # Las incoherencias de persistencia (sqlite3.Error) se propagan al supervisor.
            continue
    return resultados
