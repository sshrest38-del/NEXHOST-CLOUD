"""
NEXHOST CLOUD - Plotly Interactive Charts and Telemetry Visualizations
Author: @Harsh_54x
"""

from typing import List, Dict, Any
import plotly.graph_objects as go
import plotly.express as px

def create_resource_gauge(value: float, max_value: float, title: str, unit: str = "%", color: str = "#6366F1") -> go.Figure:
    """Create circular modern gauge chart."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': 14, 'color': '#9CA3AF'}},
        number={'suffix': f" {unit}", 'font': {'size': 24, 'color': '#FFFFFF'}},
        gauge={
            'axis': {'range': [0, max_value], 'tickwidth': 1, 'tickcolor': "#4B5563"},
            'bar': {'color': color},
            'bgcolor': "rgba(31, 41, 55, 0.5)",
            'borderwidth': 0,
            'steps': [
                {'range': [0, max_value * 0.7], 'color': "rgba(16, 185, 129, 0.15)"},
                {'range': [max_value * 0.7, max_value * 0.9], 'color': "rgba(245, 158, 11, 0.15)"},
                {'range': [max_value * 0.9, max_value], 'color': "rgba(239, 68, 68, 0.2)"}
            ]
        }
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=180,
        margin=dict(l=15, r=15, t=30, b=10),
    )
    return fig

def create_resource_history_chart(timestamps: List[str], cpu_values: List[float], ram_values: List[float]) -> go.Figure:
    """Create dual-axis time-series line chart for telemetry."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=cpu_values,
        mode='lines+markers',
        name='CPU Usage (%)',
        line=dict(color='#6366F1', width=2),
        fill='tozeroy',
        fillcolor='rgba(99, 102, 241, 0.1)'
    ))
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=ram_values,
        mode='lines+markers',
        name='RAM Usage (MB)',
        line=dict(color='#10B981', width=2),
        yaxis='y2'
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(17, 24, 39, 0.5)',
        font=dict(color='#9CA3AF', size=11),
        margin=dict(l=20, r=20, t=25, b=20),
        height=260,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(title='CPU %', range=[0, 100], showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
        yaxis2=dict(title='RAM (MB)', overlaying='y', side='right', showgrid=False)
    )
    return fig

def create_status_donut(running: int, stopped: int, failed: int) -> go.Figure:
    """Project status distribution donut chart."""
    labels = ['Running', 'Stopped', 'Failed']
    values = [running, stopped, failed]
    colors = ['#10B981', '#F59E0B', '#EF4444']

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.6,
        marker=dict(colors=colors),
        textinfo='value'
    )])
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#9CA3AF', size=11),
        height=200,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    return fig
