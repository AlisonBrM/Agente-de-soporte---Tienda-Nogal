"""Registro de reclamos sobre pedidos entregados."""
import unicodedata
from typing import Literal

from pydantic import BaseModel, Field

from agente.herramientas.comun import pedido_del_cliente
from agente.herramientas.registro import ErrorDeHerramienta, herramienta
from agente.sesion import Sesion
from tienda import repositorio

# Plazo para reclamar, en días calendario desde la entrega (política de reclamos).
PLAZOS_DIAS = {"perecedero": 3, "hogar": 15, "ropa": 30, "electronica": 90}
DIAS_EXTRA_PREFERENTE = 15


class ArgsRegistrarReclamo(BaseModel):
    numero: str = Field(description="Número del pedido sobre el que se reclama, por ejemplo P-1002.")
    tipo: Literal["defectuoso", "incompleto", "distinto"] = Field(
        description="Tipo de problema: 'defectuoso' (llegó dañado o no funciona), 'incompleto' "
        "(faltan productos o partes) o 'distinto' (llegó algo diferente a lo comprado)."
    )
    motivo: str = Field(
        description="El problema descrito con las palabras del cliente. Si el cliente no lo ha dicho, "
        "pregúntaselo antes de llamar esta herramienta; no lo inventes."
    )
    producto: str | None = Field(
        default=None,
        description="Nombre del producto con el problema, si el pedido tiene varios productos.",
    )


def _sin_tildes(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn"
    ).strip()


def _plazo_dias(pedido: repositorio.Pedido, producto: str | None, preferente: bool) -> int:
    """Plazo del producto reclamado; si no se indica, el de mayor cobertura del pedido (ANALISIS.md)."""
    if producto:
        buscado = _sin_tildes(producto)
        coincidencias = [p for p in pedido.productos if buscado in _sin_tildes(p.nombre)]
        if not coincidencias:
            nombres = ", ".join(p.nombre for p in pedido.productos)
            raise ErrorDeHerramienta(f"Ese producto no está en el pedido. Productos del pedido: {nombres}.")
        base = PLAZOS_DIAS[coincidencias[0].categoria]
    else:
        base = max(PLAZOS_DIAS[p.categoria] for p in pedido.productos)
    return base + (DIAS_EXTRA_PREFERENTE if preferente else 0)


def _siguiente_id(reclamos: list[repositorio.Reclamo]) -> str:
    numeros = [int(r.id.split("-")[1]) for r in reclamos if r.id.startswith("R-")]
    return f"R-{max(numeros, default=0) + 1:03d}"


@herramienta
def registrar_reclamo(sesion: Sesion, args: ArgsRegistrarReclamo) -> dict:
    """Registra un reclamo por producto defectuoso, incompleto o distinto al comprado sobre un pedido
    entregado del cliente. Antes de llamarla, el cliente debe haber dicho el número de pedido y
    el motivo con sus palabras. Si el reclamo no procede, responde con un error que explica por qué."""
    pedido = pedido_del_cliente(sesion, args.numero)

    if pedido.estado != "entregado":
        raise ErrorDeHerramienta(
            f"El pedido está '{pedido.estado}'. Solo se puede reclamar cuando figura como entregado."
        )

    reclamos = repositorio.leer_reclamos()
    abierto = next(
        (r for r in reclamos if r.numero_pedido == pedido.numero and r.estado == "abierto"), None
    )
    if abierto:
        raise ErrorDeHerramienta(
            f"Este pedido ya tiene un reclamo abierto ({abierto.id}, registrado el "
            f"{abierto.fecha.isoformat()}, motivo: «{abierto.motivo}»). No se abre otro: "
            "infórmale al cliente el estado de ese reclamo."
        )

    cliente = next(c for c in repositorio.leer_clientes() if c.id == sesion.cliente_id)
    plazo = _plazo_dias(pedido, args.producto, cliente.categoria == "preferente")
    # El día de entrega cuenta como día 1: se permite si (HOY - fecha_entrega).days < plazo (ANALISIS.md).
    dias = (repositorio.HOY - pedido.fecha_entrega).days
    if dias >= plazo:
        raise ErrorDeHerramienta(
            f"El plazo para reclamar venció: era de {plazo} días desde la entrega "
            f"({pedido.fecha_entrega.isoformat()}) y ya pasaron {dias + 1} días contando el de entrega."
        )

    if not args.motivo.strip():
        raise ErrorDeHerramienta("Falta el motivo. Pregúntale al cliente qué problema tiene el producto.")

    detalle = f"{args.producto.strip()}: " if args.producto else ""
    reclamo = repositorio.Reclamo(
        id=_siguiente_id(reclamos),
        numero_pedido=pedido.numero,
        cliente_id=sesion.cliente_id,
        fecha=repositorio.HOY,
        motivo=f"[{args.tipo}] {detalle}{args.motivo.strip()}",
        estado="abierto",
    )
    repositorio.guardar_reclamos(reclamos + [reclamo])
    return {
        "registrado": True,
        "reclamo": {"id": reclamo.id, "numero_pedido": reclamo.numero_pedido,
                    "fecha": reclamo.fecha.isoformat(), "motivo": reclamo.motivo, "estado": reclamo.estado},
    }
