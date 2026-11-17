"""Tienda comercial: imágenes locales, carrito, cotización y entrega completas."""
import os
import tempfile
import threading
import unittest
from pathlib import Path
from playwright.async_api import async_playwright,expect
from werkzeug.serving import make_server

from scripts.iniciar_tienda import preparar_tienda
from src.backend.app import create_app
from src.database.database import connect_database


class TiendaBrowserTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.path=Path(temp.name)/'tienda.sqlite3';preparar_tienda(self.path)
        self.key='clave-de-operaciones-para-la-prueba'
        self.server=make_server('127.0.0.1',0,create_app(self.path,operations_key=self.key),threaded=True)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.addCleanup(self.stop)
        self.url=f'http://127.0.0.1:{self.server.server_port}'
        self.pw=await async_playwright().start();self.addAsyncCleanup(self.pw.stop)
        self.browser=await self.pw.chromium.launch();self.addAsyncCleanup(self.browser.close)
        self.page=await self.browser.new_page(viewport={'width':1440,'height':1000})
        self.errors=[];self.page.on('pageerror',lambda e:self.errors.append(str(e)))

    def stop(self):
        self.server.shutdown();self.thread.join(timeout=5);self.server.server_close()

    async def asyncTearDown(self):self.assertEqual(self.errors,[])

    async def open(self):
        await self.page.goto(self.url)
        await expect(self.page.locator('.product')).to_have_count(16)

    async def checkout(self,quantity=1):
        await self.open()
        for _ in range(quantity):await self.page.locator('.add-cart').first.click()
        await self.page.locator('#cart-open').click()
        await expect(self.page.locator('#cart-checkout')).to_be_visible()
        await self.page.locator('#cart-checkout').click()
        await expect(self.page.locator('#edit-view')).to_be_visible()
        await self.page.locator('#customer').fill('Cliente de prueba')
        await self.page.locator('#reference').select_option('MIRAFLORES')
        await self.page.locator('#phone').fill('987654321')
        await self.page.locator('#address').fill('Calle de prueba 123')

    async def capture(self,name,full=False):
        if os.environ.get('EVIDENCE_DIR'):
            target=Path(os.environ['EVIDENCE_DIR']);target.mkdir(parents=True,exist_ok=True)
            await self.page.screenshot(path=str(target/name),full_page=full)

    async def test_carrito_checkout_y_operaciones_hasta_entregado(self):
        await self.checkout(2)
        await expect(self.page.locator('#edit-summary')).to_contain_text('153.80')
        await self.page.locator('#review-order').click()
        await expect(self.page.locator('#review-view')).to_be_visible()
        await expect(self.page.locator('#review-prices')).to_contain_text('153.80')
        await expect(self.page.locator('#review-prices')).to_contain_text('Sin costo')
        await self.capture('pedido-revision.png',True)
        await self.page.locator('#confirm-order').click()
        await expect(self.page.locator('#success-view')).to_be_visible()
        await expect(self.page.locator('#success-prices')).to_contain_text('153.80')
        await expect(self.page.locator('[data-cart-count]').first).to_have_text('0')
        code=(await self.page.locator('#order-tracking-code').inner_text()).split(': ')[1]
        self.assertEqual(await self.page.evaluate("JSON.parse(localStorage.getItem('inkafarma.carrito.v1'))"),[])
        await self.capture('pedido-confirmado.png',True)
        await self.page.goto(self.url+'/operaciones')
        await self.page.locator('#demo-key').fill(self.key)
        await self.page.locator('#login-button').click()
        await expect(self.page.locator('#refresh')).to_be_enabled()
        await expect(self.page.locator('#order-detail')).to_contain_text('Calle de prueba 123')
        await expect(self.page.locator('#order-detail')).to_contain_text('153.80')
        for label in ['Iniciar preparación','Marcar como preparado']:
            await self.page.get_by_role('button',name=label,exact=True).click()
            await expect(self.page.locator('#refresh')).to_be_enabled()
        await self.page.locator('#driver-select').select_option(index=1)
        for label in ['Asignar repartidor','Registrar salida','Confirmar entrega']:
            await self.page.get_by_role('button',name=label,exact=True).click()
            await expect(self.page.locator('#refresh')).to_be_enabled()
        await expect(self.page.locator('.detail-heading .state-badge')).to_have_text('Entregado')
        await self.capture('operaciones-comercial.png',True)
        await self.page.goto(self.url+'/seguimiento#'+code)
        await expect(self.page.locator('#tracking-state')).to_have_text('Entregado')
        await expect(self.page.locator('#tracking-history li')).to_have_count(5)
        self.assertNotIn('987654321',await self.page.locator('body').inner_text())
        await self.capture('seguimiento-comercial.png',True)
        with connect_database(self.path) as db:
            self.assertEqual(db.execute('SELECT total_centimos FROM pedidos_comerciales').fetchone()[0],15380)
            self.assertEqual(db.execute("SELECT cantidad FROM inventario i JOIN productos p ON p.id=i.producto_id JOIN sucursales s ON s.id=i.sucursal_id WHERE p.codigo='023735' AND s.codigo='MIRAFLORES'").fetchone()[0],16)

    async def test_carrito_persistente_cantidades_quitar_y_sin_datos_personales(self):
        await self.open();await self.page.locator('.add-cart').first.click();await self.page.reload()
        await expect(self.page.locator('[data-cart-count]').first).to_have_text('1')
        await self.page.locator('#cart-open').click();await expect(self.page.locator('#cart-checkout')).to_be_visible()
        await self.page.get_by_role('button',name='Aumentar cantidad',exact=True).click()
        await expect(self.page.locator('#cart-totals')).to_contain_text('153.80')
        await expect(self.page.locator('#cart-totals')).to_contain_text('Sin costo')
        stored=await self.page.evaluate("JSON.parse(localStorage.getItem('inkafarma.carrito.v1'))")
        self.assertEqual(stored,[{'producto_codigo':'023735','cantidad':2}])
        await self.page.get_by_role('button',name='Quitar',exact=True).click()
        await expect(self.page.locator('#cart-checkout')).to_be_hidden()
        await expect(self.page.locator('#cart-message')).to_contain_text('esperando tus esenciales')

    async def test_precio_actualizado_vuelve_a_revision_sin_pedido_parcial(self):
        await self.checkout();await self.page.locator('#review-order').click()
        await expect(self.page.locator('#review-view')).to_be_visible()
        with connect_database(self.path) as db:
            db.execute("UPDATE catalogo_comercial SET precio_centimos=7700 WHERE producto_id=(SELECT id FROM productos WHERE codigo='023735')")
        await self.page.locator('#confirm-order').click()
        await expect(self.page.locator('#edit-view')).to_be_visible()
        await expect(self.page.locator('#order-error')).to_contain_text('El precio cambió')
        with connect_database(self.path) as db:self.assertEqual(db.execute('SELECT count(*) FROM pedidos').fetchone()[0],0)
        await self.page.locator('#review-order').click()
        await expect(self.page.locator('#review-prices')).to_contain_text('83.90')
        await self.page.locator('#confirm-order').click()
        await expect(self.page.locator('#success-view')).to_be_visible()
        await expect(self.page.locator('#success-prices')).to_contain_text('83.90')

    async def test_categorias_busqueda_marca_orden_y_ficha(self):
        await self.open();await self.page.locator('[data-category=SOLAR]').click()
        await expect(self.page.locator('.product')).to_have_count(2)
        await self.page.locator('#sort').select_option('menor')
        await expect(self.page.locator('.product h3').first).to_contain_text('Eucerin')
        await self.page.locator('.product-detail').first.click()
        await expect(self.page.locator('#product-dialog')).to_be_visible()
        await expect(self.page.locator('#product-title')).to_contain_text('Eucerin')
        await self.page.keyboard.press('Escape');await expect(self.page.locator('#product-dialog')).to_be_hidden()
        await self.page.locator('#clear').click();await self.page.locator('#search').fill('gsk')
        await expect(self.page.locator('.product')).to_have_count(1)
        await expect(self.page.locator('.product h3')).to_have_text('Panadol 500mg Tableta')
        await self.page.goto(self.url+'/?categoria=DERMO#catalogo')
        await expect(self.page.locator('#category')).to_have_value('DERMO')
        await expect(self.page.locator('.product')).to_have_count(5)

    async def test_fotos_locales_portada_y_vistas_adaptables(self):
        external=[];self.page.on('request',lambda r:external.append(r.url) if not r.url.startswith(self.url) else None)
        for width,height in [(1440,1000),(390,844),(320,780)]:
            await self.page.set_viewport_size({'width':width,'height':height});await self.open()
            await self.page.evaluate("document.querySelectorAll('img').forEach(i=>i.loading='eager')")
            await self.page.wait_for_function("Array.from(document.querySelectorAll('.product .art img')).every(i=>i.complete&&i.naturalWidth>0)",timeout=10000)
            self.assertTrue(await self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            self.assertTrue(await self.page.locator('.product .art img').evaluate_all('imgs=>imgs.every(i=>i.complete&&i.naturalWidth>0)'))
            await self.capture(f'tienda-{width}.png')
            if width==1440:
                await self.page.locator('#catalogo').scroll_into_view_if_needed();await self.capture('catalogo-comercial.png')
            await self.page.locator('.add-cart').first.click();await self.page.locator('#cart-open').click()
            await expect(self.page.locator('#cart-checkout')).to_be_visible()
            self.assertTrue(await self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            await self.capture(f'carrito-{width}.png')
            await self.page.locator('#cart-close').click()
        self.assertEqual(external,[])

    async def test_checkout_movil_y_mensajes_comerciales(self):
        await self.page.set_viewport_size({'width':390,'height':844});await self.checkout()
        self.assertTrue(await self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
        await self.capture('checkout-movil.png',True)
        await self.page.locator('#review-order').click();await expect(self.page.locator('#review-view')).to_be_visible()
        self.assertTrue(await self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
        await self.capture('revision-movil.png',True)
        for url in ['/','/pedido','/ayuda','/privacidad','/seguimiento','/operaciones']:
            await self.page.goto(self.url+url)
            text=(await self.page.locator('body').inner_text()).lower()
            for word in ['demostración','académic','fictici','prototipo','simula los roles']:
                self.assertNotIn(word,text,(url,word))

    async def test_fallo_cotizacion_conserva_carrito_y_permite_reintentar(self):
        await self.open();await self.page.locator('.add-cart').first.click()
        async def fail(route):await route.abort()
        await self.page.route('**/api/pedidos/cotizacion',fail)
        await self.page.locator('#cart-open').click()
        await expect(self.page.locator('#cart-message')).not_to_contain_text('Revisando')
        await expect(self.page.locator('#cart-checkout')).to_be_hidden()
        await expect(self.page.locator('.cart-item')).to_have_count(1)
        await self.page.unroute('**/api/pedidos/cotizacion',fail)
        await self.page.locator('#cart-close').click();await self.page.locator('#cart-open').click()
        await expect(self.page.locator('#cart-checkout')).to_be_visible()
        await expect(self.page.locator('#cart-totals')).to_contain_text('83.80')


if __name__=='__main__':unittest.main()
