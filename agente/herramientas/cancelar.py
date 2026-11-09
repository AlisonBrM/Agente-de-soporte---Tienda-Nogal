"""Cancelación de pedidos del cliente con confirmación explícita en dos turnos."""
from pydantic import BaseModel, Field

from agente.herramientas.comun import pedido_del_cliente, registrar_reembolso, validar_reembolso
from agente.herramientas.confirmacion import registrar_pendiente, verificar_confirmacion
from agente.herramientas.registro import ErrorDeHerramienta, herramienta
from agente.sesion import Sesion
from tienda import repositorio

class ArgsCancelarPedido(BaseModel):
    numero: str = Field(
        description="Número del pedido que el cliente quiere cancelar, por ejemplo P-1001."
    )


@herramienta
def cancelar_pedido(sesion: Sesion, args: ArgsCancelarPedido) -> dict:
    """Cancela un pedido del cliente que tiene la sesión iniciada si la política lo permite
    (pagado, o en preparación con máximo 24 horas desde la compra) y genera el reembolso
    correspondiente. Requiere confirmación explícita del cliente en el turno siguiente."""
    pedido = pedido_del_cliente(sesion, args.numero)

    if pedido.estado == "enviado":
        raise ErrorDeHerramienta(
            f"El pedido {pedido.numero} ya fue enviado y no se puede cancelar. "
            "El cliente puede rechazar la entrega en la puerta o presentar un reclamo después de recibirlo."
        )

    if pedido.estado == "entregado":
        raise ErrorDeHerramienta(
            f"El pedido {pedido.numero} ya fue entregado y no aplica la cancelación."
        )

    if pedido.estado == "cancelado":
        raise ErrorDeHerramienta(
            f"El pedido {pedido.numero} ya se encuentra cancelado."
        )

    if pedido.estado == "en_preparacion":
        dias = (repositorio.HOY - pedido.fecha_compra).days
        if dias > 1:
            raise ErrorDeHerramienta(
                f"El pedido {pedido.numero} está en preparación pero fue comprado el "
                f"{pedido.fecha_compra.isoformat()} (hace {dias} días). Solo se puede cancelar "
                "si no han pasado más de 24 horas desde la compra."
            )

    clave = f"cancelar:{pedido.numero}"
    venia_del_turno_anterior = (
        sesion.confirmaciones_pendientes.get(clave) == sesion.turnos - 1
    )
    if not verificar_confirmacion(sesion, clave):
        if venia_del_turno_anterior:
            return {
                "cancelado": False,
                "pedido": pedido.numero,
                "mensaje": (
                    "El cliente no confirmó la cancelación; el pedido NO se canceló. "
                    "No insistas ni vuelvas a preguntar; pregúntale si necesita algo más. "
                    "Si luego pide cancelar de nuevo, llama esta herramienta otra vez."
                ),
            }
        registrar_pendiente(sesion, clave)
        return {
            "requiere_confirmacion": True,
            "pedido": pedido.numero,
            "mensaje": (
                f"Se requiere confirmación explícita del cliente para cancelar el pedido {pedido.numero} "
                f"(total: ${pedido.total}). Pregúntale al cliente UNA sola vez si confirma que desea "
                "cancelarlo y vuelve a llamar esta herramienta solo después de que el cliente responda."
            ),
        }

    # El reembolso automático usa las funciones comunes de comun.py: la regla del tope,
    # los ids y el escalamiento (si supera $300.000) quedan en un solo lugar.
    # Se valida antes de cambiar el pedido para no dejarlo cancelado sin su reembolso.
    validar_reembolso(pedido, pedido.total)

    pedidos = repositorio.leer_pedidos()
    for p in pedidos:
        if p.numero == pedido.numero:
            p.estado = "cancelado"
            break
    repositorio.guardar_pedidos(pedidos)

    reembolso_final = registrar_reembolso(
        sesion, pedido, pedido.total, f"Reembolso automático por cancelación del pedido {pedido.numero}"
    )
    escalamiento_creado = None
    if reembolso_final.estado == "solicitado":
        # registrar_reembolso ya creó el escalamiento; se busca para devolverlo en el resultado.
        escalamiento_creado = next(
            e for e in repositorio.leer_escalamientos()
            if e.numero_pedido == pedido.numero and e.motivo == "reembolso_sobre_tope"
        )

    resultado = {
        "cancelado": True,
        "pedido": pedido.numero,
        "estado": "cancelado",
        "reembolso": {
            "id": reembolso_final.id,
            "numero_pedido": reembolso_final.numero_pedido,
            "fecha": reembolso_final.fecha.isoformat(),
            "monto": reembolso_final.monto,
            "estado": reembolso_final.estado,
        },
    }
    if escalamiento_creado is not None:
        resultado["escalamiento"] = {
            "id": escalamiento_creado.id,
            "numero_pedido": escalamiento_creado.numero_pedido,
            "fecha": escalamiento_creado.fecha.isoformat(),
            "motivo": escalamiento_creado.motivo,
            "resumen": escalamiento_creado.resumen,
        }
    return resultado
