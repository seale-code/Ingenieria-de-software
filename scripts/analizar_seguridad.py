"""Repetir los controles de remediación con bases temporales desde la raíz."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import unittest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--salida', type=Path)
    parser.add_argument('--revision', default='copia de trabajo')
    args = parser.parse_args()
    suite = unittest.defaultTestLoader.discover('tests', pattern='test_remediacion.py')
    resultado = unittest.TextTestRunner(verbosity=2).run(suite)
    reporte = dict(fecha_utc=datetime.now(timezone.utc).isoformat(), revision=args.revision,
                   casos=resultado.testsRun, fallos=len(resultado.failures), errores=len(resultado.errors),
                   omitidos=len(resultado.skipped))
    if args.salida:
        args.salida.write_text(json.dumps(reporte, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if resultado.testsRun and resultado.wasSuccessful() and not resultado.skipped else 1)


if __name__=='__main__':
    main()
