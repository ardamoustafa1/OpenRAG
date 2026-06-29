import uuid
from typing import Any
from datetime import datetime
from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

class BillingPlan(BaseModel):
    __tablename__ = "billing_plans"

    # Note: billing_plans doesn't have tenant_id as it's global
    name: Mapped[str] = mapped_column(String(255), unique=True)
    max_users: Mapped[int] = mapped_column(Integer)
    max_documents: Mapped[int] = mapped_column(Integer)
    max_tokens_per_month: Mapped[int] = mapped_column(Integer)
    max_collections: Mapped[int] = mapped_column(Integer)
    price_usd_monthly: Mapped[float] = mapped_column(Numeric(10, 2))
    features: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class TenantSubscription(BaseModel):
    __tablename__ = "tenant_subscriptions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("billing_plans.id"))
    status: Mapped[str] = mapped_column(String(50))
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255))
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255))

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="subscriptions")
    plan: Mapped["BillingPlan"] = relationship("BillingPlan")
