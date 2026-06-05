import pytest
import duckdb
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.warehouse.warehouse_loader import WarehouseLoader
from src.utils.constants import (
    DB_TABLE_DIM_API,
    DB_TABLE_DIM_DATE,
    DB_TABLE_FACT_CHECKS,
    DB_TABLE_FACT_METRICS
)

def test_warehouse_schema_creation():
    # Setup in-memory DuckDB database for testing schemas
    con = duckdb.connect(":memory:")
    
    loader = WarehouseLoader()
    loader.create_schema(con)
    
    # Verify tables exist
    tables = con.execute("SHOW TABLES;").fetchall()
    table_names = [t[0] for t in tables]
    
    assert DB_TABLE_DIM_API in table_names
    assert DB_TABLE_DIM_DATE in table_names
    assert DB_TABLE_FACT_CHECKS in table_names
    assert DB_TABLE_FACT_METRICS in table_names
    
    # Check dim_api schema
    columns = con.execute(f"DESCRIBE {DB_TABLE_DIM_API};").fetchall()
    col_names = [c[0] for c in columns]
    assert "api_key" in col_names
    assert "api_name" in col_names
    assert "api_url" in col_names
    assert "api_category" in col_names
    
    con.close()

def test_warehouse_load_dimensions():
    con = duckdb.connect(":memory:")
    
    # Create schema and load
    with patch("src.warehouse.warehouse_loader.load_config") as mock_config:
        mock_config.return_value = {
            "apis": ["GitHub", "SpaceX"],
            "database": {
                "file_name": "test.duckdb",
                "paths": {"raw": "data/raw", "processed": "data/processed", "warehouse": "data/warehouse"}
            }
        }
        
        loader = WarehouseLoader()
        loader.create_schema(con)
        loader.load_dimension_tables(con)
        
        # Verify dim_api populated
        apis = con.execute(f"SELECT api_name, api_category FROM {DB_TABLE_DIM_API} ORDER BY api_name;").fetchall()
        assert len(apis) == 2
        assert apis[0][0] == "GitHub"
        assert apis[0][1] == "VCS"
        assert apis[1][0] == "SpaceX"
        assert apis[1][1] == "Aerospace"
        
        # Verify dim_date populated
        date_count = con.execute(f"SELECT COUNT(*) FROM {DB_TABLE_DIM_DATE};").fetchone()[0]
        assert date_count > 0
        
    con.close()
