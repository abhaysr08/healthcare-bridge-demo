import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from .database import get_db
from .models import UserCreate, UserPublic, AuditLogEntry
from .security import hash_password
from .dependencies import require_admin
from .audit import log_action
from .roles import ALL_ROLES

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/users", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    request: Request,
    current_user=Depends(require_admin),
    db=Depends(get_db)
):
    if body.role not in ALL_ROLES:
        raise HTTPException(status_code=400, detail=f"Ruolo non valido. Usa uno tra: {', '.join(ALL_ROLES)}")
    if len(body.password) < 12:
        raise HTTPException(status_code=400, detail="La password deve essere di almeno 12 caratteri")

    existing = await db.fetchrow("SELECT id FROM users WHERE username=$1", body.username)
    if existing:
        raise HTTPException(status_code=409, detail="Username già in uso")

    hashed = hash_password(body.password)
    row = await db.fetchrow(
        """
        INSERT INTO users (username, hashed_password, full_name, designation, role, created_by, must_change_password)
        VALUES ($1, $2, $3, $4, $5, $6, TRUE)
        RETURNING id, username, full_name, designation, role
        """,
        body.username, hashed, body.full_name, body.designation, body.role, current_user["id"]
    )

    await log_action(
        db, current_user["id"], current_user["username"], "user_created",
        ip=request.client.host if request.client else None,
        details={"new_username": body.username, "role": body.role}
    )

    return UserPublic(**dict(row))


@router.get("/users", response_model=List[dict])
async def list_users(current_user=Depends(require_admin), db=Depends(get_db)):
    rows = await db.fetch(
        """
        SELECT id, username, full_name, designation, role, is_active, is_locked,
               failed_login_count, must_change_password, created_at
        FROM users
        ORDER BY created_at ASC
        """
    )
    return [dict(r) for r in rows]


@router.patch("/users/{user_id}/disable", status_code=status.HTTP_204_NO_CONTENT)
async def disable_user(
    user_id: int,
    request: Request,
    current_user=Depends(require_admin),
    db=Depends(get_db)
):
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Non puoi disabilitare il tuo stesso account")
    result = await db.execute(
        "UPDATE users SET is_active=FALSE, updated_at=NOW() WHERE id=$1", user_id
    )
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Utente non trovato")
    target = await db.fetchrow("SELECT username FROM users WHERE id=$1", user_id)
    await log_action(db, current_user["id"], current_user["username"], "user_disabled",
                     ip=request.client.host if request.client else None,
                     details={"target_user_id": user_id, "target_username": target["username"] if target else None})


@router.patch("/users/{user_id}/enable", status_code=status.HTTP_204_NO_CONTENT)
async def enable_user(
    user_id: int,
    request: Request,
    current_user=Depends(require_admin),
    db=Depends(get_db)
):
    result = await db.execute(
        "UPDATE users SET is_active=TRUE, updated_at=NOW() WHERE id=$1", user_id
    )
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Utente non trovato")
    target = await db.fetchrow("SELECT username FROM users WHERE id=$1", user_id)
    await log_action(db, current_user["id"], current_user["username"], "user_enabled",
                     ip=request.client.host if request.client else None,
                     details={"target_user_id": user_id, "target_username": target["username"] if target else None})


@router.patch("/users/{user_id}/unlock", status_code=status.HTTP_204_NO_CONTENT)
async def unlock_user(
    user_id: int,
    request: Request,
    current_user=Depends(require_admin),
    db=Depends(get_db)
):
    result = await db.execute(
        "UPDATE users SET is_locked=FALSE, failed_login_count=0, updated_at=NOW() WHERE id=$1", user_id
    )
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Utente non trovato")
    target = await db.fetchrow("SELECT username FROM users WHERE id=$1", user_id)
    await log_action(db, current_user["id"], current_user["username"], "user_unlocked",
                     ip=request.client.host if request.client else None,
                     details={"target_user_id": user_id, "target_username": target["username"] if target else None})


@router.get("/audit-logs")
async def get_audit_logs(
    page: int = 1,
    page_size: int = 50,
    username: Optional[str] = None,
    action: Optional[str] = None,
    fiscal_code: Optional[str] = None,
    current_user=Depends(require_admin),
    db=Depends(get_db)
):
    offset = (page - 1) * page_size
    conditions = []
    params = []
    idx = 1

    if username:
        conditions.append(f"username ILIKE ${idx}")
        params.append(f"%{username}%")
        idx += 1
    if action:
        conditions.append(f"action = ${idx}")
        params.append(action)
        idx += 1
    if fiscal_code:
        conditions.append(f"fiscal_code = ${idx}")
        params.append(fiscal_code)
        idx += 1

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    params += [page_size, offset]

    rows = await db.fetch(
        f"SELECT id, username, action, fiscal_code, ip_address, details, created_at FROM audit_logs {where} ORDER BY created_at DESC LIMIT ${idx} OFFSET ${idx+1}",
        *params
    )
    total = await db.fetchval(f"SELECT COUNT(*) FROM audit_logs {where}", *params[:-2])

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [dict(r) for r in rows]
    }
