"""Criterios técnicos de asignación para S2-04, sujetos a aprobación de S2-01.

Solo califican sucursales con stock para TODO el pedido y capacidad libre.
Entre las elegibles: menor distancia geodésica; luego mayor capacidad libre;
y, si persiste el empate, menor código de sucursal (orden alfabético).
"""

from math import asin, cos, radians, sin, sqrt


def distancia_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia Haversine aproximada (línea recta, no tiempo de carretera)."""
    radio_tierra = 6371.0088
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    valor = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * radio_tierra * asin(min(1.0, sqrt(max(0.0, valor))))


def ordenar_candidatas(candidatas: list[dict]) -> list[dict]:
    """No muta los datos de entrada; desempate reproducible."""
    return sorted(
        candidatas,
        key=lambda s: (s["distancia_km"], -s["capacidad_libre"], s["codigo"]),
    )
