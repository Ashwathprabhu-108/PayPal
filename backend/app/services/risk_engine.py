"""
PayGuard AI — Deterministic Risk Engine
========================================
This module NEVER calls an LLM. It always produces a score.
If the LLM is unavailable, this is the fallback.

All weights are configurable via environment variables.
See app/config.py for the full list.

Signal categories:
  - urgency          : time-pressure language
  - pressure         : threats, coercion
  - hide_purpose     : "don't mention" type instructions
  - bypass_payment   : unusual payment channel instructions
  - secrecy          : "don't tell anyone" type language
  - impersonation    : fake authority / official claims
  - high_amount      : transaction size risk
  - recipient_mismatch : individual receiving a business payment
  - purpose_mismatch : purpose vs description inconsistency
  - time_pressure    : deadline implied in message
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from app.config import get_settings
from app.schemas.schemas import RiskSignal

settings = get_settings()

# ──────────────────────────────────────────────────────────────
# Pattern Libraries
# ──────────────────────────────────────────────────────────────

# Urgency — time-bound pressure
URGENCY_PATTERNS = [
    r"\b(immediately|right now|urgent|asap|hurry|quick|fast)\b",
    r"\b(\d+\s*(minutes?|mins?|hours?|hrs?|seconds?|secs?)\s*(left|remaining|only))\b",
    r"\b(last chance|final offer|limited time|expires? (in|soon))\b",
    r"\b(pay (now|today|tonight|immediately|before) )\b",
    r"\b(if you don.?t pay|won.?t hold|selling to someone else|another buyer|sell it to someone else|i will sell)\b",
]

# Pressure / threats / coercion
PRESSURE_PATTERNS = [
    r"\b(or else|otherwise|consequences|threat|demand|must pay|have to pay)\b",
    r"\b(police|legal action|lawsuit|court|arrest|report you)\b",
    r"\b(you.?ll regret|i.?ll (expose|report|ruin)|destroy your)\b",
    r"\b(lose (the deal|your money|everything)|money is gone)\b",
]

# Hiding payment purpose
HIDE_PURPOSE_PATTERNS = [
    r"\b(don.?t (mention|write|say|put|note|include|reference))\b",
    r"\b(leave (blank|empty)|no description|don.?t describe)\b",
    r"\b(don.?t (tell|let|say) (anyone|them|paypal|the bank))\b",
    r"\b(mark (it |as )?(gift|personal|friend|family))\b",
    r"\b(as (a gift|personal|friends and family|f&f))\b",
    r"\b(use friends.?and.?family|use personal payment|send as gift)\b",
]

# Unusual payment instructions
BYPASS_PAYMENT_PATTERNS = [
    r"\b(crypto|bitcoin|btc|ethereum|eth|usdt|tether|monero)\b",
    r"\b(western union|money gram|wire transfer|gift card|itunes|amazon card|steam card|google play card)\b",
    r"\b(don.?t use (paypal|escrow|bank)|avoid (paypal|escrow))\b",
    r"\b(use (whatsapp|telegram|signal) to (send|pay|transfer))\b",
    r"\b(send (cash|money) (directly|to my account|to my number))\b",
]

# Secrecy
SECRECY_PATTERNS = [
    r"\b(keep (it |this )?(secret|between us|quiet|private))\b",
    r"\b(don.?t tell (anyone|your family|your friends|anyone else))\b",
    r"\b(our (secret|deal)|tell no one|just between (us|you and me))\b",
    r"\b(don.?t discuss|don.?t share|confidential deal)\b",
]

# Impersonation / fake authority
IMPERSONATION_PATTERNS = [
    r"\b(from (paypal|the bank|your bank|government|irs|income tax|rbi|police|customs|court))\b",
    r"\b(official (notice|communication|representative|agent|officer))\b",
    r"\b(verify your account|your account (has been|is) (suspended|locked|blocked|compromised))\b",
    r"\b(prize|lottery|winner|you have won|congratulations you)\b",
    r"\b(nigerian prince|inheritance|unclaimed funds|beneficiary)\b",
]

# Time pressure (deadline in message)
TIME_PRESSURE_PATTERNS = [
    r"\b(\d+\s*(minute|min|hour|hr|second|sec)s?\b)",
    r"\b(by (tonight|tomorrow|end of day|eod|today|this evening|midnight))\b",
    r"\b(deadline|expires?|last day|before \d+)\b",
]

# ──────────────────────────────────────────────────────────────
# Business-purchase keywords (for purpose/recipient mismatch)
# ──────────────────────────────────────────────────────────────
BUSINESS_PURPOSE_KEYWORDS = [
    "buy", "purchase", "order", "product", "service", "shop", "store",
    "electronics", "laptop", "phone", "mobile", "car", "vehicle",
    "rent", "lease", "subscription", "invoice", "package", "delivery",
    "freelance", "design", "development", "consulting", "course",
    "training", "ticket", "booking", "reservation",
]

PERSONAL_DESCRIPTION_KEYWORDS = [
    "personal", "gift", "family", "friends", "friend", "personal transfer",
    "personal payment", "birthday", "loan", "borrow",
]


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def _match_any(text: str, patterns: list[str]) -> list[str]:
    """Return list of matched pattern strings (for debug/evidence)."""
    text_lower = text.lower()
    matched = []
    for pattern in patterns:
        if re.search(pattern, text_lower):
            matched.append(pattern)
    return matched


def _keyword_match(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


# ──────────────────────────────────────────────────────────────
# RuleEngine
# ──────────────────────────────────────────────────────────────

@dataclass
class RuleEngineResult:
    """Raw output from the deterministic rule engine."""
    signals: list[RiskSignal] = field(default_factory=list)
    rule_score: int = 0


def run_rule_engine(
    *,
    amount: float,
    currency: str,
    recipient_type: str,
    purpose: str,
    message: str,
    description: str,
) -> RuleEngineResult:
    """
    Analyze a proposed transaction with deterministic rules.

    Returns a RuleEngineResult with individual signals and a base score.
    Score is NOT capped here — capping happens in the aggregator.
    """
    result = RuleEngineResult()
    s = settings  # alias for readability

    # Combine all free-text for pattern matching
    combined_text = f"{message} {description} {purpose}"

    def _add_signal(
        signal_type: str,
        severity: Literal["low", "medium", "high", "critical"],
        title: str,
        explanation: str,
        contribution: int,
    ) -> None:
        result.signals.append(
            RiskSignal(
                type=signal_type,
                severity=severity,
                title=title,
                explanation=explanation,
                score_contribution=contribution,
                source="rule_engine",
            )
        )
        result.rule_score += contribution

    # ── 1. Urgency ───────────────────────────────────────────
    if _match_any(combined_text, URGENCY_PATTERNS):
        _add_signal(
            "urgency",
            "high",
            "Urgency Language Detected",
            (
                "The message contains language designed to rush you into paying quickly. "
                "Legitimate sellers rarely pressure buyers with extreme urgency. "
                "Take time to verify before sending money."
            ),
            s.risk_weight_urgency,
        )

    # ── 2. Time Pressure (deadline) ───────────────────────────
    if _match_any(combined_text, TIME_PRESSURE_PATTERNS):
        _add_signal(
            "time_pressure",
            "medium",
            "Short Payment Deadline",
            (
                "A specific deadline or time limit appears in the message. "
                "Artificial deadlines are a common tactic in payment scams."
            ),
            s.risk_weight_time_pressure,
        )

    # ── 3. Pressure / Threats ────────────────────────────────
    if _match_any(combined_text, PRESSURE_PATTERNS):
        _add_signal(
            "pressure_tactics",
            "high",
            "Pressure or Threat Language",
            (
                "The message contains threatening or coercive language. "
                "Legitimate transactions should never involve threats. "
                "Consider stopping and verifying this person independently."
            ),
            s.risk_weight_pressure,
        )

    # ── 4. Request to Hide Payment Purpose ───────────────────
    if _match_any(combined_text, HIDE_PURPOSE_PATTERNS):
        _add_signal(
            "hide_purpose",
            "critical",
            "Request to Hide Payment Purpose",
            (
                "The message asks you to avoid describing the payment correctly, "
                "use 'friends & family', or send as a 'gift'. "
                "This removes your buyer protections and is a strong scam indicator."
            ),
            s.risk_weight_hide_purpose,
        )

    # ── 5. Unusual Payment Channel ───────────────────────────
    if _match_any(combined_text, BYPASS_PAYMENT_PATTERNS):
        _add_signal(
            "bypass_payment",
            "high",
            "Unusual Payment Channel Requested",
            (
                "The message suggests bypassing standard payment methods or using "
                "gift cards, cryptocurrency, or wire transfers. "
                "These channels are commonly used to make fraud untraceable."
            ),
            s.risk_weight_bypass_payment,
        )

    # ── 6. Secrecy Request ───────────────────────────────────
    if _match_any(combined_text, SECRECY_PATTERNS):
        _add_signal(
            "secrecy",
            "high",
            "Request for Secrecy",
            (
                "You are being asked to keep this payment secret. "
                "Legitimate transactions do not require secrecy. "
                "This is a common element of social engineering attacks."
            ),
            s.risk_weight_secrecy,
        )

    # ── 7. Impersonation ─────────────────────────────────────
    if _match_any(combined_text, IMPERSONATION_PATTERNS):
        _add_signal(
            "impersonation",
            "critical",
            "Possible Impersonation or Fake Authority",
            (
                "The message contains language suggesting official authority, "
                "a prize, or an inheritance. These are hallmarks of impersonation scams. "
                "Always verify directly through official channels."
            ),
            s.risk_weight_impersonation,
        )

    # ── 8. High Amount — Tier 1 (> ₹50,000) ─────────────────
    if currency == "INR" and amount > 50_000:
        _add_signal(
            "high_amount_tier1",
            "medium",
            "High-Value Transaction",
            (
                f"This payment (₹{amount:,.0f}) is above ₹50,000. "
                "High-value payments to unverified recipients deserve extra scrutiny."
            ),
            s.risk_weight_high_amount_tier1,
        )

    # ── 9. High Amount — Tier 2 (> ₹1,00,000) ───────────────
    if currency == "INR" and amount > 1_00_000:
        _add_signal(
            "high_amount_tier2",
            "high",
            "Very High-Value Transaction",
            (
                f"This payment (₹{amount:,.0f}) exceeds ₹1,00,000. "
                "Ensure you have fully verified the recipient before proceeding."
            ),
            s.risk_weight_high_amount_tier2,
        )

    # ── 10. Recipient Type vs Purpose Mismatch ───────────────
    purpose_suggests_business = _keyword_match(purpose, BUSINESS_PURPOSE_KEYWORDS)
    recipient_is_individual = recipient_type == "individual"

    if purpose_suggests_business and recipient_is_individual:
        _add_signal(
            "recipient_type_mismatch",
            "medium",
            "Business Purchase from Individual Recipient",
            (
                "Your stated purpose suggests a business transaction (buying a product/service), "
                "but the recipient appears to be an individual. "
                "Legitimate businesses typically have registered business accounts."
            ),
            s.risk_weight_individual_business_mismatch,
        )

    # ── 11. Purpose vs Description Mismatch ──────────────────
    desc_lower = description.lower()
    purpose_has_business = _keyword_match(purpose, BUSINESS_PURPOSE_KEYWORDS)
    desc_is_personal = _keyword_match(description, PERSONAL_DESCRIPTION_KEYWORDS)

    if purpose_has_business and desc_is_personal:
        _add_signal(
            "purpose_description_mismatch",
            "high",
            "Payment Description Does Not Match Purpose",
            (
                "You stated this payment is for a purchase, but the payment description "
                "describes it as a personal/gift transfer. This inconsistency can "
                "indicate an attempt to circumvent buyer protections."
            ),
            s.risk_weight_purpose_description_mismatch,
        )

    return result
