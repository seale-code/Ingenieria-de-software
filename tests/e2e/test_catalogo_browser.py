"""S1-12: navegador real → Flask HTTP → SQLite temporal. Ejecutar por separado."""
import asyncio
import os
import tempfile
import threading
import unittest
from urllib.parse import urlparse, parse_qs
from pathlib import Path

from playwright.async_api import async_playwright, expect
from werkzeug.serving import make_server

from src.backend.app import create_app
from src.database.database import connect_database, initialize_database


class CatalogoBrowserTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / 'e2e.sqlite3'
        initialize_database(self.db, demo=True)
        self.server = make_server('127.0.0.1', 0, create_app(self.db), threaded=True)
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
        self.assertEqual(self.errors, [], 'Errores JavaScript inesperados')

    async def open(self):
        await self.page.goto(self.url)
        await expect(self.page.locator('.product')).to_have_count(3)

    async def search(self, value, count):
        async with self.page.expect_response(lambda r: '/api/catalogo?' in r.url and parse_qs(urlparse(r.url).query, keep_blank_values=True).get('buscar') == [value]):
            await self.page.locator('#search').fill(value)
        await expect(self.page.locator('.product')).to_have_count(count)

    async def test_busqueda_y_filtros_combinados(self):
        await self.open()  # CP-01
        await self.search('Producto demo A', 1)  # CP-02
        await expect(self.page.locator('.product h3')).to_have_text('Producto demo A')
        await self.search('  DEMO b  ', 1)  # CP-03
        await expect(self.page.locator('.product h3')).to_have_text('Producto demo B')
        await self.page.locator('#category').select_option('DEMO-Y')
        await self.page.locator('#branch').select_option('DEMO-SUR')
        async with self.page.expect_response(lambda r: '/api/catalogo?' in r.url and 'solo_disponibles=true' in r.url):
            await self.page.locator('#only-stock').check()
        await expect(self.page.locator('.product h3')).to_have_text('Producto demo B')
        await self.page.locator('#category').select_option('DEMO-X')  # CP-08
        await expect(self.page.get_by_text('No encontramos productos')).to_be_visible()
        await self.page.locator('#clear').click()  # CP-11
        await expect(self.page.locator('.product')).to_have_count(3)
        for id in ['search', 'category', 'branch']:
            await expect(self.page.locator('#' + id)).to_have_value('')
        await expect(self.page.locator('#only-stock')).not_to_be_checked()
        await self.page.locator('#category').select_option('DEMO-X')  # CP-05
        await expect(self.page.locator('.product')).to_have_count(2)
        await self.page.locator('#category').select_option('')
        await expect(self.page.locator('.product')).to_have_count(3)
        await self.search('xyz123', 0)  # CP-04
        await expect(self.page.get_by_text('No encontramos productos')).to_be_visible()

    async def test_stock_sucursal_y_cero(self):
        await self.open()
        await self.page.locator('#branch').select_option('DEMO-NORTE')
        await self.page.locator('#only-stock').check()  # CP-06
        await expect(self.page.locator('.product h3')).to_have_text('Producto demo A')
        await self.page.locator('.detail-toggle').click()  # CP-09
        await expect(self.page.locator('.detail')).to_contain_text('5 unidades')
        await expect(self.page.locator('.detail')).to_contain_text('0 unidades · Sin stock')
        await self.page.locator('#branch').select_option('DEMO-SUR')  # CP-07
        await expect(self.page.locator('.product h3')).to_have_text('Producto demo B')
        await self.page.locator('#clear').click()
        await self.search('demo c', 1)  # CP-10
        await expect(self.page.locator('.pill')).to_have_text('Sin stock')
        await self.page.locator('.detail-toggle').click()
        await expect(self.page.locator('.detail strong')).to_have_text(['0 unidades · Sin stock', '0 unidades · Sin stock'])
        await self.page.locator('#only-stock').check()
        await expect(self.page.locator('.product')).to_have_count(0)

    async def test_fixtures_vacios_unicode_y_texto_literal(self):
        with connect_database(self.db) as db:
            db.execute("INSERT INTO categorias(codigo,nombre) VALUES ('VACIA','Vacía')")
            db.execute("INSERT INTO productos(codigo,nombre,categoria_id) SELECT 'SIN-REGISTRO','Sin inventario',id FROM categorias WHERE codigo='DEMO-X'")
            db.execute("INSERT INTO productos(codigo,nombre,categoria_id) SELECT 'UNICODE','Ácido de prueba',id FROM categorias WHERE codigo='DEMO-X'")
        await self.page.goto(self.url)
        await expect(self.page.locator('.product')).to_have_count(5)
        await self.page.locator('#category').select_option('VACIA')  # CP-12
        await expect(self.page.get_by_text('No encontramos productos')).to_be_visible()
        await self.page.locator('#clear').click()
        await self.search('Sin inventario', 1)  # CP-13
        await expect(self.page.locator('.pill')).to_have_text('Sin inventario registrado')
        await self.page.locator('.detail-toggle').click()
        await expect(self.page.locator('.detail')).to_have_text('Sin inventario registrado.')
        await self.search('ÁCIDO', 1)  # CP-14
        await expect(self.page.locator('.product h3')).to_have_text('Ácido de prueba')
        for value in ["' OR 1=1 --", '%', '_']:  # CP-15
            await self.search(value, 0)
            await expect(self.page.get_by_text('No encontramos productos')).to_be_visible()

    async def test_carga_error_y_reintento(self):
        reached = asyncio.Event()
        release = asyncio.Event()
        async def slow(route):
            reached.set()
            await release.wait()
            await route.continue_()
        await self.page.route('**/api/catalogo?*', slow)
        await self.page.goto(self.url)
        await asyncio.wait_for(reached.wait(), 10)  # CP-16
        await expect(self.page.get_by_text('Cargando productos…')).to_be_visible()
        release.set()
        await expect(self.page.locator('.product')).to_have_count(3)
        await self.page.unroute('**/api/catalogo?*', slow)
        async def fail(route):
            await route.fulfill(status=503, content_type='application/json', body='{"error":"fallo de prueba"}')
        await self.page.route('**/api/catalogo?*', fail)
        await self.page.locator('#clear').click()  # CP-17
        await expect(self.page.get_by_text('No pudimos cargar el catálogo')).to_be_visible()
        await expect(self.page.locator('.product')).to_have_count(0)
        await self.page.unroute('**/api/catalogo?*', fail)
        await self.page.get_by_role('button', name='Reintentar', exact=True).click()
        await expect(self.page.locator('.product')).to_have_count(3)

    async def test_actualizacion_real_desde_sqlite(self):
        await self.open()
        with connect_database(self.db) as db:
            db.execute("UPDATE inventario SET cantidad=2 WHERE producto_id=(SELECT id FROM productos WHERE codigo='DEMO-A') AND sucursal_id=(SELECT id FROM sucursales WHERE codigo='DEMO-NORTE')")
        await self.search('demo a', 1)  # CP-18
        await expect(self.page.locator('.availability')).to_contain_text('2 unidades')
        await self.page.locator('.detail-toggle').click()
        await expect(self.page.locator('.detail')).to_contain_text('2 unidades')

    async def test_respuesta_antigua_no_sobrescribe_busqueda(self):
        await self.open()
        # Desactivar cancelación de transporte solo en esta prueba fuerza la carrera.
        await self.page.evaluate("""() => { const original = window.fetch; window.fetch = (url, options) => original(url, {...options, signal: undefined}); }""")
        reached = asyncio.Event()
        release = asyncio.Event()
        done = asyncio.Event()
        async def slow_a(route):
            response = await route.fetch()
            reached.set()
            await release.wait()
            await route.fulfill(response=response)
            done.set()
        await self.page.route('**/api/catalogo?buscar=demo+a&*', slow_a)
        await self.page.locator('#search').fill('demo a')
        await asyncio.wait_for(reached.wait(), 10)
        await self.search('demo b', 1)  # CP-19
        await expect(self.page.locator('.product h3')).to_have_text('Producto demo B')
        release.set()
        await asyncio.wait_for(done.wait(), 10)
        await self.page.wait_for_timeout(100)
        await expect(self.page.locator('.product h3')).to_have_text('Producto demo B')

    async def test_responsive_teclado_y_capturas(self):
        await self.open()
        for width, height in [(1366, 900), (390, 844)]:  # CP-20
            await self.page.set_viewport_size({'width': width, 'height': height})
            self.assertTrue(await self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            await self.page.locator('#search').focus()
            await self.page.keyboard.press('Tab')
            await expect(self.page.locator('#category')).to_be_focused()
            await self.page.locator('#branch').select_option('DEMO-NORTE')
            await self.page.locator('#only-stock').check()
            await expect(self.page.locator('.product h3')).to_have_text('Producto demo A')
            await self.page.locator('.detail-toggle').click()
            await expect(self.page.locator('.detail')).to_contain_text('5 unidades')
            if os.environ.get('EVIDENCE_DIR'):
                dest = Path(os.environ['EVIDENCE_DIR'])
                dest.mkdir(parents=True, exist_ok=True)
                await self.page.screenshot(path=str(dest / f'catalogo-{width}.png'), full_page=True)
            await self.page.locator('#clear').click()
            await expect(self.page.locator('.product')).to_have_count(3)

    async def test_error_de_filtros_y_stock_recuperable(self):
        async def fail(route):
            await route.abort()
        await self.page.route('**/api/filtros', fail)
        await self.page.goto(self.url)
        await expect(self.page.get_by_text('No pudimos cargar el catálogo')).to_be_visible()
        await self.page.unroute('**/api/filtros', fail)
        await self.page.get_by_role('button', name='Reintentar', exact=True).click()
        await expect(self.page.locator('.product')).to_have_count(3)
        await self.search('demo a', 1)
        await self.page.route('**/api/productos/*/stock', fail)
        await self.page.locator('.detail-toggle').click()
        await expect(self.page.locator('.detail')).to_contain_text('No pudimos consultar el stock')
        await self.page.unroute('**/api/productos/*/stock', fail)
        await self.page.get_by_role('button', name='Reintentar disponibilidad').click()
        await expect(self.page.locator('.detail')).to_contain_text('5 unidades')


if __name__ == '__main__':
    unittest.main()
