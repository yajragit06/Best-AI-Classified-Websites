"""Secure listing creation and retrieval endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core import specs_guard
from app.database import get_db
from app.models.enums import ListingStatus, SubscriptionTier
from app.models.listing import KnowledgeQuestion, Listing
from app.models.user import User
from app.schemas.listing import ListingCreate, ListingPublic

router = APIRouter(prefix="/listings", tags=["listings"])


def _active_listing_count(db: Session, seller_id: int) -> int:
    return db.scalar(
        select(func.count())
        .select_from(Listing)
        .where(Listing.seller_id == seller_id, Listing.status == ListingStatus.ACTIVE)
    )


@router.post("", response_model=ListingPublic, status_code=status.HTTP_201_CREATED)
def create_listing(
    payload: ListingCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> Listing:
    """Create a listing, enforcing the seller's SaaS tier limits.

    Requires authentication (secure creation). Enforces the Basic-tier active
    listing cap, then attaches Product Knowledge Gateway questions — either the
    seller's own, or AI-generated ones via the Specs Guard (Pro/Business).
    """
    sub = current.subscription
    tier = sub.tier if sub else SubscriptionTier.BASIC
    limit = sub.listing_limit if sub else 5

    if limit is not None and _active_listing_count(db, current.id) >= limit:
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            f"Your {tier.value} plan allows up to {limit} active listings. "
            "Upgrade to Pro for unlimited listings.",
        )

    listing = Listing(
        seller_id=current.id,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        list_price=payload.list_price,
        floor_percent=payload.floor_percent,
        sale_mode=payload.sale_mode,
        speed_discount_percent=payload.speed_discount_percent,
        district=payload.district,
        delivery_available=payload.delivery_available,
        min_buyer_adab=payload.min_buyer_adab,
    )

    # --- Product Knowledge Gateway questions ------------------------------
    for q in payload.knowledge_questions:
        if q.correct_index >= len(q.options):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "correct_index out of range")
        listing.knowledge_questions.append(
            KnowledgeQuestion(
                prompt=q.prompt,
                options=q.options,
                correct_index=q.correct_index,
                ai_generated=False,
            )
        )

    # Auto-generate via Specs Guard when the seller supplied none and their
    # tier includes it.
    if (
        not listing.knowledge_questions
        and payload.auto_generate_questions
        and sub
        and sub.has_specs_guard
    ):
        for gen in specs_guard.generate_questions(payload.title, payload.description, n=2):
            if gen["correct_index"] < len(gen["options"]):
                listing.knowledge_questions.append(
                    KnowledgeQuestion(
                        prompt=gen["prompt"],
                        options=gen["options"],
                        correct_index=gen["correct_index"],
                        ai_generated=True,
                    )
                )

    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


@router.get("", response_model=list[ListingPublic])
def list_active(
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
) -> list[Listing]:
    stmt = (
        select(Listing)
        .where(Listing.status == ListingStatus.ACTIVE)
        .order_by(Listing.created_at.desc())
        .limit(min(limit, 100))
        .offset(offset)
    )
    return list(db.scalars(stmt).all())


@router.get("/{listing_id}", response_model=ListingPublic)
def get_listing(listing_id: int, db: Session = Depends(get_db)) -> Listing:
    listing = db.get(Listing, listing_id)
    if listing is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Listing not found")
    return listing
