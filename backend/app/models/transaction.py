"""
PayGuard AI — SQLAlchemy Database Models
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.sqlite import JSON

import enum


class RecipientType(str, enum.Enum):
    individual = "individual"
    business = "business"
    unknown = "unknown"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PayPalStatus(str, enum.Enum):
    NOT_INITIATED = "NOT_INITIATED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    CAPTURED = "CAPTURED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class Base(DeclarativeBase):
    pass


class Transaction(Base):
    """
    Stores every payment analysis and its outcome.
    No payment credentials or personal data beyond what the user entered.
    """
    __tablename__ = "transactions"

    # ── Identity ──────────────────────────────────────────────
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Payment Details (user-entered) ─────────────────────────
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    paypal_amount_usd: Mapped[float] = mapped_column(Float, nullable=True)

    recipient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient_type: Mapped[str] = mapped_column(
        String(20), default=RecipientType.unknown.value, nullable=False
    )
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=True, default="")
    description: Mapped[str] = mapped_column(Text, nullable=True, default="")

    # ── Risk Analysis ──────────────────────────────────────────
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(10), nullable=False)
    signals: Mapped[Any] = mapped_column(JSON, nullable=False, default=list)
    intent_mismatch: Mapped[bool] = mapped_column(Boolean, default=False)
    intent_mismatch_explanation: Mapped[str] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    disclaimer: Mapped[str] = mapped_column(
        Text,
        default=(
            "This is an AI-generated risk assessment and does not guarantee "
            "that a transaction is fraudulent or safe. The final decision rests with you."
        ),
    )

    # ── LLM Metadata ──────────────────────────────────────────
    llm_provider: Mapped[str] = mapped_column(String(50), nullable=True)
    llm_used: Mapped[bool] = mapped_column(Boolean, default=False)

    # ── PayPal Integration ─────────────────────────────────────
    paypal_order_id: Mapped[str] = mapped_column(String(255), nullable=True)
    paypal_status: Mapped[str] = mapped_column(
        String(20), default=PayPalStatus.NOT_INITIATED.value, nullable=False
    )
    paypal_capture_id: Mapped[str] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<Transaction id={self.id!r} "
            f"amount={self.amount} {self.currency} "
            f"risk={self.risk_score}/{self.risk_level}>"
        )
