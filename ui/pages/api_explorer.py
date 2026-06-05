from nicegui import ui
import pandas as pd

from ui.state import state
from ui.queries import UIQueries

# Drawer reference that will be defined inside page render
selected_api_details = None

def render_api_explorer(container: ui.element, queries: UIQueries):
    """Renders the API Explorer page view."""
    container.clear()
    
    # Detail drawer state variables (local context references)
    drawer_state = {
        "api_name": "",
        "category": "",
        "url": "",
        "health": "",
        "sla": "",
        "latency": "",
        "status": "",
        "reliability": ""
    }

    # Retrieve top-level drawer elements from state
    drawer_el = state.detail_drawer
    drawer_content = state.detail_drawer_content

    def show_drawer(api_item):
        """Populate and slide out the details drawer for a clicked API."""
        drawer_state.update(api_item)
        drawer_content.clear()
        
        recent_checks_df = queries.get_api_recent_checks(api_item["name"], limit=20)
        
        status_colors = {
            "Healthy": "bg-[#065f46] text-[#34d399] border-[#047857]",
            "Degraded": "bg-[#78350f] text-[#fbbf24] border-[#d97706]",
            "Offline": "bg-[#7f1d1d] text-[#fca5a5] border-[#b91c1c]"
        }
        status_class = status_colors.get(api_item["status"], "bg-[#1f2937] text-white")
        
        with drawer_content:
            # Header
            with ui.row().classes("w-full justify-between items-center no-wrap"):
                with ui.column().classes("gap-1"):
                    ui.label(api_item["name"]).classes("text-2xl font-extrabold tracking-tight")
                    ui.label(api_item["category"].upper()).classes("text-[10px] font-bold tracking-widest text-[#9ca3af]")
                
                ui.button(icon="close", on_click=drawer_el.hide).props("flat dense").classes("text-[#9ca3af] hover:text-white")
                
            ui.label(api_item["url"]).classes("text-xs text-[#3b82f6] break-all border-b border-[#374151] pb-3 w-full")
            
            # Status Badge
            with ui.row().classes("w-full justify-between items-center mt-2"):
                ui.label("CURRENT HEALTH STATUS").classes("text-[10px] font-bold text-[#9ca3af]")
                ui.label(api_item["status"].upper()).classes(f"px-2.5 py-1 rounded text-xs font-bold border {status_class}")
                
            # KPI stats grid in drawer
            with ui.grid(columns=2).classes("w-full gap-3 mt-2"):
                with ui.card().classes("bg-[#1f2937]/50 border border-[#374151] p-3 gap-1 rounded"):
                    ui.label("HEALTH SCORE").classes("text-[9px] text-[#9ca3af] font-bold")
                    ui.label(api_item["health"]).classes("text-lg font-bold text-white")
                    
                with ui.card().classes("bg-[#1f2937]/50 border border-[#374151] p-3 gap-1 rounded"):
                    ui.label("SLA SCORE").classes("text-[9px] text-[#9ca3af] font-bold")
                    ui.label(api_item["sla"]).classes("text-lg font-bold text-white")
                    
                with ui.card().classes("bg-[#1f2937]/50 border border-[#374151] p-3 gap-1 rounded"):
                    ui.label("LATENCY (AVG)").classes("text-[9px] text-[#9ca3af] font-bold")
                    ui.label(api_item["latency"]).classes("text-lg font-bold text-white")
                    
                with ui.card().classes("bg-[#1f2937]/50 border border-[#374151] p-3 gap-1 rounded"):
                    ui.label("RELIABILITY").classes("text-[9px] text-[#9ca3af] font-bold")
                    ui.label(api_item["reliability"]).classes("text-lg font-bold text-white")
            
            # Recent Logs Table
            ui.label("RECENT RESPONSE LOGS").classes("text-[10px] font-bold tracking-wider text-[#9ca3af] mt-4 border-b border-[#374151] pb-2 w-full")
            
            if not recent_checks_df.empty:
                cols = [
                    {"name": "date", "label": "Time", "field": "date", "align": "left"},
                    {"name": "status_code", "label": "Status", "field": "status_code", "align": "center"},
                    {"name": "response_time_ms", "label": "Time (ms)", "field": "response_time_ms", "align": "right"},
                ]
                
                # Format response log rows
                rows = []
                for _, log in recent_checks_df.head(10).iterrows():
                    log_time = pd.to_datetime(log["date"]).strftime("%H:%M:%S")
                    rows.append({
                        "date": log_time,
                        "status_code": int(log["status_code"]),
                        "response_time_ms": f"{log['response_time_ms']:.0f}ms" if log["response_time_ms"] > 0 else "Err"
                    })
                    
                ui.table(
                    columns=cols,
                    rows=rows,
                    row_key="date"
                ).props("dark flat dense bordered wrap-cells").classes("w-full bg-[#111827] text-xs")
            else:
                ui.label("No active execution logs recorded.").classes("text-xs text-gray-500 italic")
                
        drawer_el.show()

    # Main Grid Rerender Function
    def render_api_grid():
        grid_container.clear()
        
        search_val = state.explorer_search
        sort_val = state.explorer_sort
        
        api_list = queries.get_api_explorer_list(search_val, sort_val)
        
        if not api_list:
            with grid_container:
                with ui.column().classes("w-full items-center justify-center p-12 bg-[#111827] border border-[#374151] rounded-lg mt-4"):
                    ui.icon("search_off").classes("text-4xl text-gray-500 mb-2")
                    ui.label("No APIs found matching search parameters").classes("text-sm text-[#9ca3af]")
            return
            
        with grid_container:
            with ui.grid(columns=1).classes("w-full gap-4 md:grid-cols-2 lg:grid-cols-3 mt-4"):
                for api in api_list:
                    # Choose badge class
                    status_colors = {
                        "Healthy": "bg-[#065f46] text-[#34d399] border-[#047857]",
                        "Degraded": "bg-[#78350f] text-[#fbbf24] border-[#d97706]",
                        "Offline": "bg-[#7f1d1d] text-[#fca5a5] border-[#b91c1c]"
                    }
                    badge_class = status_colors.get(api["status"], "bg-[#1f2937] text-[#e5e7eb]")
                    
                    # Custom closures for click event
                    def make_click_handler(api_item=api):
                        return lambda: show_drawer(api_item)
                        
                    # Card body
                    with ui.card().classes(
                        "bg-[#111827] border border-[#374151] rounded-lg p-5 flex flex-col justify-between cursor-pointer hover:border-[#3b82f6] hover:scale-[1.01] transition-all duration-200"
                    ).on("click", make_click_handler()):
                        
                        # Top line: Name & Status Badge
                        with ui.row().classes("w-full justify-between items-start no-wrap"):
                            with ui.column().classes("gap-0"):
                                ui.label(api["name"]).classes("text-lg font-bold text-white tracking-tight")
                                ui.label(api["category"].upper()).classes("text-[9px] font-extrabold text-[#9ca3af] tracking-wider")
                            
                            ui.label(api["status"].upper()).classes(f"px-2 py-0.5 rounded text-[9px] font-bold border {badge_class}")
                            
                        ui.label(api["url"]).classes("text-[11px] text-[#4b5563] truncate mt-2 w-full")
                        
                        # KPI Grid values
                        with ui.row().classes("w-full justify-between items-center border-t border-[#374151]/50 pt-3 mt-3 no-wrap"):
                            with ui.column().classes("items-center gap-0 flex-1"):
                                ui.label("LATENCY").classes("text-[9px] text-[#9ca3af] font-bold")
                                ui.label(api["latency"]).classes("text-sm font-bold text-white")
                                
                            with ui.column().classes("items-center gap-0 flex-1 border-x border-[#374151]/30"):
                                ui.label("HEALTH").classes("text-[9px] text-[#9ca3af] font-bold")
                                ui.label(api["health"]).classes("text-sm font-bold text-[#10b981]")
                                
                            with ui.column().classes("items-center gap-0 flex-1"):
                                ui.label("SLA").classes("text-[9px] text-[#9ca3af] font-bold")
                                ui.label(api["sla"]).classes("text-sm font-bold text-[#8b5cf6]")

    # Building page HTML layout
    with container:
        with ui.column().classes("w-full gap-4 p-1"):
            
            # Toolbar row: search bar, sorting dropdowns
            with ui.row().classes("w-full justify-between items-center gap-4 bg-[#111827] border border-[#374151] p-4 rounded-lg flex-wrap"):
                # Search Input
                ui.input(
                    placeholder="Search by API name or category...",
                    value=state.explorer_search,
                    on_change=lambda e: [setattr(state, "explorer_search", e.value), render_api_grid()]
                ).props("dark dense outlined clearable").classes("w-full sm:w-[320px] text-white").props("prepend-icon=search")
                
                # Sorting Option
                with ui.row().classes("items-center gap-2"):
                    ui.label("Sort By").classes("text-xs text-[#9ca3af] font-bold")
                    ui.select(
                        options=["API Name", "Health Score", "SLA Score", "Latency", "Reliability"],
                        value=state.explorer_sort,
                        on_change=lambda e: [setattr(state, "explorer_sort", e.value), render_api_grid()]
                    ).props("dark dense outlined options-dense").classes("w-[160px] text-white")
                    
            # Main Grid Wrapper container
            grid_container = ui.column().classes("w-full")
            
            # Call grid render
            render_api_grid()
