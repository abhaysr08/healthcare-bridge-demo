from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .database import get_db
from .security import decode_access_token

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db=Depends(get_db),
) -> dict:
    payload = decode_access_token(credentials.credentials)
    user_id = int(payload["sub"])

    user = await db.fetchrow(
        "SELECT id, username, full_name, designation, role, is_active, is_locked, must_change_password FROM users WHERE id = $1",
        user_id,
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utente non trovato")
    if not user["is_active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabilitato")
    if user["is_locked"]:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Account bloccato")

    return dict(user)


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accesso riservato agli amministratori")
    return current_user


def require_operator_or_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] not in ("admin", "operator"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permessi insufficienti")
    return current_user
