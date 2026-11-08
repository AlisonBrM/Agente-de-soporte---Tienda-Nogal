"""Pruebas de cancelar_pedido. No llaman al modelo: ejecutan la herramienta directamente.

Fecha simulada de la tienda: HOY = 2026-11-02.
"""
import json
from datetime import date, timedelta

import pytest

from agente import herramientas  # noqa: F401  (registra las herramientas)
from agente.herramientas.comun import PEDIDO_NO_ENCONTRADO
from agente.herramientas.registro import ejecutar
from agente.sesion import Sesion
from tienda import repositorio


def llamar_cancelar(sesion: Sesion, numero: str) -> dict:
    return ejecutar("cancelar_pedido", json.dumps({"numero": numero}), sesion)


def pedido_actual(numero: str) -> repositorio.Pedido:
    return next(p for p in repositorio.leer_pedidos() if p.numero == numero)


def reembolsos_de(numero: str) -> list[repositorio.Reembolso]:
    return [r for r in repositorio.leer_reembolsos() if r.numero_pedido == numero]


def escalamientos_de(numero: str) -> list[repositorio.Escalamiento]:
    return [e for e in repositorio.leer_escalamientos() if e.numero_pedido == numero]


# --- 1. Pedido inexistente o de otro cliente ---


def test_pedido_inexistente():
    pedidos_antes = repositorio.leer_pedidos()
    sesion = Sesion(cliente_id="C-01", turnos=1, ultimo_mensaje="Quiero cancelar P-9999")
    resultado = llamar_cancelar(sesion, "P-9999")

    assert resultado == {"error": PEDIDO_NO_ENCONTRADO}
    assert sesion.confirmaciones_pendientes == {}
    assert repositorio.leer_pedidos() == pedidos_antes
    assert repositorio.leer_reembolsos() == []
    assert repositorio.leer_escalamientos() == []


def test_pedido_de_otro_cliente_deja_datos_intactos():
    # P-1005 pertenece a C-02 (en_preparacion). C-01 intenta cancelarlo.
    pedidos_antes = repositorio.leer_pedidos()
    sesion = Sesion(cliente_id="C-01", turnos=1, ultimo_mensaje="Cancela P-1005")
    resultado = llamar_cancelar(sesion, "P-1005")

    assert resultado == {"error": PEDIDO_NO_ENCONTRADO}
    assert sesion.confirmaciones_pendientes == {}
    assert pedido_actual("P-1005").estado == "en_preparacion"
    assert repositorio.leer_pedidos() == pedidos_antes
    assert repositorio.leer_reembolsos() == []


# --- 2. Validación por estado y plazo ---


def test_pagado_pide_confirmacion():
    # P-1001 (C-01): estado "pagado", fecha_compra 2026-11-01, total 180000.
    sesion = Sesion(cliente_id="C-01", turnos=1, ultimo_mensaje="Quiero cancelar P-1001")
    resultado = llamar_cancelar(sesion, "P-1001")

    assert resultado["requiere_confirmacion"] is True
    assert resultado["pedido"] == "P-1001"
    assert sesion.confirmaciones_pendientes == {"cancelar:P-1001": 1}
    assert pedido_actual("P-1001").estado == "pagado"
    assert reembolsos_de("P-1001") == []


def test_en_preparacion_con_1_dia_pide_confirmacion(monkeypatch):
    # P-1005 (C-02): estado "en_preparacion", fecha_compra 2026-11-02.
    # Con HOY = 2026-11-03, (HOY - fecha_compra).days == 1 (<= 1).
    monkeypatch.setattr(repositorio, "HOY", date(2026, 11, 3))
    sesion = Sesion(cliente_id="C-02", turnos=1, ultimo_mensaje="Quiero cancelar P-1005")
    resultado = llamar_cancelar(sesion, "P-1005")

    assert resultado["requiere_confirmacion"] is True
    assert resultado["pedido"] == "P-1005"
    assert sesion.confirmaciones_pendientes == {"cancelar:P-1005": 1}
    assert pedido_actual("P-1005").estado == "en_preparacion"
    assert reembolsos_de("P-1005") == []


def test_en_preparacion_con_2_dias_se_niega_y_no_guarda_pendiente(monkeypatch):
    # P-1009 (C-03): en_preparacion, fecha_compra 2026-10-30 (3 días con HOY = 2026-11-02).
    sesion_p1009 = Sesion(cliente_id="C-03", turnos=1, ultimo_mensaje="Quiero cancelar P-1009")
    res_p1009 = llamar_cancelar(sesion_p1009, "P-1009")
    assert "error" in res_p1009
    assert sesion_p1009.confirmaciones_pendientes == {}
    assert pedido_actual("P-1009").estado == "en_preparacion"

    # P-1005 (C-02): fecha_compra 2026-11-02. Con HOY = 2026-11-04, (HOY - fecha_compra).days == 2 (> 1).
    monkeypatch.setattr(repositorio, "HOY", date(2026, 11, 4))
    sesion = Sesion(cliente_id="C-02", turnos=1, ultimo_mensaje="Quiero cancelar P-1005")
    resultado = llamar_cancelar(sesion, "P-1005")

    assert "error" in resultado
    assert "24 horas" in resultado["error"]
    assert sesion.confirmaciones_pendientes == {}
    assert pedido_actual("P-1005").estado == "en_preparacion"
    assert reembolsos_de("P-1005") == []


def test_enviado_entregado_y_cancelado_se_niegan_sin_guardar_pendiente():
    # P-1015 (C-01): enviado
    sesion_enviado = Sesion(cliente_id="C-01", turnos=1, ultimo_mensaje="Cancela P-1015")
    res_enviado = llamar_cancelar(sesion_enviado, "P-1015")
    assert "error" in res_enviado
    assert "puerta" in res_enviado["error"] and "reclamo" in res_enviado["error"]
    assert sesion_enviado.confirmaciones_pendientes == {}
    assert pedido_actual("P-1015").estado == "enviado"

    # P-1002 (C-01): entregado
    sesion_entregado = Sesion(cliente_id="C-01", turnos=1, ultimo_mensaje="Cancela P-1002")
    res_entregado = llamar_cancelar(sesion_entregado, "P-1002")
    assert "error" in res_entregado
    assert "entregado" in res_entregado["error"]
    assert sesion_entregado.confirmaciones_pendientes == {}
    assert pedido_actual("P-1002").estado == "entregado"

    # P-1008 (C-03): cancelado
    sesion_cancelado = Sesion(cliente_id="C-03", turnos=1, ultimo_mensaje="Cancela P-1008")
    res_cancelado = llamar_cancelar(sesion_cancelado, "P-1008")
    assert "error" in res_cancelado
    assert "cancelado" in res_cancelado["error"]
    assert sesion_cancelado.confirmaciones_pendientes == {}
    assert pedido_actual("P-1008").estado == "cancelado"


# --- 3. Mecanismo de confirmación en dos turnos ---


def test_primera_llamada_no_cambia_datos():
    # P-1001 (C-01): pagado, 180000
    pedidos_antes = repositorio.leer_pedidos()
    sesion = Sesion(cliente_id="C-01", turnos=1, ultimo_mensaje="sí, cancélalo de una vez")
    resultado = llamar_cancelar(sesion, "P-1001")

    assert resultado["requiere_confirmacion"] is True
    assert repositorio.leer_pedidos() == pedidos_antes
    assert repositorio.leer_reembolsos() == []
    assert repositorio.leer_escalamientos() == []


def test_segunda_llamada_en_el_mismo_turno_no_cancela():
    sesion = Sesion(cliente_id="C-01", turnos=1, ultimo_mensaje="sí")
    primera = llamar_cancelar(sesion, "P-1001")
    segunda = llamar_cancelar(sesion, "P-1001")

    assert primera["requiere_confirmacion"] is True
    assert segunda["requiere_confirmacion"] is True
    assert pedido_actual("P-1001").estado == "pagado"
    assert reembolsos_de("P-1001") == []


def test_turno_siguiente_con_si_cancela_y_crea_reembolso():
    sesion = Sesion(cliente_id="C-01", turnos=1, ultimo_mensaje="Quiero cancelar P-1001")
    llamar_cancelar(sesion, "P-1001")

    sesion.turnos = 2
    sesion.ultimo_mensaje = "sí"
    resultado = llamar_cancelar(sesion, "P-1001")

    assert resultado["cancelado"] is True
    assert sesion.confirmaciones_pendientes == {}
    assert pedido_actual("P-1001").estado == "cancelado"
    reembolsos = reembolsos_de("P-1001")
    assert len(reembolsos) == 1
    assert reembolsos[0].monto == 180000
    assert reembolsos[0].estado == "aprobado"
    assert reembolsos[0].fecha == repositorio.HOY


def test_turno_siguiente_con_mejor_no_no_cancela_y_borra_pendiente():
    sesion = Sesion(cliente_id="C-01", turnos=1, ultimo_mensaje="Quiero cancelar P-1001")
    llamar_cancelar(sesion, "P-1001")
    assert "cancelar:P-1001" in sesion.confirmaciones_pendientes

    sesion.turnos = 2
    sesion.ultimo_mensaje = "mejor no"
    resultado = llamar_cancelar(sesion, "P-1001")

    assert resultado["cancelado"] is False
    assert resultado["pedido"] == "P-1001"
    assert "requiere_confirmacion" not in resultado
    assert "cancelar:P-1001" not in sesion.confirmaciones_pendientes
    assert sesion.confirmaciones_pendientes == {}
    assert pedido_actual("P-1001").estado == "pagado"
    assert reembolsos_de("P-1001") == []

    # Si el cliente pide cancelar otra vez en un turno posterior, sí queda una pendiente nueva.
    sesion.turnos = 3
    sesion.ultimo_mensaje = "Ahora sí quiero cancelar P-1001"
    nuevo_intento = llamar_cancelar(sesion, "P-1001")

    assert nuevo_intento["requiere_confirmacion"] is True
    assert sesion.confirmaciones_pendientes == {"cancelar:P-1001": 3}
    assert pedido_actual("P-1001").estado == "pagado"


def test_si_dos_turnos_despues_no_cancela_porque_vencio():
    sesion = Sesion(cliente_id="C-01", turnos=1, ultimo_mensaje="Quiero cancelar P-1001")
    llamar_cancelar(sesion, "P-1001")

    # Dos turnos después (turno 3 en vez de turno 2)
    sesion.turnos = 3
    sesion.ultimo_mensaje = "sí"
    resultado = llamar_cancelar(sesion, "P-1001")

    assert resultado["requiere_confirmacion"] is True
    assert pedido_actual("P-1001").estado == "pagado"
    assert reembolsos_de("P-1001") == []


def test_confirmacion_de_otro_pedido_no_sirve():
    # Simulamos que en el turno 1 quedó pendiente otro pedido del cliente (ej. P-1002 o clave distinta)
    sesion = Sesion(cliente_id="C-01", turnos=1, ultimo_mensaje="Quiero cancelar")
    sesion.confirmaciones_pendientes["cancelar:P-1002"] = 1

    sesion.turnos = 2
    sesion.ultimo_mensaje = "sí, confirmo"
    resultado = llamar_cancelar(sesion, "P-1001")

    assert resultado["requiere_confirmacion"] is True
    assert pedido_actual("P-1001").estado == "pagado"
    assert reembolsos_de("P-1001") == []


# --- 4. Ejecución: reembolsos y escalamientos ---


def test_total_menor_o_igual_a_300000_deja_reembolso_aprobado():
    # P-1001 (C-01): pagado, total = 180000 (<= 300000)
    sesion = Sesion(cliente_id="C-01", turnos=1, ultimo_mensaje="Cancela P-1001")
    llamar_cancelar(sesion, "P-1001")

    sesion.turnos = 2
    sesion.ultimo_mensaje = "sí, de acuerdo"
    resultado = llamar_cancelar(sesion, "P-1001")

    assert resultado["cancelado"] is True
    assert pedido_actual("P-1001").estado == "cancelado"
    reembolsos = reembolsos_de("P-1001")
    assert len(reembolsos) == 1
    assert reembolsos[0].estado == "aprobado"
    assert reembolsos[0].monto == 180000
    assert reembolsos[0].cliente_id == "C-01"
    assert reembolsos[0].fecha == repositorio.HOY
    assert escalamientos_de("P-1001") == []


def test_total_mayor_a_300000_deja_reembolso_solicitado_y_escalamiento():
    # P-1013 (C-05): pagado, total = 2300000 (> 300000)
    sesion = Sesion(cliente_id="C-05", turnos=1, ultimo_mensaje="Cancela P-1013")
    llamar_cancelar(sesion, "P-1013")

    sesion.turnos = 2
    sesion.ultimo_mensaje = "sí"
    resultado = llamar_cancelar(sesion, "P-1013")

    assert resultado["cancelado"] is True
    assert pedido_actual("P-1013").estado == "cancelado"

    reembolsos = reembolsos_de("P-1013")
    assert len(reembolsos) == 1
    assert reembolsos[0].estado == "solicitado"
    assert reembolsos[0].monto == 2300000
    assert reembolsos[0].cliente_id == "C-05"
    assert reembolsos[0].fecha == repositorio.HOY

    escalamientos = escalamientos_de("P-1013")
    assert len(escalamientos) == 1
    assert escalamientos[0].cliente_id == "C-05"
    assert escalamientos[0].numero_pedido == "P-1013"
    assert escalamientos[0].fecha == repositorio.HOY
    assert escalamientos[0].resumen.strip() != ""


def test_no_duplica_un_reembolso_existente():
    # Pre-cargamos un reembolso existente para P-1001 (ya que semilla/reembolsos.json inicia vacío)
    reembolso_previo = repositorio.Reembolso(
        id="RE-001",
        numero_pedido="P-1001",
        cliente_id="C-01",
        fecha=repositorio.HOY,
        monto=180000,
        motivo="Reembolso previo",
        estado="aprobado",
    )
    repositorio.guardar_reembolsos([reembolso_previo])

    sesion = Sesion(cliente_id="C-01", turnos=1, ultimo_mensaje="Cancela P-1001")
    llamar_cancelar(sesion, "P-1001")

    sesion.turnos = 2
    sesion.ultimo_mensaje = "sí"
    resultado = llamar_cancelar(sesion, "P-1001")

    assert resultado["cancelado"] is True
    assert pedido_actual("P-1001").estado == "cancelado"
    reembolsos = reembolsos_de("P-1001")
    assert len(reembolsos) == 1
    assert reembolsos[0].id == "RE-001"
    assert reembolsos[0].motivo == "Reembolso previo"


# --- 5. Casos detallados de pedidos en_preparacion (P-1005, cliente C-02) ---


def test_en_preparacion_mismo_dia_0_dias_pide_confirmacion(monkeypatch):
    # P-1005 (C-02): en_preparacion, fecha_compra 2026-11-02, total 420000.
    monkeypatch.setattr(repositorio, "HOY", date(2026, 11, 2))
    sesion = Sesion(cliente_id="C-02", turnos=1, ultimo_mensaje="Quiero cancelar P-1005")
    resultado = llamar_cancelar(sesion, "P-1005")

    assert resultado["requiere_confirmacion"] is True
    assert resultado["pedido"] == "P-1005"
    assert sesion.confirmaciones_pendientes == {"cancelar:P-1005": 1}
    assert pedido_actual("P-1005").estado == "en_preparacion"
    assert reembolsos_de("P-1005") == []
    assert escalamientos_de("P-1005") == []


def test_en_preparacion_1_dia_confirmado_cancela_y_crea_reembolso(monkeypatch):
    # HOY = fecha_compra + 1 día (2026-11-03)
    monkeypatch.setattr(repositorio, "HOY", date(2026, 11, 3))
    sesion = Sesion(cliente_id="C-02", turnos=1, ultimo_mensaje="Quiero cancelar P-1005")
    primera = llamar_cancelar(sesion, "P-1005")

    assert primera["requiere_confirmacion"] is True
    assert pedido_actual("P-1005").estado == "en_preparacion"

    sesion.turnos = 2
    sesion.ultimo_mensaje = "sí"
    resultado = llamar_cancelar(sesion, "P-1005")

    assert resultado["cancelado"] is True
    assert sesion.confirmaciones_pendientes == {}
    assert pedido_actual("P-1005").estado == "cancelado"
    reembolsos = reembolsos_de("P-1005")
    assert len(reembolsos) == 1
    assert reembolsos[0].monto == 420000
    assert reembolsos[0].cliente_id == "C-02"
    assert reembolsos[0].fecha == date(2026, 11, 3)


def test_en_preparacion_2_dias_se_niega_con_mensaje_de_24_horas(monkeypatch):
    # HOY = fecha_compra + 2 días (2026-11-04)
    monkeypatch.setattr(repositorio, "HOY", date(2026, 11, 4))
    sesion = Sesion(cliente_id="C-02", turnos=1, ultimo_mensaje="Quiero cancelar P-1005")
    resultado = llamar_cancelar(sesion, "P-1005")

    assert "error" in resultado
    assert "24 horas" in resultado["error"]
    assert sesion.confirmaciones_pendientes == {}
    assert pedido_actual("P-1005").estado == "en_preparacion"
    assert reembolsos_de("P-1005") == []
    assert escalamientos_de("P-1005") == []


def test_en_preparacion_vencido_no_cancela_aunque_se_confirme(monkeypatch):
    # Con 2 días (2026-11-04), ni en el primer turno ni avanzando turno con "sí" se cancela
    monkeypatch.setattr(repositorio, "HOY", date(2026, 11, 4))
    sesion = Sesion(cliente_id="C-02", turnos=1, ultimo_mensaje="Quiero cancelar P-1005")
    primera = llamar_cancelar(sesion, "P-1005")
    assert "error" in primera

    sesion.turnos = 2
    sesion.ultimo_mensaje = "sí"
    segunda = llamar_cancelar(sesion, "P-1005")

    assert "error" in segunda
    assert "24 horas" in segunda["error"]
    assert sesion.confirmaciones_pendientes == {}
    assert pedido_actual("P-1005").estado == "en_preparacion"
    assert reembolsos_de("P-1005") == []
    assert escalamientos_de("P-1005") == []


def test_en_preparacion_1_dia_dice_no_en_turno_siguiente_no_cancela(monkeypatch):
    # Con 1 día (2026-11-03): pide confirmación; en el turno siguiente dice "mejor no"
    monkeypatch.setattr(repositorio, "HOY", date(2026, 11, 3))
    sesion = Sesion(cliente_id="C-02", turnos=1, ultimo_mensaje="Quiero cancelar P-1005")
    primera = llamar_cancelar(sesion, "P-1005")
    assert primera["requiere_confirmacion"] is True
    assert "cancelar:P-1005" in sesion.confirmaciones_pendientes

    sesion.turnos = 2
    sesion.ultimo_mensaje = "mejor no"
    resultado = llamar_cancelar(sesion, "P-1005")

    assert resultado["cancelado"] is False
    assert "requiere_confirmacion" not in resultado
    assert "cancelar:P-1005" not in sesion.confirmaciones_pendientes
    assert sesion.confirmaciones_pendientes == {}
    assert pedido_actual("P-1005").estado == "en_preparacion"
    assert reembolsos_de("P-1005") == []
    assert escalamientos_de("P-1005") == []


def test_en_preparacion_sobre_tope_1_dia_deja_reembolso_solicitado(monkeypatch):
    # P-1005 tiene total 420000 (> 300000): con 1 día y confirmación queda "solicitado" y escala
    monkeypatch.setattr(repositorio, "HOY", date(2026, 11, 3))
    sesion = Sesion(cliente_id="C-02", turnos=1, ultimo_mensaje="Quiero cancelar P-1005")
    llamar_cancelar(sesion, "P-1005")

    sesion.turnos = 2
    sesion.ultimo_mensaje = "sí"
    resultado = llamar_cancelar(sesion, "P-1005")

    assert resultado["cancelado"] is True
    assert pedido_actual("P-1005").estado == "cancelado"

    reembolsos = reembolsos_de("P-1005")
    assert len(reembolsos) == 1
    assert reembolsos[0].estado == "solicitado"
    assert reembolsos[0].monto == 420000
    assert reembolsos[0].cliente_id == "C-02"
    assert reembolsos[0].fecha == date(2026, 11, 3)

    escalamientos = escalamientos_de("P-1005")
    assert len(escalamientos) == 1
    assert escalamientos[0].numero_pedido == "P-1005"
    assert escalamientos[0].cliente_id == "C-02"
    assert escalamientos[0].fecha == date(2026, 11, 3)


@pytest.mark.parametrize(
    "dias,debe_pedir_confirmacion",
    [
        (0, True),
        (1, True),
        (2, False),
        (3, False),
        (10, False),
    ],
)
def test_en_preparacion_borde_exacto_parametrizado(monkeypatch, dias, debe_pedir_confirmacion):
    monkeypatch.setattr(repositorio, "HOY", date(2026, 11, 2) + timedelta(days=dias))
    sesion = Sesion(cliente_id="C-02", turnos=1, ultimo_mensaje="Quiero cancelar P-1005")
    resultado = llamar_cancelar(sesion, "P-1005")

    if debe_pedir_confirmacion:
        assert resultado["requiere_confirmacion"] is True
        assert sesion.confirmaciones_pendientes == {"cancelar:P-1005": 1}
    else:
        assert "error" in resultado
        assert "24 horas" in resultado["error"]
        assert sesion.confirmaciones_pendientes == {}

    assert pedido_actual("P-1005").estado == "en_preparacion"
    assert reembolsos_de("P-1005") == []
    assert escalamientos_de("P-1005") == []


def test_en_preparacion_otro_cliente_no_se_puede_cancelar(monkeypatch):
    monkeypatch.setattr(repositorio, "HOY", date(2026, 11, 2))
    pedidos_antes = repositorio.leer_pedidos()
    sesion = Sesion(cliente_id="C-01", turnos=1, ultimo_mensaje="Quiero cancelar P-1005")
    resultado = llamar_cancelar(sesion, "P-1005")

    assert resultado == {"error": PEDIDO_NO_ENCONTRADO}
    assert sesion.confirmaciones_pendientes == {}
    assert pedido_actual("P-1005").estado == "en_preparacion"
    assert repositorio.leer_pedidos() == pedidos_antes
    assert repositorio.leer_reembolsos() == []
    assert repositorio.leer_escalamientos() == []

