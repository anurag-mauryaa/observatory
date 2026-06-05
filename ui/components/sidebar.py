from nicegui import ui
from ui.state import state
from typing import Callable

@ui.refreshable
def sidebar_menu(active_page: str, on_navigate: Callable):
    """Renders the navigation menu items, refreshable to update highlighted active state."""
    menu_items = [
        {"key": "dashboard", "label": "Dashboard", "icon": "dashboard"},
        {"key": "api-explorer", "label": "API Explorer", "icon": "search"},
        {"key": "reliability", "label": "Reliability", "icon": "trending_up"},
        {"key": "rankings", "label": "Rankings", "icon": "leaderboard"},
        {"key": "reports", "label": "Reports", "icon": "description"}
    ]
    with ui.column().classes("w-full gap-1"):
        for item in menu_items:
            is_active = active_page == item["key"]
            
            # Highlight colors
            bg_class = "bg-gradient-to-r from-[#1e293b] to-[#0f172a] border-l-2 border-[#3b82f6] text-[#3b82f6]" if is_active else "text-[#94a3b8] hover:bg-[#1e293b]/50 hover:text-white"
            icon_class = "text-[#3b82f6]" if is_active else "text-[#64748b]"
            
            def make_click_handler(key=item["key"]):
                def click_handler():
                    if state.active_page != key:
                        state.active_page = key
                        on_navigate()
                return click_handler

            with ui.row().classes(
                f"w-full items-center gap-3 px-3 py-2.5 rounded-r-md cursor-pointer transition-all duration-150 {bg_class}"
            ).on("click", make_click_handler()):
                ui.icon(item["icon"]).classes(f"text-[20px] {icon_class}")
                ui.label(item["label"]).classes("text-[13px] font-semibold tracking-wide")

def sidebar(on_navigate: Callable, is_mobile: bool = False):
    """Renders the left navigation sidebar with premium dark styling."""
    container_classes = (
        "h-full w-full bg-[#0f172a] p-4 flex flex-col justify-between"
        if is_mobile
        else "h-full w-[240px] bg-[#0f172a] border-r border-[#1e293b] p-4 desktop-sidebar flex flex-col justify-between"
    )
    with ui.column().classes(container_classes):
        with ui.column().classes("w-full gap-6"):
            # Brand Header with a gradient effect
            with ui.row().classes("items-center gap-3 w-full px-2 py-2"):
                ui.icon("layers").classes("text-[26px] text-[#3b82f6]")
                with ui.column().classes("gap-0"):
                    ui.label("OBSERVATORY").classes(
                        "text-sm font-black tracking-widest bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent"
                    )
                    ui.label("API HEALTH PLATFORM").classes("text-[9px] text-[#64748b] tracking-wider font-semibold")
                    
            # Navigation Items (Refreshable)
            sidebar_menu(state.active_page, on_navigate)
            
        # Footer branding
        with ui.column().classes("w-full items-center py-2 px-2 border-t border-[#1e293b]/70 gap-1"):
            ui.label("API Observatory v1.0").classes("text-[10px] text-[#64748b] font-medium")
            ui.label("Powered by NiceGUI & DuckDB").classes("text-[9px] text-[#475569] font-medium")

