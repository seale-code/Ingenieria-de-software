"""S3-05: expositor y cliente en Chromium, HTTP real y SQLite temporal v4."""
import os
import tempfile
import threading
import unittest
from pathlib import Path
from uuid import uuid4

from playwright.async_api import async_playwright, expect
from werkzeug.serving import make_server

from src.backend.app import create_app
from src.backend.pedidos_s2 import iniciar_modulo, registrar_pedido
from src.backend.repartidores_s3 import registrar_repartidor
from src.database.database import initialize_database, connect_database
from src.database.migrate_josue import migrar


class OperacionesBrowserTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / 'demo.sqlite3'
        initialize_database(self.path,demo=True)
        migrar(self.path,hasta=4)
        iniciar_modulo(self.path)
        self.driver = registrar_repartidor('DEMO-REP','Repartidor de prueba',self.path)
        self.key = 'clave-aleatoria-de-demo-para-pruebas'
        self.server = make_server('127.0.0.1',0,create_app(self.path,demo_key=self.key),threaded=True)
        self.thread = threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)
        self.url = f'http://127.0.0.1:{self.server.server_port}'
        self.pw = await async_playwright().start()
        self.addAsyncCleanup(self.pw.stop)
        self.browser = await self.pw.chromium.launch()
        self.addAsyncCleanup(self.browser.close)
        self.page = await self.browser.new_page(viewport={'width':1366,'height':950})
        self.errors = []
        self.page.on('pageerror',lambda e:self.errors.append(str(e)))

    def stop_server(self):
        self.server.shutdown(); self.thread.join(timeout=5); self.server.server_close()

    async def asyncTearDown(self):
        self.assertEqual(self.errors,[])

    def order(self):
        token = str(uuid4())
        result = registrar_pedido(dict(cliente='Cliente ficticio',latitud=-12.0,longitud=-77.05,
            items=[dict(producto_codigo='DEMO-A',cantidad=2)]),self.path,confirmacion_id=token)
        return result['pedido_id'],'WEB-'+token

    async def login(self):
        await self.page.goto(self.url+'/operaciones')
        await expect(self.page.locator('#login-panel')).to_be_visible()
        await self.page.locator('#demo-key').fill(self.key)
        await self.page.locator('#login-button').click()
        await expect(self.page.locator('#workspace')).to_be_visible()
        await expect(self.page.locator('#refresh')).to_be_enabled()

    async def step(self,label):
        await self.page.get_by_role('button',name=label,exact=True).click()
        await expect(self.page.locator('#ops-message')).not_to_contain_text('Guardando')
        await expect(self.page.locator('#refresh')).to_be_enabled()

    async def ready(self):
        await self.step('Iniciar preparación')
        await self.step('Marcar como preparado')
        await self.page.locator('#driver-select').select_option(str(self.driver['id']))
        await self.step('Asignar repartidor')

    async def screenshot(self,name):
        if os.environ.get('EVIDENCE_DIR'):
            path = Path(os.environ['EVIDENCE_DIR']); path.mkdir(parents=True,exist_ok=True)
            await self.page.screenshot(path=str(path/name),full_page=True)

    async def test_pedido_web_panel_y_seguimiento_hasta_entregado(self):
        await self.page.goto(self.url+'/pedido')
        await expect(self.page.locator('#edit-view')).to_be_visible()
        await self.page.locator('.order-product').select_option('DEMO-A')
        await self.page.locator('.order-quantity').fill('2')
        await self.page.locator('#customer').fill('Cliente ficticio')
        await self.page.locator('#reference').select_option('DEMO-NORTE')
        await self.page.locator('#review-order').click()
        await self.page.locator('#confirm-order').click()
        await expect(self.page.locator('#success-view')).to_be_visible()
        code = (await self.page.locator('#order-tracking-code').inner_text()).split(': ')[1]
        # Cliente en contexto separado: no comparte la sesión del expositor.
        context = await self.browser.new_context()
        self.addAsyncCleanup(context.close)
        customer = await context.new_page()
        await customer.goto(self.url+'/seguimiento#'+code)
        await expect(customer.locator('#tracking-state')).to_have_text('Asignado')
        await self.login()
        await self.ready()
        await self.step('Registrar salida')
        await customer.locator('#tracking-button').click()
        await expect(customer.locator('#tracking-state')).to_have_text('En camino')
        await self.step('Confirmar entrega')
        await expect(self.page.locator('.detail-heading .state-badge')).to_have_text('Entregado')
        await expect(self.page.locator('#metric-done')).to_have_text('1')
        await expect(self.page.locator('.history-list li')).to_have_count(5)
        await self.screenshot('operaciones-entregado.png')
        await customer.locator('#tracking-button').click()
        await expect(customer.locator('#tracking-state')).to_have_text('Entregado')
        await expect(customer.locator('#tracking-history li')).to_have_count(5)
        await expect(customer.locator('#tracking-progress .complete')).to_have_count(5)
        if os.environ.get('EVIDENCE_DIR'):
            dest = Path(os.environ['EVIDENCE_DIR']); dest.mkdir(parents=True,exist_ok=True)
            await customer.screenshot(path=str(dest/'seguimiento-entregado.png'),full_page=True)
        self.assertEqual(customer.url,self.url+'/seguimiento')
        self.assertEqual((await customer.request.get(self.url+'/api/demo/pedidos')).status,401)
        with connect_database(self.path) as db:
            self.assertEqual(db.execute("SELECT cantidad FROM inventario WHERE producto_id=(SELECT id FROM productos WHERE codigo='DEMO-A') AND sucursal_id=(SELECT id FROM sucursales WHERE codigo='DEMO-NORTE')").fetchone()[0],3)

    async def test_cancelar_requiere_confirmacion_y_actualiza_seguimiento(self):
        _,code = self.order()
        await self.login()
        await self.page.get_by_role('button',name='Cancelar pedido',exact=True).click()
        await expect(self.page.locator('#cancel-dialog')).to_be_visible()
        await self.page.get_by_role('button',name='Volver',exact=True).click()
        await expect(self.page.locator('.detail-heading .state-badge')).to_have_text('Asignado')
        await self.page.get_by_role('button',name='Cancelar pedido',exact=True).click()
        await self.page.get_by_role('button',name='Confirmar cancelación',exact=True).click()
        await expect(self.page.locator('.detail-heading .state-badge')).to_have_text('Cancelado')
        await expect(self.page.locator('.products-table')).to_contain_text('Reserva liberada')
        await self.page.goto(self.url+'/seguimiento#'+code)
        await expect(self.page.locator('#tracking-state')).to_have_text('Cancelado')
        await expect(self.page.locator('#tracking-progress')).to_be_hidden()

    async def test_incidencias_completas_y_texto_sin_ejecutar_html(self):
        self.order()
        await self.login()
        await self.page.get_by_text('+ Reportar una incidencia',exact=True).click()
        await self.page.locator('#incident-description').fill('<img src=x onerror=alert(1)> problema ficticio')
        await self.step('Registrar incidencia')
        await expect(self.page.locator('.incident-card')).to_contain_text('<img src=x onerror=alert(1)>')
        self.assertEqual(await self.page.locator('.incident-card img').count(),0)
        await self.step('Iniciar revisión')
        await self.page.locator('#resolution-1').fill('Solución ficticia comunicada y registrada.')
        await self.step('Resolver incidencia')
        await expect(self.page.locator('.incident-card .state-badge')).to_have_text('Resuelta')
        await expect(self.page.locator('#metric-incidents')).to_have_text('0')
        await self.screenshot('operaciones-incidencia-resuelta.png')

    async def test_clave_incorrecta_sesion_persistente_y_salida(self):
        self.order()
        await self.page.goto(self.url+'/operaciones')
        await self.page.locator('#demo-key').fill('incorrecta')
        await self.page.locator('#login-button').click()
        await expect(self.page.locator('#ops-message')).to_contain_text('no es correcta')
        await expect(self.page.locator('#workspace')).to_be_hidden()
        await self.page.locator('#demo-key').fill(self.key)
        await self.page.locator('#login-button').click()
        await expect(self.page.locator('#workspace')).to_be_visible()
        await expect(self.page.locator('#refresh')).to_be_enabled()
        await self.page.reload()
        await expect(self.page.locator('#workspace')).to_be_visible()
        await expect(self.page.locator('#refresh')).to_be_enabled()
        await self.page.locator('#logout').click()
        await expect(self.page.locator('#login-panel')).to_be_visible()
        await expect(self.page.locator('#order-detail')).to_be_empty()
        await self.page.reload()
        await expect(self.page.locator('#login-panel')).to_be_visible()

    async def test_salida_aceptada_con_respuesta_perdida_se_recupera(self):
        self.order(); await self.login(); await self.ready()
        async def accepted_lost(route):
            await route.fetch(); await route.abort()
        await self.page.route('**/api/demo/pedidos/1/acciones',accepted_lost,times=1)
        await self.step('Registrar salida')
        await expect(self.page.locator('#ops-message')).to_contain_text('No pudimos comprobar')
        await self.page.locator('#refresh').click()
        await expect(self.page.get_by_role('button',name='Confirmar entrega',exact=True)).to_be_visible()
        await expect(self.page.locator('.history-list li')).to_have_count(4)
        with connect_database(self.path) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM reservas_stock WHERE estado='CONSUMIDA'").fetchone()[0],1)

    async def test_bandeja_vacia_busqueda_y_vista_movil(self):
        await self.login()
        await expect(self.page.locator('#inbox-empty')).to_be_visible()
        await expect(self.page.get_by_text('Todo empieza con un pedido')).to_be_visible()
        self.order()
        await self.page.locator('#refresh').click()
        await expect(self.page.locator('.order-row')).to_have_count(1)
        await self.page.locator('#order-search').fill('inexistente')
        await expect(self.page.locator('#inbox-empty')).to_be_visible()
        await self.page.locator('#order-search').fill('ficticio')
        await expect(self.page.locator('.order-row')).to_have_count(1)
        for width,height in [(1366,950),(390,844),(320,780)]:
            await self.page.set_viewport_size({'width':width,'height':height})
            self.assertTrue(await self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            await expect(self.page.get_by_role('button',name='Iniciar preparación',exact=True)).to_be_enabled()
            await self.screenshot(f'operaciones-{width}.png')

    async def test_catalogo_enlaza_producto_preseleccionado(self):
        await self.page.goto(self.url)
        await expect(self.page.locator('.product')).to_have_count(3)
        await self.page.locator('.product-order').first.click()
        await expect(self.page.locator('.order-product')).to_have_value('DEMO-A')
        await self.page.goto(self.url+'/pedido?producto=NO-EXISTE')
        await expect(self.page.locator('#edit-view')).to_be_visible()
        await expect(self.page.locator('.order-product')).to_have_value('')
