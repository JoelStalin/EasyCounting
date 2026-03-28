from __future__ import annotations

import pytest

from app.billing.validators import normalize_tipo_ecf, validate_encf, validate_encf_for_tipo


def test_validate_encf_accepts_dgii_ecf_shape() -> None:
    validate_encf("E310000000005")


def test_validate_encf_rejects_non_ecf_prefix() -> None:
    with pytest.raises(ValueError):
        validate_encf("B010000000005")


def test_normalize_tipo_ecf_accepts_e_prefixed_or_plain() -> None:
    assert normalize_tipo_ecf("E31") == "31"
    assert normalize_tipo_ecf("31") == "31"


def test_validate_encf_for_tipo_must_match_tipo() -> None:
    validate_encf_for_tipo("E320000000012", "E32")
    with pytest.raises(ValueError):
        validate_encf_for_tipo("E320000000012", "E31")
