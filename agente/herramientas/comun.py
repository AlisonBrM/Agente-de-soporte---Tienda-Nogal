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


def _pesos(monto: int) -> str:
    """300000 -> '$300.000'."""
    return f"${monto:,}".replace(",", ".")


def validar_reembolso(pedido: repositorio.Pedido, monto: int) -> None:
    """Revisa que se pueda reembolsar ese monto de ese pedido; si no, lanza ErrorDeHerramienta.

    Un pedido tiene un solo reembolso y siempre es por el valor total pagado. La usan
    registrar_reembolso (al guardar) y solicitar_reembolso (antes de pedir la confirmación al
    cliente, para no pedirle confirmar algo que luego se va a negar)."""
    previo = next((r for r in repositorio.leer_reembolsos() if r.numero_pedido == pedido.numero), None)
    if previo:
        raise ErrorDeHerramienta(
            f"Este pedido ya tiene un reembolso ({previo.id}) por {_pesos(previo.monto)} en estado "
            f"'{previo.estado}'. No se registra otro: infórmale al cliente el estado de ese reembolso."
        )
    if monto <= 0:
        raise ErrorDeHerramienta("El monto del reembolso debe ser mayor que cero.")
    if monto > pedido.total:
        raise ErrorDeHerramienta(
            f"El reembolso no puede superar el valor pagado por el pedido ({_pesos(pedido.total)})."
        )
    if monto != pedido.total:
        raise ErrorDeHerramienta(
            f"El reembolso procede solo por el valor total pagado ({_pesos(pedido.total)})."
        )


def registrar_reembolso(
    sesion: Sesion, pedido: repositorio.Pedido, monto: int, motivo: str
) -> repositorio.Reembolso:
    """Guarda un reembolso en reembolsos.json. Lo usan solicitar_reembolso y cancelar_pedido
    (la cancelación genera un reembolso automático), así la regla del tope vive en un solo lugar.

    Reglas que valida aquí, sin importar quién la llame:
    - El pedido es del cliente de la sesión.
    - Un pedido tiene un solo reembolso (el reembolso es siempre por el valor total pagado).
    - El monto es el valor total del pedido: ni más (nunca supera lo pagado) ni menos.
    - Hasta $300.000 queda 'aprobado'. Por encima queda 'solicitado' y se escala a un asesor.

    No valida si el pedido está cancelado o tiene un reclamo abierto: eso lo revisa
    solicitar_reembolso, porque cancelar_pedido llama esta función justo al cancelar.
    """
    if pedido.cliente_id != sesion.cliente_id:
        raise ErrorDeHerramienta(PEDIDO_NO_ENCONTRADO)

    motivo = motivo.strip()
    if not motivo:
        raise ErrorDeHerramienta("Falta el motivo del reembolso.")

    validar_reembolso(pedido, monto)
    reembolsos = repositorio.leer_reembolsos()
    numeros = [int(r.id.split("-")[1]) for r in reembolsos if r.id.startswith("RE-")]
    estado = "aprobado" if monto <= TOPE_REEMBOLSO else "solicitado"
    nuevo = repositorio.Reembolso(
        id=f"RE-{max(numeros, default=0) + 1:03d}",
        numero_pedido=pedido.numero,
        cliente_id=sesion.cliente_id,
        fecha=repositorio.HOY,
        monto=monto,
        motivo=motivo,
        estado=estado,
    )
    repositorio.guardar_reembolsos(reembolsos + [nuevo])

    if estado == "solicitado":
        registrar_escalamiento(
            sesion,
            "reembolso_sobre_tope",
            f"Reembolso de {_pesos(monto)} del pedido {pedido.numero} pendiente de aprobación "
            f"por un asesor (supera el tope de {_pesos(TOPE_REEMBOLSO)}). Motivo: {motivo}",
            pedido.numero,
        )
    return nuevo
