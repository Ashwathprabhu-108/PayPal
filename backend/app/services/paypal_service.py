"""
PayGuard AI — PayPal Sandbox Integration Service
==================================================
Handles:
  - OAuth 2.0 token acquisition
  - Order creation (PayPal v2 Orders API)
  - Order capture
  - Status retrieval

SANDBOX ONLY — no real money is processed.
Verified endpoints from PayPal Developer Documentation:
  https://developer.paypal.com/docs/api/orders/v2/

Currency note: PayPal Sandbox Orders API accepts USD.
INR amounts are converted at the demo rate set in config.
"""
from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger("payguard.paypal")
settings = get_settings()

# ──────────────────────────────────────────────────────────────
# Verified PayPal Sandbox Endpoints
# Base URL comes from env: https://api-m.sandbox.paypal.com
# ──────────────────────────────────────────────────────────────
TOKEN_ENDPOINT = "/v1/oauth2/token"
CREATE_ORDER_ENDPOINT = "/v2/checkout/orders"
CAPTURE_ORDER_ENDPOINT = "/v2/checkout/orders/{order_id}/capture"


class PayPalError(Exception):
    """Raised when PayPal API returns an error."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class PayPalService:
    """
    Async PayPal Sandbox client.
    Manages OAuth token lifecycle — fetches a new token per request.
    (For production, implement token caching with expiry.)
    """

    def __init__(self) -> None:
        self.base_url = settings.paypal_base_url.rstrip("/")
        self.client_id = settings.paypal_client_id
        self.client_secret = settings.paypal_client_secret

    def _check_configured(self) -> None:
        if not settings.paypal_configured:
            raise PayPalError(
                "PayPal credentials are not configured. "
                "Set PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET in your .env file."
            )

    async def _get_access_token(self) -> str:
        """
        Fetch a fresh OAuth 2.0 access token from PayPal Sandbox.
        POST /v1/oauth2/token
        """
        url = f"{self.base_url}{TOKEN_ENDPOINT}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                auth=(self.client_id, self.client_secret),
                data={"grant_type": "client_credentials"},
                headers={"Accept": "application/json"},
            )
            if response.status_code != 200:
                logger.error("PayPal token error: %s %s", response.status_code, response.text)
                raise PayPalError(
                    f"Failed to get PayPal access token: {response.text}",
                    status_code=response.status_code,
                )
            data = response.json()
            return data["access_token"]

    async def create_order(
        self,
        amount_usd: float,
        transaction_id: str,
        recipient_name: str,
        purpose: str,
    ) -> dict:
        """
        Create a PayPal Sandbox order.
        POST /v2/checkout/orders

        Returns the full PayPal order response including approval URL.

        Note: PayPal Sandbox processes USD only for standard orders.
        The amount_usd parameter should already be converted from INR.
        """
        self._check_configured()
        token = await self._get_access_token()

        url = f"{self.base_url}{CREATE_ORDER_ENDPOINT}"
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": transaction_id,
                    "description": f"PayGuard AI Demo — {purpose[:120]}",
                    "amount": {
                        "currency_code": "USD",
                        "value": f"{amount_usd:.2f}",
                    },
                    "payee": {
                        "email_address": "sandbox-business@payguardai.com",
                    },
                }
            ],
            "application_context": {
                "brand_name": "PayGuard AI",
                "landing_page": "NO_PREFERENCE",
                "user_action": "PAY_NOW",
                "return_url": f"{settings.frontend_url}/payment/success",
                "cancel_url": f"{settings.frontend_url}/payment/cancel",
            },
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation",
                },
            )

        if response.status_code not in (200, 201):
            logger.error("PayPal create order error: %s %s", response.status_code, response.text)
            raise PayPalError(
                f"Failed to create PayPal order: {response.text}",
                status_code=response.status_code,
            )

        order_data = response.json()
        logger.info("PayPal order created: %s", order_data.get("id"))
        return order_data

    async def capture_order(self, order_id: str) -> dict:
        """
        Capture an approved PayPal Sandbox order.
        POST /v2/checkout/orders/{order_id}/capture
        """
        self._check_configured()
        token = await self._get_access_token()

        url = f"{self.base_url}{CAPTURE_ORDER_ENDPOINT.format(order_id=order_id)}"

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                url,
                json={},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )

        if response.status_code not in (200, 201):
            logger.error("PayPal capture error: %s %s", response.status_code, response.text)
            raise PayPalError(
                f"Failed to capture PayPal order: {response.text}",
                status_code=response.status_code,
            )

        capture_data = response.json()
        logger.info("PayPal order captured: %s", order_data.get("id") if False else order_id)
        return capture_data

    async def get_order(self, order_id: str) -> dict:
        """
        Get PayPal order details.
        GET /v2/checkout/orders/{order_id}
        """
        self._check_configured()
        token = await self._get_access_token()

        url = f"{self.base_url}{CREATE_ORDER_ENDPOINT}/{order_id}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
            )

        if response.status_code != 200:
            raise PayPalError(
                f"Failed to get PayPal order: {response.text}",
                status_code=response.status_code,
            )
        return response.json()


def get_paypal_service() -> PayPalService:
    """FastAPI dependency — returns a PayPalService instance."""
    return PayPalService()
