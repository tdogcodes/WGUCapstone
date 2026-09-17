from datetime import date
from pathlib import Path
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from backend.db.models import get_engine
from backend.ml.features import FEATURE_COLS, build_dataset, category_map, current_period, load_tables

ARTIFACT_DIR = Path(__file__).parent / "artifacts"
ARTIFACT_PATH = ARTIFACT_DIR / "demand_model.joblib"
N_ESTIMATORS = 200
N_SPLITS = 5
RANDOM_STATE = 42

def make_model() -> RandomForestRegressor:
    return RandomForestRegressor(n_estimators=N_ESTIMATORS, random_state=RANDOM_STATE)

def main() -> None:
    engine = get_engine()
    products, _, _ = load_tables(engine)
    cmap = category_map(products)

    df = build_dataset(engine)
    X = df[FEATURE_COLS]
    y = df["demand"]

    tscv = TimeSeriesSplit(n_splits=N_SPLITS)
    maes, rmses, r2s = [], [], []
    for train_idx, test_idx in tscv.split(X):
        model = make_model()
        model.fit(X.iloc[train_idx], y.iloc[train_idx])
        pred = model.predict(X.iloc[test_idx])
        maes.append(mean_absolute_error(y.iloc[test_idx], pred))
        rmses.append(root_mean_squared_error(y.iloc[test_idx], pred))
        r2s.append(r2_score(y.iloc[test_idx], pred))

    final = make_model()
    final.fit(X, y)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    artifact = {
        "model": final,
        "feature_cols": FEATURE_COLS,
        "category_map": cmap,
        "metrics": {
            "mae_mean": float(sum(maes) / len(maes)),
            "mae_std": float(sum((m - sum(maes) / len(maes)) ** 2 for m in maes) ** 0.5 / len(maes) ** 0.5),
            "rmse_mean": float(sum(rmses) / len(rmses)),
            "r2_mean": float(sum(r2s) / len(r2s)),
        },
        "n_samples": len(df),
        "trained_on": date.today().isoformat(),
        "predicting_month": str((current_period() + 1).month),
    }
    joblib.dump(artifact, ARTIFACT_PATH)

    print(f"Training rows: {len(df)} across {df['product_id'].nunique()} products")
    print(f"TimeSeriesSplit MAE: {artifact['metrics']['mae_mean']:.2f} +/- {artifact['metrics']['mae_std']:.2f} units")
    print(f"RMSE: {artifact['metrics']['rmse_mean']:.2f}  R2: {artifact['metrics']['r2_mean']:.3f}")
    print(f"Model saved to {ARTIFACT_PATH}")

if __name__ == "__main__":
    main()