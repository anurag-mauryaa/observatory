from nicegui import ui
from typing import Optional

def metric_card(
    title: str,
    value: str,
    trend: Optional[str] = None,
    trend_positive: bool = True,
    icon: Optional[str] = None,
    color: str = "blue"
):
    """
    Renders a Datadog-style KPI metric card.
    color: 'blue', 'purple', 'green', 'red', 'yellow'
    """
    border_colors = {
        "blue": "border-l-4 border-l-[#0284c7]",
        "purple": "border-l-4 border-l-[#7c3aed]",
        "green": "border-l-4 border-l-[#10b981]",
        "red": "border-l-4 border-l-[#ef4444]",
        "yellow": "border-l-4 border-l-[#f59e0b]"
    }
    
    border_class = border_colors.get(color, "border-l-4 border-l-[#0284c7]")
    
    with ui.card().classes(
        f"bg-[#111827] border border-[#374151] rounded-lg shadow-lg p-5 flex flex-col justify-between w-full lg:flex-1 h-[120px] transition-transform hover:scale-[1.02] duration-200 {border_class}"
    ):
        with ui.row().classes("w-full justify-between items-center no-wrap"):
            ui.label(title.upper()).classes("text-[10px] font-bold tracking-widest text-[#9ca3af]")
            if icon:
                ui.icon(icon).classes(f"text-[20px] text-gray-500")
                
        ui.label(value).classes("text-3xl font-extrabold text-[#f3f4f6] mt-1")
        
        if trend:
            with ui.row().classes("w-full items-center mt-2 no-wrap text-[11px]"):
                trend_color = "#10b981" if trend_positive else "#ef4444"
                trend_icon = "arrow_upward" if trend_positive else "arrow_downward"
                ui.icon(trend_icon).style(f"color: {trend_color}; font-size: 14px;")
                ui.label(trend).style(f"color: {trend_color}; font-weight: 600;")
        else:
            ui.label("").classes("h-[14px]")
