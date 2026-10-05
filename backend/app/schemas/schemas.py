"""
PayGuard AI — Pydantic Schemas
Request / response models for the REST API.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator


# ──────────────────────────────────────────────────────────────
# Enums as string literals
# ──────────────────────────────────────────────────────────────
RecipientTypeStr = Literal["individual", "business", "unknown"]
RiskLevelStr = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
PayPalStatusStr = Literal[
    "NOT_INITIATED", "PENDING", "APPROVED", "CAPTURED", "CANCELLED", "FAILED"
]
SeverityStr = Literal["low", "medium", "high", "critical"]


# ──────────────────────────────────────────────────────────────
# Analysis — Request
# ──────────────────────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    """User submits this to request a payment risk analysis."""

    amount: float = Field(..., gt=0, description="Payment amount in the stated currency")
    currency: str = Field(default="INR", max_length=3, description="ISO 4217 currency code")
    recipient_name: str = Field(..., min_length=1, max_length=255)
    recipient_type: RecipientTypeStr = "unknown"
    purpose: str = Field(..., min_length=2, max_length=2000, description="User's stated reason for payment")
    message: str = Field(default="", max_length=5000, description="Any message/text from the seller or conversation")
    description: str = Field(default="", max_length=500, description="Payment description / reference note")

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("recipient_name", "purpose")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()


# ──────────────────────────────────────────────────────────────
# Analysis — Individual Signal
# ──────────────────────────────────────────────────────────────
class RiskSignal(BaseModel):
    """A single detected risk indicator."""

    type: str = Field(..., description="Machine-readable signal category")
    severity: SeverityStr
    title: str = Field(..., description="Short human-readable title")
    explanation: str = Field(..., description="Plain-language explanation of why this matters")
    score_contribution: int = Field(default=0, ge=0, le=50, description="How much this added to the score")
    source: Literal["rule_engine", "llm", "intent_check"] = "rule_engine"


# ──────────────────────────────────────────────────────────────
# Analysis — Response
# ──────────────────────────────────────────────────────────────
class AnalyzeResponse(BaseModel):
    """Full risk analysis result returned to the frontend."""

    transaction_id: str
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: RiskLevelStr
    signals: list[RiskSignal]

    intent_mismatch: bool
    intent_mismatch_explanation: Optional[str] = None
    intent_summary: Optional[str] = None

    recommendation: str
    disclaimer: str = (
        "This is an AI-generated risk assessment and does not guarantee "
        "that a transaction is fraudulent or safe. The final decision rests with you."
    )

    # Metadata
    llm_used: bool
    llm_provider: Optional[str] = None
    paypal_amount_usd: Optional[float] = None
    currency_note: Optional[str] = None


# ──────────────────────────────────────────────────────────────
# PayPal — Create Order
# ──────────────────────────────────────────────────────────────
class CreateOrderRequest(BaseModel):
    """Links a transaction to a PayPal Sandbox order."""

    transaction_id: str = Field(..., description="ID returned from /api/analyze")


class CreateOrderResponse(BaseModel):
    order_id: str
    approval_url: str
    status: str
    currency_note: str = (
        "Payment processed in USD via PayPal Sandbox. "
        "INR amount shown for reference only."
    )


# ──────────────────────────────────────────────────────────────
# PayPal — Capture Order
# ──────────────────────────────────────────────────────────────
class CaptureOrderRequest(BaseModel):
    transaction_id: str
    order_id: str


class CaptureOrderResponse(BaseModel):
    order_id: str
    capture_id: str
    status: str
    payer_name: Optional[str] = None
    payer_email: Optional[str] = None
    amount_usd: Optional[float] = None


# ──────────────────────────────────────────────────────────────
# Transaction History
# ──────────────────────────────────────────────────────────────
class TransactionSummary(BaseModel):
    """Lightweight summary for the history dashboard."""

    id: str
    created_at: datetime
    amount: float
    currency: str
    recipient_name: str
    purpose: str
    risk_score: int
    risk_level: RiskLevelStr
    paypal_status: PayPalStatusStr
    intent_mismatch: bool


class TransactionDetail(BaseModel):
    """Full transaction record including all signals."""

    id: str
    created_at: datetime
    amount: float
    currency: str
    paypal_amount_usd: Optional[float]
    recipient_name: str
    recipient_type: str
    purpose: str
    message: str
    description: str
    risk_score: int
    risk_level: RiskLevelStr
    signals: list[RiskSignal]
    intent_mismatch: bool
    intent_mismatch_explanation: Optional[str]
    recommendation: str
    disclaimer: str
    llm_used: bool
    llm_provider: Optional[str]
    paypal_order_id: Optional[str]
    paypal_status: PayPalStatusStr
    paypal_capture_id: Optional[str]


class TransactionListResponse(BaseModel):
    transactions: list[TransactionSummary]
    total: int


# ──────────────────────────────────────────────────────────────
# Health Check
# ──────────────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    status: str
    version: str
    llm_available: bool
    llm_provider: str
    paypal_configured: bool
    database: str
