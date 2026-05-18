# trained_models/

Place your trained ML artifact files here.

## Required Files

| File | Description |
|------|-------------|
| `model.joblib` | The trained scikit-learn estimator (e.g. RandomForestRegressor) |
| `scaler.joblib` | Fitted StandardScaler or MinMaxScaler used during training |
| `label_encoders.joblib` | Dict mapping categorical feature names to fitted LabelEncoder objects |
| `feature_names.joblib` | Python list of feature names in the exact order used during training |

## How to Save These After Training

After training your model in Jupyter Notebook or a training script,
save the artifacts like this:

```python
import joblib

# Save model
joblib.dump(rf_model, "trained_models/model.joblib")

# Save scaler (fit only on training data)
joblib.dump(scaler, "trained_models/scaler.joblib")

# Save label encoders (dict of {column_name: fitted_LabelEncoder})
joblib.dump(label_encoders, "trained_models/label_encoders.joblib")

# Save ordered feature names
joblib.dump(feature_names_list, "trained_models/feature_names.joblib")
```

## Demo Mode

If these files are **not present**, the system automatically activates
**Demo Mode** — a rule-based fallback that produces plausible (but not
real ML) predictions. This allows the API and frontend to function
fully during development and project demonstrations.

A warning message will appear in the logs when Demo Mode is active.

## Security

Do NOT commit real model files to public repositories if they contain
sensitive training data. Add large `.joblib` files to `.gitignore`.
