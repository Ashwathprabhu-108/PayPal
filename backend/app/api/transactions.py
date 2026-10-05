"""
PayGuard AI — Transaction History API Router
GET /api/transactions
GET /api/transactions/{id}
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models import Transaction
from app.schemas import (
    TransactionDetail,
    TransactionListResponse,
    TransactionSummary,
    RiskSignal,
)

logger = logging.getLogger("payguard.api.transactions")
router = APIRouter()


def _transaction_to_summary(t: Transaction) -> TransactionSummary:
    return TransactionSummary(
        id=t.id,
        created_at=t.created_at,
        amount=t.amount,
        currency=t.currency,
        recipient_name=t.recipient_name,
        purpose=t.purpose,
        risk_score=t.risk_score,
        risk_level=t.risk_level,
        paypal_status=t.paypal_status,
        intent_mismatch=t.intent_mismatch,
    )


def _transaction_to_detail(t: Transaction) -> TransactionDetail:
    # Deserialize signals from JSON
    signals = []
    for s in (t.signals or []):
        try:
            signals.append(RiskSignal(**s))
        except Exception:
            pass

    return TransactionDetail(
        id=t.id,
        created_at=t.created_at,
        amount=t.amount,
        currency=t.currency,
        paypal_amount_usd=t.paypal_amount_usd,
        recipient_name=t.recipient_name,
        recipient_type=t.recipient_type,
        purpose=t.purpose,
        message=t.message or "",
        description=t.description or "",
        risk_score=t.risk_score,
        risk_level=t.risk_level,
        signals=signals,
        intent_mismatch=t.intent_mismatch,
        intent_mismatch_explanation=t.intent_mismatch_explanation,
        recommendation=t.recommendation,
        disclaimer=t.disclaimer or (
            "This is an AI-generated risk assessment and does not guarantee "
            "that a transaction is fraudulent or safe."
        ),
        llm_used=t.llm_used,
        llm_provider=t.llm_provider,
        paypal_order_id=t.paypal_order_id,
        paypal_status=t.paypal_status,
        paypal_capture_id=t.paypal_capture_id,
    )


@router.get("/transactions", response_model=TransactionListResponse)
async def list_transactions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> TransactionListResponse:
    """
    Return a paginated list of transactions ordered by most recent first.
    """
    stmt = (
        select(Transaction)
        .order_by(desc(Transaction.created_at))
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    transactions = result.scalars().all()

    # Get total count
    count_stmt = select(Transaction)
    count_result = await db.execute(count_stmt)
    total = len(count_result.scalars().all())

    return TransactionListResponse(
        transactions=[_transaction_to_summary(t) for t in transactions],
        total=total,
    )


@router.get("/transactions/{transaction_id}", response_model=TransactionDetail)
async def get_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
) -> TransactionDetail:
    """
    Return the full details of a single transaction.
    """
    result = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id)
    )
    transaction: Transaction | None = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found.")

    return _transaction_to_detail(transaction)
