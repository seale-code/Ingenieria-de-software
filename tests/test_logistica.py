"""HU02/03/09/14 sobre SQLite v6 real: reservas, concurrencia y reversión."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import patch
from uuid import uuid4

from scripts.iniciar_tienda import preparar_tienda
from src.backend.inventario import consultar_inventario, registrar_movimiento
from src.backend.logistica import (
    ErrorLogistica, configurar_plazo, fecha_utc, procesar_vencimientos, resolver_falta_atencion,
)
from src.backend.pedidos_s2 import configurar_capacidad, iniciar_modulo, obtener_pedido, registrar_pedido
from src.backend.preparacion_pedidos import (
    completar_preparacion_pedido, iniciar_preparacion_pedido, obtener_pedido_preparacion,
)
from src.backend.entregas_s3 import DatosEntregaInvalidos, registrar_entrega
from src.backend.reparto_integrado import avanzar_reparto
from src.backend.soporte_pedidos_s3 import PermisoDenegado, cancelar_pedido
from src.backend.vencimientos import vigilar_reservas
from src.database.database import connect_database, initialize_database
from src.database.migrate_josue import migrar


class LogisticaTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.path = Path(temp.name)/'operaciones.sqlite3'
        preparar_tienda(self.path)

    def pedido(self, productos=None):
        return registrar_pedido(dict(cliente='Cliente de prueba',latitud=-12.1211,longitud=-77.0294,
            items=productos or [dict(producto_codigo='023735',cantidad=2)]),self.path)['pedido_id']

    def detalle(self, pedido):
        return obtener_pedido_preparacion(pedido,self.path)

    def reasignar(self, pedido, **extra):
        datos = dict(pedido_id=pedido,asignacion_id=self.detalle(pedido)['logistica']['asignacion_id'],
            motivo='El producto no se encontró en la sucursal.',solicitud_id=str(uuid4()),db_path=self.path)
        datos.update(extra)
        return resolver_falta_atencion(**datos)

    def saldo(self, sucursal='MIRAFLORES', producto='023735'):
        return next(f for f in consultar_inventario(self.path)['existencias']
                    if f['producto_codigo']==producto and f['sucursal_codigo']==sucursal)

    def movimiento(self, tipo='ENTRADA', cantidad=3, sucursal='MIRAFLORES', **extra):
        datos = dict(producto_codigo='023735',sucursal_codigo=sucursal,tipo=tipo,cantidad=cantidad,
            motivo='Recepción de mercadería, guía 001-024.',solicitud_id=str(uuid4()),db_path=self.path)
        if tipo=='AJUSTE': datos['cantidad_esperada']=self.saldo(sucursal)['fisico']
        datos.update(extra)
        return registrar_movimiento(**datos)

    def limite(self, pedido):
        return datetime.fromisoformat(self.detalle(pedido)['logistica']['fecha_limite'].replace('Z','+00:00'))

    def snapshot(self):
        with connect_database(self.path,read_only=True) as db:
            return {t:[tuple(r) for r in db.execute(f'SELECT * FROM {t} ORDER BY 1')]
                for t in ('pedidos','reservas_stock','control_reservas','historial_asignaciones',
                          'historial_estados','incidencias_pedido','inventario','movimientos_inventario','s2_solicitudes')}

    def test_reserva_nueva_tiene_plazo_y_aceptacion_es_atomica(self):
        pedido=self.pedido(); detalle=self.detalle(pedido)
        self.assertIsNone(detalle['logistica']['aceptada_en'])
        self.assertGreater(self.limite(pedido),datetime.now(timezone.utc))
        with connect_database(self.path,read_only=True) as db:
            self.assertEqual(db.execute('SELECT fecha_vencimiento FROM reservas_stock WHERE pedido_id=?',(pedido,)).fetchone()[0],
                             detalle['logistica']['fecha_limite'])
        iniciar_preparacion_pedido(pedido,self.path,asignacion_id=detalle['logistica']['asignacion_id'])
        self.assertIsNotNone(self.detalle(pedido)['logistica']['aceptada_en'])
        self.assertEqual(procesar_vencimientos(self.path,ahora=self.limite(pedido)+timedelta(days=2)),[])
        self.assertEqual(self.saldo()['reservado'],2)

    def test_reasignacion_libera_origen_y_reserva_destino_sin_tocar_fisico(self):
        pedido=self.pedido(); respuesta=self.reasignar(pedido)
        self.assertTrue(respuesta['reasignado']); self.assertEqual(respuesta['sucursal_codigo'],'SAN-ISIDRO')
        self.assertEqual((self.saldo()['fisico'],self.saldo()['reservado']),(18,0))
        self.assertEqual((self.saldo('SAN-ISIDRO')['fisico'],self.saldo('SAN-ISIDRO')['reservado']),(18,2))
        with connect_database(self.path,read_only=True) as db:
            self.assertEqual([r[0] for r in db.execute('SELECT estado FROM reservas_stock WHERE pedido_id=? ORDER BY id',(pedido,))],['LIBERADA','ACTIVA'])
            self.assertEqual(db.execute("SELECT count(*) FROM movimientos_inventario WHERE tipo!='APERTURA'").fetchone()[0],0)
            self.assertEqual(db.execute('SELECT estado FROM incidencias_pedido').fetchone()[0],'RESUELTA')
            self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[])
        self.assertEqual(len(self.detalle(pedido)['items']),1)
        self.assertEqual(len(obtener_pedido(pedido,self.path)['items']),1)

    def test_falta_durante_preparacion_reinicia_aceptacion_en_destino(self):
        pedido=self.pedido(); iniciar_preparacion_pedido(pedido,self.path)
        self.reasignar(pedido)
        detalle=self.detalle(pedido)
        self.assertEqual(detalle['estado'],'ASIGNADO'); self.assertIsNone(detalle['logistica']['aceptada_en'])
        self.assertEqual([h['estado_nuevo'] for h in detalle['historial']],['ASIGNADO','EN_PREPARACION','ASIGNADO'])

    def test_descarta_sucursal_sin_capacidad_o_sin_todos_los_productos(self):
        pedido=self.pedido([dict(producto_codigo='023735',cantidad=2),dict(producto_codigo='073726',cantidad=1)])
        self.movimiento('AJUSTE',0,'SAN-ISIDRO',producto_codigo='073726',cantidad_esperada=self.saldo('SAN-ISIDRO','073726')['fisico'])
        self.assertEqual(self.reasignar(pedido)['sucursal_codigo'],'SURCO')

    def test_capacidad_llena_obliga_a_elegir_otra_sucursal(self):
        pedido=self.pedido(); configurar_capacidad('SAN-ISIDRO',0,self.path)
        self.assertEqual(self.reasignar(pedido)['sucursal_codigo'],'SURCO')

    def test_sin_alternativa_cancela_y_libera_en_vez_de_rebotar(self):
        pedido=self.pedido()
        configurar_capacidad('SAN-ISIDRO',0,self.path); configurar_capacidad('SURCO',0,self.path)
        respuesta=self.reasignar(pedido)
        self.assertFalse(respuesta['reasignado']); self.assertEqual(respuesta['estado_nuevo'],'CANCELADO')
        self.assertEqual(self.saldo()['disponible'],18)
        self.assertIsNone(self.detalle(pedido)['logistica']['fecha_limite'])

    def test_cada_sucursal_se_intenta_una_sola_vez(self):
        pedido=self.pedido(); self.reasignar(pedido); self.reasignar(pedido)
        ultimo=self.reasignar(pedido)
        self.assertFalse(ultimo['reasignado'])
        historial=self.detalle(pedido)['logistica']['historial']
        self.assertEqual(len(historial),4)
        self.assertEqual(len({h['sucursal_destino_id'] for h in historial if h['sucursal_destino_id']}),3)
        with connect_database(self.path,read_only=True) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM reservas_stock WHERE estado='ACTIVA'").fetchone()[0],0)

    def test_uuid_repetido_no_rechaza_a_la_siguiente_sucursal(self):
        pedido=self.pedido(); generacion=self.detalle(pedido)['logistica']['asignacion_id']; clave=str(uuid4())
        primero=self.reasignar(pedido,asignacion_id=generacion,solicitud_id=clave); antes=self.snapshot()
        segundo=self.reasignar(pedido,asignacion_id=generacion,solicitud_id=clave)
        self.assertTrue(segundo['reintento']); self.assertEqual(segundo['asignacion_id'],primero['asignacion_id'])
        self.assertEqual(self.snapshot(),antes)
        with self.assertRaises(ErrorLogistica):
            self.reasignar(pedido,asignacion_id=generacion,solicitud_id=clave,motivo='Un motivo distinto al original.')

    def test_generacion_anterior_no_puede_preparar_ni_rechazar_destino(self):
        pedido=self.pedido(); anterior=self.detalle(pedido)['logistica']['asignacion_id']; self.reasignar(pedido)
        antes=self.snapshot()
        with self.assertRaises(ErrorLogistica): iniciar_preparacion_pedido(pedido,self.path,asignacion_id=anterior)
        with self.assertRaises(ErrorLogistica): self.reasignar(pedido,asignacion_id=anterior)
        self.assertEqual(self.snapshot(),antes)

    def test_solo_personal_de_origen_o_administracion_pueden_reasignar(self):
        pedido=self.pedido()
        for rol,actor in [('ASESOR',None),('REPARTIDOR',1),('PERSONAL_SUCURSAL',2),('SISTEMA',None)]:
            with self.subTest(rol=rol),self.assertRaises(PermisoDenegado): self.reasignar(pedido,rol=rol,actor_id=actor)
        respuesta=self.reasignar(pedido,rol='PERSONAL_SUCURSAL',actor_id=1)
        self.assertTrue(respuesta['reasignado'])

    def test_no_reasigna_un_pedido_preparado_cancelado_o_en_camino(self):
        pedido=self.pedido(); iniciar_preparacion_pedido(pedido,self.path); completar_preparacion_pedido(pedido,self.path)
        with self.assertRaises(ErrorLogistica): self.reasignar(pedido)
        registrar_entrega(pedido,1,db_path=self.path); avanzar_reparto(pedido,'EN_CAMINO','REPARTIDOR',1,self.path)
        with self.assertRaises(ErrorLogistica): self.reasignar(pedido)
        cancelado=self.pedido(); cancelar_pedido(cancelado,'ADMINISTRADOR',db_path=self.path)
        with self.assertRaises(ErrorLogistica): self.reasignar(cancelado)

    def test_v6_no_permite_crear_entrega_que_bloquee_una_asignacion_pendiente(self):
        pedido=self.pedido()
        with self.assertRaises(DatosEntregaInvalidos): registrar_entrega(pedido,1,db_path=self.path)
        self.assertTrue(self.reasignar(pedido)['reasignado'])

    def test_fallo_despues_de_liberar_revierte_todos_los_efectos(self):
        pedido=self.pedido(); antes=self.snapshot()
        with patch('src.backend.pedidos_integracion.evaluar_sucursales',side_effect=sqlite3.OperationalError('fallo inyectado')):
            with self.assertRaises(sqlite3.OperationalError): self.reasignar(pedido)
        self.assertEqual(self.snapshot(),antes)

    def test_fallo_al_reservar_destino_revierte_asignacion_e_incidencia(self):
        pedido=self.pedido()
        with connect_database(self.path) as db:
            db.execute("""CREATE TRIGGER fallo_destino BEFORE INSERT ON reservas_stock WHEN NEW.sucursal_id=2
                BEGIN SELECT RAISE(ABORT,'fallo inyectado'); END""")
        antes=self.snapshot()
        with self.assertRaises(sqlite3.IntegrityError): self.reasignar(pedido)
        self.assertEqual(self.snapshot(),antes)

    def test_cuatro_reintentos_concurrentes_solo_generan_una_reasignacion(self):
        pedido=self.pedido(); generacion=self.detalle(pedido)['logistica']['asignacion_id']; clave=str(uuid4())
        with ThreadPoolExecutor(max_workers=4) as pool:
            resultados=list(pool.map(lambda _:self.reasignar(pedido,asignacion_id=generacion,solicitud_id=clave),range(4)))
        self.assertEqual(sum(not r['reintento'] for r in resultados),1)
        self.assertEqual(len({r['asignacion_id'] for r in resultados}),1)
        self.assertEqual(self.saldo('SAN-ISIDRO')['reservado'],2)

    def test_dos_pedidos_compiten_por_el_ultimo_stock_alternativo(self):
        pedidos=[self.pedido(),self.pedido()]; self.movimiento('AJUSTE',2,'SAN-ISIDRO')
        configurar_capacidad('SURCO',0,self.path)
        with ThreadPoolExecutor(max_workers=2) as pool: resultados=list(pool.map(self.reasignar,pedidos))
        self.assertEqual(sum(r['reasignado'] for r in resultados),1)
        self.assertEqual(self.saldo('SAN-ISIDRO')['disponible'],0)
        self.assertEqual(self.saldo()['reservado'],0)

    def test_no_vence_antes_del_limite_y_si_en_el_instante_exacto(self):
        pedido=self.pedido(); limite=self.limite(pedido)
        self.assertEqual(procesar_vencimientos(self.path,ahora=limite-timedelta(milliseconds=1)),[])
        resultados=procesar_vencimientos(self.path,ahora=limite)
        self.assertEqual(len(resultados),1); self.assertEqual(resultados[0]['sucursal_codigo'],'SAN-ISIDRO')
        self.assertEqual(self.limite(pedido),limite+timedelta(minutes=15))
        self.assertEqual(procesar_vencimientos(self.path,ahora=limite),[])

    def test_no_se_puede_aceptar_una_reserva_vencida(self):
        pedido=self.pedido()
        with connect_database(self.path) as db:
            db.execute('UPDATE control_reservas SET fecha_limite=? WHERE pedido_id=?',
                       (fecha_utc(datetime.now(timezone.utc)-timedelta(seconds=1)),pedido))
        antes=self.snapshot()
        with self.assertRaises(ErrorLogistica): iniciar_preparacion_pedido(pedido,self.path)
        self.assertEqual(self.snapshot(),antes)

    def test_dos_procesos_de_vencimiento_no_duplican_intentos(self):
        pedido=self.pedido(); limite=self.limite(pedido)
        with ThreadPoolExecutor(max_workers=2) as pool:
            resultados=list(pool.map(lambda _:procesar_vencimientos(self.path,ahora=limite),range(2)))
        self.assertEqual(sum(len(r) for r in resultados),1)
        self.assertEqual(len(self.detalle(pedido)['logistica']['historial']),2)

    def test_vencimientos_terminan_cancelando_si_ninguna_sucursal_acepta(self):
        pedido=self.pedido()
        for _ in range(3): self.assertEqual(len(procesar_vencimientos(self.path,ahora=self.limite(pedido))),1)
        self.assertEqual(self.detalle(pedido)['estado'],'CANCELADO')
        self.assertEqual(procesar_vencimientos(self.path,ahora=datetime.now(timezone.utc)+timedelta(days=1)),[])

    def test_plazo_configurable_solo_afecta_asignaciones_nuevas(self):
        pedido=self.pedido(); limite=self.limite(pedido); configurar_plazo(30,self.path)
        self.assertEqual(self.limite(pedido),limite)
        nuevo=self.pedido(); self.assertGreater(self.limite(nuevo),datetime.now(timezone.utc)+timedelta(minutes=29))
        for valor in [0,1441,True,1.5]:
            with self.assertRaises(ErrorLogistica): configurar_plazo(valor,self.path)

    def test_supervisor_procesa_sin_visitas_a_la_web(self):
        pedido=self.pedido()
        with connect_database(self.path) as db:
            db.execute('UPDATE control_reservas SET fecha_limite=? WHERE pedido_id=?',
                       (fecha_utc(datetime.now(timezone.utc)-timedelta(seconds=1)),pedido))
        with vigilar_reservas(self.path,intervalo=.05):
            fin=time.monotonic()+3
            while time.monotonic()<fin and self.detalle(pedido)['sucursal_codigo']=='MIRAFLORES': time.sleep(.02)
            self.assertEqual(self.detalle(pedido)['sucursal_codigo'],'SAN-ISIDRO')

    def test_entrada_y_ajuste_actualizan_disponible_y_conservan_motivo(self):
        self.pedido(); entrada=self.movimiento(cantidad=5)
        self.assertEqual((entrada['cantidad_anterior'],entrada['cantidad_nueva']),(18,23))
        self.assertEqual(self.saldo()['disponible'],21)
        ajuste=self.movimiento('AJUSTE',20,motivo='Conteo físico documentado por inventario.')
        self.assertEqual(ajuste['variacion'],-3); self.assertEqual(self.saldo()['disponible'],18)

    def test_ajuste_no_puede_afectar_reservas_y_revierte_el_movimiento(self):
        self.pedido(); antes=self.snapshot()
        with self.assertRaises(ErrorLogistica): self.movimiento('AJUSTE',1)
        self.assertEqual(self.snapshot(),antes)

    def test_ajuste_rechaza_saldo_obsoleto(self):
        saldo=self.saldo()['fisico']; self.movimiento(cantidad=2)
        with self.assertRaises(ErrorLogistica): self.movimiento('AJUSTE',10,cantidad_esperada=saldo)
        self.assertEqual(self.saldo()['fisico'],20)

    def test_reintento_entrada_no_suma_dos_veces_incluso_despues_de_otro_movimiento(self):
        clave=str(uuid4()); primero=self.movimiento(solicitud_id=clave); self.movimiento(cantidad=1)
        antes=self.snapshot(); segundo=self.movimiento(solicitud_id=clave)
        self.assertTrue(segundo['reintento']); self.assertEqual(segundo['id'],primero['id'])
        self.assertEqual(self.snapshot(),antes)
        with self.assertRaises(ErrorLogistica): self.movimiento(cantidad=8,solicitud_id=clave)

    def test_entradas_concurrentes_no_pierden_unidades(self):
        with ThreadPoolExecutor(max_workers=4) as pool: list(pool.map(lambda _:self.movimiento(cantidad=1),range(4)))
        self.assertEqual(self.saldo()['fisico'],22)

    def test_entrada_repetida_concurrente_se_registra_una_vez(self):
        clave=str(uuid4())
        with ThreadPoolExecutor(max_workers=4) as pool:
            resultados=list(pool.map(lambda _:self.movimiento(solicitud_id=clave),range(4)))
        self.assertEqual(sum(not r['reintento'] for r in resultados),1); self.assertEqual(self.saldo()['fisico'],21)

    def test_roles_de_inventario_restringen_sucursal(self):
        for rol,actor in [('ASESOR',None),('REPARTIDOR',1),('PERSONAL_SUCURSAL',2)]:
            with self.subTest(rol=rol),self.assertRaises(PermisoDenegado): self.movimiento(rol=rol,actor_id=actor)
        self.movimiento(rol='PERSONAL_SUCURSAL',actor_id=1)
        self.assertEqual(self.saldo()['fisico'],21)

    def test_validacion_de_movimiento_no_crea_registros(self):
        antes=self.snapshot()
        for extra in [dict(cantidad=True),dict(cantidad=-1),dict(cantidad=1.5),dict(tipo='SALIDA_PEDIDO'),
                      dict(motivo='x'),dict(solicitud_id='incorrecta'),dict(tipo='AJUSTE',cantidad_esperada=None)]:
            with self.subTest(extra=extra),self.assertRaises(ErrorLogistica): self.movimiento(**extra)
        self.assertEqual(self.snapshot(),antes)

    def test_inventario_e_historial_no_admiten_cambios_sin_trazabilidad(self):
        self.pedido()
        with connect_database(self.path) as db:
            for sql in ['UPDATE inventario SET cantidad=99 WHERE producto_id=1 AND sucursal_id=1',
                        "UPDATE movimientos_inventario SET motivo='Alterado'",'DELETE FROM movimientos_inventario',
                        "UPDATE historial_asignaciones SET observacion='Alterado'",'DELETE FROM historial_asignaciones',
                        'DELETE FROM reservas_stock']:
                with self.subTest(sql=sql),self.assertRaises(sqlite3.IntegrityError): db.execute(sql)

    def test_despacho_tras_reasignar_solo_descontara_el_destino_y_una_vez(self):
        pedido=self.pedido(); self.reasignar(pedido); iniciar_preparacion_pedido(pedido,self.path)
        completar_preparacion_pedido(pedido,self.path); registrar_entrega(pedido,1,db_path=self.path)
        with ThreadPoolExecutor(max_workers=4) as pool:
            resultados=list(pool.map(lambda _:avanzar_reparto(pedido,'EN_CAMINO','REPARTIDOR',1,self.path),range(4)))
        self.assertEqual(sum(not r['reintento'] for r in resultados),1)
        self.assertEqual(self.saldo()['fisico'],18); self.assertEqual(self.saldo('SAN-ISIDRO')['fisico'],16)
        with connect_database(self.path,read_only=True) as db:
            salidas=db.execute("SELECT * FROM movimientos_inventario WHERE tipo='SALIDA_PEDIDO'").fetchall()
            self.assertEqual(len(salidas),1); self.assertEqual(salidas[0]['variacion'],-2)

    def test_fallo_en_salida_revierte_ledger_stock_fecha_e_historial(self):
        pedido=self.pedido(); iniciar_preparacion_pedido(pedido,self.path); completar_preparacion_pedido(pedido,self.path)
        registrar_entrega(pedido,1,db_path=self.path)
        with connect_database(self.path) as db:
            db.execute("""CREATE TRIGGER fallo_ledger BEFORE INSERT ON movimientos_inventario WHEN NEW.tipo='SALIDA_PEDIDO'
                BEGIN SELECT RAISE(ABORT,'fallo inyectado'); END""")
        antes=self.snapshot()
        with self.assertRaises(sqlite3.IntegrityError): avanzar_reparto(pedido,'EN_CAMINO','REPARTIDOR',1,self.path)
        self.assertEqual(self.snapshot(),antes)
        with connect_database(self.path,read_only=True) as db:
            self.assertIsNone(db.execute('SELECT fecha_salida FROM entregas WHERE pedido_id=?',(pedido,)).fetchone()[0])

    def test_reiniciar_preserva_movimientos_y_politica(self):
        self.movimiento(); configurar_plazo(20,self.path); antes=self.snapshot(); preparar_tienda(self.path)
        self.assertEqual(self.snapshot(),antes)
        with connect_database(self.path,read_only=True) as db:
            self.assertEqual(db.execute('SELECT plazo_minutos FROM politica_reservas').fetchone()[0],20)
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')

    def test_migrar_v5_preserva_reservas_cerradas_ids_stock_y_fks(self):
        path=self.path.with_name('anterior.sqlite3'); initialize_database(path,demo=True); migrar(path,hasta=5); iniciar_modulo(path)
        pedido=registrar_pedido(dict(cliente='Anterior',latitud=-12,longitud=-77.05,
            items=[dict(producto_codigo='DEMO-A',cantidad=2)]),path)['pedido_id']
        cancelar_pedido(pedido,'ADMINISTRADOR',db_path=path)
        with connect_database(path,read_only=True) as db:
            reservas=[tuple(f) for f in db.execute('SELECT * FROM reservas_stock')]
            stock=[tuple(f) for f in db.execute('SELECT * FROM inventario')]
        self.assertEqual(migrar(path,hasta=6),[6]); self.assertEqual(migrar(path,hasta=6),[])
        with connect_database(path,read_only=True) as db:
            self.assertEqual([tuple(f) for f in db.execute('SELECT * FROM reservas_stock')],reservas)
            self.assertEqual([tuple(f) for f in db.execute('SELECT * FROM inventario')],stock)
            self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[])

    def test_migracion_fallida_revierte_reconstruccion_y_version(self):
        from src.database.migrate_josue import DIRECTORY
        path=self.path.with_name('migracion.sqlite3'); initialize_database(path,demo=True); migrar(path,hasta=5)
        carpeta=self.path.parent/'sql'; carpeta.mkdir()
        (carpeta/'006_logistica_inventario.sql').write_text(
            (DIRECTORY/'006_logistica_inventario.sql').read_text()+'\nSELECT * FROM tabla_que_no_existe;')
        with patch('src.database.migrate_josue.DIRECTORY',carpeta):
            with self.assertRaises(sqlite3.OperationalError): migrar(path,hasta=6)
        with connect_database(path,read_only=True) as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],5)
            self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[])
            self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='movimientos_inventario'").fetchone())
            self.assertEqual(db.execute('SELECT sum(cantidad) FROM inventario').fetchone()[0],8)


if __name__=='__main__': unittest.main()
