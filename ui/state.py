from typing import Dict, Any

class GlobalState:
    def __init__(self):
        self.selected_api: str = "All"
        self.selected_date_range: str = "Last 30 Days"
        self.active_page: str = "dashboard"
        
        # Details for detail drawer in API Explorer
        self.explorer_search: str = ""
        self.explorer_sort: str = "API Name"
        
    def get_date_days(self) -> int:
        """Helper to get integer days for filtering queries."""
        mapping = {
            "Last 7 Days": 7,
            "Last 30 Days": 30,
            "Last 90 Days": 90,
            "All Time": 120
        }
        return mapping.get(self.selected_date_range, 30)

# Single global instance for this session
state = GlobalState()
