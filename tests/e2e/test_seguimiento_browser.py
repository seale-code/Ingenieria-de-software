"""S3-05 / #17: navegador real -> pedido -> preparación -> seguimiento de #15."""
import asyncio
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
from src.backend.preparacion_pedidos import iniciar_preparacion_pedido, completar_preparacion_pedido
from src.database.database import connect_database, initialize_database
from src.database.migrate_josue import migrar


class SeguimientoBrowserTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / 'seguimiento.sqlite3'
        initialize_database(self.path, demo=True)
        migrar(self.path)
        iniciar_modulo(self.path)
        self.server = make_server('127.0.0.1', 0, create_app(self.path), threaded=True)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)
        self.url = f'http://127.0.0.1:{self.server.server_port}'
        self.pw = await async_playwright().start()
        self.addAsyncCleanup(self.pw.stop)
        self.browser = await self.pw.chromium.launch()
        self.addAsyncCleanup(self.browser.close)
        self.page = await self.browser.new_page(viewport={'width': 1366, 'height': 900})
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))

    def stop_server(self):
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()

    async def asyncTearDown(self):
        self.assertEqual(self.errors, [])

    def pedido(self):
        token = str(uuid4())
        result = registrar_pedido(dict(cliente='Cliente ficticio', latitud=-12.0464,
            longitud=-77.0428, items=[dict(producto_codigo='DEMO-A', cantidad=1)]),
            self.path, confirmacion_id=token)
        return result['pedido_id'], 'WEB-' + token

    async def abrir(self, codigo):
        await self.page.goto(self.url + '/seguimiento#' + codigo)
        await expect(self.page.locator('#tracking-result')).to_be_visible()

    async def confirmar_en_pantalla(self):
        await self.page.goto(self.url + '/pedido')
        await expect(self.page.locator('#edit-view')).to_be_visible()
        await self.page.locator('.order-product').select_option('DEMO-A')
        await self.page.locator('.order-quantity').fill('1')
        await self.page.locator('#customer').fill('Cliente ficticio')
        await self.page.locator('#reference').select_option('DEMO-NORTE')
        await self.page.get_by_role('button', name='Revisar pedido').click()
        await self.page.locator('#confirm-order').click()
        await expect(self.page.locator('#success-view')).to_be_visible()

    async def test_confirmacion_enlaza_pedido_correcto_sin_codigo_en_url_http(self):
        requests = []
        self.page.on('request', lambda req: requests.append(req))
        await self.confirmar_en_pantalla()
        code = (await self.page.locator('#order-tracking-code').inner_text()).split(': ')[1]
        await self.page.locator('#order-tracking-link').click()
        await expect(self.page.locator('#tracking-result')).to_be_visible()
        await expect(self.page.locator('#tracking-state')).to_have_text('Asignado')
        await expect(self.page.locator('#tracking-history li')).to_have_count(1)
        await expect(self.page.locator('#tracking-code')).to_have_value(code)
        self.assertEqual(self.page.url, self.url + '/seguimiento')
        api = [req for req in requests if req.url.endswith('/api/seguimiento')]
        self.assertEqual(len(api), 1)
        self.assertEqual(api[0].headers.get('x-codigo-pedido'), code)
        for req in requests:
            # HTTP no envía el fragmento. Tampoco lo acepta el endpoint como query.
            self.assertNotIn(code, req.url.split('#', 1)[0])

    async def test_copiar_codigo_y_crear_otro_pedido_no_reutiliza_anterior(self):
        await self.page.context.grant_permissions(['clipboard-read', 'clipboard-write'], origin=self.url)
        await self.confirmar_en_pantalla()
        first = (await self.page.locator('#order-tracking-code').inner_text()).split(': ')[1]
        await self.page.locator('#order-copy-tracking').click()
        await expect(self.page.locator('#order-copy-status')).to_contain_text('Código copiado')
        self.assertEqual(await self.page.evaluate('navigator.clipboard.readText()'), first)
        await self.page.locator('#new-order').click()
        await self.page.locator('.order-product').select_option('DEMO-A')
        await self.page.locator('.order-quantity').fill('1')
        await self.page.locator('#customer').fill('Otro cliente ficticio')
        await self.page.locator('#reference').select_option('DEMO-NORTE')
        await self.page.get_by_role('button', name='Revisar pedido').click()
        await self.page.locator('#confirm-order').click()
        await expect(self.page.locator('#success-view')).to_be_visible()
        second = (await self.page.locator('#order-tracking-code').inner_text()).split(': ')[1]
        self.assertNotEqual(first, second)
        await self.page.locator('#order-copy-tracking').click()
        await expect(self.page.locator('#order-copy-status')).to_contain_text('Código copiado')
        self.assertEqual(await self.page.evaluate('navigator.clipboard.readText()'), second)
        await self.page.locator('#order-tracking-link').click()
        await expect(self.page.locator('#tracking-title')).to_have_text('Pedido #2')

    async def test_portapapeles_bloqueado_muestra_alternativa(self):
        await self.confirmar_en_pantalla()
        await self.page.evaluate("""Object.defineProperty(navigator, 'clipboard', {
            value: {writeText: async () => { throw new Error('Permiso denegado de prueba'); }}
        })""")
        await self.page.locator('#order-copy-tracking').click()
        await expect(self.page.locator('#order-copy-status')).to_contain_text('Selecciona y copia')
        await self.page.locator('#order-tracking-link').click()
        await expect(self.page.locator('#tracking-result')).to_be_visible()

    async def test_preparacion_real_actualiza_estado_e_historial(self):
        pedido, code = self.pedido()
        await self.abrir(code)
        iniciar_preparacion_pedido(pedido, self.path)
        await self.page.locator('#tracking-button').click()
        await expect(self.page.locator('#tracking-state')).to_have_text('En preparación')
        completar_preparacion_pedido(pedido, self.path)
        await self.page.locator('#tracking-button').click()
        await expect(self.page.locator('#tracking-state')).to_have_text('Preparado')
        rows = self.page.locator('#tracking-history li')
        await expect(rows).to_have_count(3)
        texts = await rows.all_text_contents()
        self.assertTrue(all(text.startswith(label) for text, label in
                        zip(texts, ['Asignado', 'En preparación', 'Preparado'])))
        if os.environ.get('EVIDENCE_DIR'):
            dest = Path(os.environ['EVIDENCE_DIR'])
            dest.mkdir(parents=True, exist_ok=True)
            await self.page.screenshot(path=str(dest / 'seguimiento-preparado.png'), full_page=True)

    async def test_codigo_incorrecto_inexistente_y_corregir(self):
        _, code = self.pedido()
        await self.page.goto(self.url + '/seguimiento')
        for value, message in [('1', 'Introduce el código completo'),
                ('WEB-' + str(uuid4()), 'No encontramos ese pedido')]:
            await self.page.locator('#tracking-code').fill(value)
            await self.page.locator('#tracking-button').click()
            await expect(self.page.locator('#tracking-message')).to_contain_text(message)
            await expect(self.page.locator('#tracking-result')).to_be_hidden()
        await self.page.locator('#tracking-code').fill(code)
        await self.page.locator('#tracking-button').click()
        await expect(self.page.locator('#tracking-state')).to_have_text('Asignado')

    async def test_desconexion_oculta_datos_viejos_y_permite_reintento(self):
        _, code = self.pedido()
        await self.abrir(code)
        async def offline(route):
            await route.abort()
        await self.page.route('**/api/seguimiento', offline)
        await self.page.locator('#tracking-button').click()
        await expect(self.page.locator('#tracking-message')).to_contain_text('No pudimos conectar')
        await expect(self.page.locator('#tracking-result')).to_be_hidden()
        await expect(self.page.locator('#tracking-button')).to_be_enabled()
        await expect(self.page.locator('#tracking-code')).to_have_value(code)
        await self.page.unroute('**/api/seguimiento', offline)
        await self.page.locator('#tracking-button').click()
        await expect(self.page.locator('#tracking-result')).to_be_visible()

    async def test_carga_y_error_503_recuperable(self):
        _, code = self.pedido()
        await self.page.goto(self.url + '/seguimiento')
        reached, release = asyncio.Event(), asyncio.Event()
        async def unavailable(route):
            reached.set()
            await release.wait()
            await route.fulfill(status=503, content_type='application/json',
                body='{"error":"Servicio temporalmente no disponible"}')
        await self.page.route('**/api/seguimiento', unavailable)
        await self.page.locator('#tracking-code').fill(code)
        await self.page.locator('#tracking-button').click()
        await asyncio.wait_for(reached.wait(), 10)
        try:
            await expect(self.page.locator('#tracking-message')).to_contain_text('Consultando')
            await expect(self.page.locator('#tracking-button')).to_be_disabled()
            self.assertTrue(await self.page.locator('#tracking-code').evaluate('e => e.readOnly'))
        finally:
            release.set()
        await expect(self.page.locator('#tracking-message')).to_contain_text('Servicio temporalmente')
        await self.page.unroute('**/api/seguimiento', unavailable)
        await self.page.locator('#tracking-button').click()
        await expect(self.page.locator('#tracking-result')).to_be_visible()

    async def test_vista_movil_confirmacion_y_seguimiento_sin_desbordar(self):
        await self.page.set_viewport_size({'width': 390, 'height': 844})
        await self.confirmar_en_pantalla()
        self.assertTrue(await self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        await self.page.locator('#order-tracking-link').click()
        await expect(self.page.locator('#tracking-result')).to_be_visible()
        for width, height in [(390, 844), (1366, 900)]:
            await self.page.set_viewport_size({'width': width, 'height': height})
            self.assertTrue(await self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            await self.page.locator('#tracking-code').focus()
            await self.page.keyboard.press('Tab')
            await expect(self.page.locator('#tracking-button')).to_be_focused()
            if os.environ.get('EVIDENCE_DIR'):
                dest = Path(os.environ['EVIDENCE_DIR'])
                dest.mkdir(parents=True, exist_ok=True)
                await self.page.screenshot(path=str(dest / f'seguimiento-{width}.png'), full_page=True)

    async def test_respuesta_confirmacion_perdida_recupera_mismo_seguimiento(self):
        async def accepted_but_lost(route):
            await route.fetch()
            await route.abort()
        await self.page.route('**/api/pedidos', accepted_but_lost, times=1)
        await self.page.goto(self.url + '/pedido')
        await expect(self.page.locator('#edit-view')).to_be_visible()
        await self.page.locator('.order-product').select_option('DEMO-A')
        await self.page.locator('.order-quantity').fill('1')
        await self.page.locator('#customer').fill('Cliente ficticio')
        await self.page.locator('#reference').select_option('DEMO-NORTE')
        await self.page.get_by_role('button', name='Revisar pedido').click()
        await self.page.locator('#confirm-order').click()
        await expect(self.page.locator('#confirm-order')).to_have_text('Comprobar confirmación')
        await self.page.locator('#confirm-order').click()
        await expect(self.page.locator('#success-view')).to_be_visible()
        await self.page.locator('#order-tracking-link').click()
        await expect(self.page.locator('#tracking-title')).to_have_text('Pedido #1')
        with connect_database(self.path) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM pedidos').fetchone()[0], 1)
            self.assertEqual(db.execute('SELECT count(*) FROM reservas_stock').fetchone()[0], 1)
