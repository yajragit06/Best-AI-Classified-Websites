"""Offer endpoints wiring together the anti-lowball, gateway, adab and
logistics engines."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core import adab
from app.core.anti_lowball import evaluate_offer
from app.core.knowledge_gateway import grade_quiz
from app.core.logistics import delivery_fee
from app.database import get_db
from app.models.enums import AdabEventType, ListingStatus, OfferStatus
from app.models.listing import Listing
from app.models.offer import Offer
from app.models.user import User
from app.schemas.offer import OfferCreate, OfferPublic, OfferResult

router = APIRouter(tags=["offers"])


@router.post(
    "/listings/{listing_id}/offers",
    response_model=OfferResult,
    status_code=status.HTTP_201_CREATED,
)
def make_offer(
    listing_id: int,
    payload: OfferCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> OfferResult:
    listing = db.get(Listing, listing_id)
    if listing is None or listing.status != ListingStatus.ACTIVE:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Listing not available")
    if listing.seller_id == current.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot offer on your own listing")

    # --- Adab gate: low-courtesy buyers can't even reach the seller --------
    if current.adab_score < listing.min_buyer_adab:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Your Adab score is below this seller's minimum. Complete polite, "
            "reliable deals to raise it.",
        )

    # --- Product Knowledge Gateway ----------------------------------------
    quiz = grade_quiz(listing, payload.quiz_answers)
    if not quiz.passed:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Please answer the listing's questions correctly first "
            f"({quiz.correct}/{quiz.total}). Re-read the description.",
        )
    if quiz.total > 0:
        adab.apply_event(current, AdabEventType.QUIZ_PASSED)

    # --- Logistics: fair delivery fee -------------------------------------
    fee = 0.0
    if payload.want_delivery:
        if not listing.delivery_available:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Seller does not offer delivery")
        fee = delivery_fee(listing.district, current.home_district)

    # --- Anti-Lowball Engine ----------------------------------------------
    amount = float(payload.amount)
    decision = evaluate_offer(listing, amount, payload.is_take_tonight)

    offer = Offer(
        listing_id=listing.id,
        buyer_id=current.id,
        amount=payload.amount,
        is_take_tonight=payload.is_take_tonight,
        status=decision.status,
        rejection_reason=decision.reason,
        floor_price_at_offer=decision.floor_price,
        delivery_fee=fee,
        passed_knowledge_gate=quiz.passed,
    )
    db.add(offer)
    db.commit()

    # Silent rejection: the buyer gets a neutral message, the seller is never
    # notified, protecting the seller's sentiment.
    if decision.status == OfferStatus.AUTO_REJECTED:
        return OfferResult(
            accepted_for_review=False,
            message="Thanks — your offer wasn't a match for this listing.",
            delivery_fee=fee if payload.want_delivery else None,
        )

    return OfferResult(
        accepted_for_review=True,
        message="Your offer has been sent to the seller for review.",
        delivery_fee=fee if payload.want_delivery else None,
    )


@router.get("/listings/{listing_id}/offers", response_model=list[OfferPublic])
def list_offers_for_seller(
    listing_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> list[Offer]:
    """Seller-only view of offers. Auto-rejected lowballs are never returned."""
    listing = db.get(Listing, listing_id)
    if listing is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Listing not found")
    if listing.seller_id != current.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your listing")

    stmt = (
        select(Offer)
        .where(Offer.listing_id == listing_id, Offer.status != OfferStatus.AUTO_REJECTED)
        .order_by(Offer.amount.desc())
    )
    return list(db.scalars(stmt).all())
