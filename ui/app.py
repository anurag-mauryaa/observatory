from nicegui import ui
import os
import threading
from pathlib import Path

# Fix NiceGUI background import issues if running inside package
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))

from ui.state import state
from ui.queries import UIQueries
from ui.components.sidebar import sidebar, sidebar_menu
from ui.components.navbar import navbar, navbar_title

# Page views
from ui.pages.dashboard import render_dashboard
from ui.pages.api_explorer import render_api_explorer
from ui.pages.reliability import render_reliability
from ui.pages.rankings import render_rankings
from ui.pages.reports import render_reports

queries = UIQueries()
content_container = None
main_layout = None

def check_db_initialized() -> bool:
    """Checks if the data warehouse is created and dim_api table populated."""
    try:
        con = queries._get_connection()
        res = con.execute("SELECT COUNT(*) FROM dim_api").fetchone()
        con.close()
        return res and res[0] > 0
    except Exception:
        return False

def run_db_initialization():
    """Initializes the database using simulated data (run in thread to prevent freezing)."""
    ui.notify("Initializing data warehouse with 30 days of simulation history...", type="warning")
    try:
        from src.utils.history_simulator import HistorySimulator
        from src.processing.data_cleaner import DataCleaner
        from src.processing.metric_calculator import MetricCalculator
        from src.warehouse.warehouse_loader import WarehouseLoader
        from src.analytics.reporting import Reporting
        
        # 1. Simulate checks
        sim = HistorySimulator()
        sim.simulate_history(days=30)
        
        # 2. Clean data
        cleaner = DataCleaner()
        cleaner.run()
        
        # 3. Calculate metrics
        calc = MetricCalculator()
        calc.run()
        
        # 4. Load warehouse
        loader = WarehouseLoader()
        loader.run()
        
        # 5. Export analytics
        rep = Reporting()
        rep.export_report_csv()
        
        ui.notify("Data warehouse initialized successfully!", type="positive")
        # Reload views
        ui.timer(1.0, navigate, once=True)
    except Exception as e:
        ui.notify(f"Initialization failed: {e}", type="negative")

def render_setup_page():
    """Renders a friendly setup page if the database is uninitialized."""
    content_container.clear()
    with content_container:
        with ui.column().classes("w-full items-center justify-center py-24 gap-6"):
            with ui.card().classes(
                "bg-[#111827] border border-[#374151] rounded-xl p-8 max-w-[500px] text-center shadow-2xl gap-5"
            ):
                ui.icon("layers_clear").classes("text-6xl text-blue-500 mx-auto")
                
                with ui.column().classes("gap-1"):
                    ui.label("Data Warehouse Empty").classes("text-xl font-black text-white")
                    ui.label("API Observatory is ready, but no API logs have been loaded into the database yet.").classes("text-sm text-[#9ca3af]")
                    
                ui.button(
                    "POPULATE DEMO DATA (30 DAYS)", 
                    icon="auto_awesome", 
                    on_click=lambda: threading.Thread(target=run_db_initialization, daemon=True).start()
                ).props("color=blue").classes("w-full py-3 font-bold mt-2")
                
                ui.label("Or execute 'python run_pipeline.py --simulate' from your command line.").classes("text-[11px] text-gray-500 italic")

def navigate():
    """Routes the content_container rendering to the current active page."""
    global content_container
    if content_container is None:
        return
        
    if hasattr(state, "detail_drawer") and state.detail_drawer:
        state.detail_drawer.hide()
        
    if hasattr(state, "mobile_drawer") and state.mobile_drawer:
        state.mobile_drawer.hide()
        
    if not check_db_initialized():
        render_setup_page()
        return

    # Refresh sidebars and titles to current page key
    sidebar_menu.refresh(state.active_page, navigate)
    navbar_title.refresh(state.active_page)

    page_key = state.active_page
    
    if page_key == "dashboard":
        render_dashboard(content_container, queries)
    elif page_key == "api-explorer":
        render_api_explorer(content_container, queries)
    elif page_key == "reliability":
        render_reliability(content_container, queries)
    elif page_key == "rankings":
        render_rankings(content_container, queries)
    elif page_key == "reports":
        render_reports(content_container, queries)

@ui.page("/")
def index():
    """NiceGUI main page layout structure."""
    global content_container, main_layout
    
    # 1. Setup Headers & Styles
    ui.add_head_html('<link rel="preconnect" href="https://fonts.googleapis.com">')
    ui.add_head_html('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>')
    ui.add_head_html('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">')
    
    ui.add_head_html("""
        <style>
            *:not(.material-icons):not(.q-icon) {
                font-family: 'Inter', sans-serif !important;
            }
            body {
                background-color: #0b0f19;
                margin: 0;
                padding: 0;
                overflow: hidden;
            }
            @media (max-width: 1023px) {
                .desktop-sidebar {
                    display: none !important;
                }
            }
            /* Styling scrollbars for modern dark look */
            ::-webkit-scrollbar {
                width: 6px;
                height: 6px;
            }
            ::-webkit-scrollbar-track {
                background: #0f172a;
            }
            ::-webkit-scrollbar-thumb {
                background: #374151;
                border-radius: 4px;
            }
            ::-webkit-scrollbar-thumb:hover {
                background: #4b5563;
            }
            /* NiceGUI table overrides to match design */
            .q-table__container {
                background-color: #111827 !important;
                border: 1px solid #374151 !important;
                border-radius: 8px !important;
            }
            .q-table th {
                color: #9ca3af !important;
                font-weight: 700 !important;
                font-size: 11px !important;
                letter-spacing: 0.05em !important;
                text-transform: uppercase !important;
                border-bottom: 1px solid #374151 !important;
                background-color: #1f2937/40 !important;
            }
            .q-table td {
                border-bottom: 1px solid #1f2937 !important;
                font-size: 12px !important;
            }
            .q-table tbody tr:hover {
                background-color: #1f2937/30 !important;
            }
        </style>
    """)
    
    # 2. Main Flex Layout
    # Mobile navigation drawer
    mobile_drawer = ui.left_drawer(value=False).classes("bg-[#0f172a] border-r border-[#1e293b] p-0").props("width=240")
    with mobile_drawer:
        sidebar(on_navigate=navigate, is_mobile=True)
    state.mobile_drawer = mobile_drawer
    
    with ui.row().classes("w-full h-screen no-wrap m-0 p-0 bg-[#0b0f19] gap-0"):
        
        # Left Navigation Sidebar (Desktop view)
        sidebar(on_navigate=navigate, is_mobile=False)
        
        # Right Area (Navbar + Dynamic Page Content)
        with ui.column().classes("flex-1 h-screen overflow-hidden bg-[#0b0f19] text-white gap-0"):
            # Navbar
            # Pass navigate as callback so changing the persistent date/API filters refreshes the charts
            # Pass mobile_drawer.toggle so sidebar can be toggled on mobile screen
            navbar(on_filter_change=navigate, toggle_sidebar=mobile_drawer.toggle)
            
            # Content container
            # Scrollable main container body
            content_container = ui.column().classes("w-full p-6 flex-1 overflow-y-auto gap-6")
            
            # Trigger initial view load
            navigate()
            
    # Right Drawer (Direct child of page content, not nested in layout columns/rows!)
    detail_drawer = ui.drawer(value=False, side="right").classes("bg-[#111827] border-l border-[#374151] p-6")
    with detail_drawer:
        detail_drawer_content = ui.column().classes("w-full gap-4 text-white")
    
    state.detail_drawer = detail_drawer
    state.detail_drawer_content = detail_drawer_content


if __name__ in {"__main__", "__mp_main__"}:
    # In production/deployment pipeline, ui.run is invoked via run_pipeline.py
    # We allow running direct for development
    ui.run(title="API Observatory", dark=True,host="0.0.0.0", port=8080)
