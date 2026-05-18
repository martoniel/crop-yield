"""
model_training.py
──────────────────
Reference training script for the CropYieldAI model.

This script documents the full training pipeline used to produce
the model artifacts deployed in the backend API.

USAGE:
    python model_training.py

This will:
  1. Load and clean the dataset
  2. Encode categorical features
  3. Scale numeric features
  4. Train a RandomForestRegressor
  5. Evaluate on test set
  6. Save all artifacts to trained_models/

NOTE: Replace `load_dataset()` with your actual data source.
The FAO / Kaggle "Crop Yield Prediction Dataset" was used in this project.
"""

import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

# ─────────────────────────────────────────────────────────────
# 1. CONFIGURATION
# ─────────────────────────────────────────────────────────────
OUTPUT_DIR = Path("trained_models")
OUTPUT_DIR.mkdir(exist_ok=True)

RANDOM_STATE = 42
TEST_SIZE = 0.20

# Categorical columns that require label encoding
CATEGORICAL_COLS = ["crop_name", "region", "soil_type", "season"]

# Numeric feature columns
NUMERIC_COLS = [
    "rainfall", "temperature", "humidity",
    "fertilizer_usage", "pesticide_usage",
    "area_cultivated", "year",
]

# All features in training order (matches DEFAULT_FEATURE_NAMES in loader.py)
FEATURE_NAMES = NUMERIC_COLS + [f"{c}_enc" for c in CATEGORICAL_COLS]

TARGET_COL = "yield_tons_per_ha"


# ─────────────────────────────────────────────────────────────
# 2. DATA LOADING (replace with real CSV path)
# ─────────────────────────────────────────────────────────────
def load_dataset(path: str = "data/crop_yield_data.csv") -> pd.DataFrame:
    """
    Load the crop yield dataset from CSV.

    Expected columns:
        crop_name, region, soil_type, rainfall, temperature, humidity,
        fertilizer_usage, pesticide_usage, area_cultivated, season,
        year, yield_tons_per_ha
    """
    df = pd.read_csv(path)
    print(f"[DATA] Loaded {len(df):,} rows, {df.shape[1]} columns")
    return df


def generate_synthetic_dataset(n_samples: int = 5000) -> pd.DataFrame:
    """
    Generate a synthetic dataset for demonstration/testing when real data
    is unavailable. Yields follow plausible distributions per crop.

    ⚠️ This is for academic demonstration only.
    Use a real agronomic dataset for your actual project.
    """
    rng = np.random.default_rng(RANDOM_STATE)
    crops = ["Maize", "Rice", "Sorghum", "Cassava", "Wheat", "Yam",
             "Cowpea", "Groundnut", "Millet", "Sugarcane", "Tomato", "Cotton"]
    regions = ["Kano", "Lagos", "Benue", "Kaduna", "Oyo", "Enugu",
               "Rivers", "Plateau", "Katsina", "Sokoto", "FCT", "Niger"]
    soils = ["Loamy", "Clay", "Sandy", "Clay Loam", "Sandy Loam"]
    seasons = ["Wet", "Dry", "Kharif", "Rabi"]
    base_yields = {
        "Maize": 4.5, "Rice": 5.8, "Sorghum": 2.9, "Cassava": 18.0,
        "Wheat": 3.2, "Yam": 12.0, "Cowpea": 1.4, "Groundnut": 2.1,
        "Millet": 1.8, "Sugarcane": 65.0, "Tomato": 22.0, "Cotton": 1.9,
    }

    crop_col = rng.choice(crops, size=n_samples)
    rows = []
    for crop in crop_col:
        base = base_yields[crop]
        rainfall = rng.uniform(200, 1800)
        temp = rng.uniform(18, 38)
        humidity = rng.uniform(30, 90)
        fertilizer = rng.uniform(20, 400)
        pesticide = rng.uniform(0.5, 15)
        area = rng.uniform(0.5, 20)
        season = rng.choice(seasons)
        region = rng.choice(regions)
        soil = rng.choice(soils)
        year = int(rng.integers(2005, 2024))

        # Yield influenced by inputs (for synthetic correlation)
        y = (
            base
            * (1 + 0.0003 * (rainfall - 600))
            * (1 + 0.001 * (fertilizer - 100))
            * (1 - 0.01 * max(0, temp - 30))
            + rng.normal(0, base * 0.08)
        )
        rows.append({
            "crop_name": crop,
            "region": region,
            "soil_type": soil,
            "rainfall": round(rainfall, 1),
            "temperature": round(temp, 1),
            "humidity": round(humidity, 1),
            "fertilizer_usage": round(fertilizer, 1),
            "pesticide_usage": round(pesticide, 2),
            "area_cultivated": round(area, 2),
            "season": season,
            "year": year,
            "yield_tons_per_ha": round(max(0.1, y), 3),
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────
# 3. PREPROCESSING
# ─────────────────────────────────────────────────────────────
def preprocess_dataframe(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, LabelEncoder]]:
    """
    Encode categorical columns and return (encoded_df, label_encoders_dict).
    """
    df = df.copy()

    # Drop rows with missing target
    df = df.dropna(subset=[TARGET_COL])

    # Fill numeric NaNs with median
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())

    # Encode categoricals
    label_encoders: dict[str, LabelEncoder] = {}
    for col in CATEGORICAL_COLS:
        le = LabelEncoder()
        df[f"{col}_enc"] = le.fit_transform(df[col].astype(str))
        label_encoders[col] = le
        print(f"[ENCODE] {col}: {list(le.classes_)}")

    return df, label_encoders


# ─────────────────────────────────────────────────────────────
# 4. TRAINING
# ─────────────────────────────────────────────────────────────
def train_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
) -> RandomForestRegressor:
    """Train the RandomForestRegressor with tuned hyperparameters."""
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        max_features="sqrt",
        n_jobs=-1,              # use all CPU cores
        random_state=RANDOM_STATE,
        verbose=0,
    )
    print("[TRAIN] Fitting Random Forest...")
    model.fit(X_train, y_train)
    print(f"[TRAIN] Done. Trees: {model.n_estimators}")
    return model


# ─────────────────────────────────────────────────────────────
# 5. EVALUATION
# ─────────────────────────────────────────────────────────────
def evaluate_model(
    model: RandomForestRegressor,
    X_test: np.ndarray,
    y_test: np.ndarray,
    X_train: np.ndarray,
    y_train: np.ndarray,
) -> dict:
    y_pred = model.predict(X_test)

    r2   = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae  = mean_absolute_error(y_test, y_pred)

    # 5-fold cross-validation on training data
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="r2", n_jobs=-1)

    metrics = {
        "r2_score":       round(r2, 4),
        "rmse":           round(rmse, 4),
        "mae":            round(mae, 4),
        "cv_r2_mean":     round(cv_scores.mean(), 4),
        "cv_r2_std":      round(cv_scores.std(), 4),
        "test_samples":   len(y_test),
        "train_samples":  len(y_train),
    }

    print("\n[EVAL] ── Model Evaluation ──────────────────────")
    for k, v in metrics.items():
        print(f"       {k:20s}: {v}")
    print("[EVAL] ─────────────────────────────────────────\n")

    # Feature importances
    importances = sorted(
        zip(FEATURE_NAMES, model.feature_importances_),
        key=lambda x: x[1], reverse=True
    )
    print("[FEAT] Feature importances:")
    for fname, imp in importances:
        bar = "█" * int(imp * 60)
        print(f"       {fname:25s} {imp:.4f}  {bar}")

    return metrics


# ─────────────────────────────────────────────────────────────
# 6. SAVE ARTIFACTS
# ─────────────────────────────────────────────────────────────
def save_artifacts(
    model: RandomForestRegressor,
    scaler: StandardScaler,
    label_encoders: dict,
    feature_names: list,
) -> None:
    joblib.dump(model,          OUTPUT_DIR / "model.joblib")
    joblib.dump(scaler,         OUTPUT_DIR / "scaler.joblib")
    joblib.dump(label_encoders, OUTPUT_DIR / "label_encoders.joblib")
    joblib.dump(feature_names,  OUTPUT_DIR / "feature_names.joblib")
    print(f"\n[SAVE] Artifacts saved to: {OUTPUT_DIR.resolve()}/")
    for f in OUTPUT_DIR.glob("*.joblib"):
        size_kb = f.stat().st_size / 1024
        print(f"       {f.name:35s} {size_kb:.1f} KB")


# ─────────────────────────────────────────────────────────────
# 7. MAIN PIPELINE
# ─────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  CropYieldAI — Model Training Pipeline")
    print("  Final Year Project · Fayyad Inda Musa · FUD")
    print("=" * 55)

    # Load data — swap generate_synthetic_dataset() for load_dataset()
    # when your real dataset is ready.
    print("\n[DATA] Generating synthetic training data (replace with real CSV)...")
    df = generate_synthetic_dataset(n_samples=10000)
    print(f"[DATA] Dataset shape: {df.shape}")
    print(f"[DATA] Target stats:\n{df[TARGET_COL].describe().round(3)}\n")

    # Preprocess
    df_enc, label_encoders = preprocess_dataframe(df)

    # Assemble feature matrix and target vector
    X = df_enc[FEATURE_NAMES].values.astype(np.float64)
    y = df_enc[TARGET_COL].values.astype(np.float64)

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    print(f"[SPLIT] Train: {len(X_train):,}  Test: {len(X_test):,}")

    # Fit scaler on training data only (NEVER on test data)
    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)

    # Train
    model = train_model(X_train_sc, y_train)

    # Evaluate
    metrics = evaluate_model(model, X_test_sc, y_test, X_train_sc, y_train)

    # Save
    save_artifacts(model, scaler, label_encoders, FEATURE_NAMES)

    print("\n✅  Training complete. You can now start the API server.")
    print("   uvicorn app.main:app --reload\n")
    return metrics


if __name__ == "__main__":
    main()
