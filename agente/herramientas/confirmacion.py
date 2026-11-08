"""Mecanismo de confirmación en dos turnos para acciones de alto riesgo."""
import re
import unicodedata

from agente.sesion import Sesion

PALABRAS_NEGACION_O_DUDA = {
    "no",
    "nunca",
    "jamas",
    "tampoco",
    "espera",
    "espere",
    "esperar",
    "todavia",
    "aun",
    "duda",
    "dudo",
    "quizas",
    "talvez",
    "despues",
    "luego",
    "detente",
    "para",
}

FRASES_NEGACION_O_DUDA = (
    "mejor no",
    "cancelar no",
    "ahora no",
    "por ahora no",
    "no quiero",
    "no estoy seguro",
    "no estoy segura",
    "me arrepenti",
    "lo voy a pensar",
)

PALABRAS_INTERROGATIVAS = {
    "que",
    "cual",
    "como",
    "cuando",
    "cuanto",
    "donde",
}

PALABRAS_AFIRMATIVAS = {
    "confirmo",
    "confirmado",
    "confirmar",
    "dale",
    "ok",
    "okay",
    "claro",
    "adelante",
    "procede",
    "proceda",
    "bueno",
    "listo",
    "vale",
    "acepto",
    "correcto",
    "seguro",
    "exacto",
    "afirmativo",
    "hagale",
}

FRASES_AFIRMATIVAS = (
    "de acuerdo",
    "por supuesto",
    "esta bien",
)

MAX_PALABRAS_CONFIRMACION = 10


def _normalizar(texto: str) -> str:
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(c) != "Mn"
    )
    limpio = re.sub(r"[^a-z0-9\s]", " ", sin_tildes)
    return " ".join(limpio.split())


def es_afirmativo(texto: str) -> bool:
    """Evalúa si un mensaje corto del cliente expresa confirmación explícita sin negación ni duda."""
    texto_original = texto or ""
    if "?" in texto_original or "¿" in texto_original:
        return False

    normalizado = _normalizar(texto_original)
    if not normalizado:
        return False

    palabras = normalizado.split()
    if len(palabras) > MAX_PALABRAS_CONFIRMACION:
        return False

    if palabras[0] in PALABRAS_INTERROGATIVAS or palabras[:2] == ["por", "que"]:
        return False

    if any(p in PALABRAS_NEGACION_O_DUDA for p in palabras):
        return False
    if any(frase in normalizado for frase in FRASES_NEGACION_O_DUDA):
        return False

    if palabras[0] == "si":
        return True
    if any(p in PALABRAS_AFIRMATIVAS for p in palabras):
        return True
    if any(frase in normalizado for frase in FRASES_AFIRMATIVAS):
        return True

    return False


def registrar_pendiente(sesion: Sesion, clave: str) -> None:
    """Registra una confirmación pendiente con el número del turno actual."""
    sesion.confirmaciones_pendientes[clave] = sesion.turnos


def verificar_confirmacion(sesion: Sesion, clave: str) -> bool:
    """Devuelve True solo si la clave está pendiente de un turno previo y el último mensaje es afirmativo."""
    if clave not in sesion.confirmaciones_pendientes:
        return False

    turno_guardado = sesion.confirmaciones_pendientes[clave]
    if sesion.turnos <= turno_guardado:
        return False

    del sesion.confirmaciones_pendientes[clave]
    return es_afirmativo(sesion.ultimo_mensaje)
