"""
PayGuard AI — PayPal API Router
POST /api/paypal/create-order
POST /api/paypal/capture-order
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Transaction
from app.schemas import (
    CreateOrderRequest,
    CreateOrderResponse,
    CaptureOrderRequest,
    CaptureOrderResponse,
)
from app.services import PayPalService, PayPalError, get_paypal_service

logger = logging.getLogger("payguard.api.paypal")
router = APIRouter(prefix="/paypal")


@router.post("/create-order", response_model=CreateOrderResponse)
async def create_paypal_order(
    request: CreateOrderRequest,
    db: AsyncSession = Depends(get_db),
    paypal: PayPalService = Depends(get_paypal_service),
) -> CreateOrderResponse:
    """
    Create a PayPal Sandbox order for an analyzed transaction.

    The transaction must have been previously analyzed via POST /api/analyze.
    The PayPal order is created in USD (converted from INR at demo rate).
    """
    # Load transaction
    result = await db.execute(
        select(Transaction).where(Transaction.id == request.transaction_id)
    )
    transaction: Transaction | None = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found. Run /api/analyze first.")

    if transaction.paypal_order_id:
        raise HTTPException(
            status_code=409,
            detail=f"A PayPal order already exists for this transaction: {transaction.paypal_order_id}",
        )

    # Determine USD amount
    amount_usd = transaction.paypal_amount_usd
    if amount_usd is None:
        # Fallback conversion
        from app.config import get_settings
        s = get_settings()
        amount_usd = round(transaction.amount / s.inr_to_usd_demo_rate, 2)

    try:
        order_data = await paypal.create_order(
            amount_usd=amount_usd,
            transaction_id=transaction.id,
            recipient_name=transaction.recipient_name,
            purpose=transaction.purpose,
        )
    except PayPalError as e:
        logger.error("PayPal order creation failed: %s", e)
        raise HTTPException(
            status_code=502,
            detail=f"PayPal error: {e}. Ensure Sandbox credentials are configured correctly.",
        )

    # Extract approval URL from HATEOAS links
    approval_url = ""
    for link in order_data.get("links", []):
        if link.get("rel") == "approve":
            approval_url = link.get("href", "")
            break

    if not approval_url:
        logger.error("PayPal response missing approval URL: %s", order_data)
        raise HTTPException(
            status_code=502,
            detail="PayPal order created but no approval URL returned.",
        )

    # Update transaction
    transaction.paypal_order_id = order_data["id"]
    transaction.paypal_status = "PENDING"
    await db.commit()

    return CreateOrderResponse(
        order_id=order_data["id"],
        approval_url=approval_url,
        status=order_data.get("status", "CREATED"),
    )


@router.post("/capture-order", response_model=CaptureOrderResponse)
async def capture_paypal_order(
    request: CaptureOrderRequest,
    db: AsyncSession = Depends(get_db),
    paypal: PayPalService = Depends(get_paypal_service),
) -> CaptureOrderResponse:
    """
    Capture an approved PayPal Sandbox order.

    Call this after the user has approved the payment on the PayPal approval page.
    """
    result = await db.execute(
        select(Transaction).where(Transaction.id == request.transaction_id)
    )
    transaction: Transaction | None = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found.")

    if transaction.paypal_status == "CAPTURED":
        raise HTTPException(status_code=409, detail="This order has already been captured.")

    try:
        capture_data = await paypal.capture_order(request.order_id)
    except PayPalError as e:
        logger.error("PayPal capture failed: %s", e)
        # Update status to FAILED
        transaction.paypal_status = "FAILED"
        await db.commit()
        raise HTTPException(status_code=502, detail=f"PayPal capture failed: {e}")

    # Extract capture details
    capture_id = ""
    payer_name = None
    payer_email = None
    amount_usd = None

    try:
        payer = capture_data.get("payer", {})
        payer_name_obj = payer.get("name", {})
        payer_name = f"{payer_name_obj.get('given_name', '')} {payer_name_obj.get('surname', '')}".strip()
        payer_email = payer.get("email_address")

        purchase_units = capture_data.get("purchase_units", [])
        if purchase_units:
            captures = purchase_units[0].get("payments", {}).get("captures", [])
            if captures:
                capture_id = captures[0].get("id", "")
                amount_info = captures[0].get("amount", {})
                amount_usd = float(amount_info.get("value", 0))
    except (KeyError, IndexError, ValueError) as e:
        logger.warning("Could not parse capture details: %s", e)

    # Update transaction
    transaction.paypal_status = capture_data.get("status", "CAPTURED")
    transaction.paypal_capture_id = capture_id
    await db.commit()

    return CaptureOrderResponse(
        order_id=request.order_id,
        capture_id=capture_id,
        status=capture_data.get("status", "COMPLETED"),
        payer_name=payer_name or None,
        payer_email=payer_email,
        amount_usd=amount_usd,
    )
