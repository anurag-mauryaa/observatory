from nicegui import ui
import pandas as pd

from ui.state import state
from ui.queries import UIQueries
from ui.components.api_table import leaderboard_table, ranking_table
from src.analytics.ranking_analytics import RankingAnalytics
from src.analytics.performance_analytics import PerformanceAnalytics

def render_rankings(container: ui.element, queries: UIQueries):
    """Renders the leaderboards and API rankings view."""
    container.clear()
    
    # Instantiate analytical classes
    ranking = RankingAnalytics()
    perf = PerformanceAnalytics()
    
    # Query data
    leaderboard_df = ranking.api_leaderboard()
    fastest_df = perf.fastest_apis(limit=10)
    sla_df = ranking.sla_ranking()
    reliability_df = ranking.reliability_ranking()
    health_df = ranking.health_score_ranking()
    
    with container:
        with ui.column().classes("w-full gap-6 p-1"):
            
            # Leaderboard Table Card (Full Width)
            with ui.card().classes("bg-[#111827] border border-[#374151] rounded-lg p-5 w-full shadow-md"):
                leaderboard_table(leaderboard_df)
                
            # Sub Rankings in a 2x2 grid
            with ui.grid(columns=1).classes("w-full gap-4 md:grid-cols-2"):
                
                # Table 1: Fastest APIs (Latency)
                with ui.card().classes("bg-[#111827] border border-[#374151] rounded-lg p-5 shadow-md"):
                    ranking_table(
                        df=fastest_df,
                        value_field="avg_response_time_ms",
                        value_label="Avg Latency (ms)",
                        title="FASTEST APIs (LOWER IS BETTER)"
                    )
                    
                # Table 2: Highest SLA APIs
                with ui.card().classes("bg-[#111827] border border-[#374151] rounded-lg p-5 shadow-md"):
                    ranking_table(
                        df=sla_df,
                        value_field="sla_score",
                        value_label="SLA Compliance (%)",
                        title="HIGHEST SLA COMPLIANCE"
                    )
                    
                # Table 3: Highest Reliability APIs
                with ui.card().classes("bg-[#111827] border border-[#374151] rounded-lg p-5 shadow-md"):
                    ranking_table(
                        df=reliability_df,
                        value_field="reliability_score",
                        value_label="Reliability Score (0-100)",
                        title="HIGHEST RELIABILITY SCORE"
                    )
                    
                # Table 4: Highest Health Score APIs
                with ui.card().classes("bg-[#111827] border border-[#374151] rounded-lg p-5 shadow-md"):
                    ranking_table(
                        df=health_df,
                        value_field="health_score",
                        value_label="Health Index (0-100)",
                        title="HIGHEST HEALTH SCORE"
                    )
