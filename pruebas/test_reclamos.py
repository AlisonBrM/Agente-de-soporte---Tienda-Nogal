"""Pruebas de registrar_reclamo. No llaman al modelo: ejecutan la herramienta directamente.

Fecha simulada de la tienda: HOY = 2026-11-02. El día de entrega cuenta como día 1,
así que el reclamo procede si (HOY - fecha_entrega).days < plazo.
"""
import json
from datetime import date

from agente import herramientas  # noqa: F401  (registra las herramientas)
from agente.herramientas.comun import PEDIDO_NO_ENCONTRADO
from agente.herramientas.registro import ejecutar
from agente.sesion import Sesion
from tienda import repositorio


def reclamar(cliente_id: str, numero: str, tipo="defectuoso", motivo="No funciona", producto=None) -> dict:
    args = {"numero": numero, "tipo": tipo, "motivo": motivo}
    if producto is not None:
        args["producto"] = producto
    return ejecutar("registrar_reclamo", json.dumps(args), Sesion(cliente_id=cliente_id))


def reclamos_de(numero: str) -> list:
    return [r for r in repositorio.leer_reclamos() if r.numero_pedido == numero]


# --- Casos que sí registran ---

def test_registra_reclamo_dentro_de_plazo():
    # P-1002: electrónica (90 días), entregado hace 13 días.
    resultado = reclamar("C-01", "P-1002", motivo="El audífono izquierdo no suena")
    assert resultado["registrado"] is True
    assert resultado["reclamo"]["estado"] == "abierto"
    nuevos = reclamos_de("P-1002")
    assert len(nuevos) == 1
    assert nuevos[0].cliente_id == "C-01"
    assert "El audífono izquierdo no suena" in nuevos[0].motivo
    assert "[defectuoso]" in nuevos[0].motivo


def test_id_consecutivo():
    resultado = reclamar("C-01", "P-1002")
    assert resultado["reclamo"]["id"] == "R-004"  # la semilla trae R-001, R-002 y R-003 (P-9201)


def test_reclamo_cerrado_no_bloquea_uno_nuevo():
    # P-1004 (C-02, preferente): ropa 30 + 15 = 45 días; entregado hace 43; R-002 está cerrado.
    resultado = reclamar("C-02", "P-1004", tipo="distinto", motivo="Llegó otro color")
    assert resultado["registrado"] is True


def test_preferente_suma_15_dias_tambien_en_perecederos():
    # P-1012 (C-05, preferente): perecedero 3 + 15 = 18 días; entregado hace 6.
    resultado = reclamar("C-05", "P-1012", motivo="Las flores llegaron marchitas")
    assert resultado["registrado"] is True


# --- Casos que se niegan ---

def test_pedido_de_otro_cliente():
    resultado = reclamar("C-01", "P-1007")
    assert resultado == {"error": PEDIDO_NO_ENCONTRADO}
    assert len(reclamos_de("P-1007")) == 1  # solo el R-001 que ya existía


def test_pedido_no_entregado():
    # P-1015 está enviado.
    resultado = reclamar("C-01", "P-1015")
    assert "entregado" in resultado["error"]
    assert reclamos_de("P-1015") == []


def test_ya_tiene_reclamo_abierto():
    # P-1007 (C-03) tiene R-001 abierto.
    resultado = reclamar("C-03", "P-1007", motivo="Otro problema")
    assert "R-001" in resultado["error"]
    assert len(reclamos_de("P-1007")) == 1


def test_fuera_de_plazo_regular():
    # P-1003 (C-01, regular): perecedero 3 días; entregado hace 8.
    resultado = reclamar("C-01", "P-1003", motivo="Fruta dañada")
    assert "plazo" in resultado["error"]
    assert reclamos_de("P-1003") == []


def test_fuera_de_plazo_aun_siendo_preferente():
    # P-1014 (C-05, preferente): hogar 15 + 15 = 30 días; entregado hace 93.
    resultado = reclamar("C-05", "P-1014")
    assert "plazo" in resultado["error"]


def test_motivo_vacio():
    resultado = reclamar("C-01", "P-1002", motivo="   ")
    assert "motivo" in resultado["error"].lower()
    assert reclamos_de("P-1002") == []


def test_tipo_fuera_de_la_politica():
    resultado = reclamar("C-01", "P-1002", tipo="no_me_gusto")
    assert "error" in resultado
    assert reclamos_de("P-1002") == []


# --- Límite del plazo (día de entrega = día 1) ---

def test_ultimo_dia_del_plazo_si_procede(monkeypatch):
    # P-1003: perecedero 3 días, entregado el 25 oct. El 27 oct es el día 3.
    monkeypatch.setattr(repositorio, "HOY", date(2026, 10, 27))
    assert reclamar("C-01", "P-1003")["registrado"] is True


def test_un_dia_despues_del_plazo_no_procede(monkeypatch):
    # El 28 oct sería el día 4.
    monkeypatch.setattr(repositorio, "HOY", date(2026, 10, 28))
    assert "plazo" in reclamar("C-01", "P-1003")["error"]


# --- Pedido con varios tipos de producto (P-1010: perecedero + electrónica) ---

def test_pedido_mixto_usa_el_plazo_del_producto_indicado(monkeypatch):
    # P-1010 entregado el 31 oct. El 5 nov: 5 días, pasó el plazo del perecedero (3) pero no el de electrónica (90).
    monkeypatch.setattr(repositorio, "HOY", date(2026, 11, 5))
    assert "plazo" in reclamar("C-04", "P-1010", producto="chocolates")["error"]
    assert reclamar("C-04", "P-1010", producto="parlante")["registrado"] is True


def test_pedido_mixto_sin_producto_usa_el_de_mayor_cobertura(monkeypatch):
    monkeypatch.setattr(repositorio, "HOY", date(2026, 11, 5))
    assert reclamar("C-04", "P-1010")["registrado"] is True


def test_producto_que_no_esta_en_el_pedido():
    resultado = reclamar("C-04", "P-1010", producto="televisor")
    assert "no está en el pedido" in resultado["error"]
    assert reclamos_de("P-1010") == []


# --- Pedido propio P-9001 (tienda/semilla): ropa entregada el 4 oct, cliente regular (30 días) ---

def test_p9001_ultimo_dia_del_plazo_si_procede():
    # HOY = 2 nov: 29 días después de la entrega, es decir, el día 30 contando el de entrega.
    resultado = reclamar("C-01", "P-9001", tipo="defectuoso", motivo="El pantalón llegó con una costura rota")
    assert resultado["registrado"] is True
    assert len(reclamos_de("P-9001")) == 1


def test_p9001_un_dia_despues_ya_no_procede(monkeypatch):
    # El 3 nov sería el día 31.
    monkeypatch.setattr(repositorio, "HOY", date(2026, 11, 3))
    assert "plazo" in reclamar("C-01", "P-9001")["error"]
    assert reclamos_de("P-9001") == []
