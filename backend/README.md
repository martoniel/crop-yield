# CropYieldAI — Backend API

**Final Year Computer Science Project**  
*Crop Yield Prediction Using Machine Learning Models*

> **Developer:** Fayyad Inda Musa  
> **Department:** Computer Science  
> **Institution:** Federal University, Dutsin-Ma  
> **Academic Year:** 2024/2025

---

## Project Overview

CropYieldAI is a web-based system that predicts crop yields for Nigerian agricultural
regions using a trained **Random Forest Regressor** machine learning model.
Users submit environmental and agronomic parameters through a frontend interface;
the backend processes the request, runs the ML pipeline, and returns a structured
yield estimate with confidence scoring.

---

## Architecture

```
cropai/
├── app/
│   ├── main.py                  ← FastAPI app factory & lifespan
│   ├── api/
│   │   ├── router.py            ← Master API router (/api/v1)
│   │   ├── dependencies.py      ← JWT auth dependencies
│   │   ├── error_handlers.py    ← Global exception handlers
│   │   └── routes/
│   │       ├── predict.py       ← POST /predict
│   │       ├── predictions.py   ← GET/DELETE /predictions
│   │       ├── auth.py          ← POST /auth/register & /login
│   │       └── model_info.py    ← GET /model-info & /health
│   ├── core/
│   │   ├── config.py            ← Pydantic settings (reads .env)
│   │   ├── logging.py           ← Structured logging setup
│   │   ├── security.py          ← JWT + bcrypt helpers
│   │   └── exceptions.py        ← Custom exception classes
│   ├── db/
│   │   └── base.py              ← Async SQLAlchemy engine + session
│   ├── models/
│   │   ├── user.py              ← User ORM model
│   │   └── prediction.py        ← Prediction ORM model
│   ├── schemas/
│   │   ├── prediction.py        ← Request/response Pydantic schemas
│   │   ├── user.py              ← Auth schemas
│   │   └── common.py            ← APIResponse envelope
│   ├── services/
│   │   ├── prediction_service.py ← ML pipeline orchestration
│   │   └── auth_service.py      ← User registration & login logic
│   └── ml/
│       ├── loader.py            ← Artifact loading + demo fallback
│       └── preprocessor.py      ← Feature engineering pipeline
│
├── trained_models/              ← Place .joblib files here
├── tests/
│   └── test_predict.py          ← Integration tests
├── model_training.py            ← Reference training script
├── requirements.txt
├── .env.example
├── pytest.ini
└── README.md
```

---

## Quick Start

### 1. Clone and create virtual environment

```bash
git clone <your-repo-url>
cd cropai

python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env — at minimum set a strong SECRET_KEY
```

### 4. (Optional) Train the model

If you have real crop yield data (CSV), place it at `data/crop_yield_data.csv`
and run:

```bash
python model_training.py
```

This generates the four `.joblib` files in `trained_models/`.

> **Without real model files**, the system automatically activates **Demo Mode** —
> a rule-based fallback that produces plausible predictions for demonstrations.

### 5. Start the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API is now running at:

| Interface | URL |
|-----------|-----|
| Base URL | `http://localhost:8000` |
| Swagger UI | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |
| Health | `http://localhost:8000/api/v1/health` |

---

## API Reference

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Create new user account |
| `POST` | `/api/v1/auth/login` | Login, receive JWT token |
| `GET`  | `/api/v1/auth/me` | Get current user profile |

### Prediction

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/predict` | Run crop yield prediction |

### History

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`    | `/api/v1/predictions` | List predictions (paginated) |
| `GET`    | `/api/v1/predictions/stats` | Aggregate analytics |
| `GET`    | `/api/v1/predictions/{id}` | Get single record |
| `DELETE` | `/api/v1/predictions/{id}` | Delete a record |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/model-info` | ML model metadata |
| `GET` | `/api/v1/health` | System health check |

---

## Example API Usage

### Register a user

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Fayyad Inda Musa",
    "email": "fayyad@fud.edu.ng",
    "password": "SecurePass123"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Account created successfully.",
  "data": {
    "id": 1,
    "full_name": "Fayyad Inda Musa",
    "email": "fayyad@fud.edu.ng",
    "role": "user",
    "is_active": true,
    "created_at": "2025-06-01T10:00:00Z"
  }
}
```

---

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "fayyad@fud.edu.ng", "password": "SecurePass123"}'
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful.",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": { "id": 1, "full_name": "Fayyad Inda Musa", ... }
  }
}
```

---

### Make a Prediction

```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
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
    "year": 2025
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Crop yield prediction generated successfully.",
  "data": {
    "prediction_id": 42,
    "predicted_yield": 4.72,
    "yield_unit": "tons/ha",
    "confidence_score": 87.3,
    "model_used": "Random Forest Regressor",
    "interpretation": "Based on the provided agricultural conditions, Maize cultivated in Kano State during the Wet season of 2025 is expected to yield approximately 4.72 tons per hectare. This estimate is generated with high confidence (87.3%) by the Random Forest model.",
    "input_summary": {
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
      "year": 2025
    },
    "timestamp": "2025-06-01T14:30:00Z",
    "status": "success"
  }
}
```

---

### Get Prediction History

```bash
curl http://localhost:8000/api/v1/predictions?page=1&page_size=10 \
  -H "Authorization: Bearer <your_token>"
```

---

## Running Tests

```bash
pytest tests/ -v
```

Expected output:
```
PASSED tests/test_predict.py::test_health_check
PASSED tests/test_predict.py::test_root
PASSED tests/test_predict.py::test_predict_valid
PASSED tests/test_predict.py::test_predict_invalid_crop
PASSED tests/test_predict.py::test_predict_missing_field
PASSED tests/test_predict.py::test_list_predictions_empty
PASSED tests/test_predict.py::test_predict_and_retrieve
PASSED tests/test_predict.py::test_register_and_login
...
```

---

## Connecting to the Frontend

Set these values in your React frontend's environment (`.env`):

```
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

Then replace `mockPredict` in the frontend with:

```javascript
const API = import.meta.env.VITE_API_BASE_URL;

// POST /predict
const response = await fetch(`${API}/predict`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${localStorage.getItem("token")}`
  },
  body: JSON.stringify(formData)
});
const data = await response.json();
// data.data.predicted_yield, data.data.confidence_score, etc.
```

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI 0.111 |
| Language | Python 3.11+ |
| ORM | SQLAlchemy 2.0 (async) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| ML | scikit-learn 1.4, pandas, numpy |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Validation | Pydantic v2 |
| Server | Uvicorn (ASGI) |
| Testing | pytest + pytest-asyncio + httpx |

---

## Production Deployment Notes

1. Set `APP_ENV=production` and `DEBUG=false` in `.env`
2. Use a strong random `SECRET_KEY` (generate with `openssl rand -hex 32`)
3. Switch `DATABASE_URL` to PostgreSQL
4. Run behind a reverse proxy (nginx) with HTTPS
5. Use `gunicorn` with uvicorn workers: `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker`
6. Place real `.joblib` model files in `trained_models/`

---

*CropYieldAI Backend — Final Year CS Project — Federal University Dutsin-Ma — 2025*
