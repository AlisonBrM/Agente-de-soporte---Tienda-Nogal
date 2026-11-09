"""Pruebas unitarias para el mecanismo de confirmación."""
import pytest

from agente.herramientas.confirmacion import (
    es_afirmativo,
    registrar_pendiente,
    verificar_confirmacion,
)
from agente.sesion import Sesion


def test_mismo_turno_no_confirma():
    sesion = Sesion(cliente_id="C-01", turnos=1, ultimo_mensaje="sí, cancélalo")
    registrar_pendiente(sesion, "cancelar:P-1001")

    assert verificar_confirmacion(sesion, "cancelar:P-1001") is False
    assert "cancelar:P-1001" in sesion.confirmaciones_pendientes


def test_turno_siguiente_con_si_confirma_y_borra_pendiente():
    sesion = Sesion(cliente_id="C-01", turnos=1, ultimo_mensaje="quiero cancelar P-1001")
    registrar_pendiente(sesion, "cancelar:P-1001")

    sesion.turnos = 2
    sesion.ultimo_mensaje = "Sí, cancélalo"

    assert verificar_confirmacion(sesion, "cancelar:P-1001") is True
    assert "cancelar:P-1001" not in sesion.confirmaciones_pendientes


def test_turno_siguiente_con_mejor_no_no_confirma_y_borra_pendiente():
    sesion = Sesion(cliente_id="C-01", turnos=1, ultimo_mensaje="quiero cancelar P-1001")
    registrar_pendiente(sesion, "cancelar:P-1001")

    sesion.turnos = 2
    sesion.ultimo_mensaje = "mejor no"

    assert verificar_confirmacion(sesion, "cancelar:P-1001") is False
    assert "cancelar:P-1001" not in sesion.confirmaciones_pendientes


def test_clave_distinta_otro_monto_no_confirma():
    sesion = Sesion(cliente_id="C-01", turnos=1, ultimo_mensaje="reembolsar P-1001")
    registrar_pendiente(sesion, "reembolso:P-1001:50000")

    sesion.turnos = 2
    sesion.ultimo_mensaje = "sí, confirmo"

    assert verificar_confirmacion(sesion, "reembolso:P-1001:90000") is False
    assert "reembolso:P-1001:50000" in sesion.confirmaciones_pendientes


def test_una_confirmacion_no_se_reutiliza():
    sesion = Sesion(cliente_id="C-01", turnos=1, ultimo_mensaje="cancelar P-1001")
    registrar_pendiente(sesion, "cancelar:P-1001")

    sesion.turnos = 2
    sesion.ultimo_mensaje = "confirmo"

    assert verificar_confirmacion(sesion, "cancelar:P-1001") is True
    assert verificar_confirmacion(sesion, "cancelar:P-1001") is False


@pytest.mark.parametrize(
    "frase",
    [
        "si",
        "¡Sí!",
        "confirmo",
        "dale",
        "ok",
        "claro",
        "adelante",
        "sí, cancélalo",
        "si, cancelalo",
        "Si, confirmo la cancelación",
        "De acuerdo, procede",
        "sí por favor",
        "Sí.",
    ],
)
def test_frases_afirmativas(frase):
    assert es_afirmativo(frase) is True


@pytest.mark.parametrize(
    "frase",
    [
        "",
        "no",
        "mejor no",
        "espera",
        "todavía",
        "todavia no",
        "cancelar no",
        "sí pero espera un momento",
        "no, gracias",
        "¿qué pasa si lo cancelo?",
        "dime que pasa si cancelo",
        # Duda o condiciones: no cuentan como confirmación.
        "bueno, déjame pensarlo",
        "ok, pero primero dime cuánto me devuelven",
        "claro, aunque prefiero esperar",
        "quiero confirmar algo primero",
        # "si" condicional, no afirmativo.
        "si me explicas por qué",
        "si puedes, dime el estado del pedido",
        # Pregunta, aunque diga "sí".
        "¿sí?",
    ],
)
def test_frases_negativas_o_con_duda(frase):
    assert es_afirmativo(frase) is False


def test_pendiente_vence_si_pasa_mas_de_un_turno():
    # Propuesta en el turno 1; el cliente dice "ok" en el turno 3 (por otro tema).
    sesion = Sesion(cliente_id="C-01", turnos=1, ultimo_mensaje="quiero cancelar P-1001")
    registrar_pendiente(sesion, "cancelar:P-1001")

    sesion.turnos = 3
    sesion.ultimo_mensaje = "ok"

    assert verificar_confirmacion(sesion, "cancelar:P-1001") is False
    # La pendiente se descarta: el agente debe volver a preguntar.
    assert "cancelar:P-1001" not in sesion.confirmaciones_pendientes


def test_turno_siguiente_exacto_si_confirma():
    # Control del caso anterior: en el turno 2 (el siguiente) el mismo "ok" sí confirma.
    sesion = Sesion(cliente_id="C-01", turnos=1, ultimo_mensaje="quiero cancelar P-1001")
    registrar_pendiente(sesion, "cancelar:P-1001")

    sesion.turnos = 2
    sesion.ultimo_mensaje = "ok"

    assert verificar_confirmacion(sesion, "cancelar:P-1001") is True
