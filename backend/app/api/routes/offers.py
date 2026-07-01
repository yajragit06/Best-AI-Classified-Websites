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


def _seller_offer(offer_id: int, db: Session, current: User) -> Offer:
    """Fetch an offer, ensuring the caller is the listing's seller."""
    offer = db.get(Offer, offer_id)
    if offer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Offer not found")
    listing = db.get(Listing, offer.listing_id)
    if listing is None or listing.seller_id != current.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your listing")
    # Auto-rejected lowballs are invisible to the seller — treat as not found.
    if offer.status == OfferStatus.AUTO_REJECTED:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Offer not found")
    return offer


@router.post("/offers/{offer_id}/accept", response_model=OfferPublic)
def accept_offer(
    offer_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> Offer:
    offer = _seller_offer(offer_id, db, current)
    if offer.status != OfferStatus.PENDING:
        raise HTTPException(status.HTTP_409_CONFLICT, "Offer is no longer pending")
    offer.status = OfferStatus.ACCEPTED
    offer.listing.status = ListingStatus.RESERVED
    db.commit()
    db.refresh(offer)
    return offer


@router.post("/offers/{offer_id}/decline", response_model=OfferPublic)
def decline_offer(
    offer_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> Offer:
    offer = _seller_offer(offer_id, db, current)
    if offer.status != OfferStatus.PENDING:
        raise HTTPException(status.HTTP_409_CONFLICT, "Offer is no longer pending")
    offer.status = OfferStatus.DECLINED
    db.commit()
    db.refresh(offer)
    return offer


@router.post("/offers/{offer_id}/complete", response_model=OfferPublic)
def complete_offer(
    offer_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> Offer:
    """Mark an accepted deal as completed and reward both parties' Adab."""
    offer = _seller_offer(offer_id, db, current)
    if offer.status != OfferStatus.ACCEPTED:
        raise HTTPException(status.HTTP_409_CONFLICT, "Only accepted offers can be completed")
    offer.listing.status = ListingStatus.SOLD
    adab.apply_event(offer.buyer, AdabEventType.COMPLETED_DEAL)
    adab.apply_event(current, AdabEventType.COMPLETED_DEAL)
    db.commit()
    db.refresh(offer)
    return offer


@router.post("/offers/{offer_id}/report-ghost", response_model=OfferPublic)
def report_ghost(
    offer_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> Offer:
    """Report a buyer who accepted then vanished ("Hilang kana tiup angin")."""
    offer = _seller_offer(offer_id, db, current)
    if offer.status != OfferStatus.ACCEPTED:
        raise HTTPException(status.HTTP_409_CONFLICT, "Can only report ghosting on accepted offers")
    adab.apply_event(offer.buyer, AdabEventType.GHOSTED)
    # Free the listing back up for other buyers.
    offer.status = OfferStatus.DECLINED
    offer.listing.status = ListingStatus.ACTIVE
    db.commit()
    db.refresh(offer)
    return offer
