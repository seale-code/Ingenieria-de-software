"""S3-05: fecha, estado, reserva e historial en una única transacción.

Los comandos de fechas de S3-03 conservan su contrato. Las nuevas acciones web
usan estos servicios para no dejar una salida registrada si falla el reparto.
"""
from src.backend.entregas_s3 import _normalizar_fecha
from src.backend.soporte_pedidos_s3 import (
    PermisoDenegado, TransicionPedidoInvalida, _cambiar_estado_en_db,
    _validar_id, _validar_rol, _verificar_esquema_soporte, _pedido,
)
from src.database.database import DEFAULT_DATABASE, connect_database


def avanzar_reparto(pedido_id, nuevo_estado, rol, actor_id, db_path=DEFAULT_DATABASE):
    """Inicia/confirma reparto; un reintento del mismo paso no duplica efectos."""
    _validar_id(pedido_id, 'pedido_id')
    _validar_id(actor_id, 'actor_id')
    if _validar_rol(rol) != 'REPARTIDOR':
        raise PermisoDenegado('Solo el repartidor asignado puede avanzar el reparto.')
    if nuevo_estado not in ('EN_CAMINO', 'ENTREGADO'):
        raise TransicionPedidoInvalida('El destino debe ser EN_CAMINO o ENTREGADO.')
    with connect_database(db_path) as db:
        _verificar_esquema_soporte(db)
        db.execute('BEGIN IMMEDIATE')
        pedido = _pedido(db, pedido_id)
        entrega = db.execute('SELECT * FROM entregas WHERE pedido_id=?', (pedido_id,)).fetchone()
        if entrega is None:
            raise TransicionPedidoInvalida('Asigna un repartidor antes de iniciar la salida.')
        if entrega['repartidor_id'] != actor_id:
            raise PermisoDenegado('Este repartidor no tiene asignado el pedido.')
        estado_entrega = 'EN_CAMINO' if nuevo_estado == 'EN_CAMINO' else 'ENTREGADA'
        if pedido['estado'] == nuevo_estado and entrega['estado'] == estado_entrega:
            return dict(pedido_id=pedido_id, estado_nuevo=nuevo_estado, reintento=True)
        esperado = 'PREPARADO' if nuevo_estado == 'EN_CAMINO' else 'EN_CAMINO'
        if pedido['estado'] != esperado:
            raise TransicionPedidoInvalida(f'El pedido debe estar {esperado} para avanzar.')
        campo = 'fecha_salida' if nuevo_estado == 'EN_CAMINO' else 'fecha_entrega'
        if nuevo_estado == 'EN_CAMINO':
            activo = db.execute('SELECT activo FROM repartidores WHERE id=?', (actor_id,)).fetchone()
            if activo is None or not activo['activo']:
                raise PermisoDenegado('El repartidor asignado está inactivo.')
            # Impide despachar pedidos sin productos o con reservas liberadas.
            detalles = db.execute('SELECT count(*) FROM detalles_pedido WHERE pedido_id=?', (pedido_id,)).fetchone()[0]
            reservas = db.execute("""SELECT count(*) FROM detalles_pedido d
                JOIN reservas_stock r ON r.pedido_id=d.pedido_id AND r.producto_id=d.producto_id
                WHERE d.pedido_id=? AND r.estado='ACTIVA' AND r.cantidad=d.cantidad""", (pedido_id,)).fetchone()[0]
            if not detalles or reservas != detalles:
                raise TransicionPedidoInvalida('El pedido no tiene todas sus reservas activas.')
        if entrega[campo] is None:
            fecha = _normalizar_fecha(None, campo)
            anterior = entrega['fecha_asignacion'] if nuevo_estado == 'EN_CAMINO' else entrega['fecha_salida']
            if anterior is None or fecha < anterior:
                raise TransicionPedidoInvalida('La fecha del paso anterior es incoherente.')
            # campo proviene exclusivamente de la lista interna anterior.
            db.execute(f'UPDATE entregas SET {campo}=? WHERE id=?', (fecha, entrega['id']))
        resultado = _cambiar_estado_en_db(db, pedido_id, nuevo_estado, actor_id)
        return dict(resultado, reintento=False)
