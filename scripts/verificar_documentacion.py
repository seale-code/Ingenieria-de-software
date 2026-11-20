"""Comprobar enlaces locales de documentos modificados y trazabilidad de 46 criterios."""
import ast
import csv
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote,urlsplit

ROOT=Path(__file__).resolve().parents[1]


def verificar():
    errores=[]
    modificados=subprocess.check_output(['git','diff','--name-only','origin/main'],cwd=ROOT,text=True).splitlines()
    nuevos=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    documentos=sorted({p for p in modificados+nuevos if p.endswith('.md') and (ROOT/p).is_file()})
    for nombre in documentos:
        p=ROOT/nombre
        texto=re.sub(r'```.*?```','',p.read_text(encoding='utf-8-sig'),flags=re.S)
        for destino in re.findall(r'\]\(([^\s)]+)\)',texto):
            partes=urlsplit(destino.strip('<>'))
            if partes.scheme or partes.netloc or not partes.path: continue
            if not (p.parent/unquote(partes.path)).resolve().exists(): errores.append(f'{nombre}: enlace ausente {destino}')
    with (ROOT/'docs/03-diagramas/uml/trazabilidad.csv').open(encoding='utf-8-sig',newline='') as f:
        originales={(r['HU'],r['Criterio']):r for r in csv.DictReader(f)}
    with (ROOT/'docs/01-requisitos/TRAZABILIDAD_IMPLEMENTACION.csv').open(encoding='utf-8-sig',newline='') as f:
        filas=list(csv.DictReader(f))
    pares=[(r['HU'],r['Criterio']) for r in filas]
    if len(filas)!=46 or len(set(pares))!=46 or set(pares)!=set(originales): errores.append('La trazabilidad no coincide con los 46 criterios originales.')
    referencias=0
    for r in filas:
        if r['Criterio original resumido']!=originales[(r['HU'],r['Criterio'])]['Resumen del criterio']:
            errores.append(f"Criterio alterado: {r['HU']}/{r['Criterio']}")
        for ruta in filter(None,(r['Código']+';'+r['Diagramas']).split(';')):
            if not (ROOT/ruta).is_file(): errores.append(f'Archivo ausente: {ruta}')
        for referencia in filter(None,r['Pruebas'].split(';')):
            referencias+=1
            try:
                archivo,identificador=referencia.split('::');clase,metodo=identificador.split('.')
                arbol=ast.parse((ROOT/archivo).read_text(encoding='utf-8-sig'))
                encontrada=any(isinstance(c,ast.ClassDef) and c.name==clase and any(
                    isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==metodo for n in c.body) for c in arbol.body)
                if not encontrada: errores.append('Prueba ausente: '+referencia)
            except (ValueError,OSError,SyntaxError): errores.append('Referencia de prueba inválida: '+referencia)
        if r['Cobertura']=='Pendiente' and r['Pruebas']: errores.append('Un criterio pendiente no debe presentarse con prueba de aceptación cubierta.')
    return dict(documentos=len(documentos),criterios=len(filas),referencias_pruebas=referencias,errores=errores)


def main():
    import json
    resultado=verificar();print(json.dumps(resultado,ensure_ascii=False,indent=2))
    raise SystemExit(bool(resultado['errores']))


if __name__=='__main__': main()
