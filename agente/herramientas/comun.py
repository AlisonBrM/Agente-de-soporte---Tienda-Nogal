"""Funciones compartidas por varias herramientas."""
from agente.herramientas.registro import ErrorDeHerramienta
from agente.sesion import Sesion
from tienda import repositorio

# Mismo mensaje para un pedido que no existe y para uno de otro cliente:
# así el agente no revela que existe un pedido ajeno con ese número.
PEDIDO_NO_ENCONTRADO = (
    "No encontré ese número de pedido entre los pedidos de este cliente. "
    "Pídele que revise el número."
)


def normalizar_numero(numero: str) -> str:
    """Quita espacios y pasa a mayúsculas: ' p-1002 ' -> 'P-1002'."""
    return numero.strip().upper()


def pedido_del_cliente(sesion: Sesion, numero: str) -> repositorio.Pedido:
    """Devuelve el pedido si existe y es del cliente de la sesión. Si no, lanza ErrorDeHerramienta."""
    numero = normalizar_numero(numero)
    for pedido in repositorio.leer_pedidos():
        if pedido.numero == numero and pedido.cliente_id == sesion.cliente_id:
            return pedido
    raise ErrorDeHerramienta(PEDIDO_NO_ENCONTRADO)


# Tope que el equipo puede aprobar solo; por encima, lo aprueba un asesor (política de reembolsos).
TOPE_REEMBOLSO = 300_000

AVISO_ESCALAMIENTO = "Un asesor contactará al cliente en un plazo máximo de un día hábil."


def registrar_escalamiento(
    sesion: Sesion, motivo: str, resumen: str, numero_pedido: str | None = None
) -> repositorio.Escalamiento:
    """Guarda un escalamiento en escalamientos.json. Lo usan escalar_a_asesor y las herramientas
    que deben escalar solas (reembolso sobre el tope). El cliente sale de la sesión.

    Si ya hay un escalamiento del mismo cliente, motivo y pedido registrado hoy, lo devuelve en vez
    de crear otro: así el cliente no acumula duplicados si el modelo insiste.
    """
    resumen = resumen.strip()
    if not resumen:
        raise ErrorDeHerramienta(
            "Falta el resumen del caso. Escribe un resumen breve (qué pasó y qué ya se le dijo "
            "al cliente) para que el asesor no tenga que volver a preguntar."
        )

    escalamientos = repositorio.leer_escalamientos()
    repetido = next(
        (
            e for e in escalamientos
            if e.cliente_id == sesion.cliente_id and e.motivo == motivo
            and e.numero_pedido == numero_pedido and e.fecha == repositorio.HOY
        ),
        None,
    )
    if repetido:
        return repetido

    numeros = [int(e.id.split("-")[1]) for e in escalamientos if e.id.startswith("E-")]
    nuevo = repositorio.Escalamiento(
        id=f"E-{max(numeros, default=0) + 1:03d}",
        cliente_id=sesion.cliente_id,
        numero_pedido=numero_pedido,
        fecha=repositorio.HOY,
        motivo=motivo,
        resumen=resumen,
    )
    repositorio.guardar_escalamientos(escalamientos + [nuevo])
    return nuevo
