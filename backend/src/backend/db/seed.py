import calendar
import random
from datetime import date, timedelta
from sqlmodel import Session, SQLModel
from backend.db.models import RawInventory, RawProduct, RawSale, get_engine

# this creates the mock datasets which contain dirty data, this will then be processed by the data cleaning pipeline in pipeline.py
random.seed(42)
TODAY = date.today()
PRODUCTS: dict[str, list[tuple[str, float]]] = {
    "Electronics": [
        ("Wireless Mouse", 24.99),
        ("Mechanical Keyboard", 89.99),
        ("Bluetooth Speaker", 49.99),
        ("Noise-Cancelling Headphones", 199.99),
    ],
    "Office Supplies": [
        ("Ballpoint Pens (12-Pack)", 6.49),
        ("Stapler", 9.99),
        ("Printer Paper (500 Sheets)", 8.49),
    ],
    "Furniture": [
        ("Standing Desk", 349.99),
        ("Ergonomic Office Chair", 279.99),
        ("Monitor Arm", 44.99),
    ],
    "Kitchen": [
        ("Coffee Maker", 54.99),
        ("Toaster Oven", 79.99),
        ("Blender", 64.99),
    ],
    "Fitness": [
        ("Yoga Mat", 22.99),
        ("Dumbbell Set (25 lb)", 59.99),
        ("Kettlebell (20 lb)", 39.99),
    ],
    "Outdoors": [
        ("Camping Tent (4-Person)", 149.99),
        ("Sleeping Bag", 69.99),
        ("LED Lantern", 24.99),
    ],
    "Books": [
        ("The Lean Startup", 16.99),
        ("Clean Code", 32.99),
    ],
    "Pet Supplies": [
        ("Dog Bed (Large)", 49.99),
        ("Cat Litter Box", 29.99),
        ("Dog Leash", 14.99),
    ],
}

BASE_LEVEL = 12.0
POPULARITY_SIGMA = 0.9
NOISE_AMP = 4
TREND_SLOPE = 0.4
N_MONTHS = 12

GLOBAL_SEASON = {
    0: 0.6, 1: 0.8, 2: 0.9, 3: 1.0, 4: 1.0, 5: 1.1,
    6: 1.2, 7: 1.3, 8: 1.4, 9: 1.5, 10: 1.7, 11: 2.0,
}
CATEGORY_SEASON = {
    "Electronics": {10: 1.2, 11: 1.35},
    "Fitness": {0: 1.25, 1: 1.15},
    "Outdoors": {4: 1.2, 5: 1.3, 6: 1.15},
    "Furniture": {11: 1.15},
    "Kitchen": {11: 1.1},
}
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

def _normalize(value: str) -> str:
    return " ".join(str(value).split())

def _clean_name(value: str) -> str:
    return _normalize(value).title()

def _clean_category(value) -> str:
    if value is None or not str(value).strip():
        return "Uncategorized"
    key = _normalize(value).lower()
    return CAPITALIZED_CATEGORIES.get(key, _normalize(value).title())

def _month_start(months_before: int) -> date:
    total = TODAY.year * 12 + (TODAY.month - 1) - months_before
    year, month = divmod(total, 12)
    return date(year, month + 1, 1)

def _demand_series(popularity: float, category: str) -> list[int]:
    series = []
    for m in range(N_MONTHS):
        season = GLOBAL_SEASON[m] * CATEGORY_SEASON.get(category, {}).get(m, 1.0)
        trend = 1.0 + TREND_SLOPE * (m / (N_MONTHS - 1))
        level = popularity * season * trend
        series.append(max(1, round(level + random.uniform(-NOISE_AMP, NOISE_AMP))))
    return series

def _split_demand(total: int) -> list[int]:
    n = random.randint(1, min(8, total))
    base, remainder = divmod(total, n)
    parts = [base] * n
    for i in range(remainder):
        parts[i] += 1
    random.shuffle(parts)
    return parts

def build_products() -> list[RawProduct]:
    products = [
        RawProduct(name=name, category=category, price=price)
        for category, items in PRODUCTS.items()
        for name, price in items
    ]

    # duplicate products with different casing and whitespaces
    products += [
        RawProduct(name="ergonomic office chair", category="Furniture", price=279.99),
        RawProduct(name="  Standing Desk  ", category="furniture", price=349.99),
        RawProduct(name="Wireless MOUSE", category="Electronics", price=24.99),
    ]

    for p in random.sample(products, 4):
        style = random.choice(["upper", "lower", "lead_ws", "trail_ws", "double_ws"])
        if style == "upper":
            p.name = p.name.upper()
        elif style == "lower":
            p.name = p.name.lower()
        elif style == "lead_ws":
            p.name = "  " + p.name
        elif style == "trail_ws":
            p.name = p.name + "   "
        else:
            p.name = p.name.replace(" ", "  ", 1)

    # inconsistent categories
    for p in random.sample(products, 4):
        if p.category:
            style = random.choice(["lower", "upper", "ws"])
            if style == "lower":
                p.category = p.category.lower()
            elif style == "upper":
                p.category = p.category.upper()
            else:
                p.category = "  " + p.category.lower() + " "

    # creating missing values
    for p in random.sample(products, 2):
        p.price = None
    for p in random.sample(products, 2):
        p.category = None

    return products


def build_sales(products: list[RawProduct]) -> list[RawSale]:
    # sales have learnable patterns (popularity, seasonality, growth, persistence)
    name_counts: dict[str, int] = {}
    for p in products:
        key = _clean_name(p.name)
        name_counts[key] = name_counts.get(key, 0) + 1

    popularity: dict[str, float] = {}
    for name, count in name_counts.items():
        popularity[name] = random.lognormvariate(0, POPULARITY_SIGMA) * BASE_LEVEL / count

    sales: list[RawSale] = []
    for p in products:
        name = _clean_name(p.name)
        category = _clean_category(p.category)
        series = _demand_series(popularity[name], category)
        for months_before, total in zip(range(N_MONTHS - 1, -1, -1), series):
            if total <= 0:
                continue
            month = _month_start(months_before)
            n_days = calendar.monthrange(month.year, month.month)[1]
            price = p.price if p.price is not None else 0.0
            for qty in _split_demand(total):
                sales.append(
                    RawSale(
                        product_id=p.id,
                        quantity=qty,
                        revenue=round(qty * price, 2),
                        sale_date=month + timedelta(days=random.randint(0, n_days - 1)),
                    )
                )

    # dirty rows with missing values for the pipeline to clean/drop
    n_dirty = max(1, int(len(sales) * 0.1))
    for _ in range(n_dirty):
        product = random.choice(products)
        sales.append(
            RawSale(
                product_id=product.id,
                quantity=None,
                revenue=None,
                sale_date=TODAY - timedelta(days=random.randint(0, 364)),
            )
        )
    return sales

BUCKET_PATTERN = ["increase", "maintain", "maintain", "increase", "decrease"]
STOCK_FACTORS = {"increase": 0.8, "maintain": 1.1, "decrease": 1.4}

def build_inventory(products: list[RawProduct], sales: list[RawSale]) -> list[RawInventory]:
    demand: dict[int, int] = {}
    for s in sales:
        if s.quantity is not None:
            demand[s.product_id] = demand.get(s.product_id, 0) + s.quantity

    inventory: list[tuple[RawInventory, str]] = []
    for i, p in enumerate(products):
        avg_monthly = demand.get(p.id, 0) / 12
        bucket = BUCKET_PATTERN[i % len(BUCKET_PATTERN)]
        stock = max(1, round(avg_monthly * STOCK_FACTORS[bucket]))
        inventory.append((RawInventory(product_id=p.id, current_stock=stock), bucket))
    candidates = [t for t in inventory if t[1] != "decrease"]
    for row, _ in random.sample(candidates, 2):
        row.current_stock = None
    return [row for row, _ in inventory]

def main() -> None:
    engine = get_engine()
    raw_tables = [RawProduct.__table__, RawSale.__table__, RawInventory.__table__]
    SQLModel.metadata.drop_all(engine, tables=raw_tables)
    SQLModel.metadata.create_all(engine, tables=raw_tables)

    with Session(engine) as session:
        products = build_products()
        session.add_all(products)
        session.flush()

        sales = build_sales(products)
        inventory = build_inventory(products, sales)
        session.add_all(sales)
        session.add_all(inventory)
        session.commit()

    print(f"Seeded raw tables: {len(products)} products, "
          f"{len(sales)} sales, {len(inventory)} inventory rows.")
    print("~10% of rows contain dirty data.")

if __name__ == "__main__":
    main()