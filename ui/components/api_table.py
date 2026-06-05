import pandas as pd
from nicegui import ui
from typing import List, Dict, Any

def render_table(df: pd.DataFrame, columns_config: List[Dict[str, Any]], title: str = ""):
    """Helper to render a highly polished dark-mode table from a Pandas DataFrame."""
    if df.empty:
        with ui.column().classes("w-full items-center p-8 bg-[#111827] border border-[#374151] rounded-lg"):
            ui.icon("table_rows").classes("text-3xl text-gray-500 mb-2")
            ui.label("No data available to display").classes("text-sm text-[#9ca3af]")
        return
        
    rows = df.to_dict("records")
    
    # Map Pandas dataframe column list to Quasar table config
    cols = []
    for col in columns_config:
        cols.append({
            "name": col["field"],
            "label": col["label"],
            "field": col["field"],
            "required": True,
            "align": col.get("align", "left"),
            "sortable": col.get("sortable", True)
        })
        
    with ui.column().classes("w-full gap-2"):
        if title:
            ui.label(title).classes("text-sm font-bold text-[#f3f4f6] tracking-wide px-1")
            
        ui.table(
            columns=cols,
            rows=rows,
            row_key=columns_config[0]["field"]
        ).props("dark flat dense bordered wrap-cells").classes("w-full bg-[#111827] text-[#e5e7eb] border-[#374151]")

def leaderboard_table(df: pd.DataFrame):
    """Renders the main API Leaderboard table."""
    config = [
        {"field": "rank", "label": "Rank", "align": "center"},
        {"field": "api_name", "label": "API Name", "align": "left"},
        {"field": "leaderboard_score", "label": "Leaderboard Score (0-100)", "align": "center"},
        {"field": "avg_reliability_score", "label": "Reliability Score", "align": "center"},
        {"field": "avg_health_score", "label": "Health Score", "align": "center"},
        {"field": "avg_sla_score", "label": "SLA Score", "align": "center"},
        {"field": "avg_response_time_ms", "label": "Avg Response Time (ms)", "align": "center"}
    ]
    render_table(df, config, "OVERALL PLATFORM STANDINGS")

def ranking_table(df: pd.DataFrame, value_field: str, value_label: str, title: str):
    """Renders specific rankings (e.g. Fastest APIs, SLA Rankings, etc.)."""
    config = [
        {"field": "rank", "label": "Rank", "align": "center"},
        {"field": "api_name", "label": "API Name", "align": "left"},
        {"field": value_field, "label": value_label, "align": "center"}
    ]
    render_table(df, config, title)
