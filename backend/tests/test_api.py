"""
PayGuard AI — API Integration Tests
Tests the FastAPI endpoints with a test database.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import init_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Initialize in-memory test DB before each test."""
    import os
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    await init_db()
    yield


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "llm_available" in data
    assert "paypal_configured" in data


@pytest.mark.asyncio
async def test_analyze_clean_transaction():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/analyze", json={
            "amount": 2500,
            "currency": "INR",
            "recipient_name": "ABC Store",
            "recipient_type": "business",
            "purpose": "Buying a book from an online store",
            "message": "",
            "description": "Book purchase",
        })
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert data["risk_score"] >= 0
    assert data["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert "signals" in data
    assert "disclaimer" in data
    assert "transaction_id" in data


@pytest.mark.asyncio
async def test_analyze_scam_scenario():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/analyze", json={
            "amount": 40000,
            "currency": "INR",
            "recipient_name": "John Kumar",
            "recipient_type": "individual",
            "purpose": "Buying a second-hand laptop",
            "message": "Send the money immediately. Do not mention the laptop in the payment description. Use personal payment. If you don't pay within 10 minutes I will sell it to someone else.",
            "description": "Personal transfer",
        })
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] >= 50
    assert data["risk_level"] in ("HIGH", "CRITICAL")
    signal_types = [s["type"] for s in data["signals"]]
    assert len(signal_types) >= 3


@pytest.mark.asyncio
async def test_analyze_invalid_amount():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/analyze", json={
            "amount": -100,
            "currency": "INR",
            "recipient_name": "John",
            "purpose": "Buying something",
        })
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_analyze_missing_required_fields():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/analyze", json={
            "amount": 1000,
            # Missing required: recipient_name, purpose
        })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_transaction_history_empty():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/transactions")
    assert response.status_code == 200
    data = response.json()
    assert "transactions" in data
    assert isinstance(data["transactions"], list)


@pytest.mark.asyncio
async def test_transaction_detail_not_found():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/transactions/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_analyze_then_retrieve():
    """Analyze a transaction, then retrieve it from history."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Analyze
        analyze_resp = await client.post("/api/analyze", json={
            "amount": 5000,
            "currency": "INR",
            "recipient_name": "Test Recipient",
            "recipient_type": "individual",
            "purpose": "Paying for a service",
            "message": "",
            "description": "Service payment",
        })
        assert analyze_resp.status_code == 200
        transaction_id = analyze_resp.json()["transaction_id"]

        # Retrieve detail
        detail_resp = await client.get(f"/api/transactions/{transaction_id}")
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["id"] == transaction_id
        assert detail["recipient_name"] == "Test Recipient"

        # Should appear in list
        list_resp = await client.get("/api/transactions")
        assert list_resp.status_code == 200
        ids = [t["id"] for t in list_resp.json()["transactions"]]
        assert transaction_id in ids
