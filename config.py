import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

# Database Configuration
DB_TYPE = os.getenv("DB_TYPE", "sqlite")  # 'mysql' or 'sqlite'
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "ecommerce")

# SQLite fallback path
SQLITE_DB_PATH = BASE_DIR / "ecommerce.db"

# Data paths
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR)))

CSV_FILES = [
    ("customers.csv", "customers"),
    ("orders.csv", "orders"),
    ("sellers.csv", "sellers"),
    ("products.csv", "products"),
    ("geolocation.csv", "geolocation"),
    ("payments.csv", "payments"),
    ("order_items.csv", "order_items"),
]

# Performance / ETL Settings
BATCH_CHUNK_SIZE = int(os.getenv("BATCH_CHUNK_SIZE", 5000))
MAX_WORKERS = int(os.getenv("MAX_WORKERS", 4))

# Server Settings
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", 8000))
