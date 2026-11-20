"""Contrato histórico para suites S1–S3 con fixtures anteriores al acceso individual."""
from pathlib import Path
from tempfile import gettempdir
from src.backend.app import _crear_base


def create_fixture(db_path, *, demo_key=None, operations_key=None):
    if not Path(db_path).resolve().is_relative_to(Path(gettempdir()).resolve()):
        raise ValueError('Los fixtures históricos necesitan una base en un directorio temporal.')
    app = _crear_base(db_path)
    app.config.update(FIXTURE_HISTORICO=True, DEMO_KEY=operations_key if operations_key is not None else demo_key,
                      TRUSTED_HOSTS=['localhost','127.0.0.1','[::1]'])
    return app
