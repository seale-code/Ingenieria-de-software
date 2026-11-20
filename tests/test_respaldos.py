"""Recuperación real en rutas temporales; no toca la base del usuario."""
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from scripts.iniciar_tienda import preparar_tienda
from scripts.respaldo_base import copiar,verificar
from src.backend.app import create_app
from src.backend.inventario import registrar_movimiento
from src.database.database import connect_database


class RespaldosTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.path=Path(temp.name)/'tienda.sqlite3';preparar_tienda(self.path)
        cliente=create_app(self.path).test_client()
        items=[dict(producto_codigo='023735',cantidad=2)]
        cotizacion=cliente.post('/api/pedidos/cotizacion',json=dict(items=items)).json['cotizacion']
        respuesta=cliente.post('/api/pedidos',json=dict(cliente='Prueba de recuperación',confirmacion_id=str(uuid4()),
            items=items,comercio=dict(cotizacion_id=cotizacion['cotizacion_id'],telefono='987654321',
                direccion='Calle de validación 123',distrito='MIRAFLORES')))
        self.assertEqual(respuesta.status_code,200,respuesta.json)
        registrar_movimiento('023735','MIRAFLORES','ENTRADA',3,'Recepción para validar respaldo.',str(uuid4()),db_path=self.path)

    def contenido(self,path):
        with connect_database(path,read_only=True) as db:
            tablas=[f[0] for f in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
            return {t:[tuple(f) for f in db.execute(f'SELECT * FROM "{t}" ORDER BY rowid')] for t in tablas}

    def test_copia_y_restauracion_conservan_todas_las_tablas_y_reservas(self):
        backup=self.path.with_name('respaldo.sqlite3');recuperada=self.path.with_name('recuperada.sqlite3')
        self.assertEqual(copiar(self.path,backup)['esquema'],6)
        copiar(backup,recuperada)
        self.assertEqual(self.contenido(self.path),self.contenido(recuperada))
        self.assertEqual(verificar(recuperada)['integridad'],'ok')

    def test_no_sobrescribe_destino_existente(self):
        destino=self.path.with_name('existente.txt');destino.write_text('conservar')
        with self.assertRaises(FileExistsError): copiar(self.path,destino)
        self.assertEqual(destino.read_text(),'conservar')

    def test_rechaza_misma_ruta(self):
        antes=self.path.read_bytes()
        with self.assertRaises(ValueError): copiar(self.path,self.path)
        self.assertEqual(self.path.read_bytes(),antes)

    def test_origen_ausente_no_crea_destino(self):
        destino=self.path.with_name('sin-origen.sqlite3')
        with self.assertRaises(ValueError): copiar(self.path.with_name('ausente.sqlite3'),destino)
        self.assertFalse(destino.exists())

    def test_base_ajena_no_se_copia(self):
        ajena=self.path.with_name('ajena.sqlite3');sqlite3.connect(ajena).close()
        destino=self.path.with_name('destino.sqlite3')
        with self.assertRaises(ValueError): copiar(ajena,destino)
        self.assertFalse(destino.exists())

    def test_fallo_de_validacion_final_limpia_solo_su_destino_y_conserva_origen(self):
        destino=self.path.with_name('fallo.sqlite3');antes=self.contenido(self.path)
        resultado=verificar(self.path)
        with patch('scripts.respaldo_base.verificar',side_effect=[resultado,ValueError('fallo inyectado')]):
            with self.assertRaises(ValueError): copiar(self.path,destino)
        self.assertFalse(destino.exists());self.assertEqual(self.contenido(self.path),antes)


if __name__=='__main__': unittest.main()
