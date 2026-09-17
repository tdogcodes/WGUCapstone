import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from backend.db.models import get_engine
from backend.ml.predict import forecast_next_month

router = APIRouter()


@router.get("/forecast/product", tags=["Forecast"])
def forecast(product_id: int | None = Query(default=None)):
    try:
        df = forecast_next_month(get_engine())
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Model not trained. Run `ml:train` first.")

    if product_id is not None:
        df = df[df["product_id"] == product_id]
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No forecast for product {product_id}")

    return df.to_dict(orient="records")