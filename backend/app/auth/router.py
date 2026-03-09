import logging
from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from .database import get_db
from .models import LoginRequest, TokenResponse, UserPublic, ChangePasswordRequest
from .security import (
    verify_password, create_access_token, create_refresh_token,
    hash_refresh_token, refresh_token_expires_at, hash_password
)
from .dependencies import get_current_user
from .audit import log_action

logger = logging.getLogger(__name__)
router = APIRouter()

REFRESH_COOKIE = "hb_refresh_token"


def _set_refresh_cookie(response: Response, raw_token: str):
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=raw_token,
        httponly=True,
        secure=True,    # HTTPS only (nginx terminates SSL)
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
        path="/auth",
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, response: Response, db=Depends(get_db)):
    ip = request.client.host if request.client else None

    user = await db.fetchrow(
        "SELECT * FROM users WHERE username = $1", body.username
    )

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenziali non valide")

    if not user["is_active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabilitato. Contattare l'amministratore.")

    if user["is_locked"]:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Account bloccato dopo troppi tentativi. Contattare l'amministratore.")

    if not verify_password(body.password, user["hashed_password"]):
        new_count = user["failed_login_count"] + 1
        if new_count >= 3:
            await db.execute(
                "UPDATE users SET failed_login_count=$1, is_locked=TRUE, updated_at=NOW() WHERE id=$2",
                new_count, user["id"]
            )
            await log_action(db, user["id"], user["username"], "account_locked", ip=ip)
            raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Account bloccato dopo troppi tentativi. Contattare l'amministratore.")
        else:
            await db.execute(
                "UPDATE users SET failed_login_count=$1, updated_at=NOW() WHERE id=$2",
                new_count, user["id"]
            )
            remaining = 3 - new_count
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Credenziali non valide. Tentativi rimasti: {remaining}"
            )

    # Success — reset counter
    await db.execute(
        "UPDATE users SET failed_login_count=0, updated_at=NOW() WHERE id=$1", user["id"]
    )

    access_token = create_access_token(user["id"], user["username"], user["role"])
    raw_refresh, hashed_refresh = create_refresh_token()
    expires_at = refresh_token_expires_at()

    await db.execute(
        "INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES ($1, $2, $3)",
        user["id"], hashed_refresh, expires_at
    )

    _set_refresh_cookie(response, raw_refresh)
    await log_action(db, user["id"], user["username"], "login", ip=ip)

    return TokenResponse(
        access_token=access_token,
        must_change_password=user["must_change_password"],
        user=UserPublic(
            id=user["id"],
            username=user["username"],
            full_name=user["full_name"],
            designation=user["designation"],
            role=user["role"],
        )
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, response: Response, db=Depends(get_db)):
    raw_token = request.cookies.get(REFRESH_COOKIE)
    if not raw_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nessun refresh token")

    token_hash = hash_refresh_token(raw_token)
    record = await db.fetchrow(
        """
        SELECT rt.*, u.id as uid, u.username, u.full_name, u.designation,
               u.role, u.is_active, u.is_locked, u.must_change_password
        FROM refresh_tokens rt
        JOIN users u ON u.id = rt.user_id
        WHERE rt.token_hash = $1
        """,
        token_hash
    )

    if not record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token non valido")

    now = __import__('datetime').datetime.now(timezone.utc)
    if record["revoked"] or record["expires_at"].replace(tzinfo=timezone.utc) < now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token scaduto")

    if not record["is_active"] or record["is_locked"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account non accessibile")

    # Rotate: revoke old, issue new
    await db.execute("UPDATE refresh_tokens SET revoked=TRUE WHERE id=$1", record["id"])

    access_token = create_access_token(record["uid"], record["username"], record["role"])
    raw_new, hashed_new = create_refresh_token()
    expires_at = refresh_token_expires_at()

    await db.execute(
        "INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES ($1, $2, $3)",
        record["uid"], hashed_new, expires_at
    )

    _set_refresh_cookie(response, raw_new)

    return TokenResponse(
        access_token=access_token,
        must_change_password=record["must_change_password"],
        user=UserPublic(
            id=record["uid"],
            username=record["username"],
            full_name=record["full_name"],
            designation=record["designation"],
            role=record["role"],
        )
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response, db=Depends(get_db)):
    raw_token = request.cookies.get(REFRESH_COOKIE)
    if raw_token:
        token_hash = hash_refresh_token(raw_token)
        await db.execute("UPDATE refresh_tokens SET revoked=TRUE WHERE token_hash=$1", token_hash)

    response.delete_cookie(key=REFRESH_COOKIE, path="/auth")


@router.get("/me", response_model=UserPublic)
async def me(current_user=Depends(get_current_user)):
    return UserPublic(
        id=current_user["id"],
        username=current_user["username"],
        full_name=current_user["full_name"],
        designation=current_user.get("designation"),
        role=current_user["role"],
    )


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: ChangePasswordRequest,
    request: Request,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    if len(body.new_password) < 12:
        raise HTTPException(status_code=400, detail="La nuova password deve essere di almeno 12 caratteri")

    user = await db.fetchrow("SELECT hashed_password FROM users WHERE id=$1", current_user["id"])
    if not verify_password(body.current_password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Password attuale non corretta")

    new_hash = hash_password(body.new_password)
    await db.execute(
        "UPDATE users SET hashed_password=$1, must_change_password=FALSE, updated_at=NOW() WHERE id=$2",
        new_hash, current_user["id"]
    )
    await log_action(db, current_user["id"], current_user["username"], "password_changed",
                     ip=request.client.host if request.client else None)
