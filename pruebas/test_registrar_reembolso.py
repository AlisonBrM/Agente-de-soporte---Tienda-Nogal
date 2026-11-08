"""Pruebas de registrar_reembolso (comun.py), la función que comparten solicitar_reembolso y
cancelar_pedido. No llaman al modelo."""
import pytest

from agente.herramientas.comun import PEDIDO_NO_ENCONTRADO, TOPE_REEMBOLSO, registrar_reembolso
from agente.herramientas.registro import ErrorDeHerramienta
from agente.sesion import Sesion
from tienda import repositorio


def pedido(numero: str):
    return next(p for p in repositorio.leer_pedidos() if p.numero == numero)


def con_total(numero: str, total: int):
    """Copia del pedido con otro total, para probar los bordes del tope."""
    return pedido(numero).model_copy(update={"total": total})


def reembolsos() -> list:
    return repositorio.leer_reembolsos()


def escalamientos() -> list:
    return repositorio.leer_escalamientos()


# --- Dentro y fuera del tope ---

def test_hasta_el_tope_queda_aprobado_y_no_escala():
    # P-1001 (C-01) vale $180.000.
    r = registrar_reembolso(Sesion(cliente_id="C-01"), pedido("P-1001"), 180_000, "Cancelación del pedido")
    assert r.estado == "aprobado"
    assert r.id == "RE-001"
    assert r.cliente_id == "C-01"
    assert r.fecha == repositorio.HOY
    assert reembolsos() == [r]
    assert escalamientos() == []


def test_justo_en_el_tope_queda_aprobado():
    r = registrar_reembolso(Sesion(cliente_id="C-01"), con_total("P-1001", TOPE_REEMBOLSO), TOPE_REEMBOLSO, "x")
    assert r.estado == "aprobado"
    assert escalamientos() == []


def test_un_peso_sobre_el_tope_queda_solicitado_y_escala():
    r = registrar_reembolso(
        Sesion(cliente_id="C-01"), con_total("P-1001", TOPE_REEMBOLSO + 1), TOPE_REEMBOLSO + 1, "x"
    )
    assert r.estado == "solicitado"
    [e] = escalamientos()
    assert e.motivo == "reembolso_sobre_tope"
    assert e.numero_pedido == "P-1001"
    assert e.cliente_id == "C-01"


def test_pedido_grande_queda_solicitado_y_escala_con_resumen():
    # P-1007 (C-03) vale $1.850.000.
    r = registrar_reembolso(Sesion(cliente_id="C-03"), pedido("P-1007"), 1_850_000, "Producto defectuoso")
    assert r.estado == "solicitado"
    [e] = escalamientos()
    assert "$1.850.000" in e.resumen
    assert "Producto defectuoso" in e.resumen


# --- Reglas que la función se niega a saltarse ---

def test_pedido_de_otro_cliente_es_error():
    with pytest.raises(ErrorDeHerramienta) as error:
        registrar_reembolso(Sesion(cliente_id="C-01"), pedido("P-1007"), 1_850_000, "x")
    assert str(error.value) == PEDIDO_NO_ENCONTRADO
    assert reembolsos() == [] and escalamientos() == []


def test_monto_mayor_al_pagado_es_error():
    with pytest.raises(ErrorDeHerramienta, match="no puede superar"):
        registrar_reembolso(Sesion(cliente_id="C-01"), pedido("P-1001"), 180_001, "x")
    assert reembolsos() == []


def test_monto_menor_al_pagado_es_error():
    with pytest.raises(ErrorDeHerramienta, match="valor total"):
        registrar_reembolso(Sesion(cliente_id="C-01"), pedido("P-1001"), 100_000, "x")
    assert reembolsos() == []


@pytest.mark.parametrize("monto", [0, -5000])
def test_monto_cero_o_negativo_es_error(monto):
    with pytest.raises(ErrorDeHerramienta, match="mayor que cero"):
        registrar_reembolso(Sesion(cliente_id="C-01"), pedido("P-1001"), monto, "x")
    assert reembolsos() == []


def test_motivo_vacio_es_error():
    with pytest.raises(ErrorDeHerramienta, match="motivo"):
        registrar_reembolso(Sesion(cliente_id="C-01"), pedido("P-1001"), 180_000, "   ")
    assert reembolsos() == []


def test_segundo_reembolso_del_mismo_pedido_es_error_e_informa_el_primero():
    sesion = Sesion(cliente_id="C-01")
    registrar_reembolso(sesion, pedido("P-1001"), 180_000, "Cancelación")
    with pytest.raises(ErrorDeHerramienta, match="RE-001") as error:
        registrar_reembolso(sesion, pedido("P-1001"), 180_000, "Otra vez")
    assert "aprobado" in str(error.value)
    assert len(reembolsos()) == 1


def test_ids_consecutivos_en_pedidos_distintos():
    registrar_reembolso(Sesion(cliente_id="C-01"), pedido("P-1001"), 180_000, "x")
    r2 = registrar_reembolso(Sesion(cliente_id="C-03"), pedido("P-1008"), 60_000, "x")
    assert r2.id == "RE-002"
