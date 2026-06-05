import plotly.graph_objects as go
import pandas as pd
from nicegui import ui
from typing import List

# Shared Plotly Dark Theme Stylesheet
PLOTLY_DARK_LAYOUT = {
    "autosize": True,
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": "#9ca3af", "family": "Inter, sans-serif"},
    "xaxis": {
        "gridcolor": "#374151",
        "linecolor": "#4b5563",
        "zerolinecolor": "#374151",
        "tickfont": {"size": 10}
    },
    "yaxis": {
        "gridcolor": "#374151",
        "linecolor": "#4b5563",
        "zerolinecolor": "#374151",
        "tickfont": {"size": 10}
    },
    "margin": {"l": 40, "r": 20, "t": 35, "b": 40},
    "hovermode": "x unified",
    "legend": {
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "right",
        "x": 1
    }
}

def latency_trend_chart(df: pd.DataFrame, api_name: str = "All APIs"):
    """Line chart showing daily average response time."""
    fig = go.Figure()
    
    if df.empty:
        fig.add_annotation(text="No data available", showarrow=False, font={"size": 14})
        fig.update_layout(PLOTLY_DARK_LAYOUT)
        return ui.plotly(fig).classes("w-full h-[320px]")
        
    df = df.sort_values(by="date")
    
    if "api_name" in df.columns and api_name == "All APIs":
        # Multi-line plot (one per API)
        colors = ["#3b82f6", "#8b5cf6", "#10b981", "#ef4444", "#f59e0b", "#06b6d4"]
        apis = df["api_name"].unique()
        for idx, api in enumerate(apis):
            api_df = df[df["api_name"] == api]
            fig.add_trace(go.Scatter(
                x=api_df["date"],
                y=api_df["average_response_time"],
                mode="lines+markers",
                name=api,
                line={"width": 2.5, "color": colors[idx % len(colors)]},
                marker={"size": 5}
            ))
    else:
        # Single API line plot
        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df["average_response_time"],
            mode="lines+markers",
            name="Latency (ms)",
            line={"width": 3, "color": "#3b82f6"},
            marker={"size": 6},
            fill="tozeroy",
            fillcolor="rgba(59, 130, 246, 0.08)"
        ))
        
    layout = PLOTLY_DARK_LAYOUT.copy()
    layout["title"] = {
        "text": f"Response Time Trend (ms) - {api_name}",
        "font": {"size": 13, "weight": "bold", "color": "#f3f4f6"}
    }
    
    fig.update_layout(layout)
    return ui.plotly(fig).classes("w-full h-[320px]")

def uptime_trend_chart(df: pd.DataFrame, api_name: str = "All APIs"):
    """Chart displaying daily uptime percentage trends."""
    fig = go.Figure()
    
    if df.empty:
        fig.add_annotation(text="No data available", showarrow=False, font={"size": 14})
        fig.update_layout(PLOTLY_DARK_LAYOUT)
        return ui.plotly(fig).classes("w-full h-[320px]")
        
    df = df.sort_values(by="date")
    
    if "api_name" in df.columns and api_name == "All APIs":
        # Grouped view (average daily uptime across all APIs)
        grouped = df.groupby("date")["uptime_percentage"].mean().reset_index()
        fig.add_trace(go.Scatter(
            x=grouped["date"],
            y=grouped["uptime_percentage"],
            mode="lines",
            name="Avg Uptime",
            line={"width": 3, "color": "#10b981"},
            fill="tozeroy",
            fillcolor="rgba(16, 185, 129, 0.08)"
        ))
    else:
        # Single API detailed bar chart
        fig.add_trace(go.Bar(
            x=df["date"],
            y=df["uptime_percentage"],
            name="Uptime %",
            marker_color="#10b981",
            opacity=0.85
        ))
        fig.update_yaxes(range=[90, 100.5])  # Focus on uptime region
        
    layout = PLOTLY_DARK_LAYOUT.copy()
    layout["title"] = {
        "text": f"Uptime Trend (%) - {api_name}",
        "font": {"size": 13, "weight": "bold", "color": "#f3f4f6"}
    }
    fig.update_layout(layout)
    return ui.plotly(fig).classes("w-full h-[320px]")

def reliability_trend_chart(df: pd.DataFrame, api_name: str = "All APIs"):
    """Line chart showing daily reliability index score."""
    fig = go.Figure()
    
    if df.empty:
        fig.add_annotation(text="No data available", showarrow=False, font={"size": 14})
        fig.update_layout(PLOTLY_DARK_LAYOUT)
        return ui.plotly(fig).classes("w-full h-[320px]")
        
    df = df.sort_values(by="date")
    
    if "api_name" in df.columns and api_name == "All APIs":
        colors = ["#3b82f6", "#8b5cf6", "#10b981", "#ef4444", "#f59e0b", "#06b6d4"]
        apis = df["api_name"].unique()
        for idx, api in enumerate(apis):
            api_df = df[df["api_name"] == api]
            fig.add_trace(go.Scatter(
                x=api_df["date"],
                y=api_df["reliability_score"],
                mode="lines",
                name=api,
                line={"width": 2, "color": colors[idx % len(colors)]}
            ))
    else:
        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df["reliability_score"],
            mode="lines+markers",
            name="Reliability Score",
            line={"width": 3, "color": "#8b5cf6"},
            marker={"size": 5},
            fill="tozeroy",
            fillcolor="rgba(139, 92, 246, 0.08)"
        ))
        fig.update_yaxes(range=[80, 101])
        
    layout = PLOTLY_DARK_LAYOUT.copy()
    layout["title"] = {
        "text": f"Reliability Index - {api_name}",
        "font": {"size": 13, "weight": "bold", "color": "#f3f4f6"}
    }
    fig.update_layout(layout)
    return ui.plotly(fig).classes("w-full h-[320px]")

def error_rate_trend_chart(df: pd.DataFrame, api_name: str = "All APIs"):
    """Chart displaying daily error rate trends."""
    fig = go.Figure()
    
    if df.empty:
        fig.add_annotation(text="No data available", showarrow=False, font={"size": 14})
        fig.update_layout(PLOTLY_DARK_LAYOUT)
        return ui.plotly(fig).classes("w-full h-[320px]")
        
    df = df.sort_values(by="date")
    
    if "api_name" in df.columns and api_name == "All APIs":
        grouped = df.groupby("date")["error_rate"].mean().reset_index()
        fig.add_trace(go.Bar(
            x=grouped["date"],
            y=grouped["error_rate"],
            name="Avg Error Rate",
            marker_color="#ef4444"
        ))
    else:
        fig.add_trace(go.Bar(
            x=df["date"],
            y=df["error_rate"],
            name="Error Rate %",
            marker_color="#ef4444",
            opacity=0.8
        ))
        
    layout = PLOTLY_DARK_LAYOUT.copy()
    layout["title"] = {
        "text": f"Error Rate Trend (%) - {api_name}",
        "font": {"size": 13, "weight": "bold", "color": "#f3f4f6"}
    }
    fig.update_layout(layout)
    return ui.plotly(fig).classes("w-full h-[320px]")

def sla_trend_chart(df: pd.DataFrame, api_name: str = "All APIs"):
    """Line chart showing daily SLA score percentage."""
    fig = go.Figure()
    
    if df.empty:
        fig.add_annotation(text="No data available", showarrow=False, font={"size": 14})
        fig.update_layout(PLOTLY_DARK_LAYOUT)
        return ui.plotly(fig).classes("w-full h-[320px]")
        
    df = df.sort_values(by="date")
    
    if "api_name" in df.columns and api_name == "All APIs":
        grouped = df.groupby("date")["sla_score"].mean().reset_index()
        fig.add_trace(go.Scatter(
            x=grouped["date"],
            y=grouped["sla_score"],
            mode="lines",
            name="Avg SLA Score",
            line={"width": 3, "color": "#f59e0b"}
        ))
    else:
        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df["sla_score"],
            mode="lines+markers",
            name="SLA Score %",
            line={"width": 3, "color": "#f59e0b"},
            marker={"size": 5}
        ))
        fig.update_yaxes(range=[80, 101])
        
    layout = PLOTLY_DARK_LAYOUT.copy()
    layout["title"] = {
        "text": f"SLA Score Trend (%) - {api_name}",
        "font": {"size": 13, "weight": "bold", "color": "#f3f4f6"}
    }
    fig.update_layout(layout)
    return ui.plotly(fig).classes("w-full h-[320px]")
