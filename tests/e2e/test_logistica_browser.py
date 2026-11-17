"""Logística v6 en Chromium: reasignación, inventario y solicitudes inciertas."""
import os
from pathlib import Path
import tempfile
import threading
import unittest
from uuid import uuid4

from playwright.async_api import async_playwright,expect
from werkzeug.serving import make_server

from scripts.iniciar_tienda import preparar_tienda
from src.backend.app import create_app
from src.backend.inventario import consultar_inventario
from src.backend.logistica import resolver_falta_atencion
from src.backend.preparacion_pedidos import obtener_pedido_preparacion
from src.database.database import connect_database


class LogisticaBrowserTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        temp=tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.path=Path(temp.name)/'logistica.sqlite3'; preparar_tienda(self.path)
        self.key='clave-de-pruebas-para-operaciones'; app=create_app(self.path,operations_key=self.key)
        cliente=app.test_client()
        quote=cliente.post('/api/pedidos/cotizacion',json={'items':[{'producto_codigo':'023735','cantidad':2}]}).json['cotizacion']
        self.token=str(uuid4())
        self.order=cliente.post('/api/pedidos',json=dict(cliente='Cliente de prueba',confirmacion_id=self.token,
            items=[dict(producto_codigo='023735',cantidad=2)],comercio=dict(cotizacion_id=quote['cotizacion_id'],
                telefono='987654321',direccion='Calle de prueba 123',distrito='MIRAFLORES'))).json['pedido']['pedido_id']
        self.server=make_server('127.0.0.1',0,app,threaded=True)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True); self.thread.start(); self.addCleanup(self.stop)
        self.url=f'http://127.0.0.1:{self.server.server_port}'
        self.pw=await async_playwright().start(); self.addAsyncCleanup(self.pw.stop)
        self.browser=await self.pw.chromium.launch(); self.addAsyncCleanup(self.browser.close)
        self.page=await self.browser.new_page(viewport={'width':1440,'height':1000})
        self.errors=[]; self.page.on('pageerror',lambda e:self.errors.append(str(e)))

    def stop(self):
        self.server.shutdown(); self.thread.join(timeout=5); self.server.server_close()

    async def asyncTearDown(self): self.assertEqual(self.errors,[])

    async def login(self):
        await self.page.goto(self.url+'/operaciones')
        await self.page.locator('#demo-key').fill(self.key); await self.page.locator('#login-button').click()
        await expect(self.page.locator('#refresh')).to_be_enabled()
        await expect(self.page.locator('#order-detail')).to_contain_text('Miraflores')

    async def capture(self,name):
        if os.environ.get('EVIDENCE_DIR'):
            destino=Path(os.environ['EVIDENCE_DIR']); destino.mkdir(parents=True,exist_ok=True)
            await self.page.screenshot(path=str(destino/name),full_page=True)

    def saldo(self,branch):
        return next(f for f in consultar_inventario(self.path)['existencias']
            if f['producto_codigo']=='023735' and f['sucursal_codigo']==branch)

    async def open_movement(self):
        await self.page.locator('#tab-inventory').click()
        await self.page.locator('#inventory-search').fill('023735')
        await self.page.locator('#inventory-rows button').click()
        await expect(self.page.locator('#movement-dialog')).to_be_visible()

    async def test_reasignar_preparar_despachar_y_seguir_el_mismo_pedido(self):
        await self.login()
        await self.page.get_by_text('La sucursal no puede atender',exact=True).click()
        await self.page.locator('#reassignment-reason').fill('Producto no localizado durante la verificación de existencias.')
        await self.page.get_by_role('button',name='Buscar otra sucursal',exact=True).click()
        await expect(self.page.locator('#ops-message')).to_contain_text('Pedido reasignado a San Isidro')
        await expect(self.page.locator('.detail-meta')).to_contain_text('San Isidro')
        await expect(self.page.locator('#order-detail .products-table tbody tr')).to_have_count(1)
        await self.capture('reasignacion-sucursal.png')
        for label in ['Iniciar preparación','Marcar como preparado']:
            await self.page.get_by_role('button',name=label,exact=True).click()
            await expect(self.page.locator('#refresh')).to_be_enabled()
        await self.page.locator('#driver-select').select_option(index=1)
        for label in ['Asignar repartidor','Registrar salida','Confirmar entrega']:
            await self.page.get_by_role('button',name=label,exact=True).click()
            await expect(self.page.locator('#refresh')).to_be_enabled()
        self.assertEqual(self.saldo('MIRAFLORES')['fisico'],18)
        self.assertEqual(self.saldo('SAN-ISIDRO')['fisico'],16)
        await self.page.goto(self.url+'/seguimiento#WEB-'+self.token)
        await expect(self.page.locator('#tracking-state')).to_have_text('Entregado')
        await expect(self.page.locator('#tracking-history')).to_contain_text('Reasignamos tu pedido a San Isidro')
        self.assertNotIn('987654321',await self.page.locator('body').inner_text())
        await self.capture('seguimiento-reasignado.png')

    async def test_entrada_conteo_y_proteccion_de_reservas_en_interfaz(self):
        await self.login(); await self.open_movement()
        await self.page.locator('#movement-quantity').fill('5')
        await self.page.locator('#movement-reason').fill('Recepción de mercadería según guía 001-024.')
        await self.page.locator('#movement-save').click()
        await expect(self.page.locator('#movement-dialog')).not_to_be_visible()
        await expect(self.page.locator('#inventory-rows')).to_contain_text('23')
        self.assertEqual(self.saldo('MIRAFLORES')['disponible'],21)
        await self.page.locator('#inventory-rows button').click()
        await self.page.locator('#movement-type').select_option('AJUSTE')
        await self.page.locator('#movement-quantity').fill('1')
        await self.page.locator('#movement-reason').fill('Conteo físico al cierre del turno.')
        await self.page.locator('#movement-save').click()
        await expect(self.page.locator('#movement-message')).to_contain_text('2 unidades reservadas')
        await self.page.locator('#movement-quantity').fill('20')
        await self.page.locator('#movement-save').click()
        await expect(self.page.locator('#movement-dialog')).not_to_be_visible()
        self.assertEqual(self.saldo('MIRAFLORES')['fisico'],20)
        await self.capture('inventario-movimientos.png')

    async def test_respuesta_perdida_se_reintenta_con_la_misma_clave_sin_doble_entrada(self):
        await self.login(); await self.open_movement()
        await self.page.locator('#movement-quantity').fill('5')
        await self.page.locator('#movement-reason').fill('Recepción con respuesta interrumpida.')
        async def perder_respuesta(route):
            await route.fetch(); await route.abort('failed')
        await self.page.route('**/api/demo/inventario/movimientos',perder_respuesta,times=1)
        await self.page.locator('#movement-save').click()
        await expect(self.page.locator('#movement-message')).to_contain_text('Reintenta con los mismos datos')
        await expect(self.page.locator('#movement-save')).to_be_enabled()
        await self.page.locator('#movement-save').click()
        await expect(self.page.locator('#movement-dialog')).not_to_be_visible()
        await expect(self.page.locator('#ops-message')).to_contain_text('ya estaba registrado')
        self.assertEqual(self.saldo('MIRAFLORES')['fisico'],23)
        with connect_database(self.path,read_only=True) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM movimientos_inventario WHERE tipo='ENTRADA'").fetchone()[0],1)

    async def test_pantalla_obsoleta_no_acepta_sucursal_que_cambio(self):
        await self.login()
        detalle=obtener_pedido_preparacion(self.order,self.path)
        resolver_falta_atencion(self.order,detalle['logistica']['asignacion_id'],'Sucursal sin existencias suficientes.',
                               str(uuid4()),db_path=self.path)
        await self.page.get_by_role('button',name='Iniciar preparación',exact=True).click()
        await expect(self.page.locator('#ops-message')).to_contain_text('Actualiza antes de continuar')
        self.assertEqual(obtener_pedido_preparacion(self.order,self.path)['estado'],'ASIGNADO')
        await self.page.locator('#refresh').click()
        await expect(self.page.locator('.detail-meta')).to_contain_text('San Isidro')

    async def test_enlace_del_panel_abre_el_seguimiento_con_el_codigo_del_pedido(self):
        await self.login()
        await self.page.get_by_role('link',name='Ver seguimiento del cliente',exact=True).click()
        await expect(self.page.locator('#tracking-state')).to_have_text('Asignado')
        self.assertEqual(self.page.url,self.url+'/seguimiento')
        self.assertEqual(await self.page.locator('#tracking-code').input_value(),'WEB-'+self.token)

    async def test_inventario_y_dialogo_funcionan_en_320_y_390_sin_desbordar(self):
        await self.login(); await self.open_movement()
        for width in [320,390]:
            await self.page.set_viewport_size({'width':width,'height':844})
            self.assertLessEqual(await self.page.evaluate('document.documentElement.scrollWidth'),width)
            await expect(self.page.locator('#movement-save')).to_be_visible()
            await self.capture(f'inventario-dialogo-{width}.png')
        await self.page.locator('#movement-close').click()
        await self.capture('inventario-390.png')


if __name__=='__main__': unittest.main()
