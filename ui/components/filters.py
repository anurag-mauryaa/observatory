from nicegui import ui
from ui.state import state
from typing import Callable

def api_selector(on_change: Callable):
    """Renders a dropdown selector for filtering APIs globally."""
    apis = ["All", "GitHub", "StackExchange", "OpenLibrary", "JSONPlaceholder", "SpaceX", "CoinGecko"]
    
    with ui.row().classes("items-center gap-2"):
        ui.icon("api").classes("text-[#9ca3af] text-lg")
        select = ui.select(
            options=apis,
            value=state.selected_api,
            on_change=lambda e: [setattr(state, "selected_api", e.value), on_change()]
        ).props("dark dense outlined options-dense").classes("w-[160px] text-white")
    return select

def date_range_filter(on_change: Callable):
    """Renders a dropdown selector for filtering date ranges globally."""
    ranges = ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"]
    
    with ui.row().classes("items-center gap-2"):
        ui.icon("schedule").classes("text-[#9ca3af] text-lg")
        select = ui.select(
            options=ranges,
            value=state.selected_date_range,
            on_change=lambda e: [setattr(state, "selected_date_range", e.value), on_change()]
        ).props("dark dense outlined options-dense").classes("w-[180px] text-white")
    return select
