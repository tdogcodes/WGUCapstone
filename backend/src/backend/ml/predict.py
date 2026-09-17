import joblib
import pandas as pd

from backend.db.models import get_engine
from backend.ml.features import (
    FEATURE_COLS,
    build_prediction_features,
    current_period,
    load_tables,
    monthly_demand,
)
from backend.ml.train import ARTIFACT_PATH

def load_artifact() -> dict:
    return joblib.load(ARTIFACT_PATH)

def _units_sold_last_month(sales: pd.DataFrame) -> pd.DataFrame:
    last_completed = current_period() - 1
    monthly = monthly_demand(sales)
    last = monthly[monthly["year_month"] == last_completed]
    return last[["product_id", "demand"]].rename(columns={"demand": "units_sold_last_month"})

def recommend(stock: float, demand: float) -> tuple[str, int]:
    if stock < demand:
        return "increase", int(-(-(demand - stock) // 1))
    if stock > demand * 1.5:
        return "decrease", -int(-(stock - demand) // 1)
    return "maintain", 0

def forecast_next_month(engine) -> pd.DataFrame:
    artifact = load_artifact()
    model = artifact["model"]
    cmap = artifact["category_map"]

    _, sales, _ = load_tables(engine)
    df = build_prediction_features(engine, cmap=cmap)
    df = df.rename(columns={"name": "product_name"})
    df["predicted_demand"] = model.predict(df[FEATURE_COLS])
    df = df.merge(_units_sold_last_month(sales), on="product_id", how="left")
    df["units_sold_last_month"] = df["units_sold_last_month"].fillna(0).astype(int)
    df[["recommendation", "adjustment"]] = df.apply(
        lambda row: pd.Series(recommend(row["current_stock"], row["predicted_demand"])),
        axis=1,
    )

    cols = [
        "product_id",
        "product_name",
        "category",
        "price",
        "units_sold_last_month",
        "current_stock",
        "predicted_demand",
        "recommendation",
        "adjustment",
    ]
    return df[cols].sort_values("product_id")

def main() -> None:
    engine = get_engine()
    df = forecast_next_month(engine)
    print(df.to_string(index=False))

if __name__ == "__main__":
    main()