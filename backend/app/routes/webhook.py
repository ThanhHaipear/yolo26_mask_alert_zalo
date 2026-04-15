from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import ZaloUser

router = APIRouter(prefix="/webhook", tags=["webhook"])


def _extract_zalo_user(payload: dict) -> dict | None:
    data = payload.get("data")
    nested_data = data if isinstance(data, dict) else {}
    candidates = [
        payload.get("sender"),
        payload.get("follower"),
        payload.get("user"),
        nested_data.get("sender"),
        nested_data.get("follower"),
    ]
    for candidate in candidates:
        if isinstance(candidate, dict) and candidate.get("id"):
            return {
                "zalo_user_id": str(candidate["id"]),
                "display_name": candidate.get("display_name") or candidate.get("name"),
                "is_following": candidate.get("is_following", True),
            }
    return None


@router.get("/zalo")
async def verify_webhook(verify_token: str | None = None):
    if not verify_token:
        raise HTTPException(status_code=400, detail="Missing verify token")
    if verify_token != settings.webhook_verify_token:
        raise HTTPException(status_code=403, detail="Invalid verify token")
    return {"ok": True, "message": "Webhook is reachable"}


@router.post("/zalo")
async def zalo_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    user_data = _extract_zalo_user(payload)

    if not user_data:
        return {"received": True, "saved": False, "message": "No user id found in payload"}

    existing = db.execute(
        select(ZaloUser).where(ZaloUser.zalo_user_id == user_data["zalo_user_id"])
    ).scalar_one_or_none()

    if existing:
        existing.display_name = user_data["display_name"]
        existing.is_following = bool(user_data["is_following"])
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return {"received": True, "saved": True, "zalo_user_id": existing.zalo_user_id}

    user = ZaloUser(
        zalo_user_id=user_data["zalo_user_id"],
        display_name=user_data["display_name"],
        is_following=bool(user_data["is_following"]),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"received": True, "saved": True, "zalo_user_id": user.zalo_user_id}
