"""Reglas de asignacion de sucursal para pedidos: stock, distancia, capacidad y desempates (S2-01 / Issue #9)."""

from __future__ import annotations

import math

RADIO_TIERRA_KM = 6371.0088
CAPACIDAD_MAXIMA_DEFAULT = 10
TOLERANCIA_EMPATE_KM = 0.001

ESTADOS_PEDIDO_ACTIVO = frozenset(
    {"REGISTRADO", "ASIGNADO", "EN_PREPARACION", "PREPARADO"}
)


def validar_coordenadas(latitud: float, longitud: float) -> None:
    """Valida que la latitud [-90, 90] y longitud [-180, 180] sean numeros validos."""
    if isinstance(latitud, bool) or not isinstance(latitud, (int, float)):
        raise ValueError("La latitud debe ser un valor numerico.")
    if isinstance(longitud, bool) or not isinstance(longitud, (int, float)):
        raise ValueError("La longitud debe ser un valor numerico.")
    if not (-90.0 <= float(latitud) <= 90.0):
        raise ValueError("La latitud debe estar entre -90 y 90 grados.")
    if not (-180.0 <= float(longitud) <= 180.0):
        raise ValueError("La longitud debe estar entre -180 y 180 grados.")


def calcular_distancia_km(
    lat_origen: float,
    lon_origen: float,
    lat_destino: float,
    lon_destino: float,
) -> float:
    """Calcula la distancia ortodromica (Haversine) en kilometros redondeada a 3 decimales."""
    validar_coordenadas(lat_origen, lon_origen)
    validar_coordenadas(lat_destino, lon_destino)

    lat1 = math.radians(float(lat_origen))
    lon1 = math.radians(float(lon_origen))
    lat2 = math.radians(float(lat_destino))
    lon2 = math.radians(float(lon_destino))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return round(RADIO_TIERRA_KM * c, 3)


def validar_items_pedido(items_solicitados: dict[str, int]) -> None:
    """Verifica que el pedido contenga al menos un producto y cantidades enteras positivas."""
    if not isinstance(items_solicitados, dict) or not items_solicitados:
        raise ValueError("El pedido debe incluir al menos un producto solicitado.")

    for codigo, cantidad in items_solicitados.items():
        if not isinstance(codigo, str) or not codigo.strip():
            raise ValueError("Cada producto debe tener un codigo de texto no vacio.")
        if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad <= 0:
            raise ValueError(
                f"La cantidad solicitada para '{codigo}' debe ser un entero positivo."
            )


def evaluar_elegibilidad_sucursal(
    sucursal: dict,
    items_solicitados: dict[str, int],
    cliente_latitud: float,
    cliente_longitud: float,
) -> dict:
    """Evalua si una sucursal cumple stock y capacidad, y calcula sus metricas de asignacion.

    Estructura esperada de `sucursal`:
        - codigo: str (ej. 'DEMO-NORTE')
        - nombre: str (opcional)
        - latitud: float
        - longitud: float
        - stock_disponible: dict[str, int] (stock fisico menos reservas activas por producto)
        - pedidos_activos: int (por defecto 0)
        - capacidad_maxima: int (por defecto CAPACIDAD_MAXIMA_DEFAULT)
    """
    validar_items_pedido(items_solicitados)

    codigo = str(sucursal.get("codigo", "")).strip()
    if not codigo:
        raise ValueError("La sucursal debe tener un codigo valido.")

    pedidos_activos = int(sucursal.get("pedidos_activos", 0))
    capacidad_maxima = int(sucursal.get("capacidad_maxima", CAPACIDAD_MAXIMA_DEFAULT))

    if pedidos_activos < 0 or capacidad_maxima <= 0:
        raise ValueError("Los valores de capacidad y pedidos activos deben ser validos.")

    distancia_km = calcular_distancia_km(
        cliente_latitud,
        cliente_longitud,
        sucursal["latitud"],
        sucursal["longitud"],
    )

    inventario_sucursal = sucursal.get("stock_disponible", {}) or {}
    faltantes = []
    stock_total_pedido = 0

    for prod_codigo, cant_req in items_solicitados.items():
        disp = int(inventario_sucursal.get(prod_codigo, 0))
        if disp < cant_req:
            faltantes.append(prod_codigo)
        else:
            stock_total_pedido += disp

    cumple_stock = len(faltantes) == 0
    capacidad_disponible = capacidad_maxima - pedidos_activos
    cumple_capacidad = capacidad_disponible > 0

    if not cumple_stock:
        motivo = "STOCK_INSUFICIENTE"
    elif not cumple_capacidad:
        motivo = "CAPACIDAD_AGOTADA"
    else:
        motivo = "ELEGIBLE"

    return {
        "codigo": codigo,
        "nombre": sucursal.get("nombre", codigo),
        "elegible": cumple_stock and cumple_capacidad,
        "motivo": motivo,
        "cumple_stock": cumple_stock,
        "cumple_capacidad": cumple_capacidad,
        "productos_faltantes": faltantes,
        "distancia_km": distancia_km,
        "pedidos_activos": pedidos_activos,
        "capacidad_maxima": capacidad_maxima,
        "capacidad_disponible": max(0, capacidad_disponible),
        "stock_total_pedido": stock_total_pedido,
    }


def _clave_ordenamiento(evaluacion: dict) -> tuple:
    """Ordena candidatos elegibles por:
    1. Menor distancia en km (redondeada a 3 decimales).
    2. Mayor capacidad disponible (desempate 1).
    3. Mayor stock disponible acumulado para el pedido (desempate 2).
    4. Menor codigo de sucursal en orden alfabetico (desempate 3 determinista).
    """
    return (
        evaluacion["distancia_km"],
        -evaluacion["capacidad_disponible"],
        -evaluacion["stock_total_pedido"],
        evaluacion["codigo"],
    )


def asignar_sucursal_pedido(
    sucursales: list[dict],
    items_solicitados: dict[str, int],
    cliente_latitud: float,
    cliente_longitud: float,
) -> dict:
    """Aplica las reglas de asignacion S2-01 y devuelve la sucursal ganadora o el motivo de rechazo."""
    validar_items_pedido(items_solicitados)
    validar_coordenadas(cliente_latitud, cliente_longitud)

    if not sucursales:
        return {
            "asignada": False,
            "sucursal_asignada": None,
            "motivo_rechazo": "SIN_SUCURSALES_REGISTRADAS",
            "mensaje": "No existen sucursales registradas para evaluar el pedido.",
            "evaluaciones": [],
        }

    evaluaciones = [
        evaluar_elegibilidad_sucursal(
            sucursal=s,
            items_solicitados=items_solicitados,
            cliente_latitud=cliente_latitud,
            cliente_longitud=cliente_longitud,
        )
        for s in sucursales
    ]

    elegibles = [e for e in evaluaciones if e["elegible"]]

    if not elegibles:
        alguna_con_stock = any(e["cumple_stock"] for e in evaluaciones)
        if not alguna_con_stock:
            motivo = "SIN_STOCK_DISPONIBLE"
            mensaje = "Ninguna sucursal cuenta con stock disponible suficiente para cubrir el pedido."
        else:
            motivo = "SIN_CAPACIDAD_DISPONIBLE"
            mensaje = "Las sucursales con stock disponible han alcanzado su capacidad maxima de pedidos activos."

        return {
            "asignada": False,
            "sucursal_asignada": None,
            "motivo_rechazo": motivo,
            "mensaje": mensaje,
            "evaluaciones": evaluaciones,
        }

    ordenadas = sorted(elegibles, key=_clave_ordenamiento)
    ganadora = ordenadas[0]

    return {
        "asignada": True,
        "sucursal_asignada": ganadora["codigo"],
        "detalle_asignacion": ganadora,
        "motivo_rechazo": None,
        "mensaje": (
            f"Pedido asignado a la sucursal {ganadora['codigo']} "
            f"({ganadora['distancia_km']} km, capacidad libre: {ganadora['capacidad_disponible']})."
        ),
        "ranking_elegibles": [e["codigo"] for e in ordenadas],
        "evaluaciones": evaluaciones,
    }
