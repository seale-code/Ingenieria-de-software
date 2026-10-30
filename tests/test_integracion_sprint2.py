"""S2-05 / #12: registro de Anderson + reglas de César + esquema de Josué."""
import concurrent.futures
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path

from src.backend.pedidos_s2 import (
    DatosInvalidos, ModuloNoInicializado, configurar_capacidad, iniciar_modulo,
    obtener_pedido, registrar_pedido,
)
from src.database.database import connect_database, initialize_database
from src.database.migrate_josue import migrar


def solicitud(codigo='DEMO-A', cantidad=2):
    return dict(cliente='Cliente ficticio', latitud=-12.0, longitud=-77.05,
                items=[dict(producto_codigo=codigo, cantidad=cantidad)])


class IntegracionSprint2Tests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / 's2.sqlite3'
        initialize_database(self.path, demo=True)
        migrar(self.path, hasta=3)
        iniciar_modulo(self.path)
        configurar_capacidad('DEMO-NORTE', 10, self.path)
        configurar_capacidad('DEMO-SUR', 10, self.path)

    def scalar(self, sql, parameters=()):
        with connect_database(self.path, read_only=True) as db:
            return db.execute(sql, parameters).fetchone()[0]

    def stock(self):
        return self.scalar("SELECT cantidad FROM inventario WHERE producto_id=(SELECT id FROM productos WHERE codigo='DEMO-A') AND sucursal_id=(SELECT id FROM sucursales WHERE codigo='DEMO-NORTE')")

    def reserva_ajena(self, cantidad):
        with connect_database(self.path) as db:
            db.execute("INSERT INTO pedidos(codigo,sucursal_id,estado) SELECT 'EXTERNO',id,'ASIGNADO' FROM sucursales WHERE codigo='DEMO-NORTE'")
            pedido = db.execute("SELECT id FROM pedidos WHERE codigo='EXTERNO'").fetchone()[0]
            producto = db.execute("SELECT id FROM productos WHERE codigo='DEMO-A'").fetchone()[0]
            sucursal = db.execute("SELECT id FROM sucursales WHERE codigo='DEMO-NORTE'").fetchone()[0]
            db.execute('INSERT INTO detalles_pedido(pedido_id,producto_id,cantidad) VALUES (?,?,?)', (pedido, producto, cantidad))
            db.execute('INSERT INTO reservas_stock(pedido_id,producto_id,sucursal_id,cantidad) VALUES (?,?,?,?)', (pedido, producto, sucursal, cantidad))

    def test_registro_usa_pedidos_y_reservas_oficiales(self):
        result = registrar_pedido(solicitud(), self.path)
        self.assertEqual(result['estado'], 'ASIGNADO')
        self.assertEqual(self.scalar('SELECT count(*) FROM pedidos'), 1)
        self.assertEqual(self.scalar('SELECT sum(cantidad) FROM reservas_stock'), 2)
        self.assertEqual(self.stock(), 5)  # Reservar no equivale a consumir.
        self.assertEqual(obtener_pedido(result['pedido_id'], self.path)['cliente'], 'Cliente ficticio')

    def test_reserva_ajena_reduce_disponible_sin_error_sql(self):
        self.reserva_ajena(4)
        result = registrar_pedido(solicitud(cantidad=2), self.path)
        self.assertEqual(result['estado'], 'SIN_ASIGNAR')
        self.assertIsNone(result['pedido_id'])
        self.assertEqual(self.scalar('SELECT count(*) FROM pedidos'), 1)
        self.assertEqual(self.stock(), 5)

    def test_desempate_por_stock_de_cesar(self):
        with connect_database(self.path) as db:
            db.execute("UPDATE sucursales SET latitud=-12.0,longitud=-77.05")
            db.execute("UPDATE inventario SET cantidad=10 WHERE producto_id=(SELECT id FROM productos WHERE codigo='DEMO-A') AND sucursal_id=(SELECT id FROM sucursales WHERE codigo='DEMO-SUR')")
        self.assertEqual(registrar_pedido(solicitud(), self.path)['sucursal_codigo'], 'DEMO-SUR')

    def test_datos_invalidos_no_insertan_ni_reservan(self):
        for cantidad in [0, -1, 1.5, True, '2', 10001]:
            with self.subTest(cantidad=cantidad), self.assertRaises(DatosInvalidos):
                registrar_pedido(solicitud(cantidad=cantidad), self.path)
        for campo, valor in [('cliente', ' '), ('latitud', float('nan')), ('longitud', 181), ('items', [])]:
            datos = solicitud()
            datos[campo] = valor
            with self.subTest(campo=campo), self.assertRaises(DatosInvalidos):
                registrar_pedido(datos, self.path)
        with self.assertRaises(DatosInvalidos):
            registrar_pedido(solicitud('NO-EXISTE'), self.path)
        self.assertEqual(self.scalar('SELECT count(*) FROM pedidos'), 0)
        self.assertEqual(self.scalar('SELECT count(*) FROM reservas_stock'), 0)
        self.assertEqual(self.stock(), 5)

    def test_stock_insuficiente_sin_registros_parciales(self):
        resultado = registrar_pedido(solicitud(cantidad=6), self.path)
        self.assertEqual(resultado['motivo_codigo'], 'SIN_STOCK_DISPONIBLE')
        self.assertIsNone(resultado['pedido_id'])
        self.assertEqual(self.scalar('SELECT count(*) FROM pedidos'), 0)
        self.assertEqual(self.scalar('SELECT count(*) FROM s2_solicitudes'), 0)
        self.assertEqual(self.stock(), 5)

    def test_pedido_multiproducto_no_se_divide_entre_sucursales(self):
        datos = solicitud(cantidad=1)
        datos['items'].append(dict(producto_codigo='DEMO-B', cantidad=1))
        self.assertEqual(registrar_pedido(datos, self.path)['estado'], 'SIN_ASIGNAR')
        self.assertEqual(self.scalar('SELECT count(*) FROM detalles_pedido'), 0)
        self.assertEqual(self.stock(), 5)

    def test_lineas_duplicadas_se_suman_antes_de_asignar(self):
        datos = solicitud(cantidad=3)
        datos['items'].append(dict(producto_codigo='DEMO-A', cantidad=3))
        self.assertEqual(registrar_pedido(datos, self.path)['estado'], 'SIN_ASIGNAR')
        datos['items'] = [dict(producto_codigo='DEMO-A', cantidad=2)] * 2
        respuesta = registrar_pedido(datos, self.path)
        self.assertEqual(respuesta['items'], [dict(producto_codigo='DEMO-A', cantidad=4)])
        self.assertEqual(self.scalar('SELECT count(*) FROM detalles_pedido'), 1)
        self.assertEqual(self.scalar('SELECT sum(cantidad) FROM reservas_stock'), 4)

    def test_capacidad_usa_pedidos_oficiales_y_permite_cero(self):
        self.reserva_ajena(1)
        configurar_capacidad('DEMO-NORTE', 1, self.path)
        resultado = registrar_pedido(solicitud(cantidad=1), self.path)
        self.assertEqual(resultado['motivo_codigo'], 'SIN_CAPACIDAD_DISPONIBLE')
        configurar_capacidad('DEMO-NORTE', 0, self.path)
        configurar_capacidad('DEMO-SUR', 0, self.path)
        self.assertEqual(registrar_pedido(solicitud(), self.path)['motivo_codigo'], 'SIN_CAPACIDAD_DISPONIBLE')

    def test_dos_clientes_concurrentes_no_sobrevenden(self):
        with connect_database(self.path) as db:
            db.execute("UPDATE inventario SET cantidad=1 WHERE producto_id=(SELECT id FROM productos WHERE codigo='DEMO-A') AND sucursal_id=(SELECT id FROM sucursales WHERE codigo='DEMO-NORTE')")
        barrera = threading.Barrier(2)
        def registrar():
            barrera.wait(timeout=5)
            return registrar_pedido(solicitud(cantidad=1), self.path)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            futuros = [pool.submit(registrar) for _ in range(2)]
            resultados = [f.result(timeout=10) for f in futuros]
        self.assertEqual(sorted(r['estado'] for r in resultados), ['ASIGNADO', 'SIN_ASIGNAR'])
        self.assertEqual(self.stock(), 1)
        self.assertEqual(self.scalar("SELECT sum(cantidad) FROM reservas_stock WHERE estado='ACTIVA'"), 1)
        self.assertEqual(self.scalar('SELECT count(*) FROM pedidos'), 1)

    def test_capacidad_concurrente_no_se_excede(self):
        configurar_capacidad('DEMO-NORTE', 1, self.path)
        barrera = threading.Barrier(2)
        def registrar():
            barrera.wait(timeout=5)
            return registrar_pedido(solicitud(cantidad=1), self.path)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            futuros = [pool.submit(registrar) for _ in range(2)]
            resultados = [f.result(timeout=10) for f in futuros]
        self.assertEqual(sorted(r['estado'] for r in resultados), ['ASIGNADO', 'SIN_ASIGNAR'])
        self.assertEqual(self.scalar('SELECT count(*) FROM pedidos'), 1)
        self.assertEqual(self.stock(), 5)

    def test_fallo_segunda_reserva_revierte_todo(self):
        with connect_database(self.path) as db:
            db.execute("UPDATE inventario SET cantidad=3 WHERE producto_id=(SELECT id FROM productos WHERE codigo='DEMO-B') AND sucursal_id=(SELECT id FROM sucursales WHERE codigo='DEMO-NORTE')")
            db.execute("""CREATE TRIGGER fallo_segunda_reserva BEFORE INSERT ON reservas_stock
                WHEN NEW.producto_id=(SELECT id FROM productos WHERE codigo='DEMO-B')
                BEGIN SELECT RAISE(ABORT,'fallo intencional'); END""")
        datos = solicitud(cantidad=1)
        datos['items'].append(dict(producto_codigo='DEMO-B', cantidad=1))
        with self.assertRaises(sqlite3.IntegrityError):
            registrar_pedido(datos, self.path)
        for tabla in ['pedidos', 'detalles_pedido', 'reservas_stock', 's2_solicitudes', 'historial_estados']:
            self.assertEqual(self.scalar('SELECT count(*) FROM ' + tabla), 0)
        self.assertEqual(self.stock(), 5)

    def test_consumir_reserva_no_descuenta_dos_veces(self):
        resultado = registrar_pedido(solicitud(cantidad=2), self.path)
        with connect_database(self.path) as db:
            db.execute("UPDATE reservas_stock SET estado='CONSUMIDA',fecha_cierre='2026-10-29T23:00:00Z' WHERE pedido_id=?", (resultado['pedido_id'],))
        self.assertEqual(self.stock(), 3)
        self.assertEqual(obtener_pedido(resultado['pedido_id'], self.path)['items'][0]['reservada'], 0)
        with self.assertRaises(sqlite3.IntegrityError), connect_database(self.path) as db:
            db.execute("UPDATE reservas_stock SET estado='CONSUMIDA' WHERE pedido_id=?", (resultado['pedido_id'],))
        self.assertEqual(self.stock(), 3)

    def test_reiniciar_no_borra_pedidos_ni_crea_otro_sistema(self):
        resultado = registrar_pedido(solicitud(), self.path)
        iniciar_modulo(self.path)
        self.assertEqual(self.scalar('SELECT count(*) FROM pedidos'), 1)
        self.assertEqual(self.scalar("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='s2_pedidos'"), 0)
        self.assertEqual(self.scalar('PRAGMA user_version'), 3)
        self.assertEqual(obtener_pedido(resultado['pedido_id'], self.path)['estado'], 'ASIGNADO')
        self.assertIsNone(obtener_pedido(999, self.path))

    def test_base_v2_sin_historial_tambien_funciona(self):
        self.path = self.path.parent / 'v2.sqlite3'
        initialize_database(self.path, demo=True)
        migrar(self.path, hasta=2)
        iniciar_modulo(self.path)
        self.assertEqual(registrar_pedido(solicitud(), self.path)['estado'], 'ASIGNADO')
        self.assertEqual(self.scalar('PRAGMA user_version'), 2)

    def test_base_con_pedidos_provisionales_exige_conciliacion(self):
        legacy = self.path.parent / 'legacy.sqlite3'
        initialize_database(legacy, demo=True)
        iniciar_modulo(legacy)
        configurar_capacidad('DEMO-NORTE', 10, legacy)
        registrar_pedido(solicitud(), legacy)
        migrar(legacy, hasta=2)
        with self.assertRaisesRegex(ModuloNoInicializado, 'provisionales'):
            iniciar_modulo(legacy)
        with self.assertRaises(ModuloNoInicializado):
            registrar_pedido(solicitud(), legacy)
        with connect_database(legacy) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM s2_pedidos').fetchone()[0], 1)
            self.assertEqual(db.execute('SELECT count(*) FROM pedidos').fetchone()[0], 0)

    def test_cli_real_registra_y_consulta_en_esquema_oficial(self):
        import json
        import subprocess
        import sys
        command = [sys.executable, '-m', 'src.backend.pedidos_s2_cli', '--db', str(self.path)]
        result = subprocess.run(command + ['registrar', '--cliente', 'Cliente CLI', '--lat', '-12', '--lon', '-77.05', '--item', 'DEMO-A:2'], capture_output=True, text=True, check=True)
        pedido = json.loads(result.stdout)
        result = subprocess.run(command + ['consultar', '--pedido', str(pedido['pedido_id'])], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout)['cliente'], 'Cliente CLI')
        self.assertEqual(self.scalar('SELECT count(*) FROM pedidos'), 1)
