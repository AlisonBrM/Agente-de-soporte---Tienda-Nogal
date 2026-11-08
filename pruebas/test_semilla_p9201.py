"""Pruebas del pedido propio P-9201 (semilla): reembolso por reclamo abierto, bajo el tope."""
import json

from agente import herramientas  # noqa: F401  (registra las herramientas)
from agente.herramientas.registro import ejecutar
from agente.sesion import Sesion
from tienda import repositorio


def test_p9201_es_valido_y_tiene_un_reclamo_abierto():
    pedido = next(p for p in repositorio.leer_pedidos() if p.numero == "P-9201")
    assert (pedido.cliente_id, pedido.estado, pedido.total) == ("C-04", "entregado", 150_000)
    abiertos = [r for r in repositorio.leer_reclamos() if r.numero_pedido == "P-9201" and r.estado == "abierto"]
    assert len(abiertos) == 1


def test_p9201_reembolso_por_reclamo_queda_aprobado_sin_escalar():
    sesion = Sesion(cliente_id="C-04", turnos=1, ultimo_mensaje="Quiero el reembolso de P-9201")
    llamada = json.dumps({"numero": "P-9201"})
    assert ejecutar("solicitar_reembolso", llamada, sesion)["estado"] == "requiere_confirmacion"
    sesion.turnos, sesion.ultimo_mensaje = 2, "Sí"
    resultado = ejecutar("solicitar_reembolso", llamada, sesion)
    assert resultado["reembolso"]["estado"] == "aprobado"
    assert repositorio.leer_escalamientos() == []
