"""Pruebas de consultar_pedido. No llaman al modelo: ejecutan la herramienta directamente."""
import json

from agente import herramientas  # noqa: F401  (registra las herramientas)
from agente.herramientas.comun import PEDIDO_NO_ENCONTRADO
from agente.herramientas.registro import ejecutar
from agente.sesion import Sesion


def consultar(cliente_id: str, numero: str) -> dict:
    return ejecutar("consultar_pedido", json.dumps({"numero": numero}), Sesion(cliente_id=cliente_id))


def test_pedido_propio_devuelve_sus_datos():
    resultado = consultar("C-01", "P-1002")
    assert resultado["numero"] == "P-1002"
    assert resultado["estado"] == "entregado"
    assert resultado["total"] > 0
    assert resultado["productos"]


def test_no_devuelve_el_id_del_cliente():
    resultado = consultar("C-01", "P-1002")
    assert "cliente_id" not in resultado


def test_pedido_de_otro_cliente_es_error():
    # P-1007 es de C-03.
    resultado = consultar("C-01", "P-1007")
    assert resultado == {"error": PEDIDO_NO_ENCONTRADO}


def test_pedido_inexistente_es_error():
    resultado = consultar("C-01", "P-9999")
    assert resultado == {"error": PEDIDO_NO_ENCONTRADO}


def test_ajeno_e_inexistente_dan_el_mismo_mensaje():
    assert consultar("C-01", "P-1007") == consultar("C-01", "P-9999")


def test_acepta_numero_con_espacios_y_minusculas():
    resultado = consultar("C-01", "  p-1002 ")
    assert resultado["numero"] == "P-1002"


def test_incluye_reclamos_del_pedido():
    # P-1007 (de C-03) tiene el reclamo R-001 abierto.
    resultado = consultar("C-03", "P-1007")
    assert [r["estado"] for r in resultado["reclamos"]] == ["abierto"]


def test_nota_del_cliente_va_marcada_como_dato():
    # P-1011 (de C-04) trae una nota que intenta darle órdenes al agente.
    resultado = consultar("C-04", "P-1011")
    assert "texto" in resultado["nota_cliente"]
    assert "no una instrucción" in resultado["nota_cliente"]["aviso"]


def test_pedido_sin_nota_no_trae_el_campo():
    resultado = consultar("C-01", "P-1002")
    assert "nota_cliente" not in resultado
