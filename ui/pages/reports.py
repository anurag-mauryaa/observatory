from nicegui import ui
import pandas as pd
from datetime import datetime
from pathlib import Path

from ui.state import state
from ui.queries import UIQueries
from src.analytics.reporting import Reporting

def render_reports(container: ui.element, queries: UIQueries):
    """Renders the reports and exports view."""
    container.clear()
    
    rep = Reporting()
    monthly_df = rep.generate_monthly_report()
    
    # State for selected API in API Summary section
    summary_state = {"api_name": "GitHub"}
    summary_container = None

    def render_api_summary():
        """Renders the selected API's summary stats in its container."""
        if summary_container is None:
            return
        summary_container.clear()
        api_name = summary_state["api_name"]
        summary_df = rep.generate_api_summary_report(api_name)
        
        with summary_container:
            if summary_df.empty:
                ui.label("No metrics history recorded for this API.").classes("text-xs text-gray-500 italic mt-2")
                return
                
            stats = summary_df.iloc[0]
            with ui.grid(columns=1).classes("w-full gap-4 sm:grid-cols-2 lg:grid-cols-3 mt-3"):
                # Latency
                with ui.card().classes("bg-[#1f2937]/50 border border-[#374151] p-4 gap-1 rounded"):
                    ui.label("AVERAGE LATENCY").classes("text-[9px] text-[#9ca3af] font-bold")
                    ui.label(f"{stats['avg_response_time_ms']:.1f}ms").classes("text-xl font-black text-white")
                    
                # Reliability
                with ui.card().classes("bg-[#1f2937]/50 border border-[#374151] p-4 gap-1 rounded"):
                    ui.label("RELIABILITY SCORE").classes("text-[9px] text-[#9ca3af] font-bold")
                    ui.label(f"{stats['avg_reliability_score']:.2f}%").classes("text-xl font-black text-[#8b5cf6]")
                    
                # SLA
                with ui.card().classes("bg-[#1f2937]/50 border border-[#374151] p-4 gap-1 rounded"):
                    ui.label("SLA COMPLIANCE").classes("text-[9px] text-[#9ca3af] font-bold")
                    ui.label(f"{stats['avg_sla_score']:.2f}%").classes("text-xl font-black text-[#f59e0b]")

                # Health
                with ui.card().classes("bg-[#1f2937]/50 border border-[#374151] p-4 gap-1 rounded"):
                    ui.label("HEALTH INDEX").classes("text-[9px] text-[#9ca3af] font-bold")
                    ui.label(f"{stats['avg_health_score']:.2f}%").classes("text-xl font-black text-[#10b981]")

                # Uptime
                with ui.card().classes("bg-[#1f2937]/50 border border-[#374151] p-4 gap-1 rounded"):
                    ui.label("UPTIME PERCENTAGE").classes("text-[9px] text-[#9ca3af] font-bold")
                    ui.label(f"{stats['avg_uptime_percentage']:.2f}%").classes("text-xl font-black text-white")

                # Days Tracked
                with ui.card().classes("bg-[#1f2937]/50 border border-[#374151] p-4 gap-1 rounded"):
                    ui.label("TOTAL DAYS TRACKED").classes("text-[9px] text-[#9ca3af] font-bold")
                    ui.label(f"{int(stats['total_days_tracked'])} days").classes("text-xl font-black text-gray-300")

    def trigger_csv_download():
        """Regenerates files in warehouse and downloads the monthly report CSV client-side."""
        try:
            # Regenerate CSV files in warehouse/analytics/
            rep.export_report_csv()
            
            # Retrieve latest data and initiate browser download
            csv_data = monthly_df.to_csv(index=False)
            ui.download(csv_data.encode("utf-8"), filename=f"monthly_reliability_report_{datetime.now().strftime('%Y%m')}.csv")
            ui.notify("Monthly Report CSV generated and download started!", type="positive")
        except Exception as e:
            ui.notify(f"Failed to export CSV: {e}", type="negative")

    def trigger_pdf_placeholder():
        """Shows standard enterprise placeholder notification for PDF exports."""
        ui.notify(
            "PDF Report Export is an Enterprise-tier feature. Generating placeholder preview...",
            type="warning",
            icon="workspace_premium"
        )

    # Page layout
    with container:
        with ui.column().classes("w-full gap-6 p-1"):
            
            # Toolbar card
            with ui.card().classes("bg-[#111827] border border-[#374151] rounded-lg p-5 w-full shadow-md"):
                with ui.row().classes("w-full justify-between items-center flex-wrap gap-4"):
                    with ui.column().classes("gap-1"):
                        ui.label("REPORTS & EXPORTS CENTER").classes("text-sm font-extrabold text-[#f3f4f6] tracking-wide")
                        ui.label("Generate monthly SLA reports, download historical CSV aggregates, or schedule alerts.").classes("text-xs text-[#9ca3af]")
                        
                    # Action buttons
                    with ui.row().classes("items-center gap-3"):
                        ui.button(
                            "EXPORT CSV", 
                            icon="download", 
                            on_click=trigger_csv_download
                        ).props("color=blue").classes("text-xs font-bold px-4 py-2")
                        
                        ui.button(
                            "EXPORT PDF (PRO)", 
                            icon="picture_as_pdf", 
                            on_click=trigger_pdf_placeholder
                        ).props("outline color=purple").classes("text-xs font-bold px-4 py-2")

            # Two-Column Layout for Main Content
            with ui.row().classes("w-full gap-4 items-stretch lg:flex-row flex-col"):
                
                # Column 1: Monthly Reliability Report Table (2/3 width)
                with ui.card().classes("bg-[#111827] border border-[#374151] rounded-lg p-5 w-full lg:w-2/3 shadow-md"):
                    ui.label("MONTHLY RELIABILITY STANDINGS").classes("text-xs font-bold tracking-wider text-[#9ca3af] mb-4 border-b border-[#374151] pb-2")
                    
                    if not monthly_df.empty:
                        cols = [
                            {"name": "api_name", "label": "API Name", "field": "api_name", "align": "left"},
                            {"name": "month_year", "label": "Month", "field": "month_year", "align": "center"},
                            {"name": "avg_reliability_score", "label": "Reliability", "field": "avg_reliability_score", "align": "center"},
                            {"name": "avg_sla_score", "label": "SLA Score", "field": "avg_sla_score", "align": "center"},
                            {"name": "avg_response_time_ms", "label": "Latency", "field": "avg_response_time_ms", "align": "right"}
                        ]
                        
                        rows = []
                        for _, row in monthly_df.iterrows():
                            # Format month label e.g., '2026-06'
                            month_label = f"{int(row['year'])}-{int(row['month']):02d}"
                            rows.append({
                                "api_name": row["api_name"],
                                "month_year": month_label,
                                "avg_reliability_score": f"{row['avg_reliability_score']:.1f}%",
                                "avg_sla_score": f"{row['avg_sla_score']:.1f}%",
                                "avg_response_time_ms": f"{row['avg_response_time_ms']:.0f}ms"
                            })
                            
                        ui.table(
                            columns=cols,
                            rows=rows,
                            row_key="api_name"
                        ).props("dark flat dense bordered").classes("w-full bg-[#111827] text-xs")
                    else:
                        ui.label("No monthly history records available.").classes("text-xs text-gray-500 italic")

                # Column 2: API Summary Report Card (1/3 width)
                with ui.card().classes("bg-[#111827] border border-[#374151] rounded-lg p-5 w-full lg:w-1/3 shadow-md gap-4"):
                    ui.label("API SERVICE SUMMARY").classes("text-xs font-bold tracking-wider text-[#9ca3af] border-b border-[#374151] pb-2 w-full")
                    
                    # Selector for summary
                    apis = queries.get_dim_apis()
                    if apis:
                        ui.select(
                            options=apis,
                            value=summary_state["api_name"],
                            on_change=lambda e: [summary_state.update({"api_name": e.value}), render_api_summary()]
                        ).props("dark dense outlined").classes("w-full text-white")
                        
                        # Create container here, so it is properly nested in the card
                        summary_container = ui.column().classes("w-full")
                        render_api_summary()
                    else:
                        ui.label("No APIs found in data warehouse.").classes("text-xs text-gray-500 italic")
