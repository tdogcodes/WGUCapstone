import os
from datetime import date
from dotenv import load_dotenv
from sqlmodel import Field, SQLModel, create_engine

load_dotenv()

def get_engine():
    return create_engine(os.getenv("DATABASE_URL", "sqlite:///./dev.db"))

# Raw datasets

class RawProduct(SQLModel, table=True):
    __tablename__ = "raw_products"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    category: str | None = None
    price: float | None = None

class RawSale(SQLModel, table=True):
    __tablename__ = "raw_sales"

    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="raw_products.id", index=True)
    quantity: int | None = None
    revenue: float | None = None
    sale_date: date

class RawInventory(SQLModel, table=True):
    __tablename__ = "raw_inventory"

    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="raw_products.id", index=True)
    current_stock: int | None = None

# cleaned datasets

class Product(SQLModel, table=True):
    __tablename__ = "products"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    category: str
    price: float

class Sale(SQLModel, table=True):
    __tablename__ = "sales"

    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    quantity: int
    revenue: float
    sale_date: date

class Inventory(SQLModel, table=True):
    __tablename__ = "inventory"

    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", unique=True)
    current_stock: int