"""
PayGuard AI — Analysis API Router
POST /api/analyze
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.database import get_db
from app.models import Transaction
from app.schemas import AnalyzeRequest, AnalyzeResponse
from app.services import analyze_transaction

logger = logging.getLogger("payguard.api.analyze")
router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_payment(
    request: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
) -> AnalyzeResponse:
    """
    Analyze a proposed payment for risk signals.

    Combines deterministic rule-based detection with optional LLM analysis
    and payment intent verification.

    Returns a risk score (0–100), risk level, detected signals,
    and a recommendation. This is a risk assessment only — not a fraud determination.
    """
    try:
        result = await analyze_transaction(request)
    except Exception as e:
        logger.exception("Error during transaction analysis")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    # Persist to database
    try:
        transaction = Transaction(
            id=result.transaction_id,
            amount=request.amount,
            currency=request.currency,
            paypal_amount_usd=result.paypal_amount_usd,
            recipient_name=request.recipient_name,
            recipient_type=request.recipient_type,
            purpose=request.purpose,
            message=request.message or "",
            description=request.description or "",
            risk_score=result.risk_score,
            risk_level=result.risk_level,
            signals=[s.model_dump() for s in result.signals],
            intent_mismatch=result.intent_mismatch,
            intent_mismatch_explanation=result.intent_mismatch_explanation,
            recommendation=result.recommendation,
            llm_used=result.llm_used,
            llm_provider=result.llm_provider,
        )
        db.add(transaction)
        await db.commit()
        logger.info("Transaction %s saved to DB", result.transaction_id)
    except Exception as db_err:
        logger.error("Failed to save transaction to DB: %s", db_err)
        # Do NOT fail the API call — DB write failure is non-critical for the analysis

    return result
