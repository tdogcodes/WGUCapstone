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

N_SALES = 1200


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


def build_sales(products: list[RawProduct], n: int = N_SALES) -> list[RawSale]:
    sales = []
    for _ in range(n):
        product = random.choice(products)
        quantity = random.randint(1, 10)
        revenue = round(quantity * product.price, 2) if product.price is not None else None
        sale_date = TODAY - timedelta(days=random.randint(0, 364))
        sales.append(
            RawSale(
                product_id=product.id,
                quantity=quantity,
                revenue=revenue,
                sale_date=sale_date,
            )
        )

    # 60 sales with missing quantity and revenue
    for s in random.sample(sales, 60):
        s.quantity = None
    for s in random.sample(sales, 60):
        s.revenue = None
    return sales


BUCKET_PATTERN = ["increase", "maintain", "maintain", "increase", "decrease"]
STOCK_FACTORS = {"increase": 0.5, "maintain": 1.25, "decrease": 3.0}


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

    # a couple nulls (not on decrease products, so the mix stays intact)
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