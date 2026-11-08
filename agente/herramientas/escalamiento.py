"""Escalamiento de un caso a un asesor humano."""
from typing import Literal

from pydantic import BaseModel, Field

from agente.herramientas.comun import (
    AVISO_ESCALAMIENTO,
    TOPE_REEMBOLSO,
    pedido_del_cliente,
    registrar_escalamiento,
)
from agente.herramientas.registro import ErrorDeHerramienta, herramienta
from agente.sesion import Sesion


class ArgsEscalarAAsesor(BaseModel):
    motivo: Literal["pide_asesor", "reembolso_sobre_tope", "problema_sin_resolver", "cobro_no_reconocido"] = Field(
        description="Por qué se escala. 'pide_asesor': el cliente pidió hablar con una persona. "
        "'reembolso_sobre_tope': un reembolso de más de $300.000 que debe aprobar un asesor. "
        "'problema_sin_resolver': el problema sigue sin resolverse tras tres intentos. "
        "'cobro_no_reconocido': el cliente reporta un cobro que no reconoce o un posible fraude."
    )
    resumen: str = Field(
        description="Resumen breve del caso para el asesor: qué pidió el cliente, qué se intentó y "
        "qué ya se le dijo, para que no tenga que volver a preguntar."
    )
    numero_pedido: str | None = Field(
        default=None,
        description="Número del pedido relacionado, solo si el cliente lo mencionó. No es obligatorio.",
    )


@herramienta
def escalar_a_asesor(sesion: Sesion, args: ArgsEscalarAAsesor) -> dict:
    """Pasa el caso a un asesor humano y deja un resumen. Úsala cuando el cliente pide hablar con
    una persona, cuando un reembolso supera $300.000, cuando el problema sigue sin resolverse tras
    tres intentos o cuando el cliente reporta un cobro que no reconoce o un posible fraude. En el
    caso de cobro no reconocido o fraude, no cancelas, reclamas ni reembolsas nada: solo escalas."""
    # El pedido es opcional (ANALISIS.md, sección 2). Si el cliente mencionó uno que no existe o es
    # de otro cliente, se escala igual pero sin asociarlo y sin revelar nada sobre ese pedido.
    pedido = None
    if args.numero_pedido and args.numero_pedido.strip():
        try:
            pedido = pedido_del_cliente(sesion, args.numero_pedido)
        except ErrorDeHerramienta:
            pedido = None

    if args.motivo == "reembolso_sobre_tope":
        # Este motivo solo vale para un pedido del cliente cuyo total supera el tope.
        if pedido is None:
            raise ErrorDeHerramienta(
                "Para escalar un reembolso necesito un pedido del cliente. Pídele el número de pedido."
            )
        if pedido.total <= TOPE_REEMBOLSO:
            raise ErrorDeHerramienta(
                f"Este pedido no supera el tope de ${TOPE_REEMBOLSO:,}".replace(",", ".")
                + ": no hay que escalarlo por reembolso. Sigue el flujo normal de reembolso."
            )

    escalamiento = registrar_escalamiento(
        sesion, args.motivo, args.resumen, pedido.numero if pedido else None
    )
    return {
        "escalado": True,
        "escalamiento": {
            "id": escalamiento.id,
            "numero_pedido": escalamiento.numero_pedido,
            "motivo": escalamiento.motivo,
            "fecha": escalamiento.fecha.isoformat(),
        },
        "aviso_al_cliente": AVISO_ESCALAMIENTO,
    }
