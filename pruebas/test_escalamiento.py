"""Pruebas de escalar_a_asesor. No llaman al modelo: ejecutan la herramienta directamente."""
import json

from agente import herramientas  # noqa: F401  (registra las herramientas)
from agente.herramientas.escalamiento import ArgsEscalarAAsesor
from agente.herramientas.registro import ejecutar
from agente.sesion import Sesion
from tienda import repositorio


def escalar(cliente_id: str, motivo="pide_asesor", resumen="El cliente pidió hablar con una persona.",
            numero_pedido=None) -> dict:
    args = {"motivo": motivo, "resumen": resumen}
    if numero_pedido is not None:
        args["numero_pedido"] = numero_pedido
    return ejecutar("escalar_a_asesor", json.dumps(args), Sesion(cliente_id=cliente_id))


def guardados() -> list:
    return repositorio.leer_escalamientos()


# --- Casos que sí escalan ---

def test_cliente_pide_asesor_sin_pedido():
    resultado = escalar("C-01")
    assert resultado["escalado"] is True
    assert "un día hábil" in resultado["aviso_al_cliente"]
    [e] = guardados()
    assert e.id == "E-001"
    assert e.cliente_id == "C-01"
    assert e.numero_pedido is None
    assert e.resumen == "El cliente pidió hablar con una persona."


def test_cobro_no_reconocido_con_pedido_propio_lo_asocia():
    resultado = escalar("C-01", "cobro_no_reconocido", "Dice que le cobraron dos veces.", "p-1002")
    assert resultado["escalado"] is True
    [e] = guardados()
    assert e.numero_pedido == "P-1002"
    assert e.motivo == "cobro_no_reconocido"


def test_reembolso_sobre_el_tope_con_pedido_propio():
    # P-1007 (C-03) vale $1.850.000.
    resultado = escalar("C-03", "reembolso_sobre_tope", "Pide reembolso total de P-1007.", "P-1007")
    assert resultado["escalado"] is True
    [e] = guardados()
    assert e.numero_pedido == "P-1007"


def test_ids_consecutivos():
    escalar("C-01", "pide_asesor", "Primer caso.")
    escalar("C-02", "pide_asesor", "Segundo caso.")
    assert [e.id for e in guardados()] == ["E-001", "E-002"]


def test_el_cliente_sale_de_la_sesion():
    assert "cliente_id" not in ArgsEscalarAAsesor.model_fields
    escalar("C-04")
    assert guardados()[0].cliente_id == "C-04"


# --- Pedido ajeno o inexistente: se escala sin asociarlo ni revelar nada ---

def test_pedido_ajeno_escala_sin_asociarlo_ni_revelarlo():
    resultado = escalar("C-01", "cobro_no_reconocido", "Cobro que no reconoce.", "P-1007")
    assert resultado["escalado"] is True
    assert guardados()[0].numero_pedido is None
    assert "P-1007" not in json.dumps(resultado)


def test_pedido_inexistente_da_la_misma_respuesta_que_uno_ajeno():
    ajeno = escalar("C-01", "pide_asesor", "Quiere un asesor.", "P-1007")
    repositorio.restablecer()
    inexistente = escalar("C-01", "pide_asesor", "Quiere un asesor.", "P-9999")
    assert ajeno == inexistente


# --- Reglas que la herramienta se niega a saltarse ---

def test_resumen_vacio_es_error_y_no_guarda():
    resultado = escalar("C-01", resumen="   ")
    assert "error" in resultado
    assert guardados() == []


def test_reembolso_sobre_tope_sin_pedido_es_error():
    resultado = escalar("C-03", "reembolso_sobre_tope", "Quiere un reembolso grande.")
    assert "error" in resultado
    assert guardados() == []


def test_reembolso_sobre_tope_con_pedido_ajeno_es_error():
    resultado = escalar("C-01", "reembolso_sobre_tope", "Reembolso de P-1007.", "P-1007")
    assert "error" in resultado
    assert guardados() == []


def test_reembolso_sobre_tope_con_pedido_que_no_supera_el_tope_es_error():
    # P-1001 (C-01) vale $180.000: lo aprueba el equipo, no hay que escalarlo.
    resultado = escalar("C-01", "reembolso_sobre_tope", "Reembolso de P-1001.", "P-1001")
    assert "error" in resultado
    assert guardados() == []


def test_motivo_fuera_de_la_politica_es_argumento_invalido():
    resultado = escalar("C-01", "me_cae_mal_el_sistema")
    assert resultado["error"] == "Argumentos inválidos."
    assert guardados() == []


def test_mismo_caso_el_mismo_dia_no_se_duplica():
    escalar("C-01", "pide_asesor", "Primera vez.")
    escalar("C-01", "pide_asesor", "El cliente insiste.")
    assert len(guardados()) == 1
