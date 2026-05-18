"""
app/ml/preprocessor.py
───────────────────────
Transforms raw API input (PredictionRequest) into a NumPy array
that is aligned with the training feature order expected by the model.

Pipeline:
  1. Extract numeric features (rainfall, temperature, etc.)
  2. Encode categorical features (crop_name, region, soil_type, season)
     using the saved LabelEncoders — or ordinal fallbacks in demo mode
  3. Assemble features in the exact order stored in feature_names.joblib
  4. Apply the StandardScaler transform
  5. Return shaped numpy array ready for model.predict()
"""

import numpy as np
from typing import Dict, List, Tuple, Any

from app.core.exceptions import PreprocessingError
from app.core.logging import get_logger
from app.ml.loader import ModelArtifacts
from app.schemas.prediction import PredictionRequest

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────
# ORDINAL FALLBACK MAPPINGS
# Used in demo mode when real LabelEncoders are not available.
# These must be kept in sync with training data class ordering.
# ─────────────────────────────────────────────────────────────
CROP_ORDINAL: Dict[str, int] = {
    "Cassava": 0, "Cotton": 1, "Cowpea": 2, "Groundnut": 3,
    "Maize": 4, "Millet": 5, "Rice": 6, "Sorghum": 7,
    "Sugarcane": 8, "Tomato": 9, "Wheat": 10, "Yam": 11,
}

SOIL_ORDINAL: Dict[str, int] = {
    "Chalky": 0, "Clay": 1, "Clay Loam": 2, "Loamy": 3,
    "Peat": 4, "Sandy": 5, "Sandy Loam": 6, "Silty Clay": 7,
}

SEASON_ORDINAL: Dict[str, int] = {
    "Dry": 0, "Kharif": 1, "Rabi": 2, "Wet": 3,
}

# Region ordinal — alphabetical ordering of all 37 states
REGION_ORDINAL: Dict[str, int] = {
    s: i for i, s in enumerate(sorted([
        "Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa",
        "Benue", "Borno", "Cross River", "Delta", "Ebonyi", "Edo", "Ekiti",
        "Enugu", "FCT", "Gombe", "Imo", "Jigawa", "Kaduna", "Kano",
        "Katsina", "Kebbi", "Kogi", "Kwara", "Lagos", "Nasarawa", "Niger",
        "Ogun", "Ondo", "Osun", "Oyo", "Plateau", "Rivers", "Sokoto",
        "Taraba", "Yobe", "Zamfara",
    ]))
}


def _encode_categorical(
    value: str,
    feature_name: str,
    encoders: Dict[str, Any],
) -> int:
    """
    Encode a single categorical value.
    - If a LabelEncoder exists for the feature, use it.
    - Otherwise fall back to the hardcoded ordinal mappings above.

    Raises PreprocessingError if the value is unseen and no fallback exists.
    """
    if feature_name in encoders:
        encoder = encoders[feature_name]
        try:
            return int(encoder.transform([value])[0])
        except ValueError:
            raise PreprocessingError(
                f"Unknown category '{value}' for feature '{feature_name}'.",
                detail=(
                    f"The trained encoder for '{feature_name}' has not seen '{value}'. "
                    "Retrain the model with updated data or use a supported value."
                ),
            )

    # Fallback ordinal mappings (demo / development mode)
    fallback_maps = {
        "crop_name":  CROP_ORDINAL,
        "region":     REGION_ORDINAL,
        "soil_type":  SOIL_ORDINAL,
        "season":     SEASON_ORDINAL,
    }
    mapping = fallback_maps.get(feature_name, {})
    if value in mapping:
        return mapping[value]

    # Last resort — hash-based encoding (not recommended for production)
    logger.warning(
        "Using hash-based fallback encoding",
        extra={"feature": feature_name, "value": value},
    )
    return hash(value) % 100


def preprocess(
    request: PredictionRequest,
    artifacts: ModelArtifacts,
) -> Tuple[np.ndarray, List[str]]:
    """
    Transform a PredictionRequest into a scaled feature array.

    Args:
        request:   Validated PredictionRequest from the API layer.
        artifacts: Loaded ModelArtifacts (scaler + encoders).

    Returns:
        Tuple of:
          - X: numpy array of shape (1, n_features) ready for model.predict()
          - feature_names: ordered list of feature names (for logging/debugging)

    Raises:
        PreprocessingError on any transformation failure.
    """
    try:
        encoders = artifacts.label_encoders or {}

        # ── 1. Encode categorical features ───────────────────
        crop_enc    = _encode_categorical(request.crop_name, "crop_name",  encoders)
        region_enc  = _encode_categorical(request.region,    "region",     encoders)
        soil_enc    = _encode_categorical(request.soil_type, "soil_type",  encoders)
        season_enc  = _encode_categorical(request.season,    "season",     encoders)

        # ── 2. Assemble raw feature vector ───────────────────
        # Order must match artifacts.feature_names exactly.
        feature_vector = {
            "rainfall":         float(request.rainfall),
            "temperature":      float(request.temperature),
            "humidity":         float(request.humidity),
            "fertilizer_usage": float(request.fertilizer_usage),
            "pesticide_usage":  float(request.pesticide_usage),
            "area_cultivated":  float(request.area_cultivated),
            "year":             float(request.year),
            "crop_name_enc":    float(crop_enc),
            "region_enc":       float(region_enc),
            "soil_type_enc":    float(soil_enc),
            "season_enc":       float(season_enc),
        }

        # ── 3. Order features as required by training pipeline ─
        ordered_features = artifacts.feature_names or list(feature_vector.keys())
        raw_array = np.array(
            [[feature_vector.get(f, 0.0) for f in ordered_features]],
            dtype=np.float64,
        )

        logger.debug(
            "Raw feature vector assembled",
            extra={"features": dict(zip(ordered_features, raw_array[0].tolist()))},
        )

        # ── 4. Apply scaler ──────────────────────────────────
        scaled_array = artifacts.scaler.transform(raw_array)

        logger.debug("Feature vector scaled successfully")

        return scaled_array, ordered_features

    except PreprocessingError:
        raise
    except Exception as exc:
        logger.exception("Unexpected error during preprocessing")
        raise PreprocessingError(
            "Failed to preprocess input data.",
            detail=str(exc),
        ) from exc


def build_interpretation(
    crop: str,
    region: str,
    season: str,
    year: int,
    predicted_yield: float,
    unit: str,
    confidence: float,
) -> str:
    """
    Generate a human-readable interpretation string for the result page.
    """
    confidence_label = (
        "high confidence" if confidence >= 85
        else "moderate confidence" if confidence >= 70
        else "low confidence"
    )
    return (
        f"Based on the provided agricultural conditions, {crop} cultivated in "
        f"{region} State during the {season} season of {year} is expected to yield "
        f"approximately {predicted_yield:.2f} {unit}. "
        f"This estimate is generated with {confidence_label} ({confidence:.1f}%) "
        f"by the Random Forest model."
    )
