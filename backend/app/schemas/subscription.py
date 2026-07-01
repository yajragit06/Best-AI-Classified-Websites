"""Subscription schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import SubscriptionTier


class SubscriptionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tier: SubscriptionTier
    listing_limit: int | None
    has_specs_guard: bool
    started_at: datetime
    renews_at: datetime | None


class UpgradeRequest(BaseModel):
    tier: SubscriptionTier
