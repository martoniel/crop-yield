"""
Convert model.pkl to model.joblib format
"""
import pickle
import joblib
import sys
from pathlib import Path

model_dir = Path("trained_models")

try:
    # Load from pickle
    print("Loading model from model.pkl...")
    with open(model_dir / "model.pkl", "rb") as f:
        model = pickle.load(f)
    print(f"✓ Model loaded successfully")
    print(f"  Model type: {type(model).__name__}")
    
    # Save as joblib
    print("\nSaving as model.joblib...")
    joblib.dump(model, model_dir / "model.joblib")
    print(f"✓ Model saved successfully")
    print(f"  Output: {model_dir / 'model.joblib'}")
    
except Exception as e:
    print(f"✗ Error: {e}", file=sys.stderr)
    sys.exit(1)
