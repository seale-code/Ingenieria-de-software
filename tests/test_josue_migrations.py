"""Pruebas de integración SQLite para Issues #21 y #19 (Sprint 2 y Sprint 3)."""
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from src.database.migrate_josue import migrar

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_V1 = ROOT / 'src/database/schema.sql'

class MigracionesJosueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.archivo = Path(self.temp.name) / 'inkafarma.sqlite3'
        # Es importante cerrar antes de borrar el directorio temporal en Windows.
        with closing(sqlite3.connect(self.archivo)) as con, con:
            con.execute('PRAGMA foreign_keys = ON')
            con.executescript(SCHEMA_V1.read_text(encoding='utf-8'))
            con.execute("INSERT INTO categorias(codigo,nombre) VALUES('CAT','Medicamentos de prueba')")
            con.execute("INSERT INTO productos(codigo,nombre,categoria_id) VALUES('P-1','Producto ficticio',1)")
            con.execute("INSERT INTO sucursales(codigo,nombre,latitud,longitud) VALUES('S-1','Sucursal ficticia',-12.1,-77.1)")
            con.execute("INSERT INTO sucursales(codigo,nombre,latitud,longitud) VALUES('S-2','Otra sucursal',-12.2,-77.2)")
            con.execute('INSERT INTO inventario(producto_id,sucursal_id,cantidad) VALUES(1,1,5)')
            con.execute('INSERT INTO inventario(producto_id,sucursal_id,cantidad) VALUES(1,2,4)')
        self.assertEqual(migrar(self.archivo), [2, 3])
        self.con = sqlite3.connect(self.archivo)
        self.con.execute('PRAGMA foreign_keys = ON')
        self.addCleanup(self.con.close)

    def crear_pedido(self, codigo='PED-1', sucursal=1, cantidad=3):
        cursor = self.con.execute('INSERT INTO pedidos(codigo,sucursal_id) VALUES(?, ?)', (codigo, sucursal))
        pedido_id = cursor.lastrowid
        self.con.execute('INSERT INTO detalles_pedido(pedido_id,producto_id,cantidad) VALUES(?,?,?)',
                         (pedido_id, 1, cantidad))
        return pedido_id

    def reservar(self, pedido_id, cantidad=3, sucursal=1):
        return self.con.execute('INSERT INTO reservas_stock(pedido_id,producto_id,sucursal_id,cantidad) VALUES(?,?,?,?)',
                                (pedido_id, 1, sucursal, cantidad)).lastrowid

    def test_migracion_idempotente_conserva_datos_sprint1(self):
        self.assertEqual(migrar(self.archivo), [])
        self.assertEqual(self.con.execute('PRAGMA user_version').fetchone()[0], 3)
        self.assertEqual(self.con.execute('SELECT cantidad FROM inventario WHERE producto_id=1 AND sucursal_id=1').fetchone()[0], 5)

    def test_reserva_valida_y_no_sobreventa(self):
        a = self.crear_pedido('P-A', cantidad=3)
        self.reservar(a)
        b = self.crear_pedido('P-B', cantidad=3)
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'Stock insuficiente'):
            self.reservar(b)
        self.assertEqual(self.con.execute('SELECT COUNT(*) FROM reservas_stock').fetchone()[0], 1)

    def test_reservas_no_pueden_superar_stock_si_se_modifica_inventario(self):
        pedido = self.crear_pedido()
        self.reservar(pedido)
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'reservado'):
            self.con.execute('UPDATE inventario SET cantidad=2 WHERE producto_id=1 AND sucursal_id=1')
        self.assertEqual(self.con.execute('SELECT cantidad FROM inventario WHERE producto_id=1 AND sucursal_id=1').fetchone()[0], 5)

    def test_liberar_reserva_permite_nueva_reserva(self):
        a = self.crear_pedido('P-A', cantidad=5)
        self.reservar(a, cantidad=5)
        self.con.execute("UPDATE reservas_stock SET estado='LIBERADA', fecha_cierre=CURRENT_TIMESTAMP WHERE pedido_id=?", (a,))
        b = self.crear_pedido('P-B', cantidad=5)
        self.reservar(b, cantidad=5)
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM reservas_stock WHERE estado='ACTIVA'").fetchone()[0], 1)

    def test_consumir_reserva_descuenta_stock_una_sola_vez(self):
        pedido = self.crear_pedido()
        self.reservar(pedido)
        self.con.execute("UPDATE reservas_stock SET estado='CONSUMIDA', fecha_cierre=CURRENT_TIMESTAMP WHERE pedido_id=?", (pedido,))
        self.assertEqual(self.con.execute('SELECT cantidad FROM inventario WHERE producto_id=1 AND sucursal_id=1').fetchone()[0], 2)
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'no permitida'):
            self.con.execute("UPDATE reservas_stock SET estado='CONSUMIDA' WHERE pedido_id=?", (pedido,))
        self.assertEqual(self.con.execute('SELECT cantidad FROM inventario WHERE producto_id=1 AND sucursal_id=1').fetchone()[0], 2)

    def test_relaciones_cantidad_y_sucursal_protegidas(self):
        pedido = self.crear_pedido(cantidad=3)
        with self.assertRaises(sqlite3.IntegrityError):
            self.reservar(pedido, cantidad=4)
        with self.assertRaises(sqlite3.IntegrityError):
            self.reservar(pedido, cantidad=3, sucursal=2)
        self.reservar(pedido)
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute('UPDATE detalles_pedido SET cantidad=1 WHERE pedido_id=?', (pedido,))
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute('DELETE FROM reservas_stock WHERE pedido_id=?', (pedido,))

    def test_no_se_puede_reservar_pedido_cancelado(self):
        pedido = self.crear_pedido()
        self.con.execute("UPDATE pedidos SET estado='CANCELADO' WHERE id=?", (pedido,))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'cerrado'):
            self.reservar(pedido)

    def test_historial_creacion_y_cambios_sin_duplicaciones(self):
        pedido = self.crear_pedido()
        self.con.execute("UPDATE pedidos SET estado='ASIGNADO' WHERE id=?", (pedido,))
        self.con.execute("UPDATE pedidos SET estado='ASIGNADO' WHERE id=?", (pedido,))
        self.con.execute("UPDATE pedidos SET estado='EN_PREPARACION' WHERE id=?", (pedido,))
        historial = self.con.execute('SELECT estado_anterior,estado_nuevo FROM historial_estados WHERE pedido_id=? ORDER BY id',
                                    (pedido,)).fetchall()
        self.assertEqual(historial, [(None,'REGISTRADO'),('REGISTRADO','ASIGNADO'),('ASIGNADO','EN_PREPARACION')])
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute('DELETE FROM historial_estados WHERE pedido_id=?', (pedido,))

    def test_entrega_asocia_pedido_repartidor_y_fechas(self):
        pedido = self.crear_pedido()
        repartidor = self.con.execute("INSERT INTO repartidores(codigo,nombre) VALUES('REP-DEMO','Repartidor prueba')").lastrowid
        self.con.execute('INSERT INTO entregas(pedido_id,repartidor_id) VALUES(?,?)', (pedido, repartidor))
        self.con.execute("UPDATE entregas SET estado='EN_CAMINO', fecha_salida='2026-10-22T12:00:00Z' WHERE pedido_id=?", (pedido,))
        self.con.execute("UPDATE entregas SET estado='ENTREGADA', fecha_entrega='2026-10-22T13:00:00Z' WHERE pedido_id=?", (pedido,))
        row = self.con.execute('SELECT estado,fecha_salida,fecha_entrega FROM entregas WHERE pedido_id=?', (pedido,)).fetchone()
        self.assertEqual(row[0], 'ENTREGADA')
        self.assertIsNotNone(row[1])
        self.assertIsNotNone(row[2])
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute('INSERT INTO entregas(pedido_id,repartidor_id) VALUES(?,?)', (pedido,repartidor))

    def test_entrega_rechaza_incoherencia_de_fechas(self):
        pedido = self.crear_pedido()
        rep = self.con.execute("INSERT INTO repartidores(codigo,nombre) VALUES('REP-01','Persona de prueba')").lastrowid
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute("INSERT INTO entregas(pedido_id,repartidor_id,estado) VALUES(?,?,'ENTREGADA')", (pedido,rep))

    def test_conserva_integridad_relacional(self):
        self.assertEqual(self.con.execute('PRAGMA foreign_key_check').fetchall(), [])

    def test_rechaza_bases_ajenas(self):
        otra = Path(self.temp.name) / 'ajena.sqlite3'
        with closing(sqlite3.connect(otra)) as con, con:
            con.execute('CREATE TABLE ejemplo (id INTEGER)')
        with self.assertRaises(ValueError):
            migrar(otra)
        with closing(sqlite3.connect(otra)) as con, con:
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0], 0)
            self.assertEqual(con.execute('SELECT COUNT(*) FROM sqlite_master WHERE name="ejemplo"').fetchone()[0], 1)

if __name__ == '__main__':
    unittest.main()
