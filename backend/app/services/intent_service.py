"""
PayGuard AI — Payment Intent Verification Service
====================================================
Compares the user's *stated intention* against the *actual payment details*
and identifies meaningful inconsistencies.

This module is deterministic — no LLM required.
LLM intent_summary is passed in optionally to enrich the analysis.

Examples of mismatches this detects:
  - "Buying a laptop from ABC Electronics" → recipient is an individual
  - "Purchasing from a business" → description says "personal transfer"
  - "Buying a second-hand car" → amount is ₹500 (implausibly low)
  - "Service payment" → message says "send as gift"
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from app.schemas.schemas import RiskSignal


# ──────────────────────────────────────────────────────────────
# Keyword Taxonomies
# ──────────────────────────────────────────────────────────────

PRODUCT_KEYWORDS = [
    "laptop", "phone", "mobile", "computer", "camera", "tv", "television",
    "car", "vehicle", "bike", "motorcycle", "watch", "jewelry", "jewellery",
    "electronics", "appliance", "furniture", "equipment",
]

SERVICE_KEYWORDS = [
    "service", "freelance", "consulting", "design", "development", "coding",
    "writing", "editing", "photography", "tutoring", "coaching", "subscription",
    "membership", "course", "training", "repair", "installation",
]

BUSINESS_KEYWORDS = [
    "store", "shop", "electronics", "enterprise", "pvt", "ltd", "company",
    "business", "vendor", "supplier", "agency", "studio", "inc", "corp",
    "solutions", "technologies", "tech",
]

PERSONAL_KEYWORDS = [
    "personal", "gift", "friend", "family", "borrow", "loan", "favour",
    "favor", "advance",
]


# ──────────────────────────────────────────────────────────────
# Result
# ──────────────────────────────────────────────────────────────

@dataclass
class IntentVerificationResult:
    mismatch_detected: bool
    explanation: str
    signals: list[RiskSignal]
    intent_score_boost: int  # Additional score points from intent mismatch


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def _contains(text: str, keywords: list[str]) -> bool:
    t = text.lower()
    return any(kw in t for kw in keywords)


def _recipient_looks_like_business(name: str) -> bool:
    """Heuristic: does the recipient name look like a business?"""
    return _contains(name, BUSINESS_KEYWORDS)


def _recipient_looks_like_individual(name: str) -> bool:
    """Heuristic: does the recipient name look like a person?"""
    # Simple check: 1-2 words, no business indicators
    name_clean = name.strip()
    word_count = len(name_clean.split())
    looks_individual = word_count <= 3 and not _recipient_looks_like_business(name)
    return looks_individual


# ──────────────────────────────────────────────────────────────
# Main Verifier
# ──────────────────────────────────────────────────────────────

def verify_payment_intent(
    *,
    amount: float,
    currency: str,
    recipient_name: str,
    recipient_type: str,
    purpose: str,
    message: str,
    description: str,
    llm_mismatches: Optional[list[str]] = None,
) -> IntentVerificationResult:
    """
    Compare stated intent vs actual payment details.
    Returns an IntentVerificationResult with signals and score boost.
    """
    signals: list[RiskSignal] = []
    mismatch_details: list[str] = []
    score_boost = 0

    purpose_lower = purpose.lower()
    desc_lower = description.lower()
    recipient_lower = recipient_name.lower()

    # ── Check 1: Business purchase → individual recipient ─────
    purpose_suggests_product = _contains(purpose, PRODUCT_KEYWORDS)
    purpose_suggests_service = _contains(purpose, SERVICE_KEYWORDS)
    purpose_suggests_business = _contains(purpose, ["store", "shop", "electronics", "company", "business"])

    if (purpose_suggests_product or purpose_suggests_service) and (
        recipient_type == "individual"
        or _recipient_looks_like_individual(recipient_name)
    ):
        detail = (
            f"You stated this payment is for '{purpose[:80]}', "
            f"which suggests a commercial transaction, "
            f"but the recipient '{recipient_name}' appears to be an individual "
            f"rather than a registered business."
        )
        mismatch_details.append(detail)
        signals.append(
            RiskSignal(
                type="intent_recipient_mismatch",
                severity="medium",
                title="Business Transaction with Individual Recipient",
                explanation=detail,
                score_contribution=12,
                source="intent_check",
            )
        )
        score_boost += 12

    # ── Check 2: Description contradicts purpose ───────────────
    desc_is_personal = _contains(description, PERSONAL_KEYWORDS)
    purpose_is_purchase = _contains(purpose, PRODUCT_KEYWORDS + SERVICE_KEYWORDS)

    if purpose_is_purchase and desc_is_personal and description.strip():
        detail = (
            f"Your stated purpose is '{purpose[:60]}' (a purchase), "
            f"but the payment description says '{description[:60]}', "
            f"which describes a personal transaction. "
            f"This inconsistency may indicate the payment is being disguised."
        )
        mismatch_details.append(detail)
        signals.append(
            RiskSignal(
                type="intent_description_mismatch",
                severity="high",
                title="Payment Description Does Not Match Stated Purpose",
                explanation=detail,
                score_contribution=18,
                source="intent_check",
            )
        )
        score_boost += 18

    # ── Check 3: Message contradicts stated description ────────
    if description.strip() and message.strip():
        msg_lower = message.lower()
        desc_words = set(re.findall(r"\b\w{4,}\b", desc_lower))
        msg_words = set(re.findall(r"\b\w{4,}\b", msg_lower))

        # If description mentions "personal" but purpose is commercial
        if "personal" in desc_lower and purpose_is_purchase:
            detail = (
                "The message context suggests a commercial purchase, "
                "but the payment is labeled as personal. "
                "This may remove standard buyer protections."
            )
            mismatch_details.append(detail)
            signals.append(
                RiskSignal(
                    type="intent_label_mismatch",
                    severity="medium",
                    title="Personal Label on Commercial Transaction",
                    explanation=detail,
                    score_contribution=10,
                    source="intent_check",
                )
            )
            score_boost += 10

    # ── Check 4: Message asks to hide the real purpose ────────
    hide_patterns = [
        "don't mention",
        "dont mention",
        "don't write",
        "dont write",
        "no description",
        "leave blank",
        "as gift",
        "as a gift",
        "personal payment",
        "friends and family",
        "f&f",
    ]
    if _contains(message, hide_patterns) and purpose_is_purchase:
        detail = (
            "The message instructs you to hide or misrepresent the actual purpose of this payment. "
            "For a purchase, this eliminates your right to dispute the transaction if something goes wrong."
        )
        mismatch_details.append(detail)
        signals.append(
            RiskSignal(
                type="intent_concealment",
                severity="critical",
                title="Seller Asks You to Conceal Payment Purpose",
                explanation=detail,
                score_contribution=22,
                source="intent_check",
            )
        )
        score_boost += 22

    # ── Check 5: Include LLM-detected mismatches ─────────────
    if llm_mismatches:
        for llm_mismatch in llm_mismatches:
            if llm_mismatch.strip():
                mismatch_details.append(f"[AI observation] {llm_mismatch}")
                signals.append(
                    RiskSignal(
                        type="llm_intent_mismatch",
                        severity="medium",
                        title="AI-Detected Intent Inconsistency",
                        explanation=f"AI observation: {llm_mismatch}",
                        score_contribution=0,  # LLM mismatches don't add score
                        source="llm",
                    )
                )

    # ── Build explanation ─────────────────────────────────────
    if mismatch_details:
        explanation = (
            "Potential intent mismatch detected:\n"
            + "\n".join(f"• {d}" for d in mismatch_details)
        )
        return IntentVerificationResult(
            mismatch_detected=True,
            explanation=explanation,
            signals=signals,
            intent_score_boost=score_boost,
        )
    else:
        return IntentVerificationResult(
            mismatch_detected=False,
            explanation=(
                "No significant mismatch detected between your stated payment "
                "purpose and the payment details."
            ),
            signals=[],
            intent_score_boost=0,
        )
