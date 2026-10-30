"""Formulario #20: recorrido HTTP real con SQLite temporal y navegador de pruebas."""
import os
import tempfile
import threading
import unittest
from pathlib import Path

from playwright.async_api import async_playwright, expect
from werkzeug.serving import make_server

from src.backend.app import create_app
from src.backend.pedidos_s2 import iniciar_modulo
from src.database.database import connect_database, initialize_database
from src.database.migrate_josue import migrar


class PedidoBrowserTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / 'formulario.sqlite3'
        initialize_database(self.path, demo=True)
        migrar(self.path, hasta=3)
        iniciar_modulo(self.path)
        self.server = make_server('127.0.0.1', 0, create_app(self.path), threaded=True)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)
        self.url = f'http://127.0.0.1:{self.server.server_port}/pedido'
        self.pw = await async_playwright().start()
        self.addAsyncCleanup(self.pw.stop)
        self.browser = await self.pw.chromium.launch()
        self.addAsyncCleanup(self.browser.close)
        self.page = await self.browser.new_page(viewport={'width': 1366, 'height': 900})
        self.js_errors = []
        self.page.on('pageerror', lambda e: self.js_errors.append(str(e)))

    def stop_server(self):
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()

    async def asyncTearDown(self):
        self.assertEqual(self.js_errors, [])

    def total(self):
        with connect_database(self.path) as db:
            return db.execute('SELECT count(*) FROM pedidos').fetchone()[0]

    async def open_form(self, codigo='DEMO-A', cantidad='2'):
        await self.page.goto(self.url)
        await expect(self.page.locator('#edit-view')).to_be_visible()
        await self.page.locator('.order-product').select_option(codigo)
        await self.page.locator('.order-quantity').fill(cantidad)
        await self.page.locator('#customer').fill('Cliente ficticio')
        await self.page.locator('#reference').select_option('DEMO-NORTE')

    async def review(self):
        await self.page.get_by_role('button', name='Revisar pedido').click()
        await expect(self.page.locator('#review-view')).to_be_visible()

    async def test_revisar_editar_y_confirmar_sin_escritura_anticipada(self):
        await self.open_form()
        await self.review()
        await expect(self.page.locator('#review-items')).to_contain_text('Producto demo A')
        self.assertEqual(self.total(), 0)
        await self.page.get_by_role('button', name='Editar pedido').click()
        await self.page.locator('.order-quantity').fill('3')
        await self.review()
        await expect(self.page.locator('#review-total')).to_contain_text('3 unidad(es)')
        self.assertEqual(self.total(), 0)
        await self.page.get_by_role('button', name='Confirmar pedido', exact=True).click()
        await expect(self.page.locator('#success-view')).to_be_visible()
        await expect(self.page.locator('#success-details')).to_contain_text('Sucursal demo Norte')
        await expect(self.page.locator('#success-items')).to_contain_text('3 unidad(es)')
        self.assertEqual(self.total(), 1)

    async def test_cantidad_invalida_y_stock_insuficiente(self):
        await self.open_form(cantidad='0')
        await self.page.get_by_role('button', name='Revisar pedido').click()
        await expect(self.page.locator('#review-view')).not_to_be_visible()
        self.assertEqual(self.total(), 0)
        await self.page.locator('.order-quantity').fill('6')
        await self.review()
        await self.page.get_by_role('button', name='Confirmar pedido', exact=True).click()
        await expect(self.page.locator('#order-error')).to_contain_text('stock disponible suficiente')
        await expect(self.page.locator('#edit-order')).to_be_enabled()
        self.assertEqual(self.total(), 0)
        await self.page.locator('#edit-order').click()
        await self.page.locator('.order-quantity').fill('2')
        await self.review()
        await self.page.locator('#confirm-order').click()
        await expect(self.page.locator('#success-view')).to_be_visible()
        self.assertEqual(self.total(), 1)

    async def test_agregar_quitar_y_agrupar_productos(self):
        await self.open_form(cantidad='2')
        await self.page.locator('#add-line').click()
        await self.page.locator('.order-product').nth(1).select_option('DEMO-A')
        await self.page.locator('.order-quantity').nth(1).fill('1')
        await self.page.locator('#add-line').click()
        await self.page.locator('.order-product').nth(2).select_option('DEMO-C')
        await self.page.locator('.order-remove').nth(2).click()
        await self.review()
        await expect(self.page.locator('#review-items tr')).to_have_count(1)
        await expect(self.page.locator('#review-total')).to_contain_text('3 unidad(es)')
        await self.page.locator('#confirm-order').click()
        await expect(self.page.locator('#success-view')).to_be_visible()
        self.assertEqual(self.total(), 1)

    async def test_respuesta_perdida_reintenta_sin_duplicar(self):
        await self.open_form()
        await self.review()
        async def lost_response(route):
            await route.fetch()  # El servidor confirma, pero el cliente pierde la respuesta.
            await route.abort()
        await self.page.route('**/api/pedidos', lost_response)
        await self.page.locator('#confirm-order').click()
        await expect(self.page.locator('#order-error')).to_contain_text('sin duplicarlo')
        await expect(self.page.locator('#edit-order')).to_be_disabled()
        self.assertEqual(self.total(), 1)
        await self.page.unroute('**/api/pedidos', lost_response)
        await self.page.get_by_role('button', name='Comprobar confirmación').click()
        await expect(self.page.locator('#success-view')).to_be_visible()
        self.assertEqual(self.total(), 1)

    async def test_error_de_carga_y_recuperacion(self):
        async def fail(route):
            await route.abort()
        await self.page.route('**/api/pedidos/opciones', fail)
        await self.page.goto(self.url)
        await expect(self.page.get_by_role('button', name='Reintentar carga')).to_be_visible()
        await expect(self.page.locator('#edit-view')).not_to_be_visible()
        await self.page.unroute('**/api/pedidos/opciones', fail)
        await self.page.get_by_role('button', name='Reintentar carga').click()
        await expect(self.page.locator('#edit-view')).to_be_visible()
        self.assertEqual(self.total(), 0)

    async def test_responsive_teclado_y_capturas(self):
        await self.open_form(codigo='DEMO-B', cantidad='1')
        for width, height in [(1366, 900), (390, 844)]:
            await self.page.set_viewport_size({'width': width, 'height': height})
            self.assertTrue(await self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            await self.page.locator('.order-product').focus()
            await self.page.keyboard.press('Tab')
            await expect(self.page.locator('.order-quantity')).to_be_focused()
            await self.capture(f'formulario-{width}.png')
            await self.review()
            self.assertTrue(await self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            await self.capture(f'resumen-{width}.png')
            await self.page.locator('#edit-order').click()
        await self.page.set_viewport_size({'width': 390, 'height': 844})
        await self.review()
        await self.page.locator('#confirm-order').click()
        await expect(self.page.locator('#success-details')).to_contain_text('Sucursal demo Sur')
        await self.capture('confirmacion-390.png')
        await self.page.locator('#new-order').click()
        await expect(self.page.locator('#edit-view')).to_be_visible()
        await expect(self.page.locator('#customer')).to_have_value('')
        self.assertEqual(self.total(), 1)

    async def capture(self, name):
        if os.environ.get('EVIDENCE_DIR'):
            dest = Path(os.environ['EVIDENCE_DIR'])
            dest.mkdir(parents=True, exist_ok=True)
            await self.page.screenshot(path=str(dest / name), full_page=True)
