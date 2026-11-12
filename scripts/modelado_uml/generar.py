"""Genera 17 diagramas UML nativos de draw.io y sus versiones vectoriales.

Requisitos de generación: Graphviz (dot), reportlab y fuentes DejaVu Sans.
Uso desde la raíz: python -m scripts.modelado_uml.generar
Los diagramas ya generados no requieren Python para abrirse en diagrams.net.
"""
from __future__ import annotations

import csv
import json
import math
import shlex
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from .grupos import GRUPOS, HISTORIAS

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/03-diagramas/uml'
INK, GREEN, MINT, BLUE, GRAY = '#263D36', '#087C49', '#EAF5EF', '#EDF3FC', '#F3F4F5'
FONTS = Path('/usr/share/fonts/truetype/dejavu')
for name, filename in [('UML','DejaVuSans.ttf'),('UML-Bold','DejaVuSans-Bold.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(FONTS / filename)))


def lines(text, width, size, bold=False):
    result = []
    font = 'UML-Bold' if bold else 'UML'
    for paragraph in str(text).split('\n'):
        line = ''
        words=[]
        for word in paragraph.split():
            chunk=''
            for ch in word:
                if chunk and pdfmetrics.stringWidth(chunk+ch,font,size)>width:
                    words.append(chunk);chunk=''
                chunk+=ch
            if chunk:words.append(chunk)
        for word in words:
            candidate = (line + ' ' + word).strip()
            if line and pdfmetrics.stringWidth(candidate, font, size) > width:
                result.append(line)
                line = word
            else:
                line = candidate
        result.append(line)
    return result


class Diagram:
    def __init__(self, id, title, subtitle, w, h, note):
        self.id, self.title, self.w, self.h = id, title, w, h
        self.nodes, self.edges, self.count = [], [], 0
        self.text(title, 45, 20, w-90, 55, 28, bold=True, align='left')
        self.text(subtitle, 45, 80, w-90, 45, 17, align='left')
        self.text(note, 45, h-100, w-90, 60, 16, align='left', fill=MINT)
        self.text('Inkafarma | Modelo de análisis funcional | Fuente: HU originales, págs. 2-16',
                  45, h-36, w-90, 32, 12, align='left')

    def node(self, label, x, y, w, h, kind='box', font=18, fill='white', bold=False,
             align='center', id=None, **attrs):
        self.count += 1
        id = id or f'n{self.count}'
        wrapped = lines(label, w-24, font, bold) if label else []
        if len(wrapped) * font * 1.3 > h-12:
            raise ValueError(f'Texto fuera de caja: {self.id}/{id}: {label}')
        self.nodes.append(dict(id=id, label='\n'.join(wrapped), x=x,y=y,w=w,h=h,
                               kind=kind,font=font,fill=fill,bold=bold,align=align,**attrs))
        return id

    def text(self, label, x,y,w,h,font=18, **attrs):
        return self.node(label,x,y,w,h,kind='text',font=font,**attrs)

    def edge(self, points, source=None, target=None, arrow='block', dash=False):
        self.count += 1
        self.edges.append(dict(id=f'e{self.count}',points=points,source=source,target=target,arrow=arrow,dash=dash))


def center(n):
    return n['x']+n['w']/2, n['y']+n['h']/2


def join(d, source, target, arrow='none', dash=False, via=None):
    a = next(n for n in d.nodes if n['id']==source)
    b = next(n for n in d.nodes if n['id']==target)
    ac, bc = center(a), center(b)
    def clip(n, c, other):
        dx,dy=other[0]-c[0],other[1]-c[1]
        ratios=[abs((n['w']/2)/dx) if dx else math.inf, abs((n['h']/2)/dy) if dy else math.inf]
        if n['kind']=='oval':
            r=1/math.sqrt((dx/(n['w']/2))**2+(dy/(n['h']/2))**2)
        else:
            r=min(ratios)
        return c[0]+dx*r,c[1]+dy*r
    points=[clip(a,ac,via[0] if via else bc),*(via or []),clip(b,bc,via[-1] if via else ac)]
    d.edge(points,source,target,arrow,dash)


def activity(g):
    # Alternative paths must merge before entering an action. Multiple incoming
    # control flows on an action would otherwise imply synchronization (AND).
    nodes=list(g['nodes']); edges=list(g['edges'])
    incoming=defaultdict(list)
    for edge in edges: incoming[edge[1]].append(edge)
    for id,kind,label in g['nodes']:
        if len(incoming[id])>1 and kind not in ('start','end'):
            merge='merge_'+id;nodes.append((merge,'merge',''))
            edges=[(a,merge if b==id else b,label) for a,b,label in edges]
            edges.append((merge,id,''))
    dot=['digraph G {','graph [rankdir=TB,ranksep=0.50,nodesep=0.60,splines=polyline];',
         'node [fontname="DejaVu Sans",fontsize=18,margin="0.22,0.25"];',
         'edge [fontname="DejaVu Sans",fontsize=14];']
    for id,kind,label in nodes:
        shape={'start':'circle','end':'doublecircle','decision':'diamond','merge':'diamond','action':'box'}[kind]
        extra=',width=0.20,height=0.20,fixedsize=true' if kind in ('start','end','merge') else ''
        dot.append(f'{id} [shape={shape},label={json.dumps(label,ensure_ascii=False)}{extra}];')
    for a,b,label in edges:
        dot.append(f'{a} -> {b} [label={json.dumps(label,ensure_ascii=False)}];')
    dot.append('}')
    result=subprocess.run(['dot','-Tplain'],input='\n'.join(dot),text=True,capture_output=True,check=True).stdout
    rows=[shlex.split(line) for line in result.splitlines()]
    gw,gh=float(rows[0][2])*72,float(rows[0][3])*72
    w,h=max(1100,gw+120),gh+300
    ox,oy=(w-gw)/2,150
    d=Diagram(g['id']+'-ACT',f"{g['id']} | Diagrama de actividades",g['title']+' | '+', '.join(g['hus']),w,h,g['note'])
    nodeinfo={id:(kind,label) for id,kind,label in nodes}
    for row in rows:
        if row[0]=='node':
            id,x,y,nw,nh=row[1],*map(float,row[2:6])
            kind,label=nodeinfo[id]
            d.node(label,ox+(x-nw/2)*72,oy+gh-(y+nh/2)*72,nw*72,nh*72,
                   kind={'action':'round','decision':'diamond','merge':'diamond','start':'start','end':'end'}[kind],
                   font=18,fill=MINT if kind=='action' else 'white',id=id)
        elif row[0]=='edge':
            count=int(row[3]); coords=list(map(float,row[4:4+2*count]))
            points=[(ox+coords[i]*72,oy+gh-coords[i+1]*72) for i in range(0,len(coords),2)]
            # DOT leaves clearance for the arrow head; preserve that geometry.
            d.edge(points,row[1],row[2])
            index=4+2*count
            if len(row)>index+2 and row[index] not in ('solid','dashed'):
                label,lx,ly=row[index],float(row[index+1]),float(row[index+2])
                labelw=max(90,pdfmetrics.stringWidth(label,'UML',14)+32)
                d.text(label,ox+lx*72-labelw/2,oy+gh-ly*72-14,labelw,32,14,fill='white')
    return d


def normalized(items):
    out=[]; i=0
    while i<len(items):
        item=items[i]
        if 'kind' not in item:
            out.append(item); i+=1; continue
        if item['kind']=='else':
            raise ValueError('else sin alt')
        if item['kind']=='alt':
            branches=[(item['guard'],normalized(item['items']))]; i+=1
            while i<len(items) and items[i].get('kind')=='else':
                branches.append((items[i]['guard'],normalized(items[i]['items']))); i+=1
            out.append(dict(kind='alt',branches=branches))
        else:
            out.append(dict(kind=item['kind'],branches=[(item['guard'],normalized(item['items']))])); i+=1
    return out


def events(g):
    """One ordering and the same guards for sequence and communication."""
    guards=[]; messages=[]
    def walk(items, ancestry=()):
        out=[]
        for item in items:
            if 'kind' not in item:
                m={**item,'number':len(messages)+1,'conditions':ancestry}
                messages.append(m); out.append(m)
            else:
                branches=[]
                for guard, children in item['branches']:
                    code='C'+str(len(guards)+1)
                    guards.append((code,item['kind'],guard))
                    branches.append((code,guard,walk(children,ancestry+(code,))))
                out.append(dict(kind=item['kind'],branches=branches))
        return out
    tree=walk(normalized(g['sequence']))
    return tree,messages,guards


def sequence(g):
    tree,messages,guards=events(g)
    def height(items):
        return sum(72 if 'number' in i else 32+sum(34+height(kids) for _,_,kids in i['branches'])+16 for i in items)
    w,h=1860,440+height(tree)
    d=Diagram(g['id']+'-SEC',f"{g['id']} | Diagrama de secuencia",g['title']+' | '+', '.join(g['hus']),w,h,g['note'])
    xs=[190,560,930,1300,1670]
    for i,(alias,name,stereotype) in enumerate(g['people']):
        d.node(f'«{stereotype}»\n{alias} : {name}',xs[i]-157,145,314,100,font=17,fill=BLUE if stereotype=='control' else MINT if stereotype=='boundary' else GRAY if stereotype=='entity' else 'white')
        d.edge([(xs[i],245),(xs[i],h-130)],arrow='none',dash=True)
    def render(items,y,depth=0):
        for item in items:
            if 'number' in item:
                a,b=xs[item['source']],xs[item['target']]
                label=f"{item['number']}: {item['label']}"
                if a==b:
                    pts=[(a,y+43),(a+85,y+43),(a+85,y+65),(a,y+65)]
                    tx,tw=a+95,min(420,w-a-120)
                    if tw<200: tx,tw=a-450,420
                    d.text(label,tx,y+5,tw,60,16,align='left')
                else:
                    pts=[(a,y+56),(b,y+56)]
                    d.text(label,min(a,b)+12,y+1,abs(a-b)-24,60,16,align='center')
                d.edge(pts,arrow='open' if item['reply'] else 'block',dash=item['reply'])
                y+=72
            else:
                top=y; total=32+sum(34+height(kids) for _,_,kids in item['branches'])+16
                d.node(item['kind'],45+depth*12,top,w-90-depth*24,total,kind='frame',font=14,fill='none',align='left')
                y+=32
                for n,(code,guard,kids) in enumerate(item['branches']):
                    if n: d.edge([(45+depth*12,y),(w-45-depth*12,y)],arrow='none',dash=True)
                    d.text(f'[{code}: {guard}]',65+depth*12,y,w-130-depth*24,32,14,align='left',fill='none')
                    y=render(kids,y+34,depth+1)
                y+=16
        return y
    render(tree,265)
    return d


def communication(g):
    _,messages,guards=events(g)
    guardlines=sum(max(1,len(lines(f'{a} ({k}): {b}',930,17))) for a,k,b in guards)
    w,h=2100,max(2400,2280+math.ceil(guardlines/2)*25+150)
    d=Diagram(g['id']+'-COL',f"{g['id']} | Diagrama de colaboración (comunicación)",
              g['title']+' | '+', '.join(g['hus']),w,h,g['note'])
    boxes=[(150,220),(150,1740),(900,980),(1600,220),(1600,1740)]
    ids=[]
    for i,(alias,name,stereotype) in enumerate(g['people']):
        x,y=boxes[i]
        ids.append(d.node(f'«{stereotype}»\n{alias} : {name}',x,y,350,130,font=19,
                          fill=BLUE if stereotype=='control' else MINT if stereotype=='boundary' else GRAY if stereotype=='entity' else 'white',underline=True))
    grouped=defaultdict(list)
    for m in messages: grouped[tuple(sorted((m['source'],m['target'])))].append(m)
    slots={(0,1):(30,610,550,850),(0,2):(410,500,620,450),(1,2):(410,1240,620,450),
           (2,3):(1210,500,750,450),(2,4):(1210,1240,750,450),(1,4):(630,1940,850,300),
           (2,2):(1270,985,760,235)}
    for pair,ms in grouped.items():
        if pair not in slots: raise ValueError(f'Falta disposición para {g["id"]} {pair}')
        a,b=pair
        if a==b:
            d.edge([(1250,1015),(1330,1015),(1330,1090),(1250,1090)],source=ids[a],target=ids[a],arrow='open')
        else:
            via=[(325,2110),(1775,2110)] if pair==(1,4) else None
            join(d,ids[a],ids[b],via=via)
        x,y,bw,bh=slots[pair]
        texts=[]
        for m in ms:
            src,tgt=g['people'][m['source']][0],g['people'][m['target']][0]
            conditions='['+','.join(m['conditions'])+'] ' if m['conditions'] else ''
            texts.append(f"{m['number']}: {src} → {tgt} | {conditions}{m['label']}")
        label='\n'.join(texts)
        compact_h=len(lines(label,bw-24,17))*17*1.3+16
        if compact_h>bh: raise ValueError(f'Etiqueta de colaboración demasiado grande: {g["id"]} {pair}')
        d.text(label,x,y+(bh-compact_h)/2,bw,compact_h,17,fill='white',align='left')
    d.text('Condiciones de los mensajes (mismas guardas que en secuencia)',50,2230,2000,40,19,bold=True,align='left')
    left=[]; right=[]
    for i,(code,kind,guard) in enumerate(guards):
        (left if i%2==0 else right).append(f'{code} ({kind}): {guard}')
    for x,content in [(50,left),(1100,right)]:
        d.text('\n'.join(content),x,2280,950,h-2410,17,align='left')
    return d


def usecases():
    d=Diagram('MCU','Modelo general de casos de uso','Sistema de Gestión de Pedidos entre Sucursales de Inkafarma',2050,2470,
              'Las 15 HU están agrupadas por proceso. Las asociaciones muestran participación; no representan orden temporal ni cobertura implementada.')
    d.node('Sistema Inkafarma',400,155,1230,2110,kind='container',font=22,fill='none',align='left')
    actor_positions={'Cliente':(70,900),'Adulto mayor':(70,1650),'Asesor':(1790,880),
      'Administrador de plataforma':(1790,1300),'Administrador de sucursal':(1790,1990),
      'Personal de sucursal':(1790,1570),'Repartidor':(1790,1780)}
    actors={}
    for name,(x,y) in actor_positions.items():
        actors[name]=d.node('',x+55,y,55,85,kind='actor')
        d.text(name,x-30,y+95,225,80,19)
    adult=next(n for n in d.nodes if n['id']==actors['Adulto mayor'])
    client=next(n for n in d.nodes if n['id']==actors['Cliente'])
    d.edge([(adult['x']+27.5,adult['y']),(95,adult['y']),(95,client['y']+85),
            (client['x']+27.5,client['y']+85)],actors['Adulto mayor'],actors['Cliente'],arrow='generalization')
    groups=[(GRUPOS[0],210,310),(GRUPOS[1],560,550),(GRUPOS[2],1160,360),(GRUPOS[3],1570,260),(GRUPOS[4],1880,270)]
    titles={'HU01':'Consultar disponibilidad','HU07':'Comparar sucursales','HU13':'Consultar alternativas',
      'HU04':'Comprar por aplicación','HU08':'Realizar compra accesible','HU10':'Consultar y repetir compras',
      'HU11':'Solicitar soporte y asesoría','HU12':'Continuar compra entre canales',
      'HU02':'Reservar medicamento','HU03':'Obtener mejor sucursal','HU09':'Controlar riesgo de cancelación',
      'HU05':'Consultar y recibir seguimiento','HU15':'Gestionar entrega del pedido',
      'HU06':'Solicitar aviso de reposición','HU14':'Gestionar inventario'}
    cases={}
    for g,y,gh in groups:
        d.node(g['id']+' - '+g['title'],450,y,1130,gh,kind='container',font=19,fill='none',align='left')
        for i,hu in enumerate(g['hus']):
            cases[hu]=d.node(hu+'\n'+titles[hu],590,y+55+i*92,780,75,kind='oval',font=19,fill=MINT)
    def associate(actor,hu,bus,left=False):
        a=next(n for n in d.nodes if n['id']==actors[actor]);b=next(n for n in d.nodes if n['id']==cases[hu])
        ay=a['y']+a['h']/2;by=b['y']+b['h']/2
        ax=a['x']+a['w'] if left else a['x'];bx=b['x'] if left else b['x']+b['w']
        d.edge([(ax,ay),(bus,ay),(bus,by),(bx,by)],actors[actor],cases[hu],arrow='none')
    for hu in HISTORIAS:
        if hu not in ('HU09','HU14'):associate('Cliente',hu,320,True)
    associate('Adulto mayor','HU08',365,True)
    for hu in ('HU11','HU13'):associate('Asesor',hu,1660)
    for actor,hus in [('Administrador de plataforma',['HU09']),('Administrador de sucursal',['HU14']),
                      ('Personal de sucursal',['HU02','HU05','HU12','HU15']),('Repartidor',['HU15'])]:
        for hu in hus:associate(actor,hu,{'Administrador de plataforma':1685,'Administrador de sucursal':1710,'Personal de sucursal':1735,'Repartidor':1760}[actor])
    return d


def components():
    d=Diagram('COMP','Diagrama general de componentes','Vista lógica de análisis | Relaciones de uso e interfaces | Módulos del modelo objetivo',1950,1790,
              'Son componentes lógicos, no microservicios ni un despliegue. Cuentas, precios, notificaciones y funciones diferidas siguen siendo requisitos de diseño.')
    def comp(label,x,y,w=440,h=150):
        return d.node('«component»\n'+label,x,y,w,h,kind='component',font=20,fill=MINT)
    web=comp('Canales de compra y consulta\nWeb / móvil / sucursal',100,180,730)
    staff=comp('Canal de operación y soporte\nSucursal / administración / asesor',1100,180,730)
    api=comp('Fachada de aplicación\nIConsulta · ICompra · IOperación',690,470,560)
    modules=[]
    layout=[(100,790),(750,790),(1400,790),(420,1140),(1100,1140)]
    for g,(x,y) in zip(GRUPOS,layout):
        modules.append(comp(g['id']+' - '+g['title']+'\n'+', '.join(g['hus']),x,y))
    repo=comp('Persistencia\nStock, pedidos, reservas, cuentas y alertas',420,1460,650)
    notification=comp('Adaptador de notificaciones\nIEnvioAvisos (canal por definir)',1240,1460,600)
    join(d,web,api,arrow='open',dash=True)
    join(d,staff,api,arrow='open',dash=True)
    routes_in=[[(320,710)],[(970,710)],[(1620,710)],[(40,650),(40,1060),(640,1060)],[(1900,650),(1900,1060),(1320,1060)]]
    routes_data=[[(320,1030),(280,1030),(280,1400),(560,1400)],[(970,1030),(970,1400),(740,1400)],
                 [(1620,1030),(1040,1030),(1040,1400),(920,1400)],None,[(1320,1390),(1010,1390)]]
    for i,module in enumerate(modules):
        join(d,api,module,arrow='open',dash=True,via=routes_in[i])
        join(d,module,repo,arrow='open',dash=True,via=routes_data[i])
    for i,route in [(2,[(1870,1010),(1870,1350),(1540,1350)]),(3,[(900,1340),(1540,1340)]),(4,None)]:
        join(d,modules[i],notification,arrow='open',dash=True,via=route)
    d.text('Dependencias punteadas: uso de servicios. Las reglas de cada grupo se detallan en sus tres diagramas.',
           80,125,1790,45,16,align='left')
    return d


def rgb(c):
    c=c.lstrip('#'); return tuple(int(c[i:i+2],16)/255 for i in (0,2,4))


def render_pdf(d,c):
    c.setPageSize((d.w*.6,d.h*.6)); c.saveState(); c.scale(.6,.6)
    def text(n):
        if not n['label']: return
        font='UML-Bold' if n['bold'] else 'UML'
        c.setFont(font,n['font']); c.setFillColorRGB(*rgb(INK))
        ll=n['label'].split('\n'); lh=n['font']*1.3
        top=n['y']+(n['h']-len(ll)*lh)/2
        if n['kind'] in ('frame','container'): top=n['y']+8
        for k,line in enumerate(ll):
            yy=d.h-top-k*lh-n['font']
            xx=n['x']+12 if n['align']=='left' or n['kind'] in ('frame','container') else n['x']+n['w']/2
            (c.drawString if n['align']=='left' or n['kind'] in ('frame','container') else c.drawCentredString)(xx,yy,line)
            if n.get('underline') and k==len(ll)-1:
                ww=pdfmetrics.stringWidth(line,font,n['font']); c.setLineWidth(.8)
                c.line(xx-ww/2,yy-3,xx+ww/2,yy-3)
    def shape(n):
        x,y,w,h=n['x'],d.h-n['y']-n['h'],n['w'],n['h']; kind=n['kind']
        c.setStrokeColorRGB(*rgb(INK)); c.setLineWidth(1.6)
        fill=n['fill']!='none'
        if fill: c.setFillColorRGB(*rgb('#FFFFFF' if n['fill']=='white' else n['fill']))
        if kind=='text':
            if n['fill']!='white' and n['fill']!='none': c.rect(x,y,w,h,stroke=0,fill=1)
            elif n.get('fill')=='white' and n['id'] not in ('n1','n2'): c.rect(x,y,w,h,stroke=0,fill=1)
        elif kind=='oval': c.ellipse(x,y,x+w,y+h,stroke=1,fill=fill)
        elif kind in ('start','end'):
            c.setFillColorRGB(*rgb(INK)); c.circle(x+w/2,y+h/2,min(w,h)/2,stroke=1,fill=kind=='start')
            if kind=='end': c.circle(x+w/2,y+h/2,min(w,h)/2-4,stroke=0,fill=1)
        elif kind=='diamond':
            p=c.beginPath(); p.moveTo(x+w/2,y+h);p.lineTo(x+w,y+h/2);p.lineTo(x+w/2,y);p.lineTo(x,y+h/2);p.close()
            c.drawPath(p,stroke=1,fill=fill)
        elif kind=='actor':
            cx=x+w/2; c.circle(cx,y+h-11,10,stroke=1,fill=0)
            for a,b in [((cx,y+h-21),(cx,y+25)),((x+3,y+h-36),(x+w-3,y+h-36)),((cx,y+25),(x+3,y)),((cx,y+25),(x+w-3,y))]: c.line(*a,*b)
        else:
            if kind=='round': c.roundRect(x,y,w,h,16,stroke=1,fill=fill)
            else: c.rect(x,y,w,h,stroke=1,fill=fill)
            if kind=='component':
                for yy in (y+h-28,y+h-53): c.rect(x+w-28,yy,20,14,stroke=1,fill=0)
            if kind=='frame':
                c.line(x,y+h-32,x+100,y+h-32);c.line(x+100,y+h-32,x+110,y+h-23);c.line(x+110,y+h-23,x+110,y+h)
        text(n)
    for n in d.nodes:
        if n['kind'] in ('frame','container'): shape(n)
    for e in d.edges:
        c.setStrokeColorRGB(*rgb(INK));c.setFillColorRGB(*rgb(INK));c.setLineWidth(1.5)
        c.setDash(6,5) if e['dash'] else c.setDash()
        pts=[(x,d.h-y) for x,y in e['points']]
        p=c.beginPath();p.moveTo(*pts[0])
        for pt in pts[1:]: p.lineTo(*pt)
        c.drawPath(p,stroke=1,fill=0);c.setDash()
        if e['arrow']!='none':
            a,b=pts[-2:];angle=math.atan2(b[1]-a[1],b[0]-a[0]);size=12
            wing=[(b[0]-size*math.cos(angle-t),b[1]-size*math.sin(angle-t)) for t in (.42,-.42)]
            p=c.beginPath();p.moveTo(*wing[0]);p.lineTo(*b);p.lineTo(*wing[1])
            closed=e['arrow'] in ('block','generalization')
            if closed:p.close()
            if e['arrow']=='generalization':c.setFillColorRGB(1,1,1)
            c.drawPath(p,stroke=1,fill=closed)
    for n in d.nodes:
        if n['kind'] not in ('frame','container'): shape(n)
    c.restoreState();c.showPage()


def graph_model(d):
    model=ET.Element('mxGraphModel',dict(dx='0',dy='0',grid='0',gridSize='10',guides='1',tooltips='1',connect='1',arrows='1',fold='1',page='1',pageScale='1',pageWidth=str(round(d.w)),pageHeight=str(round(d.h)),math='0',shadow='0',background='#FFFFFF',adaptiveColors='none'))
    root=ET.SubElement(model,'root');ET.SubElement(root,'mxCell',id='0');ET.SubElement(root,'mxCell',id='1',parent='0')
    def vertex(n):
        shapes={'box':'rectangle','round':'rectangle','text':'text','oval':'ellipse','diamond':'rhombus','start':'ellipse','end':'doubleEllipse','actor':'umlActor','component':'component','frame':'umlFrame','container':'rectangle'}
        shape=shapes[n['kind']]
        fill=INK if n['kind']=='start' else '#FFFFFF' if n['fill']=='white' else n['fill']
        sty=f"shape={shape};html=0;whiteSpace=wrap;fontFamily=DejaVu Sans;fontSize={n['font']};fontColor={INK};strokeColor={INK};strokeWidth=1.6;fillColor={fill};align={n['align']};verticalAlign=middle;"
        if n['kind']=='round':sty+='rounded=1;arcSize=20;'
        if n['kind']=='text':sty+='strokeColor=none;spacing=5;'
        if n['kind'] in ('frame','container'):sty+='verticalAlign=top;align=left;spacingTop=6;spacingLeft=10;'
        if shape in ('ellipse','doubleEllipse'):sty+='perimeter=ellipsePerimeter;'
        if shape=='rhombus':sty+='perimeter=rhombusPerimeter;'
        if n['bold'] or n.get('underline'):sty+=f"fontStyle={int(n['bold'])+4*int(n.get('underline',False))};"
        cell=ET.SubElement(root,'mxCell',id=n['id'],value=n['label'],style=sty,vertex='1',parent='1')
        ET.SubElement(cell,'mxGeometry',x=str(round(n['x'],2)),y=str(round(n['y'],2)),width=str(round(n['w'],2)),height=str(round(n['h'],2)),attrib={'as':'geometry'})
    for n in d.nodes:
        if n['kind'] in ('frame','container'):vertex(n)
    for e in d.edges:
        arrow={'none':'none','block':'block','open':'open','generalization':'block'}[e['arrow']]
        sty=f"edgeStyle=none;rounded=0;html=0;endArrow={arrow};endFill={int(e['arrow']=='block')};strokeColor={INK};strokeWidth=1.5;dashed={int(e['dash'])};"
        attrs=dict(id=e['id'],style=sty,edge='1',parent='1')
        if e['source']:attrs['source']=e['source']
        if e['target']:attrs['target']=e['target']
        cell=ET.SubElement(root,'mxCell',attrs);geo=ET.SubElement(cell,'mxGeometry',relative='1',attrib={'as':'geometry'})
        ET.SubElement(geo,'mxPoint',x=str(round(e['points'][0][0],2)),y=str(round(e['points'][0][1],2)),attrib={'as':'sourcePoint'})
        ET.SubElement(geo,'mxPoint',x=str(round(e['points'][-1][0],2)),y=str(round(e['points'][-1][1],2)),attrib={'as':'targetPoint'})
        if len(e['points'])>2:
            arr=ET.SubElement(geo,'Array',attrib={'as':'points'})
            for x,y in e['points'][1:-1]:ET.SubElement(arr,'mxPoint',x=str(round(x,2)),y=str(round(y,2)))
    for n in d.nodes:
        if n['kind'] not in ('frame','container'):vertex(n)
    return model


def mxfile(diagrams):
    root=ET.Element('mxfile',host='app.diagrams.net',agent='Inkafarma - modelo de análisis')
    for d in diagrams:
        page=ET.SubElement(root,'diagram',id=d.id,name=d.title)
        page.append(graph_model(d))
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)


def validate_data():
    seen=[]; count=0
    for g in GRUPOS:
        ids={id for id,_,_ in g['nodes']}; _,messages,_=events(g); msgids={m['id'] for m in messages}
        assert len(ids)==len(g['nodes']) and len(msgids)==len(messages)
        assert len(g['people'])<=5
        for a,b,_ in g['edges']: assert a in ids and b in ids
        for hu in g['hus']:
            seen.append(hu); assert len(g['coverage'][hu])==len(HISTORIAS[hu][1])
            for act,seq in g['coverage'][hu]:
                assert set(act.split(','))<=ids,(g['id'],hu,act)
                assert set(seq.split(','))<=msgids,(g['id'],hu,seq)
                count+=1
    assert sorted(seen)==sorted(HISTORIAS) and len(seen)==15 and count==46
    return count


def main():
    count=validate_data();OUT.mkdir(parents=True,exist_ok=True)
    all_diagrams=[usecases(),components()]
    paths=['generales/MCU.drawio','generales/componentes.drawio']
    for g in GRUPOS:
        for kind,fn in [('actividades',activity),('secuencia',sequence),('colaboracion',communication)]:
            all_diagrams.append(fn(g));paths.append(f"grupos/{g['id']}/{kind}.drawio")
    pdf=canvas.Canvas(str(OUT/'Inkafarma-modelo-UML.pdf'))
    pdf.setTitle('Inkafarma - Modelo UML por grupos de historias');pdf.setAuthor('Proyecto Ing.Software')
    qa=[]
    for page,(d,path) in enumerate(zip(all_diagrams,paths),1):
        for n in d.nodes:
            assert n['x']>=0 and n['y']>=0 and n['x']+n['w']<=d.w+1 and n['y']+n['h']<=d.h+1,(d.id,n)
        dest=OUT/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(mxfile([d]))
        pdf.bookmarkPage(d.id);pdf.addOutlineEntry(d.title,d.id,level=0)
        render_pdf(d,pdf)
        qa.append(dict(id=d.id,page=page,path=path,nodes=len(d.nodes),edges=len(d.edges),width=round(d.w),height=round(d.h)))
    pdf.save();(OUT/'Inkafarma-modelo-UML.drawio').write_bytes(mxfile(all_diagrams))
    rows=[]
    for g in GRUPOS:
        _,messages,_=events(g);numbers={m['id']:str(m['number']) for m in messages}
        for hu in g['hus']:
            for i,(act,seq) in enumerate(g['coverage'][hu]):
                rows.append([g['id'],hu,f'CA{i+1}',HISTORIAS[hu][1][i],act,','.join(numbers[id] for id in seq.split(',')),seq])
    with (OUT/'trazabilidad.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['Grupo','HU','Criterio','Resumen del criterio','Acciones de actividad','Mensajes secuencia/colaboracion','IDs de mensajes']);writer.writerows(rows)
    (OUT/'verificacion.json').write_text(json.dumps(dict(diagramas=qa,total=17,historias=15,criterios=count),indent=2,ensure_ascii=False),encoding='utf-8')
    guide='''INKAFARMA - MODELO UML POR GRUPOS DE HISTORIAS

Abre Inkafarma-modelo-UML.drawio en https://app.diagrams.net/
(Archivo > Abrir desde > Dispositivo). Tiene 17 pestañas editables.
Los mismos 17 diagramas están separados en generales/ y grupos/.
Inkafarma-modelo-UML.pdf permite leer y presentar los 17 diagramas.

G01 Consulta y comparación: HU01, HU07, HU13
G02 Compra y asistencia: HU04, HU08, HU10, HU11, HU12
G03 Reservas y asignación: HU02, HU03, HU09
G04 Seguimiento y entrega: HU05, HU15
G05 Inventario y alertas: HU06, HU14

Total: 1 MCU general + 1 componentes general + 5 actividades +
5 secuencia + 5 colaboración = 17 diagramas.
La matriz trazabilidad.csv relaciona los 46 criterios de aceptación.
Modelo de análisis funcional, no acreditación de funciones implementadas.

Fuente: HistoriasdeUsuario-Inkafarma.pdf, páginas 2-16.
Repositorio: https://github.com/seale-code/Ingenieria-de-software
'''
    (OUT/'LEEME.txt').write_text(guide,encoding='utf-8')
    included=[OUT/'Inkafarma-modelo-UML.pdf',OUT/'trazabilidad.csv',OUT/'verificacion.json',OUT/'LEEME.txt',*sorted(OUT.rglob('*.drawio'))]
    with zipfile.ZipFile(OUT/'Inkafarma-editables.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for file in included:
            archive.write(file,file.relative_to(OUT))
    print(json.dumps(dict(diagramas=len(all_diagrams),historias=15,criterios=count,salida=str(OUT)),ensure_ascii=False))


if __name__=='__main__': main()
