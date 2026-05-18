"""
tests/test_predict.py
──────────────────────
Integration tests for the prediction API.

Run with:
    pytest tests/ -v

Uses httpx AsyncClient for async FastAPI testing.
No real model files are required — the demo mode fallback is used.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.db.base import create_all_tables, drop_all_tables


# ─────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────
@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Reset database tables before each test."""
    await create_all_tables()
    yield
    await drop_all_tables()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c


# ─────────────────────────────────────────────────────────────
# SAMPLE PAYLOADS
# ─────────────────────────────────────────────────────────────
VALID_PAYLOAD = {
    "crop_name": "Maize",
    "region": "Kano",
    "soil_type": "Loamy",
    "rainfall": 820.0,
    "temperature": 28.5,
    "humidity": 65.0,
    "fertilizer_usage": 120.0,
    "pesticide_usage": 4.5,
    "area_cultivated": 3.5,
    "season": "Wet",
    "year": 2025,
}


# ─────────────────────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert data["app_name"] == "CropYieldAI"


# ─────────────────────────────────────────────────────────────
# ROOT
# ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


# ─────────────────────────────────────────────────────────────
# PREDICTION — valid input
# ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_predict_valid(client: AsyncClient):
    response = await client.post("/api/v1/predict", json=VALID_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["predicted_yield"] > 0
    assert data["yield_unit"] == "tons/ha"
    assert data["prediction_id"] >= 1
    assert "interpretation" in data
    assert data["input_summary"]["crop_name"] == "Maize"


# ─────────────────────────────────────────────────────────────
# PREDICTION — invalid crop
# ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_predict_invalid_crop(client: AsyncClient):
    bad = {**VALID_PAYLOAD, "crop_name": "Banana"}
    response = await client.post("/api/v1/predict", json=bad)
    assert response.status_code == 422


# ─────────────────────────────────────────────────────────────
# PREDICTION — missing required field
# ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_predict_missing_field(client: AsyncClient):
    bad = {**VALID_PAYLOAD}
    del bad["rainfall"]
    response = await client.post("/api/v1/predict", json=bad)
    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"


# ─────────────────────────────────────────────────────────────
# PREDICTION — out of range temperature
# ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_predict_temperature_out_of_range(client: AsyncClient):
    bad = {**VALID_PAYLOAD, "temperature": 200}
    response = await client.post("/api/v1/predict", json=bad)
    assert response.status_code == 422


# ─────────────────────────────────────────────────────────────
# HISTORY — list (empty)
# ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_list_predictions_empty(client: AsyncClient):
    response = await client.get("/api/v1/predictions")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 0
    assert data["results"] == []


# ─────────────────────────────────────────────────────────────
# HISTORY — predict then retrieve
# ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_predict_and_retrieve(client: AsyncClient):
    # Make a prediction
    pred_resp = await client.post("/api/v1/predict", json=VALID_PAYLOAD)
    assert pred_resp.status_code == 200
    prediction_id = pred_resp.json()["data"]["prediction_id"]

    # Retrieve by ID
    get_resp = await client.get(f"/api/v1/predictions/{prediction_id}")
    assert get_resp.status_code == 200
    record = get_resp.json()["data"]
    assert record["id"] == prediction_id
    assert record["crop_name"] == "Maize"
    assert record["predicted_yield"] > 0


# ─────────────────────────────────────────────────────────────
# HISTORY — not found
# ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_get_prediction_not_found(client: AsyncClient):
    response = await client.get("/api/v1/predictions/99999")
    assert response.status_code == 404


# ─────────────────────────────────────────────────────────────
# MODEL INFO
# ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_model_info(client: AsyncClient):
    response = await client.get("/api/v1/model-info")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "algorithm" in data
    assert "evaluation_metrics" in data
    assert "input_features" in data
    assert "limitations" in data


# ─────────────────────────────────────────────────────────────
# AUTH — register and login
# ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    # Register
    reg_resp = await client.post("/api/v1/auth/register", json={
        "full_name": "Test User",
        "email": "test@fud.edu.ng",
        "password": "TestPass123",
    })
    assert reg_resp.status_code == 201
    assert reg_resp.json()["data"]["email"] == "test@fud.edu.ng"

    # Login
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "test@fud.edu.ng",
        "password": "TestPass123",
    })
    assert login_resp.status_code == 200
    token_data = login_resp.json()["data"]
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_duplicate_registration(client: AsyncClient):
    payload = {
        "full_name": "Duplicate User",
        "email": "dup@fud.edu.ng",
        "password": "Pass12345",
    }
    await client.post("/api/v1/auth/register", json=payload)
    resp2 = await client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "full_name": "User X",
        "email": "userx@fud.edu.ng",
        "password": "RealPass99",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "userx@fud.edu.ng",
        "password": "WrongPass",
    })
    assert resp.status_code == 401
