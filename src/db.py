import os
import sqlite3
import logging
from typing import Optional, Tuple, Any
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance: Optional['DatabaseManager'] = None
    _engine: Optional[Engine] = None
    _active_db_type: str = "sqlite"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initializes database engine with smart fallback."""
        if config.DB_TYPE.lower() == "mysql":
            try:
                # Attempt MySQL Connection
                # Try pymysql or mysqlconnector
                db_url = f"mysql+pymysql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
                engine = create_engine(db_url, pool_recycle=3600, pool_pre_ping=True)
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                self._engine = engine
                self._active_db_type = "mysql"
                logger.info(f"Successfully connected to MySQL database: {config.DB_NAME}@{config.DB_HOST}")
                return
            except Exception as e:
                logger.warning(f"Failed to connect to MySQL ({e}). Falling back to local SQLite database.")

        # Fallback / Default to SQLite
        sqlite_path = str(config.SQLITE_DB_PATH)
        self._engine = create_engine(f"sqlite:///{sqlite_path}", echo=False)
        self._active_db_type = "sqlite"
        logger.info(f"Connected to SQLite database: {sqlite_path}")

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            self._initialize()
        return self._engine

    @property
    def db_type(self) -> str:
        return self._active_db_type

    def get_raw_connection(self):
        """Returns raw DB connection for low-level cursor operations."""
        if self._active_db_type == "sqlite":
            conn = sqlite3.connect(str(config.SQLITE_DB_PATH))
            conn.row_factory = sqlite3.Row
            return conn
        else:
            return self.engine.raw_connection()

    def execute_query(self, query: str, params: Optional[dict] = None) -> pd.DataFrame:
        """Executes a SQL query and returns result as a Pandas DataFrame."""
        try:
            with self.engine.connect() as conn:
                if params:
                    return pd.read_sql(text(query), conn, params=params)
                return pd.read_sql(text(query), conn)
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise

    def execute_statement(self, statement: str, params: Optional[dict] = None) -> None:
        """Executes DDL or DML statement."""
        with self.engine.begin() as conn:
            if params:
                conn.execute(text(statement), params)
            else:
                conn.execute(text(statement))

    def check_connection(self) -> Tuple[bool, str]:
        """Checks DB connectivity and returns status."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True, f"Active ({self._active_db_type.upper()})"
        except Exception as e:
            return False, str(e)

# Singleton helper
db = DatabaseManager()
