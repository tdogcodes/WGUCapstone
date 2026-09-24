from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from backend.db.models import get_engine
from backend.ml.features import FEATURE_COLS, build_dataset
from backend.ml.train import N_SPLITS, make_model

def main() -> None:
    engine = get_engine()
    df = build_dataset(engine)
    X = df[FEATURE_COLS]
    y = df["demand"]

    maes, rmses, r2s = [], [], []
    for train_idx, test_idx in TimeSeriesSplit(n_splits=N_SPLITS).split(X):
        model = make_model()
        model.fit(X.iloc[train_idx], y.iloc[train_idx])
        pred = model.predict(X.iloc[test_idx])
        maes.append(mean_absolute_error(y.iloc[test_idx], pred))
        rmses.append(root_mean_squared_error(y.iloc[test_idx], pred))
        r2s.append(r2_score(y.iloc[test_idx], pred))

    mae_mean = sum(maes) / len(maes)
    mae_std = (sum((m - mae_mean) ** 2 for m in maes) ** 0.5 / len(maes) ** 0.5)

    print(f"Evaluating {len(df)} rows across {df['product_id'].nunique()} products")
    print(f"TimeSeriesSplit MAE: {mae_mean:.2f} +/- {mae_std:.2f} units")
    print(f"RMSE: {sum(rmses) / len(rmses):.2f}  R2: {sum(r2s) / len(r2s):.3f}")

if __name__ == "__main__":
    main()