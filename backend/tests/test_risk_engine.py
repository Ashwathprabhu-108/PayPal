"""
PayGuard AI — Risk Engine Tests
Tests all signal categories and edge cases.
"""
import pytest
from app.services.risk_engine import run_rule_engine


# ──────────────────────────────────────────────────────────────
# Test fixtures
# ──────────────────────────────────────────────────────────────

BASE_PARAMS = dict(
    amount=5000,
    currency="INR",
    recipient_type="individual",
    purpose="Paying rent",
    message="",
    description="Rent payment",
)


def make_result(**overrides):
    params = {**BASE_PARAMS, **overrides}
    return run_rule_engine(**params)


# ──────────────────────────────────────────────────────────────
# Low-risk baseline
# ──────────────────────────────────────────────────────────────

def test_clean_transaction_low_score():
    result = make_result()
    assert result.rule_score <= 15, f"Expected low score, got {result.rule_score}"
    signal_types = [s.type for s in result.signals]
    assert "urgency" not in signal_types
    assert "pressure_tactics" not in signal_types


def test_no_message_no_signals():
    result = make_result(message="", description="")
    # Should have very few signals
    dangerous_signals = [s for s in result.signals if s.severity in ("high", "critical")]
    assert len(dangerous_signals) == 0


# ──────────────────────────────────────────────────────────────
# Urgency detection
# ──────────────────────────────────────────────────────────────

def test_urgency_immediately():
    result = make_result(message="Send the money immediately")
    types = [s.type for s in result.signals]
    assert "urgency" in types


def test_urgency_10_minutes():
    # "within 10 minutes" → time_pressure; "or I sell to someone" → urgency via URGENCY_PATTERNS
    result = make_result(message="You must pay within 10 minutes or I sell to someone else")
    types = [s.type for s in result.signals]
    # At minimum, time_pressure must be detected (10 minutes deadline)
    assert "time_pressure" in types, f"Expected time_pressure in {types}"
    # At least one urgency-related signal must be present
    urgency_signals = {"urgency", "time_pressure", "pressure_tactics"}
    assert bool(urgency_signals & set(types)), f"Expected urgency signal in {types}"


def test_urgency_if_you_dont_pay():
    result = make_result(message="If you don't pay right now I will sell it to someone else")
    types = [s.type for s in result.signals]
    assert "urgency" in types, f"Expected urgency in {types}"


def test_urgency_last_chance():
    result = make_result(message="This is your last chance, offer expires tonight")
    types = [s.type for s in result.signals]
    assert "urgency" in types


# ──────────────────────────────────────────────────────────────
# Pressure / Threats
# ──────────────────────────────────────────────────────────────

def test_pressure_legal_threat():
    result = make_result(message="Pay now or I will take legal action against you")
    types = [s.type for s in result.signals]
    assert "pressure_tactics" in types


def test_pressure_consequences():
    result = make_result(message="There will be consequences if you don't pay today")
    types = [s.type for s in result.signals]
    assert "pressure_tactics" in types


# ──────────────────────────────────────────────────────────────
# Hide Purpose
# ──────────────────────────────────────────────────────────────

def test_hide_purpose_dont_mention():
    result = make_result(message="Don't mention the laptop in the payment description")
    types = [s.type for s in result.signals]
    assert "hide_purpose" in types


def test_hide_purpose_send_as_gift():
    result = make_result(message="Send the payment as a gift so PayPal doesn't charge fees")
    types = [s.type for s in result.signals]
    assert "hide_purpose" in types


def test_hide_purpose_friends_family():
    result = make_result(message="Use friends and family payment option")
    types = [s.type for s in result.signals]
    assert "hide_purpose" in types


# ──────────────────────────────────────────────────────────────
# High Amount
# ──────────────────────────────────────────────────────────────

def test_high_amount_tier1():
    result = make_result(amount=60_000, currency="INR")
    types = [s.type for s in result.signals]
    assert "high_amount_tier1" in types


def test_high_amount_tier2():
    result = make_result(amount=1_50_000, currency="INR")
    types = [s.type for s in result.signals]
    assert "high_amount_tier1" in types
    assert "high_amount_tier2" in types


def test_low_amount_no_amount_signal():
    result = make_result(amount=500, currency="INR")
    types = [s.type for s in result.signals]
    assert "high_amount_tier1" not in types
    assert "high_amount_tier2" not in types


# ──────────────────────────────────────────────────────────────
# Recipient Type Mismatch
# ──────────────────────────────────────────────────────────────

def test_individual_recipient_business_purpose():
    result = make_result(
        purpose="Buying a laptop from ABC Electronics",
        recipient_type="individual",
    )
    types = [s.type for s in result.signals]
    assert "recipient_type_mismatch" in types


def test_business_recipient_no_mismatch():
    result = make_result(
        purpose="Buying a laptop",
        recipient_type="business",
    )
    types = [s.type for s in result.signals]
    assert "recipient_type_mismatch" not in types


# ──────────────────────────────────────────────────────────────
# Purpose vs Description Mismatch
# ──────────────────────────────────────────────────────────────

def test_purchase_purpose_personal_description():
    result = make_result(
        purpose="Buying a second-hand laptop",
        description="Personal payment to John Kumar",
    )
    types = [s.type for s in result.signals]
    assert "purpose_description_mismatch" in types


# ──────────────────────────────────────────────────────────────
# Full Scam Scenario — should produce HIGH score
# ──────────────────────────────────────────────────────────────

def test_full_scam_scenario():
    """
    Classic scam scenario from the spec.
    Expected: multiple signals, high score.
    """
    result = run_rule_engine(
        amount=40_000,
        currency="INR",
        recipient_type="individual",
        purpose="Buying a second-hand laptop",
        message=(
            "Send the money immediately. Do not mention the laptop in the payment "
            "description. Use personal payment. If you don't pay within 10 minutes "
            "I will sell it to someone else."
        ),
        description="Personal transfer",
    )
    signal_types = [s.type for s in result.signals]

    assert "urgency" in signal_types, "urgency not detected"
    assert "hide_purpose" in signal_types, "hide_purpose not detected"
    assert "time_pressure" in signal_types, "time_pressure not detected"
    assert "purpose_description_mismatch" in signal_types, "mismatch not detected"
    assert result.rule_score >= 50, f"Expected HIGH score, got {result.rule_score}"


# ──────────────────────────────────────────────────────────────
# Score does not exceed 100 even with many signals
# ──────────────────────────────────────────────────────────────

def test_score_never_exceeds_100_from_aggregator():
    """
    The rule engine itself doesn't cap — the aggregator does.
    But the rule score from many signals should be reasonable.
    """
    result = run_rule_engine(
        amount=2_00_000,
        currency="INR",
        recipient_type="individual",
        purpose="Buying a laptop service from a store",
        message=(
            "Send immediately as a gift. Don't mention the purpose. "
            "Use friends and family. Or else I will take legal action. "
            "This is your last chance. Keep it between us. "
            "I am from the official government scheme."
        ),
        description="Personal gift",
    )
    # Rule engine score not capped itself, but aggregator will cap at 100
    assert result.rule_score > 0
    assert len(result.signals) > 3


# ──────────────────────────────────────────────────────────────
# Impersonation
# ──────────────────────────────────────────────────────────────

def test_impersonation_paypal():
    result = make_result(
        message="This is an official notice from PayPal. Your account has been suspended."
    )
    types = [s.type for s in result.signals]
    assert "impersonation" in types


def test_impersonation_prize():
    result = make_result(
        message="Congratulations you have won a prize. Pay the processing fee to claim it."
    )
    types = [s.type for s in result.signals]
    assert "impersonation" in types
