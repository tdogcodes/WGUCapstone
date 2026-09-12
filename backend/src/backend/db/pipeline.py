import re
import pandas as pd
from sqlmodel import Session, SQLModel
from backend.db.models import (
    Inventory,
    Product,
    Sale,
    get_engine
)

CAPITALIZED_CATEGORIES = {
    "electronics": "Electronics",
    "office supplies": "Office Supplies",
    "furniture": "Furniture",
    "kitchen": "Kitchen",
    "fitness": "Fitness",
    "outdoors": "Outdoors",
    "books": "Books",
    "pet supplies": "Pet Supplies",
}

def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())

def clean_name(value: str) -> str:
    return normalize_text(value).title()

def clean_category(value) -> str | None:
    """Cleans category names"""
    if pd.isna(value) or not str(value).strip():
        return None
    key = normalize_text(str(value)).lower()
    if key in CAPITALIZED_CATEGORIES:
        return CAPITALIZED_CATEGORIES[key]
    return normalize_text(str(value)).title()


def clean_products(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[int, int], dict]:
    """Removes duplicate products.

    """
    df = raw.copy()
    df["clean_name"] = df["name"].map(clean_name)
    df["clean_category"] = df["category"].map(clean_category)

    by_name: dict[str, dict] = {}
    raw_id_to_name = dict(zip(df["id"], df["clean_name"]))
    for row in df.itertuples():
        rec = by_name.setdefault(
            row.clean_name, {"name": row.clean_name, "category": None, "price": None}
        )
        if rec["category"] is None and row.clean_category is not None:
            rec["category"] = row.clean_category
        if rec["price"] is None and not pd.isna(row.price):
            rec["price"] = float(row.price)

    products = pd.DataFrame(by_name.values())
    dupes_merged = len(df) - len(products)
    null_prices = products["price"].isna().sum()
    products["price"] = products["price"].fillna(
        products.groupby("category")["price"].transform("median")
    ).fillna(products["price"].median())
    prices_filled = int(null_prices.sum())
    products["category"] = products["category"].fillna("Uncategorized")
    uncategorized = int((products["category"] == "Uncategorized").sum())
    products = products.reset_index(drop=True)
    products.insert(0, "id", range(1, len(products) + 1))
    name_to_id = dict(zip(products["name"], products["id"]))
    id_map = {raw_id: name_to_id[name] for raw_id, name in raw_id_to_name.items()}

    stats = {
        "raw_rows": len(df),
        "clean_rows": len(products),
        "dupes_merged": dupes_merged,
        "prices_filled": prices_filled,
        "uncategorized": uncategorized,
    }
    return products, id_map, stats

def clean_sales(raw: pd.DataFrame, products: pd.DataFrame, id_map: dict[int, int]):
    df = raw.copy()
    before = len(df)
    df = df.dropna(subset=["quantity", "revenue", "product_id"])
    dropped = before - len(df)
    df["product_id"] = df["product_id"].astype(int).map(id_map)
    prices = products.set_index("id")["price"]
    df["revenue"] = (df["quantity"].astype(int) * df["product_id"].map(prices)).round(2)
    df["sale_date"] = pd.to_datetime(df["sale_date"]).dt.date
    return df, {"raw_rows": before, "dropped": dropped, "clean_rows": len(df)}

def clean_inventory(raw: pd.DataFrame, id_map: dict[int, int]):
    df = raw.copy()
    before = len(df)
    nulls_filled = int(df["current_stock"].isna().sum())
    df["current_stock"] = df["current_stock"].fillna(0).astype(int)
    df["product_id"] = df["product_id"].astype(int).map(id_map)
    df = df.groupby("product_id", as_index=False)["current_stock"].sum()
    return df, {
        "raw_rows": before,
        "nulls_filled": nulls_filled,
        "clean_rows": len(df),
    }

def write_clean_tables(engine, products, sales, inventory) -> None:
    clean_tables = [Product.__table__, Sale.__table__, Inventory.__table__]
    SQLModel.metadata.drop_all(engine, tables=clean_tables)
    SQLModel.metadata.create_all(engine, tables=clean_tables)

    with Session(engine) as session:
        for row in products.itertuples():
            session.add(Product(id=row.id, name=row.name, category=row.category, price=row.price))
        for row in sales.itertuples():
            session.add(
                Sale(
                    product_id=int(row.product_id),
                    quantity=int(row.quantity),
                    revenue=float(row.revenue),
                    sale_date=row.sale_date,
                )
            )
        for row in inventory.itertuples():
            session.add(
                Inventory(
                    product_id=int(row.product_id),
                    current_stock=int(row.current_stock),
                )
            )
        session.commit()


def main() -> None:
    engine = get_engine()

    raw_products = pd.read_sql_table("raw_products", engine)
    raw_sales = pd.read_sql_table("raw_sales", engine)
    raw_inventory = pd.read_sql_table("raw_inventory", engine)
    products, id_map, p_stats = clean_products(raw_products)
    sales, s_stats = clean_sales(raw_sales, products, id_map)
    inventory, i_stats = clean_inventory(raw_inventory, id_map)

    write_clean_tables(engine, products, sales, inventory)

    print("Pipeline complete:")
    print(f"  Products: {p_stats['raw_rows']} raw -> {p_stats['clean_rows']} clean ")
    print(f"  Sales: {s_stats['raw_rows']} raw -> {s_stats['clean_rows']} clean ")
    print(f"  Inventory: {i_stats['raw_rows']} raw -> {i_stats['clean_rows']} clean ")
    print("Clean tables ready")

if __name__ == "__main__":
    main()