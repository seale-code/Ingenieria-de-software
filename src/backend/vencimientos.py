"""Supervisor local de reservas; WSGI puede ejecutar el mismo proceso por CLI."""
from contextlib import contextmanager
import logging
import math
import sqlite3
from threading import Event, Thread

from src.backend.logistica import procesar_vencimientos

logger = logging.getLogger(__name__)


@contextmanager
def vigilar_reservas(db_path, *, intervalo=30):
    """Revisa al iniciar y cada 30 s; se detiene al cerrar el servidor."""
    if not isinstance(intervalo, (int, float)) or isinstance(intervalo, bool) or not math.isfinite(intervalo) or intervalo <= 0:
        raise ValueError('El intervalo debe ser positivo.')
    detener = Event()

    def ejecutar():
        while not detener.is_set():
            try:
                procesar_vencimientos(db_path)
            except (sqlite3.Error, OSError, ValueError) as error:
                logger.error('No se completó la revisión de reservas: %s', type(error).__name__)
            detener.wait(intervalo)

    hilo = Thread(target=ejecutar, name='vencimientos-reservas', daemon=True)
    hilo.start()
    try:
        yield
    finally:
        detener.set()
        hilo.join(timeout=6)
