# Default Registry for Known APIs
DEFAULT_API_REGISTRY = {
    "GitHub": {
        "url": "https://api.github.com",
        "category": "VCS"
    },
    "StackExchange": {
        "url": "https://api.stackexchange.com",
        "category": "Q&A"
    },
    "OpenLibrary": {
        "url": "https://openlibrary.org",
        "category": "Education"
    },
    "JSONPlaceholder": {
        "url": "https://jsonplaceholder.typicode.com",
        "category": "Testing"
    },
    "SpaceX": {
        "url": "https://api.spacexdata.com/v4/launches/latest",  # SpaceX v4 endpoint
        "category": "Aerospace"
    },
    "CoinGecko": {
        "url": "https://api.coingecko.com/api/v3/ping",  # CoinGecko ping endpoint is reliable
        "category": "Crypto"
    }
}

# General project constants
DB_TABLE_DIM_API = "dim_api"
DB_TABLE_DIM_DATE = "dim_date"
DB_TABLE_FACT_CHECKS = "fact_api_checks"
DB_TABLE_FACT_METRICS = "fact_api_metrics"
