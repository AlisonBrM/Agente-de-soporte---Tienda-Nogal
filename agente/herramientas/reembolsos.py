"""Solicitud de reembolso, con confirmación explícita del cliente."""
from pydantic import BaseModel, Field

from agente.herramientas.comun import (
    AVISO_ESCALAMIENTO,
    TOPE_REEMBOLSO,
    _pesos,
    pedido_del_cliente,
    registrar_reembolso,
    validar_reembolso,
)
from agente.herramientas.confirmacion import registrar_pendiente, verificar_confirmacion
from agente.herramientas.registro import ErrorDeHerramienta, herramienta
from agente.sesion import Sesion
from tienda import repositorio


class ArgsSolicitarReembolso(BaseModel):
    numero: str = Field(description="Número del pedido que se quiere reembolsar, por ejemplo P-1008.")
    monto: int | None = Field(
        default=None,
        description="Monto en pesos que pide el cliente. Si no lo dijo, no lo pongas: el reembolso "
        "siempre es por el valor total pagado del pedido.",
    )


def _motivo(pedido: repositorio.Pedido) -> str:
    """Por qué procede el reembolso: pedido cancelado o reclamo abierto. Si no, lanza error."""
    if pedido.estado == "cancelado":
        return "Pedido cancelado"
    abierto = next(
        (r for r in repositorio.leer_reclamos() if r.numero_pedido == pedido.numero and r.estado == "abierto"),
        None,
    )
    if abierto:
        return f"Reclamo abierto {abierto.id}: {abierto.motivo}"
    raise ErrorDeHerramienta(
        f"El pedido está '{pedido.estado}' y no tiene un reclamo abierto. Solo se reembolsa un pedido "
        "cancelado o con un reclamo abierto. Si el cliente tiene un problema con un pedido entregado, "
        "ofrécele registrar un reclamo."
    )


@herramienta
def solicitar_reembolso(sesion: Sesion, args: ArgsSolicitarReembolso) -> dict:
    """Solicita el reembolso de un pedido del cliente que está cancelado o tiene un reclamo abierto.
    Llámala directamente cuando el cliente pida el reembolso: no le preguntes antes si está seguro.
    La primera vez responde 'requiere_confirmacion' con un resumen: muéstraselo al cliente y pregunta
    una sola vez si confirma. Cuando el cliente responda que sí, vuelve a llamarla con los mismos
    datos. Hasta $300.000 queda aprobado; por encima lo aprueba un asesor y el caso se escala."""
    pedido = pedido_del_cliente(sesion, args.numero)
    monto = pedido.total if args.monto is None else args.monto

    # Todas las reglas se revisan antes de pedir la confirmación: no se le pide al cliente
    # confirmar algo que la política va a negar.
    motivo = _motivo(pedido)
    validar_reembolso(pedido, monto)

    clave = f"reembolso:{pedido.numero}:{monto}"
    if not verificar_confirmacion(sesion, clave):
        registrar_pendiente(sesion, clave)
        necesita_asesor = monto > TOPE_REEMBOLSO
        return {
            "estado": "requiere_confirmacion",
            "resumen": f"Reembolso de {_pesos(monto)} del pedido {pedido.numero}. Motivo: {motivo}. "
            + (
                "Como supera $300.000, lo debe aprobar un asesor y el caso se escala."
                if necesita_asesor
                else "Queda aprobado."
            ),
            "instruccion": "Muestra este resumen al cliente y pregunta una sola vez si confirma.",
        }

    reembolso = registrar_reembolso(sesion, pedido, monto, motivo)
    resultado = {
        "registrado": True,
        "reembolso": {
            "id": reembolso.id,
            "numero_pedido": reembolso.numero_pedido,
            "monto": reembolso.monto,
            "estado": reembolso.estado,
        },
        "escalado": reembolso.estado == "solicitado",
    }
    if reembolso.estado == "solicitado":
        resultado["aviso_al_cliente"] = AVISO_ESCALAMIENTO
    return resultado
