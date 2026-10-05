"""
PayGuard AI — Risk Aggregation Service
========================================
Combines outputs from:
  1. Rule-based risk engine (deterministic, always runs)
  2. LLM analysis (optional, graceful fallback)
  3. Intent verification (deterministic, always runs)

Into a final risk score, risk level, and recommendation.

Scoring formula:
  final_score = min(100, rule_score + intent_boost + llm_boost)

The LLM can only add up to LLM_MAX_BOOST points to the score.
The LLM cannot lower the rule-engine score.
The final decision is ALWAYS the user's.
"""
from __future__ import annotations

import uuid
import logging
from typing import Optional

from app.config import get_settings
from app.schemas.schemas import AnalyzeRequest, AnalyzeResponse, RiskSignal
from app.services.risk_engine import run_rule_engine
from app.services.ai_service import analyze_with_ai
from app.services.intent_service import verify_payment_intent

logger = logging.getLogger("payguard.aggregator")
settings = get_settings()

# Max additional score points the LLM can contribute
LLM_MAX_BOOST = 20

# ──────────────────────────────────────────────────────────────
# Scoring → Risk Level → Recommendation
# ──────────────────────────────────────────────────────────────

def _score_to_level(score: int) -> str:
    if score <= 25:
        return "LOW"
    elif score <= 50:
        return "MEDIUM"
    elif score <= 75:
        return "HIGH"
    else:
        return "CRITICAL"


def _recommendation(level: str, intent_mismatch: bool) -> str:
    extra = " An intent mismatch was also detected." if intent_mismatch else ""
    match level:
        case "LOW":
            return (
                "This payment shows low risk signals. "
                "Review the transaction details before proceeding."
                + extra
            )
        case "MEDIUM":
            return (
                "Some risk signals were detected. "
                "Consider verifying the recipient's identity through an independent channel "
                "before sending money."
                + extra
            )
        case "HIGH":
            return (
                "Several warning signals were detected. "
                "Carefully verify the recipient and transaction details before proceeding. "
                "If in doubt, do not send the money."
                + extra
            )
        case "CRITICAL":
            return (
                "Multiple strong warning signals were detected. "
                "Consider cancelling this payment and independently verifying the recipient "
                "through official channels before taking any action."
                + extra
            )
        case _:
            return "Review this transaction carefully before proceeding."


def _llm_boost_from_signals(llm_signals: list[RiskSignal]) -> int:
    """
    Calculate how much the LLM signals should boost the score.
    Capped at LLM_MAX_BOOST points total.
    Only high/critical severity LLM signals count.
    """
    boost = 0
    for sig in llm_signals:
        if sig.severity == "critical":
            boost += 8
        elif sig.severity == "high":
            boost += 5
        elif sig.severity == "medium":
            boost += 2
    return min(boost, LLM_MAX_BOOST)


def _inr_to_usd(amount: float) -> tuple[float, Optional[str]]:
    """Convert INR to USD for PayPal Sandbox. Returns (usd_amount, note)."""
    rate = settings.inr_to_usd_demo_rate
    usd = round(amount / rate, 2)
    note = (
        f"PayPal Sandbox uses USD. ₹{amount:,.0f} converted to "
        f"${usd:.2f} USD at demo rate of 1 USD = ₹{rate:.0f} (fixed for hackathon demo)."
    )
    return usd, note


# ──────────────────────────────────────────────────────────────
# Main Aggregator
# ──────────────────────────────────────────────────────────────

async def analyze_transaction(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Full pipeline:
    1. Run rule engine (always)
    2. Run LLM analysis (if available)
    3. Run intent verification
    4. Combine into final score + response

    Always returns a complete AnalyzeResponse.
    """
    transaction_id = str(uuid.uuid4())

    # ── Step 1: Rule Engine ──────────────────────────────────
    logger.info("Running rule engine for transaction %s", transaction_id)
    rule_result = run_rule_engine(
        amount=request.amount,
        currency=request.currency,
        recipient_type=request.recipient_type,
        purpose=request.purpose,
        message=request.message,
        description=request.description,
    )

    # ── Step 2: LLM Analysis ─────────────────────────────────
    logger.info("Running LLM analysis for transaction %s", transaction_id)
    ai_result = await analyze_with_ai(
        amount=request.amount,
        currency=request.currency,
        recipient_name=request.recipient_name,
        recipient_type=request.recipient_type,
        purpose=request.purpose,
        message=request.message,
        description=request.description,
    )

    # ── Step 3: Intent Verification ──────────────────────────
    logger.info("Running intent verification for transaction %s", transaction_id)
    intent_result = verify_payment_intent(
        amount=request.amount,
        currency=request.currency,
        recipient_name=request.recipient_name,
        recipient_type=request.recipient_type,
        purpose=request.purpose,
        message=request.message,
        description=request.description,
        llm_mismatches=ai_result.potential_mismatches if ai_result.llm_used else None,
    )

    # ── Step 4: Aggregate Score ───────────────────────────────
    llm_boost = _llm_boost_from_signals(ai_result.signals) if ai_result.llm_used else 0
    raw_score = rule_result.rule_score + intent_result.intent_score_boost + llm_boost
    final_score = min(100, raw_score)

    logger.info(
        "Score breakdown for %s: rule=%d + intent=%d + llm=%d = %d (capped: %d)",
        transaction_id,
        rule_result.rule_score,
        intent_result.intent_score_boost,
        llm_boost,
        raw_score,
        final_score,
    )

    # ── Step 5: Combine All Signals ───────────────────────────
    all_signals = (
        rule_result.signals
        + ai_result.signals
        + intent_result.signals
    )

    # Deduplicate by type+source (keep first occurrence)
    seen: set[str] = set()
    deduped_signals: list[RiskSignal] = []
    for sig in all_signals:
        key = f"{sig.type}:{sig.source}"
        if key not in seen:
            seen.add(key)
            deduped_signals.append(sig)

    # ── Step 6: Risk Level + Recommendation ───────────────────
    risk_level = _score_to_level(final_score)
    recommendation = _recommendation(risk_level, intent_result.mismatch_detected)

    # ── Step 7: Currency Note ─────────────────────────────────
    paypal_usd: Optional[float] = None
    currency_note: Optional[str] = None
    if request.currency == "INR":
        paypal_usd, currency_note = _inr_to_usd(request.amount)

    return AnalyzeResponse(
        transaction_id=transaction_id,
        risk_score=final_score,
        risk_level=risk_level,
        signals=deduped_signals,
        intent_mismatch=intent_result.mismatch_detected,
        intent_mismatch_explanation=intent_result.explanation if intent_result.mismatch_detected else None,
        intent_summary=ai_result.intent_summary or None,
        recommendation=recommendation,
        llm_used=ai_result.llm_used,
        llm_provider=ai_result.llm_provider,
        paypal_amount_usd=paypal_usd,
        currency_note=currency_note,
    )
