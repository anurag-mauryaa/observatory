from nicegui import ui
import pandas as pd

from ui.state import state
from ui.queries import UIQueries
from ui.components.charts import (
    reliability_trend_chart,
    uptime_trend_chart,
    error_rate_trend_chart,
    sla_trend_chart
)

def render_reliability(container: ui.element, queries: UIQueries):
    """Renders the detailed Reliability Analytics view."""
    container.clear()
    
    # Query databases
    days = state.get_date_days()
    trend_df = queries.get_trend_data(state.selected_api, days)
    
    with container:
        with ui.column().classes("w-full gap-6 p-1"):
            
            # Row 1: KPI text summaries or title card
            with ui.card().classes("bg-[#111827] border border-[#374151] rounded-lg p-5 w-full shadow-md"):
                with ui.row().classes("w-full justify-between items-center"):
                    with ui.column().classes("gap-1"):
                        ui.label("RELIABILITY & SLA ANALYTICS").classes("text-sm font-extrabold text-[#f3f4f6] tracking-wide")
                        ui.label("Continuous health performance graphs, incident tracking, and SLA thresholds.").classes("text-xs text-[#9ca3af]")
                        
                    # Quick target label
                    with ui.row().classes("items-center gap-1 text-[11px] font-bold text-[#10b981] bg-[#10b981]/10 px-3 py-1 rounded border border-[#10b981]/30"):
                        ui.icon("check_circle").classes("text-sm")
                        ui.label("SLA TARGET: 99.0%")
                        
            # Grid layout for charts (2x2)
            with ui.grid(columns=1).classes("w-full gap-4 md:grid-cols-2"):
                # Chart 1: Reliability Trend Index
                with ui.card().classes("bg-[#111827] border border-[#374151] rounded-lg p-4 shadow-md"):
                    reliability_trend_chart(trend_df, state.selected_api)
                    
                # Chart 2: Uptime Trend Percentage
                with ui.card().classes("bg-[#111827] border border-[#374151] rounded-lg p-4 shadow-md"):
                    uptime_trend_chart(trend_df, state.selected_api)
                    
                # Chart 3: Error Rate Percentage
                with ui.card().classes("bg-[#111827] border border-[#374151] rounded-lg p-4 shadow-md"):
                    error_rate_trend_chart(trend_df, state.selected_api)
                    
                # Chart 4: SLA Trend Percentage
                with ui.card().classes("bg-[#111827] border border-[#374151] rounded-lg p-4 shadow-md"):
                    sla_trend_chart(trend_df, state.selected_api)
