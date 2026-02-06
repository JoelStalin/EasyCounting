from fastapi import Depends, HTTPException, Request, status


def get_current_user(request: Request):
    """DEV-ONLY authentication stub for local development."""
    role = None
    user_id = None

    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header.split()[1]
        if ":" in token:
            role, user_id = token.split(":", 1)

    role = role or request.headers.get("X-User-Role") or "cliente"
    user_id = user_id or request.headers.get("X-User-Id") or "local-user"

    return {"id": user_id, "role": role}


def require_role(required: str):
    def _dep(user=Depends(get_current_user)):
        if user.get("role") != required:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return _dep
