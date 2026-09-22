import re

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from backend.db.models import get_engine

router = APIRouter()

MONTH_PATTERN = re.compile(r"^\d{4}-\d{2}$")


def _monthly_frame(engine) -> pd.DataFrame:
    sales = pd.read_sql_table("sales", engine)
    sales["sale_date"] = pd.to_datetime(sales["sale_date"])
    sales["year_month"] = sales["sale_date"].dt.strftime("%Y-%m")
    return sales


def _parse_year_month(year_month: str | None) -> str | None:
    if year_month is None:
        return None
    if not MONTH_PATTERN.match(year_month) or not 1 <= int(year_month[5:7]) <= 12:
        raise HTTPException(status_code=400, detail="year_month must be in YYYY-MM format")
    return year_month


@router.get("/shop/revenue", tags=["Shop"])
def shop_revenue(year_month: str | None = Query(default=None)):
    month = _parse_year_month(year_month)
    sales = _monthly_frame(get_engine())
    if month is not None:
        sales = sales[sales["year_month"] == month]

    monthly = (
        sales.groupby("year_month", as_index=False)["revenue"]
        .sum()
        .assign(revenue=lambda df: df["revenue"].round(2))
    )
    monthly = monthly.sort_values("year_month")
    return monthly.to_dict(orient="records")


@router.get("/shop/sales-by-category", tags=["Shop"])
def shop_sales_by_category(year_month: str | None = Query(default=None)):
    month = _parse_year_month(year_month)
    engine = get_engine()
    sales = _monthly_frame(engine)
    products = pd.read_sql_table("products", engine).rename(columns={"id": "product_id"})

    df = sales.merge(products[["product_id", "category"]], on="product_id", how="left")
    if month is not None:
        df = df[df["year_month"] == month]

    monthly = (
        df.groupby(["year_month", "category"], as_index=False)
        .agg(units_sold=("quantity", "sum"), revenue=("revenue", "sum"))
    )
    monthly["revenue"] = monthly["revenue"].round(2)
    monthly = monthly.sort_values(["year_month", "category"])
    return monthly.to_dict(orient="records")


@router.get("/shop/top-products", tags=["Shop"])
def shop_top_products(
    year_month: str | None = Query(default=None),
    limit: int = Query(default=5, ge=1, le=20),
):
    month = _parse_year_month(year_month)
    engine = get_engine()
    sales = _monthly_frame(engine)
    products = pd.read_sql_table("products", engine).rename(columns={"id": "product_id"})

    if month is None:
        month = sales["year_month"].max()

    df = sales[sales["year_month"] == month]
    df = df.merge(
        products[["product_id", "name", "category"]], on="product_id", how="left"
    )

    top = (
        df.groupby(["product_id", "name", "category"], as_index=False)
        .agg(units_sold=("quantity", "sum"), revenue=("revenue", "sum"))
        .sort_values("units_sold", ascending=False)
        .head(limit)
    )
    top["revenue"] = top["revenue"].round(2)
    return {"year_month": month, "products": top.to_dict(orient="records")}