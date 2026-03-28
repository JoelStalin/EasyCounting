"""Validaciones para emision de comprobantes."""
from __future__ import annotations

import re

RNC_REGEX = re.compile(r"^\d{9,11}$")
ENCF_REGEX = re.compile(r"^E\d{12}$")
ENCF_BY_TYPE_REGEX = re.compile(r"^E(?P<tipo>\d{2})(?P<seq>\d{10})$")


def validate_rnc(value: str) -> None:
    if not RNC_REGEX.match(value):
        raise ValueError("RNC invalido")


def validate_encf(value: str) -> None:
    if not ENCF_REGEX.match(value):
        raise ValueError("ENCF invalido")


def normalize_tipo_ecf(raw: str) -> str:
    value = (raw or "").strip().upper()
    if value.startswith("E"):
        value = value[1:]
    if not value.isdigit() or len(value) != 2:
        raise ValueError("Tipo e-CF invalido")
    return value


def validate_encf_for_tipo(encf: str, tipo_ecf: str) -> None:
    validate_encf(encf)
    tipo = normalize_tipo_ecf(tipo_ecf)
    match = ENCF_BY_TYPE_REGEX.match(encf)
    if not match or match.group("tipo") != tipo:
        raise ValueError("ENCF no coincide con el tipo e-CF")
