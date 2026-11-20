"""Comprobaciones de seguridad acotadas sobre Flask y bases temporales.

No abre puertos, no consulta servicios externos y no publica secretos ni contactos.
Las observaciones describen carencias; no se cuentan como controles aprobados.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import secrets
import tempfile
from uuid import uuid4

from scripts.iniciar_tienda import preparar_tienda
from src.backend.app import create_app
from src.backend.inventario import registrar_movimiento
from src.database.database import connect_database


RAIZ = Path(__file__).resolve().parents[1]


def carga(cliente, cantidad=2):
    items = [dict(producto_codigo='023735', cantidad=cantidad)]
    respuesta = cliente.post('/api/pedidos/cotizacion', json=dict(items=items))
    if respuesta.status_code != 200:
        raise RuntimeError('La preparación local requiere una cotización válida.')
    cotizacion = respuesta.json['cotizacion']
    return dict(cliente='Contacto sintético de seguridad', confirmacion_id=str(uuid4()),
                items=items, comercio=dict(cotizacion_id=cotizacion['cotizacion_id'],
                telefono='987654321', direccion='Dirección sintética 123', distrito='MIRAFLORES')), cotizacion


def analizar(revision):
    controles = []
    observaciones = []

    def comprobar(identificador, descripcion, condicion, **evidencia):
        controles.append(dict(id=identificador, descripcion=descripcion,
                              resultado='APROBADO' if condicion else 'FALLO', evidencia=evidencia))

    with tempfile.TemporaryDirectory() as carpeta:
        path = Path(carpeta) / 'controles.sqlite3'
        preparar_tienda(path)
        clave = secrets.token_urlsafe(32)
        app = create_app(path, operations_key=clave)
        app.testing = True
        publico = app.test_client()
        apagado = create_app(path, operations_key='').test_client()
        estados = [apagado.get(url).status_code for url in ['/operaciones', '/api/demo/inventario']]
        comprobar('C01', 'Panel deshabilitado sin clave', estados == [404, 404], estados_http=estados)
        estados = [publico.get(url).status_code for url in ['/api/demo/pedidos', '/api/demo/inventario']]
        comprobar('C02', 'Datos internos requieren sesión', estados == [401, 401], estados_http=estados)
        operador = app.test_client()
        intentos = [operador.post('/api/demo/sesion', json={'clave': 'incorrecta'}).status_code for _ in range(6)]
        acceso = operador.post('/api/demo/sesion', json={'clave': clave})
        comprobar('C03', 'Clave incorrecta rechazada y clave válida aceptada',
                  intentos == [401] * 6 and acceso.status_code == 200,
                  intentos_invalidos=6, estados_http=intentos, acceso_correcto_http=acceso.status_code)
        observaciones.append(dict(id='SEC-03', intentos_invalidos=6, limite_observado=False,
                                  siguiente_acceso_correcto_http=acceso.status_code))
        csrf = acceso.json['csrf']
        cookie = acceso.headers.get('Set-Cookie', '')
        comprobar('C04', 'Cookie HttpOnly y SameSite Strict', 'HttpOnly' in cookie and 'SameSite=Strict' in cookie,
                  httponly='HttpOnly' in cookie, samesite_strict='SameSite=Strict' in cookie)
        inicio = publico.get('/')
        observaciones.append(dict(id='SEC-04', cookie_secure='; Secure' in cookie,
            csp_presente='Content-Security-Policy' in inicio.headers,
            hsts_presente='Strict-Transport-Security' in inicio.headers, transporte='test_client HTTP local'))
        url = '/api/demo/reservas/procesar'
        respuesta = operador.post(url, json={})
        comprobar('C05', 'Mutación sin CSRF rechazada', respuesta.status_code == 403, http=respuesta.status_code)
        respuesta = operador.post(url, json={}, headers={'X-CSRF-Token': 'incorrecto'})
        comprobar('C06', 'CSRF incorrecto rechazado', respuesta.status_code == 403, http=respuesta.status_code)
        cabeceras = {'X-CSRF-Token': csrf}
        respuesta = operador.post(url, json={}, headers=dict(cabeceras, Origin='https://otro.example'))
        comprobar('C07', 'Origen externo rechazado', respuesta.status_code == 403, http=respuesta.status_code)
        respuesta = operador.post(url, data='{}', content_type='text/plain', headers=cabeceras)
        comprobar('C08', 'Mutación exige JSON', respuesta.status_code == 400, http=respuesta.status_code)
        respuesta = operador.post(url, json={}, headers=cabeceras)
        comprobar('C09', 'Sesión y CSRF válidos permiten la operación', respuesta.status_code == 200, http=respuesta.status_code)
        respuesta = operador.post(url, json={'dato': 'x' * 33000}, headers=cabeceras)
        comprobar('C10', 'Cuerpo mayor a 32 KiB rechazado', respuesta.status_code == 413, http=respuesta.status_code)
        respuesta = publico.get('/api/catalogo', query_string={'buscar': "' OR 1=1 --"})
        comprobar('C11', 'Búsqueda trata entrada SQL como dato', respuesta.status_code == 200 and respuesta.json['total'] == 0,
                  http=respuesta.status_code, coincidencias=respuesta.json.get('total'))
        estados = [publico.get(url).status_code for url in ['/assets/../../requirements.txt', '/assets/%2e%2e/%2e%2e/requirements.txt']]
        comprobar('C12', 'Rutas estáticas no sirven archivos superiores', estados == [404, 404], estados_http=estados)
        payload, cotizacion = carga(publico)
        payload.update(total_centimos=1, latitud=0, longitud=0)
        payload['items'][0]['precio_centimos'] = 1
        compra = publico.post('/api/pedidos', json=payload)
        if compra.status_code != 200:
            raise RuntimeError('El escenario requiere un pedido local confirmado.')
        pedido = compra.json['pedido']['pedido_id']
        correcto = compra.json['pedido']['comercio']['total_centimos'] == cotizacion['total_centimos']
        comprobar('C13', 'Servidor conserva precio y distrito frente a importes enviados',
                  correcto and compra.json['pedido']['sucursal_codigo'] == 'MIRAFLORES',
                  precio_servidor_conservado=correcto, distrito_servidor_conservado=compra.json['pedido']['sucursal_codigo'] == 'MIRAFLORES')
        repetido = publico.post('/api/pedidos', json=payload)
        with connect_database(path, read_only=True) as db:
            cantidad_pedidos = db.execute('SELECT count(*) FROM pedidos').fetchone()[0]
        comprobar('C14', 'Reintento de confirmación no duplica pedido',
                  repetido.status_code == 200 and repetido.json == compra.json and cantidad_pedidos == 1,
                  http=repetido.status_code, pedidos=cantidad_pedidos)
        privado = publico.get(f'/api/demo/pedidos/{pedido}')
        comprobar('C15', 'ID de pedido no autoriza detalle interno', privado.status_code == 401, http=privado.status_code)
        respuesta = publico.get('/api/seguimiento', headers={'X-Codigo-Pedido': 'WEB-' + payload['confirmacion_id']})
        texto = respuesta.get_data(as_text=True)
        omite = all(v not in texto for v in [payload['cliente'], payload['comercio']['telefono'],
                    payload['comercio']['direccion'], 'actor_id', 'solicitud_id', 'telefono', 'direccion'])
        comprobar('C16', 'Seguimiento omite contacto y actores internos', respuesta.status_code == 200 and omite,
                  http=respuesta.status_code, datos_privados_omitidos=omite)
        estados = [publico.get('/api/seguimiento', headers={'X-Codigo-Pedido': valor}).status_code
                   for valor in [str(pedido), 'WEB-' + str(uuid4())]]
        comprobar('C17', 'Seguimiento rechaza ID y código inexistente', estados == [400, 404], estados_http=estados)
        comprobar('C18', 'API sin caché y cabeceras defensivas',
            respuesta.headers.get('Cache-Control') == 'no-store' and respuesta.headers.get('X-Content-Type-Options') == 'nosniff'
            and respuesta.headers.get('Referrer-Policy') == 'no-referrer' and respuesta.headers.get('X-Frame-Options') == 'DENY',
            no_store=respuesta.headers.get('Cache-Control') == 'no-store', nosniff=respuesta.headers.get('X-Content-Type-Options') == 'nosniff',
            no_referrer=respuesta.headers.get('Referrer-Policy') == 'no-referrer', frame_deny=respuesta.headers.get('X-Frame-Options') == 'DENY')
        detalle = operador.get(f'/api/demo/pedidos/{pedido}').json['pedido']
        generacion = detalle['logistica']['asignacion_id']

        def accion(nombre, **extra):
            return operador.post(f'/api/demo/pedidos/{pedido}/acciones', json=dict(accion=nombre, **extra), headers=cabeceras)

        estados = [accion('preparar', asignacion_id=generacion, **extra).status_code
                   for extra in [dict(rol='ADMINISTRADOR'), dict(actor_id=1)]]
        comprobar('C19', 'Cliente no selecciona rol o actor', estados == [400, 400], estados_http=estados)
        estados = [accion('asignar', repartidor_id=1).status_code, accion('salir').status_code,
                   accion('listo', asignacion_id=generacion).status_code]
        comprobar('C20', 'No permite saltar preparación o reparto', estados == [409, 409, 409], estados_http=estados)
        respuesta = accion('preparar', asignacion_id=generacion + 999)
        comprobar('C21', 'Preparación exige generación vigente', respuesta.status_code == 409, http=respuesta.status_code)
        estados = [accion('preparar', asignacion_id=generacion).status_code,
                   accion('listo', asignacion_id=generacion).status_code, accion('asignar', repartidor_id=1).status_code,
                   accion('salir').status_code, accion('salir').status_code]
        with connect_database(path, read_only=True) as db:
            movimientos = db.execute("SELECT count(*) FROM movimientos_inventario WHERE tipo='SALIDA_PEDIDO'").fetchone()[0]
            saldo = db.execute("SELECT cantidad FROM inventario i JOIN productos p ON p.id=i.producto_id JOIN sucursales s ON s.id=i.sucursal_id WHERE p.codigo='023735' AND s.codigo='MIRAFLORES'").fetchone()[0]
        comprobar('C22', 'Reintento de despacho descuenta una sola vez', estados == [200] * 5 and movimientos == 1 and saldo == 16,
                  estados_http=estados, movimientos_salida=movimientos, saldo_final=saldo)
        otro = app.test_client()
        otro.post('/api/demo/sesion', json={'clave': clave})
        inventario = otro.get('/api/demo/inventario')
        sucursales = {r['sucursal_codigo'] for r in inventario.json['existencias']}
        observaciones.append(dict(id='SEC-01', segunda_sesion_inventario_http=inventario.status_code,
                                  sucursales_accesibles=len(sucursales), identidad_individual=False))
        segunda_app = create_app(path, operations_key=clave)
        otro_proceso = segunda_app.test_client()
        otro_proceso.set_cookie('session', operador.get_cookie('session').value)
        observaciones.append(dict(id='OBS-01', cookie_otra_instancia_http=otro_proceso.get('/api/demo/inventario').status_code,
                                  clave_operaciones_compartida=True))
        salida = operador.delete('/api/demo/sesion', json={}, headers=cabeceras)
        denegado = operador.get('/api/demo/inventario')
        comprobar('C23', 'Cerrar sesión retira acceso del cliente', salida.status_code == 200 and denegado.status_code == 401,
                  cierre_http=salida.status_code, siguiente_acceso_http=denegado.status_code)
        abuso_path = Path(carpeta) / 'reservas.sqlite3'
        preparar_tienda(abuso_path)
        for sucursal in ['MIRAFLORES', 'SAN-ISIDRO', 'SURCO']:
            registrar_movimiento('023735', sucursal, 'AJUSTE', 1, 'Escenario local acotado de seguridad',
                                 str(uuid4()), db_path=abuso_path, cantidad_esperada=18)
        anonimo = create_app(abuso_path, operations_key='').test_client()
        estados = []
        for _ in range(4):
            datos, _ = carga(anonimo, 1)
            estados.append(anonimo.post('/api/pedidos', json=datos).status_code)
        with connect_database(abuso_path, read_only=True) as db:
            reservas = db.execute("SELECT count(*) FROM reservas_stock WHERE estado='ACTIVA'").fetchone()[0]
            fisico = db.execute("SELECT sum(cantidad) FROM inventario i JOIN productos p ON p.id=i.producto_id WHERE p.codigo='023735'").fetchone()[0]
        observaciones.append(dict(id='SEC-02', stock_preparado_por_sucursal=1, sucursales=3, solicitudes_publicas=4,
            contactos_verificados=0, estados_http=estados, reservas_activas=reservas, stock_fisico= fisico,
            bloqueo_temporal_reproducido=estados == [200, 200, 200, 409] and reservas == 3))

    archivos = sorted([p for p in (RAIZ / 'src').rglob('*') if p.suffix in {'.py', '.js', '.html', '.css', '.sql'}]
                       + [RAIZ / 'scripts/iniciar_tienda.py', RAIZ / 'requirements.txt', RAIZ / 'requirements-test.txt'])
    hashes = {p.relative_to(RAIZ).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in archivos}
    return dict(fecha_utc=datetime.now(timezone.utc).isoformat(), revision_declarada=revision,
                python=platform.python_version(), esquema=6, alcance='Flask test_client; dos bases temporales; sin red externa',
                controles=controles, observaciones=observaciones,
                resumen=dict(controles=len(controles), aprobados=sum(c['resultado'] == 'APROBADO' for c in controles),
                             fallos=sum(c['resultado'] == 'FALLO' for c in controles), observaciones=len(observaciones)),
                sha256_fuentes=hashes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', default='sin declarar', help='Commit del código revisado; es una etiqueta, no una consulta a Git.')
    parser.add_argument('--salida', type=Path)
    args = parser.parse_args()
    resultado = analizar(args.revision)
    texto = json.dumps(resultado, ensure_ascii=False, indent=2) + '\n'
    if args.salida:
        args.salida.write_text(texto, encoding='utf-8')
    print(json.dumps(resultado['resumen'], ensure_ascii=False))
    raise SystemExit(1 if resultado['resumen']['fallos'] else 0)


if __name__ == '__main__':
    main()
