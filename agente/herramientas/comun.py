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
