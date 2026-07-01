"""Subscription (SaaS tier) endpoints."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.enums import SubscriptionTier
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.subscription import SubscriptionPublic, UpgradeRequest

router = APIRouter(prefix="/subscription", tags=["subscription"])


@router.get("", response_model=SubscriptionPublic)
def get_my_subscription(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> Subscription:
    sub = current.subscription
    if sub is None:
        # Self-heal: every user should have a Basic subscription.
        sub = Subscription(user_id=current.id, tier=SubscriptionTier.BASIC)
        db.add(sub)
        db.commit()
        db.refresh(sub)
    return sub


@router.post("/upgrade", response_model=SubscriptionPublic)
def change_tier(
    payload: UpgradeRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> Subscription:
    """Change the current user's plan.

    This is the billing hook point — in production a successful payment/webhook
    would gate this. For now it flips the tier and sets a 30-day renewal for
    paid plans.
    """
    sub = current.subscription
    if sub is None:
        sub = Subscription(user_id=current.id)
        current.subscription = sub

    if sub.tier == payload.tier:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Already on the {payload.tier.value} plan")

    sub.tier = payload.tier
    if payload.tier == SubscriptionTier.BASIC:
        sub.renews_at = None
    else:
        sub.renews_at = datetime.now(timezone.utc) + timedelta(days=30)

    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub
