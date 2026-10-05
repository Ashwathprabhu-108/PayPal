"""
PayGuard AI — AI Analysis Service
====================================
Abstracts LLM calls behind a single interface.
Provider is selected via the LLM_PROVIDER environment variable.

Supported providers:
  - gemini    : Google Gemini (gemini-1.5-flash / gemini-2.0-flash)
  - openai    : OpenAI (gpt-4o-mini / gpt-4o)
  - anthropic : Anthropic (claude-3-haiku)
  - none      : Disabled — rule engine only

The LLM is asked to return STRUCTURED JSON only.
All output is validated with Pydantic.
Malformed output is handled gracefully — returns empty signal list.

IMPORTANT: This service never makes the final risk decision.
           It provides additional signal evidence only.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from pydantic import BaseModel, Field, ValidationError

from app.config import get_settings
from app.schemas.schemas import RiskSignal

logger = logging.getLogger("payguard.ai_service")
settings = get_settings()


# ──────────────────────────────────────────────────────────────
# LLM Response Schema (Pydantic)
# This is what we DEMAND from the LLM — validated strictly.
# ──────────────────────────────────────────────────────────────

class LLMSignal(BaseModel):
    category: str
    severity: str = "medium"
    evidence: str


class LLMAnalysisResult(BaseModel):
    """Validated LLM output — if LLM returns garbage, this raises ValidationError."""
    signals: list[LLMSignal] = Field(default_factory=list)
    intent_summary: str = ""
    potential_mismatches: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


# ──────────────────────────────────────────────────────────────
# Prompt Builder
# ──────────────────────────────────────────────────────────────

def _build_analysis_prompt(
    amount: float,
    currency: str,
    recipient_name: str,
    recipient_type: str,
    purpose: str,
    message: str,
    description: str,
) -> str:
    return f"""You are a payment risk analysis assistant for PayGuard AI.

Your job is to analyze the context of a proposed payment and identify potential risk signals.

IMPORTANT RULES:
- You MUST return valid JSON only. No markdown, no prose, no explanation outside JSON.
- Do NOT conclude that a transaction is definitely fraud. Only identify evidence.
- Do NOT fabricate evidence. Only report what is present in the data.
- Be balanced — not every transaction is suspicious.

PAYMENT CONTEXT:
- Amount: {currency} {amount:,.2f}
- Recipient: {recipient_name} (type: {recipient_type})
- Stated purpose: {purpose}
- Payment description: {description if description else "(not provided)"}
- Message from seller/other party: {message if message else "(none provided)"}

TASK:
1. Identify any risk signals present in the context above.
2. For each signal, provide the category, severity (low/medium/high/critical), and the specific evidence from the text.
3. Summarize what the user appears to intend with this payment.
4. List any inconsistencies between stated purpose and payment details.
5. Provide your confidence level (0.0 to 1.0) in the analysis.

Signal categories to consider:
- urgency: time pressure or rush tactics
- pressure: threats or coercive language
- hide_purpose: instructions to conceal payment reason
- bypass_payment: unusual payment method instructions
- secrecy: requests to keep payment hidden
- impersonation: fake authority or official claims
- high_value: unusually large payment
- recipient_mismatch: mismatch between recipient type and purpose
- intent_mismatch: inconsistency between stated intent and payment details
- suspicious_promise: unrealistic offers or promises

REQUIRED OUTPUT FORMAT (strict JSON):
{{
  "signals": [
    {{
      "category": "urgency",
      "severity": "high",
      "evidence": "The message states 'pay within 10 minutes or I sell to someone else'."
    }}
  ],
  "intent_summary": "The user appears to be purchasing a second-hand laptop.",
  "potential_mismatches": [
    "Payment description says 'personal transfer' but purpose is a product purchase."
  ],
  "confidence": 0.82
}}

If no risks are found, return:
{{
  "signals": [],
  "intent_summary": "The payment appears to be a straightforward transaction.",
  "potential_mismatches": [],
  "confidence": 0.5
}}
"""


# ──────────────────────────────────────────────────────────────
# Provider-specific callers
# ──────────────────────────────────────────────────────────────

async def _call_gemini(prompt: str) -> str:
    """Call Google Gemini and return raw text response."""
    import google.generativeai as genai  # type: ignore
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(
        model_name=settings.gemini_model,
        generation_config={
            "temperature": 0.2,
            "response_mime_type": "application/json",
        },
    )
    response = model.generate_content(prompt)
    return response.text


async def _call_openai(prompt: str) -> str:
    """Call OpenAI and return raw text response."""
    from openai import AsyncOpenAI  # type: ignore
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": "You are a payment risk analysis assistant. Return only valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    return response.choices[0].message.content or "{}"


async def _call_anthropic(prompt: str) -> str:
    """Call Anthropic Claude and return raw text response."""
    from anthropic import AsyncAnthropic  # type: ignore
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


# ──────────────────────────────────────────────────────────────
# Main AIService
# ──────────────────────────────────────────────────────────────

class AIServiceResult:
    """Output of the AI analysis service."""
    def __init__(
        self,
        signals: list[RiskSignal],
        intent_summary: str,
        potential_mismatches: list[str],
        confidence: float,
        llm_used: bool,
        llm_provider: Optional[str],
        error: Optional[str] = None,
    ):
        self.signals = signals
        self.intent_summary = intent_summary
        self.potential_mismatches = potential_mismatches
        self.confidence = confidence
        self.llm_used = llm_used
        self.llm_provider = llm_provider
        self.error = error


def _severity_map(severity: str) -> str:
    """Normalize severity from LLM to allowed values."""
    mapping = {
        "low": "low",
        "medium": "medium",
        "high": "high",
        "critical": "critical",
    }
    return mapping.get(severity.lower(), "medium")


async def analyze_with_ai(
    *,
    amount: float,
    currency: str,
    recipient_name: str,
    recipient_type: str,
    purpose: str,
    message: str,
    description: str,
) -> AIServiceResult:
    """
    Run LLM-based analysis on the payment context.
    Returns an AIServiceResult — always safe to call even if LLM fails.
    """
    if not settings.llm_available:
        logger.info("LLM disabled or not configured. Skipping AI analysis.")
        return AIServiceResult(
            signals=[],
            intent_summary="",
            potential_mismatches=[],
            confidence=0.0,
            llm_used=False,
            llm_provider=None,
            error="LLM not configured",
        )

    prompt = _build_analysis_prompt(
        amount=amount,
        currency=currency,
        recipient_name=recipient_name,
        recipient_type=recipient_type,
        purpose=purpose,
        message=message,
        description=description,
    )

    raw_text: str = ""
    provider = settings.llm_provider

    try:
        if provider == "gemini":
            raw_text = await _call_gemini(prompt)
        elif provider == "openai":
            raw_text = await _call_openai(prompt)
        elif provider == "anthropic":
            raw_text = await _call_anthropic(prompt)
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")

        # Clean up common LLM markdown wrapping
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()

        # Parse and validate
        raw_dict = json.loads(cleaned)
        parsed: LLMAnalysisResult = LLMAnalysisResult(**raw_dict)

        # Convert LLM signals → RiskSignal objects
        risk_signals: list[RiskSignal] = []
        for llm_sig in parsed.signals:
            try:
                risk_signals.append(
                    RiskSignal(
                        type=llm_sig.category,
                        severity=_severity_map(llm_sig.severity),
                        title=llm_sig.category.replace("_", " ").title(),
                        explanation=llm_sig.evidence,
                        score_contribution=0,  # LLM signals don't add score directly
                        source="llm",
                    )
                )
            except (ValidationError, Exception) as sig_err:
                logger.warning("Skipping malformed LLM signal: %s", sig_err)

        logger.info(
            "LLM analysis complete. Provider=%s, signals=%d, confidence=%.2f",
            provider,
            len(risk_signals),
            parsed.confidence,
        )

        return AIServiceResult(
            signals=risk_signals,
            intent_summary=parsed.intent_summary,
            potential_mismatches=parsed.potential_mismatches,
            confidence=parsed.confidence,
            llm_used=True,
            llm_provider=provider,
        )

    except json.JSONDecodeError as e:
        logger.error("LLM returned invalid JSON: %s | Raw: %s", e, raw_text[:200])
        return AIServiceResult(
            signals=[],
            intent_summary="",
            potential_mismatches=[],
            confidence=0.0,
            llm_used=False,
            llm_provider=provider,
            error=f"LLM returned invalid JSON: {e}",
        )
    except ValidationError as e:
        logger.error("LLM output failed Pydantic validation: %s", e)
        return AIServiceResult(
            signals=[],
            intent_summary="",
            potential_mismatches=[],
            confidence=0.0,
            llm_used=False,
            llm_provider=provider,
            error=f"LLM output validation failed: {e}",
        )
    except Exception as e:
        logger.error("LLM call failed: %s", e)
        return AIServiceResult(
            signals=[],
            intent_summary="",
            potential_mismatches=[],
            confidence=0.0,
            llm_used=False,
            llm_provider=provider,
            error=str(e),
        )
