from __future__ import annotations

import re


COMMON_CORRECTIONS = {
    "gurada": "guarda",
    "essos": "esos",
    "conversacion": "conversación",
    "conversasion": "conversación",
    "comversasion": "conversación",
    "funcion": "función",
    "gramatica": "gramática",
    "ortografia": "ortografía",
    "organizan": "organiza",
    "leguague": "lenguaje",
    "inecesario": "innecesario",
    "gitingnore": ".gitignore",
    "mensajeria": "mensajería",
    "integracion": "integración",
    "configuracion": "configuración",
    "autenticacion": "autenticación",
    "autorizacion": "autorización",
    "sesion": "sesión",
    "informacion": "información",
    "documentacion": "documentación",
    "automaticamente": "automáticamente",
    "analisis": "análisis",
    "revision": "revisión",
}

CAPITALIZED_CORRECTIONS = {
    "dgii": "DGII",
    "odoo": "Odoo",
    "cloudflare": "Cloudflare",
    "aws": "AWS",
    "getupsoft": "GetUpSoft",
}

CONSTRAINT_MARKERS = ("no ", "sin ", "debe ", "deben ", "evita", "evitar", "solo ", "solamente ")


def normalize_whitespace(text: str) -> str:
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r" ?([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"([,.;:!?])([^\s])", r"\1 \2", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _replace_word(text: str, source: str, target: str) -> str:
    pattern = re.compile(rf"\b{re.escape(source)}\b", re.IGNORECASE)

    def _match_case(match: re.Match[str]) -> str:
        value = match.group(0)
        if value.isupper():
            return target.upper()
        if value[0].isupper():
            return target[0].upper() + target[1:]
        return target

    return pattern.sub(_match_case, text)


def correct_spanish_text(text: str) -> str:
    corrected = normalize_whitespace(text)
    for source, target in COMMON_CORRECTIONS.items():
        corrected = _replace_word(corrected, source, target)
    for source, target in CAPITALIZED_CORRECTIONS.items():
        corrected = _replace_word(corrected, source, target)
    corrected = re.sub(r"\s+\.\.\.", "...", corrected)
    if corrected and corrected[0].isalpha():
        corrected = corrected[0].upper() + corrected[1:]
    return corrected


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?:\n+|(?<=[.!?])\s+)", text)
    return [part.strip(" -\t") for part in parts if part.strip(" -\t")]


def extract_constraints(text: str) -> list[str]:
    constraints: list[str] = []
    for sentence in split_sentences(text):
        lowered = sentence.lower()
        if any(marker in lowered for marker in CONSTRAINT_MARKERS):
            constraints.append(sentence)
    return constraints


def to_ai_friendly_prompt(text: str, *, tags: list[str] | None = None) -> str:
    cleaned = correct_spanish_text(text)
    constraints = extract_constraints(cleaned)
    tag_text = ", ".join(tags or []) or "sin etiquetas detectadas"
    constraints_text = "; ".join(constraints) if constraints else "sin restricciones explícitas"
    return (
        f"Objetivo: {cleaned}\n"
        f"Contexto detectado: {tag_text}\n"
        f"Restricciones detectadas: {constraints_text}"
    )
