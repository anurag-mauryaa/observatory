from nicegui import ui
from ui.components.filters import api_selector, date_range_filter
from ui.state import state
from typing import Callable

@ui.refreshable
def navbar_title(active_page: str):
    """Renders the breadcrumb and current page title, refreshable on navigation."""
    # Mapping active_page keys to human-readable titles
    titles = {
        "dashboard": "Executive Dashboard",
        "api-explorer": "API Explorer",
        "reliability": "Reliability Analytics",
        "rankings": "Leaderboards & Rankings",
        "reports": "Analytical Reports"
    }
    current_title = titles.get(active_page, "API Observatory")
    
    with ui.column().classes("gap-0"):
        with ui.row().classes("items-center gap-2 text-xs text-[#9ca3af] font-medium"):
            ui.label("API Observatory")
            ui.label("/")
            ui.label(current_title).classes("text-[#d1d5db]")
        ui.label(current_title).classes("text-xl font-extrabold text-[#f3f4f6] tracking-tight")

def navbar(on_filter_change: Callable, toggle_sidebar: Callable):
    """Renders the top navbar with page titles, connection status, and persistent filters."""
    with ui.row().classes(
        "w-full justify-between items-center bg-[#111827] border-b border-[#374151] px-6 py-4 flex-row flex-wrap md:flex-nowrap gap-4"
    ):
        # Left side: Page Title Breadcrumbs & Status Indicator
        with ui.row().classes("items-center gap-4 no-wrap"):
            # Hamburger Menu Button for mobile/tablet (screens < lg)
            ui.button(icon="menu", on_click=toggle_sidebar).props("flat dense").classes("lg:hidden text-[#9ca3af] hover:text-white mr-1")
            
            # Refreshable title
            navbar_title(state.active_page)
            
            # Status Badge
            with ui.row().classes(
                "items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#065f46] text-[#34d399] text-[10px] font-semibold border border-[#047857]"
            ):
                ui.element("span").classes("w-2 h-2 rounded-full bg-[#10b981] animate-pulse")
                ui.label("SYSTEM HEALTHY")
                
        # Right side: Global persistent selectors
        with ui.row().classes("items-center gap-4 no-wrap"):
            api_selector(on_filter_change)
            date_range_filter(on_filter_change)

