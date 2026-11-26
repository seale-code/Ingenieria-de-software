"""Vista de implementación comercial v6; conserva el modelo objetivo original."""
from pathlib import Path
import json, zipfile, xml.etree.ElementTree as ET
from reportlab.pdfgen import canvas
from . import generar as u
from .grupos import msg, frame

OUT = u.ROOT / 'docs/03-diagramas/uml/as-is'

def group(id,title,hus,note,people,actions,edges,sequence):
    return dict(id=id,title=title,hus=hus.split(),note=note,people=people,nodes=[('s','start','')]+[(a,'decision' if b.startswith('¿') else 'action',b) for a,b in actions]+[('z','end','')],edges=[(a,b,c) for a,b,c in edges],sequence=sequence)

def people(a,b,c,d,e):
    return [('actor',a,'actor'),('web',b,'boundary'),('api',c,'control'),('db',d,'entity'),('extra',e,'control')]
def m(id,a,b,t,r=False): return msg(id,a,b,t,reply=r)
def f(kind,guard,*items): return frame(kind,guard,*items)
G=[
group('G01','Consulta de catálogo','HU01 HU07 HU13','Parcial: sin comparación de precios por sucursal, cercanía en consulta ni alternativas automáticas.',people('Cliente','Catálogo web','API catálogo','SQLite','Detalle de stock'),[
('a','Buscar por nombre o marca\ny aplicar filtros'),('b','Consultar catálogo y stock\ndisponible'),('c','¿Consulta correcta?'),('d','Mostrar error y permitir reintento'),('e','¿Hay resultados?'),('g','Mostrar catálogo con fotos y precios;\nordenar en navegador'),('h','Mostrar resultado vacío'),('i','Consultar detalle de stock por sucursal'),('j','Mostrar disponibilidad o falta de stock'),('q','¿Seleccionar producto?'),('k','Seleccionar producto para carrito (G02)')],
[('s','a',''),('a','b',''),('b','c',''),('c','d','[no]'),('d','z',''),('c','e','[sí]'),('e','h','[no]'),('h','z',''),('e','g','[sí]'),('g','i',''),('i','j',''),('j','q',''),('q','k','[sí]'),('q','z','[no]'),('k','z','')],
[m('a',0,1,'buscar / filtrar'),m('b',1,2,'GET /api/catalogo'),m('c',2,3,'leer catálogo y stock efectivo'),m('d',3,2,'productos o error',True),f('alt','consulta correcta',m('e',2,1,'productos y total',True),m('f',1,0,'mostrar / ordenar resultados',True),f('opt','consultar stock de producto',m('g',0,1,'abrir detalle'),m('h',1,2,'GET stock por código'),m('i',2,3,'leer stock efectivo'),m('j',3,2,'filas por sucursal',True),m('k',2,1,'stock',True),m('l',1,0,'mostrar disponibilidad',True))),f('else','error',m('m',2,1,'error HTTP',True),m('n',1,0,'mostrar error y reintento',True))]),
group('G02','Compra web y cotización','HU04 HU08 HU10 HU11 HU12','Compra web sin cuentas, chat, repetición de compras ni integración de canales.',people('Cliente','Carrito web','API pedidos','SQLite','Servicio de pedidos'),[
('a','Seleccionar productos y cantidades'),('b','Solicitar cotización al servidor'),('c','¿Cotización válida?'),('d','Informar error y corregir carrito'),('e','Mostrar subtotal, envío y total'),('g','Ingresar datos de entrega y confirmar\npago al recibir'),('h','Validar datos y UUID; recotizar\ny asignar/reservar en transacción'),('i','¿Confirmación válida?'),('j','Mostrar error; revisar precio\no disponibilidad y reintentar'),('k','Guardar pedido y precios confirmados;\nmostrar código de seguimiento')],
[('s','a',''),('a','b',''),('b','c',''),('c','d','[no]'),('d','a',''),('c','e','[sí]'),('e','g',''),('g','h',''),('h','i',''),('i','j','[no]'),('j','b',''),('i','k','[sí]'),('k','z','')],
[m('a',0,1,'seleccionar artículos'),m('b',1,2,'POST /api/pedidos/cotizacion'),m('c',2,3,'leer precios y límites'),m('d',3,2,'datos comerciales',True),f('alt','cotización válida',m('e',2,1,'subtotal, envío, total, huella',True),m('f',1,0,'mostrar importe',True),m('g',0,1,'datos y confirmación'),m('h',1,2,'POST /api/pedidos'),m('i',2,4,'registrar_pedido (G03)'),m('j',4,2,'pedido o conflicto',True),f('alt','pedido confirmado',m('k',2,1,'pedido y código',True),m('l',1,0,'mostrar confirmación',True)),f('else','precio cambiado, sin asignación o error',m('m',2,1,'error HTTP',True),m('n',1,0,'mostrar revisión requerida',True))),f('else','cotización inválida',m('o',2,1,'error 400',True),m('p',1,0,'corregir carrito',True))]),
group('G03','Reservas y asignación','HU02 HU03 HU09','Plazo inicial configurable de 15 min por asignación; no hay reserva para recojo.',people('Operador / cliente','Web / panel','Logística y pedidos','SQLite','Supervisor de vencimientos'),[
('a','Evaluar stock completo, capacidad\ny distancia del distrito'),('b','¿Sucursal apta?'),('c','Informar sin asignación'),('d','Reservar líneas y registrar asignación;\nfijar plazo de aceptación'),('e','¿Sucursal acepta antes del límite?'),('f','Registrar EN_PREPARACION\ny aceptación'),('g','¿Sucursal declara incapacidad\no vence sin aceptación?'),('h','Esperar / revisar plazo'),('i','Registrar incidencia y liberar reservas;\nevaluar sucursales no intentadas'),('j','¿Hay alternativa apta?'),('k','Reasignar mismo pedido y renovar plazo'),('l','Cancelar y registrar solución;\nliberar reservas')],
[('s','a',''),('a','b',''),('b','c','[no]'),('c','z',''),('b','d','[sí]'),('d','e',''),('e','f','[sí]'),('f','g',''),('e','g','[no]'),('g','i','[sí]'),('g','h','[aún sin aceptación]'),('h','e',''),('g','z','[aceptado y continúa G04]'),('i','j',''),('j','k','[sí]'),('k','d',''),('j','l','[no]'),('l','z','')],
[m('a',0,1,'confirmar / consultar pedido'),m('b',1,2,'evaluar y asignar'),m('c',2,3,'BEGIN IMMEDIATE; stock/capacidad'),m('d',3,2,'candidatos',True),f('alt','hay sucursal apta',m('e',2,3,'reservar y registrar plazo'),m('f',2,1,'pedido asignado',True),f('loop','mientras pendiente de atención',f('alt','aceptación válida',m('g',0,1,'iniciar preparación'),m('h',1,2,'preparar(asignacion_id)'),m('i',2,3,'registrar aceptación y estado')),f('else','vence o sucursal rechaza',f('alt','vence sin aceptación',m('j',4,2,'procesar vencimiento')),f('else','incapacidad antes de preparado',m('k',1,2,'rechazar asignación')),m('l',2,3,'liberar, evaluar e historial'),f('alt','alternativa apta',m('m',2,3,'reasignar y reservar; plazo nuevo')),f('else','sin alternativa',m('n',2,3,'cancelar y liberar'))))),f('else','sin sucursal apta',m('o',2,1,'conflicto sin asignación',True))]),
group('G04','Seguimiento y entrega','HU05 HU15','Operaciones con clave compartida; seguimiento público por código, sin notificación activa ni recojo.',people('Operador / cliente','Panel / seguimiento','API operaciones','SQLite','Servicio de reparto'),[
('a','¿Consulta pública de seguimiento?'),('b','Ingresar código privado'),('c','¿Código válido y pedido existente?'),('d','Mostrar estado, sucursal e historial público'),('e','Informar error sin datos internos'),('f','Acceder con clave al panel'),('g','¿Sesión válida?'),('h','Abrir pedido asignado; iniciar preparación'),('i','Marcar preparado; asignar repartidor'),('j','¿Incidencia o cancelación autorizada?'),('k','Registrar / atender incidencia\no aplicar cancelación permitida'),('l','Iniciar reparto: consumir reserva\ny registrar salida de inventario'),('n','Confirmar entrega; registrar estado final')],
[('s','a',''),('a','b','[sí]'),('b','c',''),('c','d','[sí]'),('d','z',''),('c','e','[no]'),('e','z',''),('a','f','[no]'),('f','g',''),('g','e','[no]'),('g','h','[sí]'),('h','i',''),('i','j',''),('j','k','[sí]'),('k','z','[cancelado / revisión]'),('k','l','[resuelto y procede]'),('j','l','[no]'),('l','n',''),('n','z','')],
[f('alt','seguimiento público',m('a',0,1,'ingresar código privado'),m('b',1,2,'GET /api/seguimiento (código)'),m('c',2,3,'leer estado e historial'),m('d',3,2,'datos o ausencia',True),m('e',2,1,'resultado público o error',True),m('f',1,0,'mostrar resultado',True)),f('else','operaciones autorizadas',m('g',0,1,'ingresar clave'),m('h',1,2,'POST sesión'),m('i',2,1,'sesión / CSRF o error',True),f('opt','sesión válida',m('j',1,2,'preparar / listo / asignar'),m('k',2,3,'validar estado y persistir'),f('opt','incidencia o cancelación permitida',m('l',1,2,'registrar / atender / cancelar'),m('m',2,3,'registrar resultado')),f('opt','pedido apto para despacho',m('n',1,2,'salir / entregar'),m('o',2,4,'avanzar_reparto'),m('p',4,2,'transición y resultado',True),m('q',2,1,'estado actualizado',True))))]),
group('G05','Inventario y movimientos','HU06 HU14','Sin alertas de reposición. Entradas, ajustes y salidas auditables; no se editan movimientos.',people('Operador','Panel inventario','API / inventario','SQLite','Servicio de reparto'),[
('q','¿Evento de inicio de reparto?'),('a','Acceder al panel con sesión'),('b','Consultar físico, reservado, disponible\ny movimientos recientes'),('c','¿Registrar movimiento manual?'),('d','Ingresar entrada o ajuste, motivo y UUID'),('e','¿Validación correcta?'),('f','Informar conflicto / error'),('g','Registrar movimiento y saldo\nen una transacción'),('h','Actualizar vista de inventario'),('i','¿Transición de reparto válida?'),('j','Consumir reserva y registrar salida única')],
[('s','q',''),('q','a','[no: operación manual]'),('a','b',''),('b','c',''),('c','d','[sí]'),('d','e',''),('e','f','[no]'),('f','b',''),('e','g','[sí]'),('g','h',''),('h','z',''),('c','z','[solo consulta]'),('q','i','[sí]'),('i','j','[sí]'),('j','z',''),('i','z','[no]')],
[m('a',0,1,'abrir inventario'),m('b',1,2,'GET /api/demo/inventario'),m('c',2,3,'leer saldos y movimientos'),m('d',3,2,'físico, reservado, disponible',True),m('e',2,1,'inventario',True),m('f',1,0,'mostrar saldos',True),f('opt','entrada o ajuste autorizado',m('g',0,1,'cantidad, motivo, UUID'),m('h',1,2,'POST movimientos'),m('i',2,3,'validar saldo y reservas'),f('alt','válido',m('j',2,3,'registrar movimiento y saldo'),m('k',2,1,'resultado',True)),f('else','inválido u obsoleto',m('l',2,1,'error / conflicto',True))),f('opt','evento independiente: inicio de reparto',m('m',4,2,'consumir reserva y registrar salida'),m('n',2,3,'persistir salida única'))])]

# Vistas generales de implementación; el actor operativo agrupa roles simulados.
def general():
    d=u.Diagram('MCU-ASIS','Casos de uso | Sistema implementado','Tienda web y panel de operaciones de demostración',1550,1530,'No representa cuentas individuales ni conexión con sistemas reales de Inkafarma.')
    d.node('Inkafarma — prototipo web',300,150,950,1220,kind='container',font=22,fill='none',align='left')
    for actor,x,y in [('Cliente',100,400),('Operador',1370,900)]:
        aid=d.node('',x,y,55,85,kind='actor');d.text(actor,x-50,y+90,155,55,17)
        cases=(['Consultar catálogo y stock','Gestionar carrito y cotización','Confirmar pedido a domicilio','Consultar seguimiento por código'] if actor=='Cliente' else ['Acceder al panel con clave','Consultar y aceptar pedidos','Declarar incapacidad / reasignar','Preparar y asignar repartidor','Despachar y confirmar entrega','Registrar / atender incidencias','Consultar y ajustar inventario'])
        for i,label in enumerate(cases):
            yy=(220+i*120) if actor=='Cliente' else (700+i*88)
            case=d.node(label,500,yy,550,72,kind='oval',font=19,fill=u.MINT)
            u.join(d,aid,case,via=[(240 if actor=='Cliente' else 1310,y+42),(240 if actor=='Cliente' else 1310,yy+36)])
    return d

def components():
    d=u.Diagram('COMP-ASIS','Componentes | Sistema implementado','Arquitectura lógica local: navegador, Flask, servicios Python y SQLite',1800,1540,'Los servicios son módulos del mismo backend; no son microservicios. Sin pago externo ni notificaciones.')
    def c(t,x,y,w=450,h=120):return d.node('«component»\n'+t,x,y,w,h,kind='component',font=18,fill=u.MINT)
    web=c('Frontend público\nHTML / CSS / JavaScript',160,170,620);panel=c('Panel de operaciones\noperaciones.html / .js',1020,170,620);api=c('Flask app.py y blueprints\nAPI HTTP / sesión / CSRF',610,390,580)
    modules=[c(t,x,690,470) for t,x in [('Catálogo y comercio\ncatalogo_busqueda / comercio',80),('Pedidos y logística\npedidos_web / pedidos_s2 / logistica',665),('Operaciones y seguimiento\noperaciones_demo / seguimiento',1250)]]
    extra=[c('Inventario\ninventario.py',120,970),c('Preparación y reparto\nreparto_integrado / entregas_s3',665,970),c('Supervisor de vencimientos\nvencimientos.py',1210,970)]
    db=c('Persistencia SQLite v6\nconexiones, migraciones y transacciones',550,1250,700)
    for a in [web,panel]:u.join(d,a,api,arrow='open',dash=True)
    for a in modules:u.join(d,api,a,arrow='open',dash=True)
    u.join(d,modules[1],extra[0],arrow='open',dash=True);u.join(d,modules[2],extra[1],arrow='open',dash=True);u.join(d,extra[2],modules[1],arrow='open',dash=True)
    for a in [modules[0],modules[1],modules[2],extra[0],extra[1]]:u.join(d,a,db,arrow='open',dash=True)
    return d

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    G[0]['people']=G[0]['people'][:4]
    ds=[general(),components()]; paths=['generales/MCU.drawio','generales/componentes.drawio']
    for g in G:
        for name,fn in [('actividades',u.activity),('secuencia',u.sequence),('colaboracion',u.communication)]:
            ds.append(fn(g));paths.append(f'grupos/{g["id"]}/{name}.drawio')
    pdf=canvas.Canvas(str(OUT/'Inkafarma-AS-IS.pdf'));pdf.setTitle('Inkafarma — UML AS-IS')
    for d,p in zip(ds,paths):
        for n in d.nodes:
            if n['label'].startswith('Inkafarma | Modelo de análisis funcional'):
                n['label']='Inkafarma | AS-IS comercial v6 | DOC-02 #61'
            assert n['x']>=0 and n['y']>=0 and n['x']+n['w']<=d.w+1 and n['y']+n['h']<=d.h+1,(d.id,n)
        dest=OUT/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(u.mxfile([d]));pdf.bookmarkPage(d.id);pdf.addOutlineEntry(d.title,d.id);u.render_pdf(d,pdf)
    pdf.save();(OUT/'Inkafarma-AS-IS.drawio').write_bytes(u.mxfile(ds))
    for p in OUT.rglob('*.drawio'):
        for page in ET.parse(p).findall('diagram'):
            cells=page.findall('.//mxCell');ids={x.get('id') for x in cells};assert len(ids)==len(cells)
            for x in cells:
                for key in ('source','target','parent'):
                    if x.get(key):assert x.get(key) in ids
    print('Generados',len(ds),'diagramas')
if __name__=='__main__':main()
