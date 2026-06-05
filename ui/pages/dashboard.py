from nicegui import ui
import pandas as pd

from ui.state import state
from ui.queries import UIQueries
from ui.components.metric_card import metric_card
from ui.components.charts import latency_trend_chart, uptime_trend_chart, reliability_trend_chart

def render_dashboard(container: ui.element, queries: UIQueries):
    """Renders the Executive Dashboard view into the content container."""
    # Clear container first
    container.clear()
    
    # Query database
    days = state.get_date_days()
    kpi_data = queries.get_dashboard_summary_kpis(state.selected_api, days)
    trend_df = queries.get_trend_data(state.selected_api, days)
    
    with container:
        # Dashboard page content wrapper
        with ui.column().classes("w-full gap-6 p-1"):
            
            # Row 1: KPI Cards Grid
            with ui.row().classes("w-full gap-4 justify-between items-stretch lg:flex-row flex-col"):
                # Overall Stats Card (incorporating Counts)
                with ui.card().classes("bg-[#111827] border border-[#374151] rounded-lg p-5 flex flex-col justify-between w-full lg:flex-1 min-h-[120px]"):
                    ui.label("PLATFORM MONITORING STATUS").classes("text-[10px] font-bold tracking-widest text-[#9ca3af]")
                    
                    with ui.row().classes("w-full justify-around items-center mt-3"):
                        with ui.column().classes("items-center gap-0"):
                            ui.label(str(kpi_data.get("total_apis", 0))).classes("text-3xl font-extrabold text-white")
                            ui.label("TOTAL").classes("text-[9px] text-[#9ca3af] font-bold")
                        
                        with ui.column().classes("items-center gap-0"):
                            ui.label(str(kpi_data.get("healthy_apis", 0))).classes("text-3xl font-extrabold text-[#10b981]")
                            ui.label("HEALTHY").classes("text-[9px] text-[#10b981] font-bold")
                            
                        with ui.column().classes("items-center gap-0"):
                            ui.label(str(kpi_data.get("degraded_apis", 0))).classes("text-3xl font-extrabold text-[#f59e0b]")
                            ui.label("DEGRADED").classes("text-[9px] text-[#f59e0b] font-bold")
                            
                        with ui.column().classes("items-center gap-0"):
                            ui.label(str(kpi_data.get("offline_apis", 0))).classes("text-3xl font-extrabold text-[#ef4444]")
                            ui.label("OFFLINE").classes("text-[9px] text-[#ef4444] font-bold")
                
                # Metric 2: Avg Response Time
                metric_card(
                    title="Average Latency",
                    value=kpi_data.get("avg_response_time", "N/A"),
                    icon="speed",
                    color="blue",
                    trend="2.4% vs last period" if not trend_df.empty else None,
                    trend_positive=True
                )
                
                # Metric 3: Avg Reliability Score
                metric_card(
                    title="Avg Reliability Score",
                    value=kpi_data.get("avg_reliability", "N/A"),
                    icon="shield",
                    color="purple",
                    trend="0.8% vs last period" if not trend_df.empty else None,
                    trend_positive=True
                )
                
                # Metric 4: Avg Health Score
                metric_card(
                    title="Avg Health Score",
                    value=kpi_data.get("avg_health", "N/A"),
                    icon="health_and_safety",
                    color="green",
                    trend="1.1% vs last period" if not trend_df.empty else None,
                    trend_positive=True
                )
                
            # Row 2: Charts Row (Latency Trend & Uptime Trend)
            with ui.row().classes("w-full gap-4 items-stretch lg:flex-row flex-col"):
                with ui.card().classes("bg-[#111827] border border-[#374151] rounded-lg p-4 flex-1 shadow-md"):
                    latency_trend_chart(trend_df, state.selected_api)
                    
                with ui.card().classes("bg-[#111827] border border-[#374151] rounded-lg p-4 flex-1 shadow-md"):
                    uptime_trend_chart(trend_df, state.selected_api)

            # Row 3: Reliability trend chart (full-width)
            with ui.row().classes("w-full"):
                with ui.card().classes("bg-[#111827] border border-[#374151] rounded-lg p-4 w-full shadow-md"):
                    reliability_trend_chart(trend_df, state.selected_api)
                    
            # Row 4: Top APIs / Standings Summary list
            with ui.row().classes("w-full"):
                with ui.card().classes("bg-[#111827] border border-[#374151] rounded-lg p-5 w-full shadow-md gap-4"):
                    ui.label("TOP PERFORMING ENDPOINTS").classes("text-xs font-bold tracking-wider text-[#9ca3af]")
                    
                    from src.analytics.ranking_analytics import RankingAnalytics
                    ranking = RankingAnalytics()
                    leaderboard = ranking.api_leaderboard()
                    
                    if not leaderboard.empty:
                        # Display top 3 performing APIs in nice visual cards
                        with ui.row().classes("w-full justify-start gap-4 flex-wrap"):
                            # Filter down to top 3
                            top_3 = leaderboard.head(3)
                            for _, api in top_3.iterrows():
                                with ui.row().classes("items-center gap-3 bg-[#1f2937]/40 border border-[#374151] rounded-md px-4 py-2.5 min-w-[240px]"):
                                    # Medal icon or badge
                                    medal_colors = {1: "#f59e0b", 2: "#d1d5db", 3: "#b45309"}
                                    rank_val = int(api["rank"])
                                    color_hex = medal_colors.get(rank_val, "#9ca3af")
                                    ui.icon("emoji_events").style(f"color: {color_hex}; font-size: 24px;")
                                    
                                    with ui.column().classes("gap-0"):
                                        ui.label(api["api_name"]).classes("text-sm font-bold text-white")
                                        ui.label(f"Score: {api['leaderboard_score']}%").classes("text-[11px] text-[#9ca3af] font-semibold")
                    else:
                        ui.label("Run data pipeline simulator to display top APIs list.").classes("text-xs text-gray-500 italic")
