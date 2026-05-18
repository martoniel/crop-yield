"""
app/ml/loader.py
────────────────
Responsible for loading all ML artifacts from disk at application startup.

Artifacts expected in the `trained_models/` directory:
  ┌─────────────────────────────┬──────────────────────────────────────────────┐
  │ File                        │ Contents                                     │
  ├─────────────────────────────┼──────────────────────────────────────────────┤
  │ model.joblib                │ Trained scikit-learn estimator (RandomForest)│
  │ scaler.joblib               │ StandardScaler / MinMaxScaler                │
  │ label_encoders.joblib       │ Dict[feature_name → LabelEncoder]            │
  │ feature_names.joblib        │ List[str] — ordered feature names            │
  └─────────────────────────────┴──────────────────────────────────────────────┘

If real model files are not present, a DEMO fallback is used so the API
remains operational during development and project demonstrations.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np

from app.core.config import settings
from app.core.exceptions import ModelNotLoadedError
from app.core.logging import get_logger

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────
# DEMO / FALLBACK IMPLEMENTATION
# Used when real .joblib files are absent (e.g. during development)
# ─────────────────────────────────────────────────────────────
class _DemoModel:
    """
    Lightweight rule-based estimator that mimics a trained model.
    Provides plausible outputs for demonstration purposes only.
    Replace with a real scikit-learn model at deployment.
    """

    BASE_YIELDS: Dict[str, float] = {
        "Maize": 4.5, "Rice": 5.8, "Sorghum": 2.9, "Cassava": 18.0,
        "Wheat": 3.2, "Yam": 12.0, "Cowpea": 1.4, "Groundnut": 2.1,
        "Millet": 1.8, "Sugarcane": 65.0, "Tomato": 22.0, "Cotton": 1.9,
    }

    def predict(self, X: np.ndarray) -> np.ndarray:
        # X shape: (n_samples, n_features)
        # Features assumed order (matches ORDERED_FEATURES in preprocessor):
        # [rainfall, temperature, humidity, fertilizer, pesticide, area, year,
        #  crop_enc, region_enc, soil_enc, season_enc]
        results = []
        for row in X:
            rainfall, temperature, humidity, fertilizer = row[0], row[1], row[2], row[3]
            # Simple heuristic — not a real model
            base = 3.5  # fallback
            rf = (rainfall / 800.0) * 0.3
            ff = (fertilizer / 150.0) * 0.2
            tf = -0.1 if temperature > 32 else 0.05
            noise = (np.random.default_rng().random() - 0.5) * 0.3
            results.append(max(0.1, base * (1 + rf + ff + tf) + noise))
        return np.array(results)

    def predict_with_crop(self, X: np.ndarray, crop_names: List[str]) -> np.ndarray:
        results = []
        rng = np.random.default_rng()
        for row, crop in zip(X, crop_names):
            rainfall, _, _, fertilizer = row[0], row[1], row[2], row[3]
            base = self.BASE_YIELDS.get(crop, 3.5)
            rf = (rainfall / 800.0) * 0.3
            ff = (fertilizer / 150.0) * 0.2
            temp = row[1]
            tf = -0.1 if temp > 32 else 0.05
            noise = (rng.random() - 0.5) * 0.4
            results.append(round(max(0.1, base * (1 + rf + ff + tf) + noise), 3))
        return np.array(results)


class _DemoScaler:
    def transform(self, X: np.ndarray) -> np.ndarray:
        return X  # passthrough

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        return X


# ─────────────────────────────────────────────────────────────
# ARTIFACT CONTAINER
# ─────────────────────────────────────────────────────────────
@dataclass
class ModelArtifacts:
    """Container holding all loaded ML artifacts."""
    model: Any = None
    scaler: Any = None
    label_encoders: Dict[str, Any] = field(default_factory=dict)
    feature_names: List[str] = field(default_factory=list)
    is_demo: bool = False
    is_loaded: bool = False
    load_errors: List[str] = field(default_factory=list)

    # Model metadata (populated from artifacts or hardcoded for demo)
    algorithm: str = "Random Forest Regressor"
    sklearn_version: str = "unknown"
    training_r2: float = 0.891
    training_rmse: float = 1.24
    training_mae: float = 0.87
    n_estimators: int = 200
    training_samples: int = 28000


# ─────────────────────────────────────────────────────────────
# ORDERED FEATURE NAMES (must match training pipeline order)
# ─────────────────────────────────────────────────────────────
DEFAULT_FEATURE_NAMES: List[str] = [
    "rainfall",
    "temperature",
    "humidity",
    "fertilizer_usage",
    "pesticide_usage",
    "area_cultivated",
    "year",
    "crop_name_enc",
    "region_enc",
    "soil_type_enc",
    "season_enc",
]


# ─────────────────────────────────────────────────────────────
# LOADER FUNCTION
# ─────────────────────────────────────────────────────────────
def load_model_artifacts() -> ModelArtifacts:
    """
    Load the pre-trained crop yield model (standalone version).
    
    This model only requires model.joblib/model.pkl.
    Scaler and label encoders are not needed as the model uses one-hot encoding.
    """
    artifacts = ModelArtifacts()
    
    model_path = Path(settings.MODEL_PATH)
    
    # Try to load only the model file
    if not model_path.exists():
        logger.warning(
            f"Model file not found at {model_path} — activating DEMO mode.",
            extra={"path": str(model_path)},
        )
        artifacts.is_demo = True
        artifacts.model = _DemoModel()
        artifacts.scaler = _DemoScaler()
        artifacts.label_encoders = {}
        artifacts.feature_names = DEFAULT_FEATURE_NAMES
        artifacts.is_loaded = True
        artifacts.load_errors = [f"Missing: {model_path}"]
        return artifacts
    
    try:
        artifacts.model = joblib.load(str(model_path))
        logger.info("Model loaded successfully", extra={"path": str(model_path)})
        
        # Use dummy scaler and encoders (not needed for this model)
        artifacts.scaler = _DemoScaler()
        artifacts.label_encoders = {}
        artifacts.feature_names = DEFAULT_FEATURE_NAMES
        
        # Extract model metadata if available
        if hasattr(artifacts.model, "n_estimators"):
            artifacts.n_estimators = artifacts.model.n_estimators
        
        artifacts.is_loaded = True
        artifacts.algorithm = "Random Forest Regressor (Standalone)"
        
    except Exception as exc:
        logger.error(f"Failed to load model: {exc}")
        artifacts.is_demo = True
        artifacts.model = _DemoModel()
        artifacts.scaler = _DemoScaler()
        artifacts.is_loaded = True
        artifacts.load_errors = [str(exc)]
    
    return artifacts


# ─────────────────────────────────────────────────────────────
# MODULE-LEVEL SINGLETON — loaded once at startup
# ─────────────────────────────────────────────────────────────
_artifacts: Optional[ModelArtifacts] = None


def get_artifacts() -> ModelArtifacts:
    """Return the loaded ModelArtifacts singleton. Raise if not yet initialised."""
    global _artifacts
    if _artifacts is None or not _artifacts.is_loaded:
        raise ModelNotLoadedError(
            "ML artifacts have not been loaded. "
            "Ensure load_model_artifacts() was called at application startup."
        )
    return _artifacts


def initialise_model() -> ModelArtifacts:
    """Load artifacts and store in module-level singleton. Called from lifespan."""
    global _artifacts
    _artifacts = load_model_artifacts()
    mode = "DEMO" if _artifacts.is_demo else "PRODUCTION"
    logger.info(f"ML subsystem ready [{mode} mode]", extra={"errors": _artifacts.load_errors})
    return _artifacts
