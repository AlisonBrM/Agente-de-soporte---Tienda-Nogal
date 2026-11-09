"""Pruebas de solicitar_reembolso. No llaman al modelo: ejecutan la herramienta directamente
y simulan los turnos de la conversación moviendo sesion.turnos y sesion.ultimo_mensaje.

Datos de la semilla que se usan:
- P-1008 (C-03): cancelado, $60.000.
- P-1007 (C-03): entregado, $1.850.000, con el reclamo abierto R-001.
- P-1004 (C-02): entregado, con el reclamo R-002 cerrado.
- P-1006 (C-02): enviado. P-1002 (C-01): entregado sin reclamos.
"""
import json

from agente import herramientas  # noqa: F401  (registra las herramientas)
from agente.herramientas.comun import PEDIDO_NO_ENCONTRADO
from agente.herramientas.reembolsos import ArgsSolicitarReembolso
from agente.herramientas.registro import ejecutar
from agente.sesion import Sesion
from tienda import repositorio


def turno(sesion: Sesion, mensaje: str) -> None:
    """El cliente escribe un mensaje: avanza el turno como lo hace el ciclo."""
    sesion.turnos += 1
    sesion.ultimo_mensaje = mensaje


def solicitar(sesion: Sesion, numero: str, monto: int | None = None) -> dict:
    args = {"numero": numero}
    if monto is not None:
        args["monto"] = monto
    return ejecutar("solicitar_reembolso", json.dumps(args), sesion)


def reembolsos() -> list:
    return repositorio.leer_reembolsos()


def escalamientos() -> list:
    return repositorio.leer_escalamientos()


def pedir_y_confirmar(sesion: Sesion, numero: str, monto: int | None = None) -> dict:
    """Turno 1: el cliente pide. Turno 2: confirma con «sí». Devuelve la respuesta del turno 2."""
    turno(sesion, "Quiero que me reembolsen ese pedido")
    assert solicitar(sesion, numero, monto)["estado"] == "requiere_confirmacion"
    turno(sesion, "Sí")
    return solicitar(sesion, numero, monto)


# --- Flujo normal ---

def test_pedido_cancelado_pide_confirmacion_y_luego_aprueba():
    sesion = Sesion(cliente_id="C-03")
    turno(sesion, "Quiero el reembolso de P-1008")
    primera = solicitar(sesion, "P-1008")
    assert primera["estado"] == "requiere_confirmacion"
    assert "$60.000" in primera["resumen"]
    assert reembolsos() == []  # todavía no se registró nada

    turno(sesion, "Sí, confirmo")
    segunda = solicitar(sesion, "P-1008")
    assert segunda["registrado"] is True
    assert segunda["reembolso"]["estado"] == "aprobado"
    assert segunda["escalado"] is False
    [r] = reembolsos()
    assert (r.numero_pedido, r.cliente_id, r.monto, r.estado) == ("P-1008", "C-03", 60_000, "aprobado")
    assert escalamientos() == []


def test_monto_explicito_igual_al_total_es_valido():
    resultado = pedir_y_confirmar(Sesion(cliente_id="C-03"), "P-1008", 60_000)
    assert resultado["registrado"] is True


def test_reclamo_abierto_sobre_el_tope_queda_solicitado_y_escala():
    resultado = pedir_y_confirmar(Sesion(cliente_id="C-03"), "P-1007")
    assert resultado["reembolso"]["estado"] == "solicitado"
    assert resultado["escalado"] is True
    assert "un día hábil" in resultado["aviso_al_cliente"]
    [r] = reembolsos()
    assert (r.monto, r.estado) == (1_850_000, "solicitado")
    [e] = escalamientos()
    assert (e.motivo, e.numero_pedido, e.cliente_id) == ("reembolso_sobre_tope", "P-1007", "C-03")


def test_el_resumen_avisa_que_un_asesor_debe_aprobar_si_supera_el_tope():
    sesion = Sesion(cliente_id="C-03")
    turno(sesion, "Quiero el reembolso de P-1007")
    assert "asesor" in solicitar(sesion, "P-1007")["resumen"]


# --- La confirmación no se puede saltar ---

def test_no_ejecuta_en_el_mismo_turno_aunque_la_herramienta_se_llame_dos_veces():
    sesion = Sesion(cliente_id="C-03")
    turno(sesion, "Quiero el reembolso de P-1008")
    assert solicitar(sesion, "P-1008")["estado"] == "requiere_confirmacion"
    assert solicitar(sesion, "P-1008")["estado"] == "requiere_confirmacion"
    assert reembolsos() == []


def test_un_si_sin_propuesta_previa_no_ejecuta():
    sesion = Sesion(cliente_id="C-03")
    turno(sesion, "Sí")
    assert solicitar(sesion, "P-1008")["estado"] == "requiere_confirmacion"
    assert reembolsos() == []


def test_si_el_cliente_se_arrepiente_no_ejecuta():
    sesion = Sesion(cliente_id="C-03")
    turno(sesion, "Quiero el reembolso de P-1008")
    solicitar(sesion, "P-1008")
    turno(sesion, "Mejor no")
    assert solicitar(sesion, "P-1008")["estado"] == "requiere_confirmacion"
    assert reembolsos() == []


def test_confirmar_otro_pedido_no_ejecuta():
    sesion = Sesion(cliente_id="C-03")
    turno(sesion, "Quiero el reembolso de P-1008")
    solicitar(sesion, "P-1008")
    turno(sesion, "Sí")
    # El cliente confirmó P-1008, no P-1007.
    assert solicitar(sesion, "P-1007")["estado"] == "requiere_confirmacion"
    assert reembolsos() == []


# --- Reglas que la herramienta se niega a saltarse (y no pide confirmación) ---

def test_pedido_enviado_sin_reclamo_es_error():
    sesion = Sesion(cliente_id="C-02")
    turno(sesion, "Quiero el reembolso de P-1006")
    resultado = solicitar(sesion, "P-1006")
    assert "error" in resultado and "enviado" in resultado["error"]
    assert sesion.confirmaciones_pendientes == {}
    assert reembolsos() == []


def test_pedido_entregado_sin_reclamo_es_error():
    sesion = Sesion(cliente_id="C-01")
    turno(sesion, "Quiero el reembolso de P-1002")
    assert "reclamo" in solicitar(sesion, "P-1002")["error"]
    assert reembolsos() == []


def test_reclamo_cerrado_no_habilita_el_reembolso():
    sesion = Sesion(cliente_id="C-02")
    turno(sesion, "Quiero el reembolso de P-1004")
    assert "error" in solicitar(sesion, "P-1004")
    assert reembolsos() == []


def test_pedido_de_otro_cliente_es_error():
    sesion = Sesion(cliente_id="C-01")
    turno(sesion, "Quiero el reembolso de P-1008")
    assert solicitar(sesion, "P-1008")["error"] == PEDIDO_NO_ENCONTRADO
    assert reembolsos() == []


def test_pedido_inexistente_da_el_mismo_error_que_uno_ajeno():
    sesion = Sesion(cliente_id="C-01")
    turno(sesion, "Quiero el reembolso de P-9999")
    assert solicitar(sesion, "P-9999")["error"] == PEDIDO_NO_ENCONTRADO


def test_monto_mayor_al_pagado_es_error():
    sesion = Sesion(cliente_id="C-03")
    turno(sesion, "Quiero que me devuelvan 70.000 de P-1008")
    resultado = solicitar(sesion, "P-1008", 70_000)
    assert "superar" in resultado["error"]
    assert sesion.confirmaciones_pendientes == {}


def test_monto_menor_al_pagado_es_error():
    sesion = Sesion(cliente_id="C-03")
    turno(sesion, "Quiero que me devuelvan 30.000 de P-1008")
    assert "valor total" in solicitar(sesion, "P-1008", 30_000)["error"]
    assert reembolsos() == []


def test_segundo_reembolso_del_mismo_pedido_es_error_e_informa_el_primero():
    sesion = Sesion(cliente_id="C-03")
    pedir_y_confirmar(sesion, "P-1008")
    turno(sesion, "Quiero otro reembolso de P-1008")
    resultado = solicitar(sesion, "P-1008")
    assert "RE-001" in resultado["error"] and "aprobado" in resultado["error"]
    assert len(reembolsos()) == 1


def test_el_cliente_sale_de_la_sesion():
    assert "cliente_id" not in ArgsSolicitarReembolso.model_fields
