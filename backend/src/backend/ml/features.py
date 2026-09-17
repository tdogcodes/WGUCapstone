import pandas as pd

FEATURE_COLS = [
    "demand_lag_1",
    "demand_lag_2",
    "demand_lag_3",
    "price",
    "category_code",
    "current_stock",
    "month",
]

LAG_MONTHS = 3

def load_tables(engine) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    products = pd.read_sql_table("products", engine).rename(columns={"id": "product_id"})
    sales = pd.read_sql_table("sales", engine)
    inventory = pd.read_sql_table("inventory", engine)
    return products, sales, inventory

def category_map(products: pd.DataFrame) -> dict[str, int]:
    categories = sorted(products["category"].unique())
    return {cat: i for i, cat in enumerate(categories)}

def current_period() -> pd.Period:
    return pd.Timestamp.today().to_period("M")

def monthly_demand(sales: pd.DataFrame) -> pd.DataFrame:
    df = sales.copy()
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    df["year_month"] = df["sale_date"].dt.to_period("M")

    monthly = (
        df.groupby(["product_id", "year_month"], as_index=False)["quantity"]
        .sum()
        .rename(columns={"quantity": "demand"})
    )

    months = pd.period_range(monthly["year_month"].min(), monthly["year_month"].max(), freq="M")
    grid = pd.DataFrame(
        pd.MultiIndex.from_product(
            [monthly["product_id"].unique(), months], names=["product_id", "year_month"]
        ).tolist(),
        columns=["product_id", "year_month"],
    )
    monthly = grid.merge(monthly, on=["product_id", "year_month"], how="left")
    monthly["demand"] = monthly["demand"].fillna(0)
    return monthly

def add_lags(monthly: pd.DataFrame) -> pd.DataFrame:
    df = monthly.copy().sort_values(["product_id", "year_month"])
    for i in range(1, LAG_MONTHS + 1):
        df[f"demand_lag_{i}"] = df.groupby("product_id")["demand"].shift(i)
    return df

def completed_monthly_demand(sales: pd.DataFrame) -> pd.DataFrame:
    monthly = monthly_demand(sales)
    return monthly[monthly["year_month"] < current_period()]

def build_dataset(engine) -> pd.DataFrame:
    products, sales, inventory = load_tables(engine)
    cmap = category_map(products)
    monthly = completed_monthly_demand(sales)
    monthly = add_lags(monthly)
    products_with_sales = set(sales["product_id"].unique())
    monthly = monthly[monthly["product_id"].isin(products_with_sales)]
    
    df = monthly.merge(products, on="product_id")
    df = df.merge(inventory[["product_id", "current_stock"]], on="product_id")
    df["month"] = df["year_month"].dt.month
    df["category_code"] = df["category"].map(cmap)
    df.columns = [str(c) for c in df.columns]
    return df.dropna(subset=[f"demand_lag_{i}" for i in range(1, LAG_MONTHS + 1)])

def build_prediction_features(engine, cmap: dict[str, int] | None = None) -> pd.DataFrame:
    products, sales, inventory = load_tables(engine)
    if cmap is None:
        cmap = category_map(products)
    current = current_period()
    lag_months = [current - i for i in range(LAG_MONTHS, 0, -1)]
    monthly = monthly_demand(sales)
    recent = monthly[monthly["year_month"].isin(lag_months)]
    pivot = (
        recent.pivot(index="product_id", columns="year_month", values="demand")
        .reindex(columns=lag_months)
        .reset_index()
    )
    pivot.columns = ["product_id"] + [f"demand_lag_{i}" for i in range(1, LAG_MONTHS + 1)]

    df = products.merge(pivot, on="product_id", how="left")
    df = df.merge(inventory[["product_id", "current_stock"]], on="product_id", how="left")
    lag_cols = [f"demand_lag_{i}" for i in range(1, LAG_MONTHS + 1)]
    df[lag_cols + ["current_stock"]] = df[lag_cols + ["current_stock"]].fillna(0)
    df["month"] = (current + 1).month
    df["category_code"] = df["category"].map(cmap).fillna(len(cmap))
    df.columns = [str(c) for c in df.columns]
    return df