"""
Data Visualization Module for SupeRR SCOUT Platform.
Generates polished, responsive Plotly charts strictly styled with Rajasthan Royals'
signature visual identity: Deep Navy (#080D20), RR Royal Pink (#E6007E), and Deep Royal Blue (#1746A2).
"""

from typing import Any, List, Dict, Optional
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# Rajasthan Royals Mandatory Brand Color Palette
RR_PINK = "#E6007E"          # RR Royal Pink
RR_BLUE = "#1746A2"          # Deep Royal Blue
RR_ELECTRIC = "#287BFF"      # Electric Blue
RR_NAVY = "#080D20"          # Deep Navy
RR_CARD_BG = "#111A32"       # Card Background
RR_WHITE = "#F7F8FC"         # White
RR_MUTED = "#A8B3CC"         # Muted Text

RR_CYAN = "#00E5FF"
RR_GOLD = "#F39C12"
RR_PURPLE = "#8E44AD"
RR_GREEN = "#2ECC71"

CHART_BG = "#111A32"         # Card Background
PAPER_BG = "#080D20"         # Deep Navy Background
GRID_COLOR = "#1D2B52"       # Card Border / Grid Line

FONT_FAMILY = "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"


def apply_rr_theme(fig: go.Figure) -> go.Figure:
    """Apply consistent Rajasthan Royals styling and layout defaults to a Plotly figure."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=CHART_BG,
        font=dict(family=FONT_FAMILY, color=RR_WHITE, size=12),
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(
            gridcolor=GRID_COLOR,
            zerolinecolor=GRID_COLOR,
            showline=True,
            linecolor=GRID_COLOR
        ),
        yaxis=dict(
            gridcolor=GRID_COLOR,
            zerolinecolor=GRID_COLOR,
            showline=True,
            linecolor=GRID_COLOR
        ),
        legend=dict(
            bgcolor="rgba(19, 23, 34, 0.7)",
            bordercolor=GRID_COLOR,
            borderwidth=1,
            font=dict(size=11)
        ),
        hoverlabel=dict(
            bgcolor="#1F2430",
            font_size=12,
            font_family=FONT_FAMILY
        )
    )
    return fig


def plot_pressure_distribution(df: pd.DataFrame, threshold: float = 65.0) -> go.Figure:
    """Histogram & density distribution of Batting and Bowling Pressure across all deliveries."""
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=df["pressure_batting"],
        name="Batting Pressure",
        marker_color=RR_PINK,
        opacity=0.65,
        nbinsx=40,
        histnorm="probability density"
    ))
    
    fig.add_trace(go.Histogram(
        x=df["pressure_bowling"],
        name="Bowling Pressure",
        marker_color=RR_BLUE,
        opacity=0.65,
        nbinsx=40,
        histnorm="probability density"
    ))
    
    # Add vertical line for threshold
    fig.add_vline(
        x=threshold,
        line_dash="dash",
        line_color=RR_GOLD,
        line_width=2,
        annotation_text=f"High Pressure Threshold ({threshold:.0f})",
        annotation_position="top right",
        annotation_font_color=RR_GOLD
    )
    
    fig.update_layout(
        title=dict(text="Delivery-Level Pressure Index Distribution (0â€“100)", font=dict(size=16)),
        xaxis_title="Pressure Index",
        yaxis_title="Probability Density",
        barmode="overlay"
    )
    return apply_rr_theme(fig)


def plot_top_10_horizontal_bar(top_df: pd.DataFrame, title: str, is_batter: bool = True) -> go.Figure:
    """Horizontal bar chart showcasing Top 10 players sorted with rank and score badges."""
    df_sorted = top_df.sort_values("reliability_score", ascending=True).copy()
    
    primary_color = RR_PINK if is_batter else RR_ELECTRIC
    secondary_color = RR_BLUE if is_batter else RR_BLUE
    
    # Labels with rank and name
    y_labels = [f"#{r} {name}" for r, name in zip(df_sorted["rank"], df_sorted["player_name"])]
    
    # Custom hover text
    hover_texts = []
    for _, row in df_sorted.iterrows():
        if is_batter:
            ht = (
                f"<b>{row['player_name']}</b> (Rank #{row['rank']})<br>"
                f"Reliability Score: <b>{row['reliability_score']:.1f}</b><br>"
                f"HP Balls: {row['hp_balls']:.0f}<br>"
                f"HP Strike Rate: {row['hp_strike_rate']:.1f}<br>"
                f"HP Average: {row['hp_average']:.1f}<br>"
                f"SR Delta: {row['sr_delta']:+.1f}<br>"
                f"95% CI: [{row['ci_lower']:.1f} - {row['ci_upper']:.1f}]"
            )
        else:
            ht = (
                f"<b>{row['player_name']}</b> (Rank #{row['rank']})<br>"
                f"Reliability Score: <b>{row['reliability_score']:.1f}</b><br>"
                f"HP Legal Balls: {row['hp_legal_balls']:.0f}<br>"
                f"HP Wickets: {row['hp_wickets']:.0f}<br>"
                f"HP Economy: {row['hp_economy']:.2f}<br>"
                f"Econ Delta: {row['econ_delta']:+.2f}<br>"
                f"95% CI: [{row['ci_lower']:.1f} - {row['ci_upper']:.1f}]"
            )
        hover_texts.append(ht)
        
    fig = go.Figure(go.Bar(
        x=df_sorted["reliability_score"],
        y=y_labels,
        orientation="h",
        marker=dict(
            color=df_sorted["reliability_score"],
            colorscale=[[0, secondary_color], [1, primary_color]],
            line=dict(color=RR_WHITE, width=1)
        ),
        text=[f"  <b>{s:.1f}</b>" for s in df_sorted["reliability_score"]],
        textposition="outside",
        hovertext=hover_texts,
        hoverinfo="text"
    ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        xaxis_title="Pressure Reliability Score (0â€“100)",
        yaxis_title="",
        xaxis=dict(range=[0, 105]),
        height=450
    )
    return apply_rr_theme(fig)


def plot_batting_scatter(bat_df: pd.DataFrame, min_balls: int = 60) -> go.Figure:
    """Scatter plot matrix: High-Pressure Strike Rate vs Average with bubble size for balls faced."""
    sub = bat_df[bat_df["hp_balls"] >= min_balls].copy()
    
    fig = px.scatter(
        sub,
        x="hp_strike_rate",
        y="hp_average",
        size="hp_balls",
        color="reliability_score",
        hover_name="player_name",
        hover_data={
            "hp_balls": True,
            "hp_runs": True,
            "hp_strike_rate": ":.1f",
            "hp_average": ":.1f",
            "sr_delta": ":+.1f",
            "reliability_score": ":.1f"
        },
        color_continuous_scale=[[0, "#1746A2"], [0.5, "#287BFF"], [1, "#E6007E"]],
        title=f"Batting Efficiency under High Pressure (Min {min_balls} Balls Faced)"
    )
    
    # Add benchmark reference lines
    fig.add_hline(y=30.0, line_dash="dot", line_color=RR_MUTED, annotation_text="Benchmark Avg (30.0)")
    fig.add_vline(x=150.0, line_dash="dot", line_color=RR_MUTED, annotation_text="Benchmark SR (150.0)")
    
    fig.update_layout(
        xaxis_title="High-Pressure Strike Rate",
        yaxis_title="High-Pressure Average (Runs/Dismissal)",
        height=520
    )
    return apply_rr_theme(fig)


def plot_bowling_scatter(bowl_df: pd.DataFrame, min_balls: int = 60) -> go.Figure:
    """Scatter plot: Bowling Economy vs Strike Rate (axes inverted so top-right represents elite)."""
    sub = bowl_df[bowl_df["hp_legal_balls"] >= min_balls].copy()
    
    fig = px.scatter(
        sub,
        x="hp_economy",
        y="hp_strike_rate",
        size="hp_wickets",
        color="reliability_score",
        hover_name="player_name",
        hover_data={
            "hp_legal_balls": True,
            "hp_wickets": True,
            "hp_economy": ":.2f",
            "hp_strike_rate": ":.1f",
            "hp_dot_pct": ":.1f",
            "reliability_score": ":.1f"
        },
        color_continuous_scale=[[0, "#1746A2"], [0.5, "#287BFF"], [1, "#E6007E"]],
        title=f"Bowling Containment vs Wicket-Taking Matrix (Min {min_balls} Balls)"
    )
    
    # Invert axes so lower economy and lower strike rate are at the top-right!
    fig.update_xaxes(autorange="reversed")
    fig.update_yaxes(autorange="reversed")
    
    fig.add_vline(x=8.5, line_dash="dot", line_color=RR_MUTED, annotation_text="Elite Econ (<= 8.5)")
    fig.add_hline(y=14.0, line_dash="dot", line_color=RR_MUTED, annotation_text="Elite SR (<= 14 balls/wkt)")
    
    fig.update_layout(
        xaxis_title="High-Pressure Economy Rate (Inverted: Left is higher, Right is lower)",
        yaxis_title="High-Pressure Bowling Strike Rate (Inverted: Top is faster wickets)",
        height=520
    )
    return apply_rr_theme(fig)


def plot_pressure_vs_normal_comparison(row: pd.Series, is_batter: bool = True) -> go.Figure:
    """Paired bar chart comparing High-Pressure vs Normal performance for a player."""
    fig = go.Figure()
    
    if is_batter:
        categories = ["Strike Rate", "Average", "Boundary %", "Dot %"]
        hp_vals = [row["hp_strike_rate"], row["hp_average"], row["hp_boundary_pct"], row["hp_dot_pct"]]
        norm_vals = [row["norm_strike_rate"], row["norm_average"], row["norm_boundary_pct"], row["norm_dot_pct"]]
    else:
        categories = ["Economy Rate", "Strike Rate", "Dot %", "Boundary Conceded %"]
        hp_vals = [row["hp_economy"], row["hp_strike_rate"], row["hp_dot_pct"], row["hp_boundary_pct"]]
        norm_vals = [row["norm_economy"], row["norm_strike_rate"], row["norm_dot_pct"], row["norm_boundary_pct"]]
        
    fig.add_trace(go.Bar(
        name="High Pressure (Index â‰¥ 65)",
        x=categories,
        y=hp_vals,
        marker_color=RR_PINK,
        text=[f"{v:.1f}" for v in hp_vals],
        textposition="outside"
    ))
    
    fig.add_trace(go.Bar(
        name="Normal Match State",
        x=categories,
        y=norm_vals,
        marker_color=RR_BLUE,
        text=[f"{v:.1f}" for v in norm_vals],
        textposition="outside"
    ))
    
    fig.update_layout(
        title=dict(text=f"{row['player_name']}: Pressure vs Normal Comparison", font=dict(size=15)),
        barmode="group",
        yaxis_title="Metric Value",
        height=380
    )
    return apply_rr_theme(fig)


def plot_player_radar(players_df: pd.DataFrame, is_batter: bool = True) -> go.Figure:
    """Interactive radar chart comparing multiple players across 5 core normalized performance axes."""
    fig = go.Figure()
    
    colors = [RR_PINK, RR_ELECTRIC, RR_GOLD, RR_CYAN, "#D500F9"]
    
    if is_batter:
        categories = [
            "Scoring Rate", "Survival / Avg", "Boundary Pct",
            "Clutch Delta", "Consistency"
        ]
        cols = ["sub_scoring_rate", "sub_survival", "sub_boundary_dot", "sub_clutch_delta", "sub_consistency"]
    else:
        categories = [
            "Containment / Econ", "Breakthrough / SR", "Dot Creation",
            "Clutch Delta", "Consistency"
        ]
        cols = ["sub_containment", "sub_wicket_threat", "sub_dot_suppress", "sub_clutch_delta", "sub_consistency"]
        
    for i, (_, row) in enumerate(players_df.iterrows()):
        color = colors[i % len(colors)]
        values = [row.get(c, 50.0) for c in cols]
        # Close radar loop
        values_closed = values + [values[0]]
        cat_closed = categories + [categories[0]]
        
        fig.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=cat_closed,
            fill="toself",
            name=row["player_name"],
            line_color=color,
            opacity=0.7
        ))
        
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor=GRID_COLOR, tickfont=dict(size=9)),
            angularaxis=dict(gridcolor=GRID_COLOR)
        ),
        title=dict(text="Multi-Dimensional Pressure Reliability Profile", font=dict(size=16)),
        height=480
    )
    return apply_rr_theme(fig)


def plot_phase_breakdown(df: pd.DataFrame) -> go.Figure:
    """Distribution of high-pressure deliveries by innings phase (Powerplay, Middle, Death, Super Over)."""
    phase_bat = df[df["is_high_pressure_bat"]]["phase"].value_counts().reset_index()
    phase_bat.columns = ["phase", "hp_bat_deliveries"]
    
    phase_bowl = df[df["is_high_pressure_bowl"]]["phase"].value_counts().reset_index()
    phase_bowl.columns = ["phase", "hp_bowl_deliveries"]
    
    merged = phase_bat.merge(phase_bowl, on="phase", how="outer").fillna(0)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=merged["phase"],
        y=merged["hp_bat_deliveries"],
        name="HP Batting Balls",
        marker_color=RR_PINK
    ))
    fig.add_trace(go.Bar(
        x=merged["phase"],
        y=merged["hp_bowl_deliveries"],
        name="HP Bowling Balls",
        marker_color=RR_BLUE
    ))
    
    fig.update_layout(
        title=dict(text="High-Pressure Delivery Occurrence by Match Phase", font=dict(size=15)),
        barmode="group",
        xaxis_title="Match Phase",
        yaxis_title="High-Pressure Deliveries",
        height=380
    )
    return apply_rr_theme(fig)


def plot_ipl_vs_combined_scores(
    dossier_df: pd.DataFrame,
    category: str = "Batter"
) -> go.Figure:
    """Grouped bar chart comparing Combined Score vs IPL Score for shortlisted players."""
    sub = dossier_df[dossier_df["category"] == category].dropna(subset=["ipl_score"]).copy()
    sub = sub.sort_values(by="ipl_score", ascending=True)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=sub["player_name"],
        x=sub["comb_score"],
        name="Combined (IPL + T20I)",
        orientation="h",
        marker_color="rgba(139, 148, 158, 0.7)",
        hovertemplate="<b>%{y}</b><br>Combined Score: %{x:.1f}<extra></extra>"
    ))
    
    fig.add_trace(go.Bar(
        y=sub["player_name"],
        x=sub["ipl_score"],
        name="IPL-Only Reliability",
        orientation="h",
        marker_color=RR_PINK if category == "Batter" else RR_BLUE,
        hovertemplate="<b>%{y}</b><br>IPL-Only Score: %{x:.1f}<extra></extra>"
    ))
    
    fig.update_layout(
        title=dict(text=f"Overall vs IPL-Specific Reliability Score ({category}s)", font=dict(size=15)),
        barmode="group",
        xaxis_title="Reliability Score (0â€“100)",
        yaxis_title="Player",
        height=max(360, len(sub) * 36)
    )
    return apply_rr_theme(fig)


def plot_phase_allocation_stacked(
    dossier_df: pd.DataFrame,
    category: str = "Batter"
) -> go.Figure:
    """100% stacked bar chart showing each player's phase distribution (Powerplay, Middle, Death)."""
    sub = dossier_df[dossier_df["category"] == category].copy()
    sub = sub.sort_values(by="death_pct", ascending=True)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=sub["player_name"],
        x=sub["powerplay_pct"],
        name="Powerplay (Overs 1-6)",
        orientation="h",
        marker_color="#2ECC71",
        hovertemplate="<b>%{y}</b><br>Powerplay: %{x:.1f}%<extra></extra>"
    ))
    
    fig.add_trace(go.Bar(
        y=sub["player_name"],
        x=sub["middle_pct"],
        name="Middle (Overs 7-15)",
        orientation="h",
        marker_color="#F39C12",
        hovertemplate="<b>%{y}</b><br>Middle: %{x:.1f}%<extra></extra>"
    ))
    
    fig.add_trace(go.Bar(
        y=sub["player_name"],
        x=sub["death_pct"],
        name="Death (Overs 16-20)",
        orientation="h",
        marker_color=RR_PINK if category == "Batter" else RR_BLUE,
        hovertemplate="<b>%{y}</b><br>Death: %{x:.1f}%<extra></extra>"
    ))
    
    fig.update_layout(
        title=dict(text=f"Phase Concentration in High-Pressure Deliveries ({category}s)", font=dict(size=15)),
        barmode="stack",
        xaxis=dict(title="Percentage of HP Deliveries (%)", range=[0, 100]),
        yaxis_title="Player",
        height=max(380, len(sub) * 32)
    )
    return apply_rr_theme(fig)


def plot_single_player_split(
    splits: Dict[str, Dict[str, Any]],
    player_name: str,
    is_batter: bool = True
) -> go.Figure:
    """Side-by-side grouped bar chart comparing IPL vs T20I for a single player."""
    categories = ["IPL", "T20I", "Combined"]
    
    if is_batter:
        srs = [splits[c].get("hp_sr", 0.0) for c in categories]
        avgs = [splits[c].get("hp_avg", 0.0) for c in categories]
        balls = [splits[c].get("hp_balls", 0) for c in categories]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=categories,
            y=srs,
            name="HP Strike Rate",
            marker_color=RR_PINK,
            text=[f"{v:.1f}" if v > 0 else "N/A" for v in srs],
            textposition="auto"
        ))
        fig.add_trace(go.Bar(
            x=categories,
            y=avgs,
            name="HP Average",
            marker_color=RR_BLUE,
            text=[f"{v:.1f}" if v > 0 else "N/A" for v in avgs],
            textposition="auto"
        ))
        
        fig.update_layout(
            title=dict(text=f"{player_name} â€” Competition Performance Breakdown (HP)", font=dict(size=15)),
            barmode="group",
            yaxis_title="Metric Value",
            height=340
        )
    else:
        econs = [splits[c].get("hp_economy", 0.0) for c in categories]
        wkts = [splits[c].get("hp_wickets", 0) for c in categories]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=categories,
            y=econs,
            name="HP Economy Rate",
            marker_color=RR_CYAN,
            text=[f"{v:.2f}" if v > 0 else "N/A" for v in econs],
            textposition="auto"
        ))
        fig.add_trace(go.Bar(
            x=categories,
            y=wkts,
            name="HP Wickets",
            marker_color=RR_GOLD,
            text=[f"{v}" if v > 0 else "0" for v in wkts],
            textposition="auto"
        ))
        
        fig.update_layout(
            title=dict(text=f"{player_name} â€” Competition Performance Breakdown (HP)", font=dict(size=15)),
            barmode="group",
            yaxis_title="Metric Value",
            height=340
        )
        
    return apply_rr_theme(fig)


