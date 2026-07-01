"""Subscription model for the SaaS tiering logic."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import SubscriptionTier

# Active-listing limits per tier. ``None`` means unlimited.
TIER_LISTING_LIMITS: dict[SubscriptionTier, int | None] = {
    SubscriptionTier.BASIC: 5,
    SubscriptionTier.PRO: None,
    SubscriptionTier.BUSINESS: None,
}

# Which tiers unlock the AI Specs Guard.
TIER_HAS_SPECS_GUARD: dict[SubscriptionTier, bool] = {
    SubscriptionTier.BASIC: False,
    SubscriptionTier.PRO: True,
    SubscriptionTier.BUSINESS: True,
}


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    tier: Mapped[SubscriptionTier] = mapped_column(
        Enum(SubscriptionTier, native_enum=False),
        nullable=False,
        default=SubscriptionTier.BASIC,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    renews_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="subscription")

    @property
    def listing_limit(self) -> int | None:
        return TIER_LISTING_LIMITS[self.tier]

    @property
    def has_specs_guard(self) -> bool:
        return TIER_HAS_SPECS_GUARD[self.tier]
