import os
import yaml
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def load_config(config_path: Path = None) -> dict:
    """Load configuration from config.yaml."""
    if config_path is None:
        env_path = os.getenv("API_OBSERVATORY_CONFIG_PATH")
        if env_path:
            config_path = Path(env_path)
        else:
            config_path = PROJECT_ROOT / "config" / "config.yaml"
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    return config

def get_path(relative_path_str: str) -> Path:
    """Resolve a path relative to the project root and ensure parent exists."""
    path = PROJECT_ROOT / relative_path_str
    return path

def get_db_path(config: dict = None) -> Path:
    """Get the absolute path to the DuckDB database file."""
    if config is None:
        config = load_config()
    warehouse_dir = get_path(config["database"]["paths"]["warehouse"])
    warehouse_dir.mkdir(parents=True, exist_ok=True)
    return warehouse_dir / config["database"]["file_name"]
