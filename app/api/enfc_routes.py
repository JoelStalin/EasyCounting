# FILE: app/api/enfc_routes.py
"""FastAPI router exposing DGII ENFC validation endpoints."""
from __future__ import annotations

import json
import hashlib
from typing import Any, Dict, Tuple
from xml.etree.ElementTree import Element, SubElement, tostring

from fastapi import APIRouter, Header, HTTPException, Request, Response, status
import structlog
from pydantic import ValidationError

from app.api.schemas.enfc_schemas import AprobacionReq, CertReq, RecepcionReq
from app.services.aprobacion_service import procesar_aprobacion
from app.infra.settings import settings
from app.security.xml import parse_secure, validate_with_xsd
from app.security.xml_verify import verify_xml_signature_details
from app.services.auth_service import emitir_semilla, emitir_token, validar_certificado, validar_token
from app.services.idempotency import idempotency_store
from app.services.recepcion_service import procesar_ecf

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/fe", tags=["ENFC"])

_ALLOWED_CONTENT_TYPES = {"application/json", "application/xml", "text/xml"}


def _accepts_json(request: Request) -> bool:
    accept = (request.headers.get("accept") or "").lower()
    return "application/json" in accept


def _xml_response(root: Element) -> Response:
    xml_bytes = tostring(root, encoding="utf-8", xml_declaration=True)
    return Response(content=xml_bytes, media_type="application/xml")


def _semilla_to_xml(semilla: Dict[str, object]) -> Response:
    root = Element(
        "SemillaModel",
        {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xmlns:xsd": "http://www.w3.org/2001/XMLSchema",
        },
    )
    SubElement(root, "valor").text = str(semilla.get("valor", ""))
    SubElement(root, "fecha").text = str(semilla.get("fecha", ""))
    return _xml_response(root)


def _token_to_xml(token_payload: Dict[str, object]) -> Response:
    root = Element("RespuestaAutenticacion")
    SubElement(root, "token").text = str(token_payload.get("token", ""))
    SubElement(root, "expira").text = str(token_payload.get("expira", ""))
    SubElement(root, "expedido").text = str(token_payload.get("expedido", ""))
    return _xml_response(root)


def _require_or_validate_bearer(authorization: str | None) -> None:
    if not authorization:
        if settings.enfc_require_bearer_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Falta Authorization Bearer")
        return
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization inválido")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token vacío")
    if settings.enfc_require_bearer_token and not validar_token(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")


def _normalize_content_type(raw: str | None) -> str:
    if not raw:
        return ""
    return raw.split(";", 1)[0].strip().lower()


def _hash_payload(content_type: str, body: bytes) -> str:
    if content_type == "application/json":
        try:
            parsed = json.loads(body.decode()) if body else {}
        except json.JSONDecodeError as exc:  # noqa: PERF203
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="JSON inválido") from exc
        canonical = json.dumps(parsed, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(canonical).hexdigest()
    return hashlib.sha256(body).hexdigest()


async def _read_request(request: Request) -> Tuple[str, bytes]:
    content_type = _normalize_content_type(request.headers.get("content-type"))
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        xml_field = form.get("xml")
        if xml_field is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Falta campo xml")
        file_obj = getattr(xml_field, "file", None)
        if file_obj is not None:
            body = await xml_field.read()
        else:
            body = str(xml_field).encode("utf-8")
        if not body:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cuerpo requerido")
        return "application/xml", body

    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Content-Type no soportado")
    body = await request.body()
    if not body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cuerpo requerido")
    return content_type, body


async def _handle_idempotency(key: str, payload_hash: str, response: Response):
    try:
        cached = await idempotency_store.get(key, payload_hash)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if cached:
        response.status_code = cached.status_code
        response.headers.update(cached.headers)
        response.headers["Idempotent-Replay"] = "true"
        return cached.body
    return None


async def _store_idempotent_response(
    key: str,
    payload_hash: str,
    status_code: int,
    body: Dict[str, Any],
    *,
    headers: Dict[str, str] | None = None,
) -> None:
    await idempotency_store.set(key, payload_hash, status_code, body, headers=headers)


@router.post("/recepcion/api/ecf")
async def recepcion_ecf(
    request: Request,
    response: Response,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> Dict[str, Any]:
    _require_or_validate_bearer(authorization)

    content_type, body = await _read_request(request)
    payload_hash = _hash_payload(content_type, body)

    resolved_key = idempotency_key or hashlib.sha256(f"{request.url.path}:{payload_hash}".encode()).hexdigest()

    cached_body = await _handle_idempotency(resolved_key, payload_hash, response)
    if cached_body is not None:
        if _accepts_json(request):
            return cached_body
        root = Element("AcuseRecepcion")
        for k, v in cached_body.items():
            SubElement(root, k).text = str(v)
        return _xml_response(root)  # type: ignore[return-value]

    try:
        if content_type == "application/json":
            try:
                payload_dict = json.loads(body.decode())
                payload = RecepcionReq(**payload_dict).model_dump()
            except (json.JSONDecodeError, ValidationError) as exc:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"JSON inválido: {exc}") from exc
        else:
            payload = body
        result = await procesar_ecf(payload)
    except ValueError as exc:
        logger.warning("recepcion.ecf.error", error=str(exc))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    response.headers["Idempotent-Replay"] = "false"
    await _store_idempotent_response(
        resolved_key,
        payload_hash,
        status.HTTP_200_OK,
        result,
        headers={"Content-Type": "application/json"},
    )
    if _accepts_json(request):
        return result
    root = Element("AcuseRecepcion")
    for k, v in result.items():
        SubElement(root, k).text = str(v)
    return _xml_response(root)  # type: ignore[return-value]


@router.post("/aprobacioncomercial/api/ecf")
async def aprobacion_ecf(
    request: Request,
    response: Response,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> Dict[str, Any]:
    _require_or_validate_bearer(authorization)

    content_type, body = await _read_request(request)
    payload_hash = _hash_payload(content_type, body)

    resolved_key = idempotency_key or hashlib.sha256(f"{request.url.path}:{payload_hash}".encode()).hexdigest()

    cached_body = await _handle_idempotency(resolved_key, payload_hash, response)
    if cached_body is not None:
        if _accepts_json(request):
            return cached_body
        root = Element("AcuseAprobacion")
        for k, v in cached_body.items():
            SubElement(root, k).text = str(v)
        return _xml_response(root)  # type: ignore[return-value]

    try:
        if content_type == "application/json":
            try:
                payload_dict = json.loads(body.decode())
                payload = AprobacionReq(**payload_dict).model_dump()
            except (json.JSONDecodeError, ValidationError) as exc:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"JSON inválido: {exc}") from exc
        else:
            payload = body
        result = await procesar_aprobacion(payload)
    except ValueError as exc:
        logger.warning("aprobacion.ecf.error", error=str(exc))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    response.headers["Idempotent-Replay"] = "false"
    await _store_idempotent_response(
        resolved_key,
        payload_hash,
        status.HTTP_200_OK,
        result,
        headers={"Content-Type": "application/json"},
    )
    if _accepts_json(request):
        return result
    root = Element("AcuseAprobacion")
    for k, v in result.items():
        SubElement(root, k).text = str(v)
    return _xml_response(root)  # type: ignore[return-value]


@router.get("/autenticacion/api/semilla")
async def obtener_semilla(request: Request) -> Response | Dict[str, Any]:
    semilla = emitir_semilla()
    if _accepts_json(request):
        return semilla
    return _semilla_to_xml(semilla)


@router.post("/autenticacion/api/validacioncertificado")
async def validacion_certificado(request: Request) -> Response | Dict[str, Any]:
    content_type = _normalize_content_type(request.headers.get("content-type"))
    if content_type == "application/json":
        req_json = await request.json()
        try:
            req = CertReq(**req_json)
        except ValidationError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"JSON inválido: {exc}") from exc
        return validar_certificado(req.model_dump())

    _ct, body = await _read_request(request)
    try:
        verify_xml_signature_details(body, require_x509=settings.enfc_require_x509_signature)
        validate_with_xsd(body, "xsd/Semilla v.1.0.xsd")
        parsed = parse_secure(body)
        valor_node = parsed.find("valor")
        valor_semilla = valor_node.text.strip() if valor_node is not None and valor_node.text else ""
        if not valor_semilla:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Semilla sin valor")
        token_payload = emitir_token(valor_semilla)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if _accepts_json(request):
        return token_payload
    return _token_to_xml(token_payload)
