"""
Power BI-Style Visualizations & Cross-Filtering Helpers for Executive Overview.
Implements interactive horizontal leaderboards, pressure performance scatter plots,
5-band pressure heatmaps, competition comparisons, phase donuts, and season trends.
"""

from typing import Optional, Dict, Any, List, Tuple
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from src.visualizations import (
    apply_rr_theme, RR_PINK, RR_BLUE, RR_ELECTRIC, RR_NAVY,
    RR_CARD_BG, RR_WHITE, RR_MUTED, RR_GOLD, RR_GREEN, GRID_COLOR
)


def build_pbi_leaderboard_chart(
    ranked_df: pd.DataFrame,
    is_batter: bool = True,
    selected_player: Optional[str] = None,
    top_n: int = 10
) -> go.Figure:
    """
    Build interactive horizontal bar chart for the Top N players.
    Supports click cross-filtering and visually accents the selected player.
    """
    if ranked_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No players qualify under current filter parameters", showarrow=False, font=dict(color=RR_MUTED, size=14))
        return apply_rr_theme(fig)

    # Filter to eligible and take top N
    df = ranked_df.copy()
    if "rank" not in df.columns:
        df = df.sort_values("reliability_score", ascending=False).reset_index(drop=True)
        df["rank"] = df.index + 1
        
    if "is_eligible" in df.columns:
        eligible = df[df["is_eligible"]].head(top_n).copy()
        if eligible.empty:
            eligible = df.head(top_n).copy()
    else:
        # Pre-ranked dataframe already containing eligible entries
        eligible = df.head(top_n).copy()
        
    # Sort ascending for horizontal bar chart (top rank on top)
    eligible = eligible.sort_values("reliability_score", ascending=True).reset_index(drop=True)
    
    # Setup bar colors: accent selected player if active
    bar_colors = []
    base_color = RR_PINK if is_batter else RR_ELECTRIC
    
    for p in eligible["player_name"]:
        if selected_player and p == selected_player:
            bar_colors.append(RR_GOLD)  # Bright gold for selected player
        elif selected_player:
            bar_colors.append("rgba(230, 0, 126, 0.40)" if is_batter else "rgba(40, 123, 255, 0.40)")
        else:
            bar_colors.append(base_color)
            
    # Text labels
    opp_col = "hp_balls" if is_batter else "hp_legal_balls"
    if opp_col not in eligible.columns:
        alt_col = "total_balls" if is_batter else "total_legal_balls"
        if alt_col in eligible.columns:
            eligible[opp_col] = eligible[alt_col]
        else:
            eligible[opp_col] = 0

    labels = [
        f"<b>{score:.1f}</b> <span style='font-size:10px; color:{RR_MUTED};'>({int(b)}b)</span>"
        for score, b in zip(eligible["reliability_score"], eligible[opp_col])
    ]
    
    sr_or_econ = eligible["hp_strike_rate"] if (is_batter and "hp_strike_rate" in eligible.columns) else (
        eligible["hp_economy"] if ("hp_economy" in eligible.columns) else np.zeros(len(eligible))
    )
    ci_low = eligible["ci_lower"] if "ci_lower" in eligible.columns else np.zeros(len(eligible))
    ci_upp = eligible["ci_upper"] if "ci_upper" in eligible.columns else np.zeros(len(eligible))

    custom_data = np.stack((
        eligible["player_name"],
        eligible["rank"],
        eligible["reliability_score"],
        eligible[opp_col],
        sr_or_econ,
        ci_low,
        ci_upp
    ), axis=-1)
    
    fig = go.Figure(go.Bar(
        x=eligible["reliability_score"],
        y=eligible["player_name"],
        orientation="h",
        marker=dict(
            color=bar_colors,
            line=dict(
                color=[RR_WHITE if (selected_player and p == selected_player) else "rgba(0,0,0,0)" for p in eligible["player_name"]],
                width=[2 if (selected_player and p == selected_player) else 0 for p in eligible["player_name"]]
            )
        ),
        text=labels,
        textposition="outside",
        customdata=custom_data,
        hovertemplate=(
            "<b>%{customdata[0]}</b> (Rank #%{customdata[1]})<br/>"
            "Reliability Score: <b>%{customdata[2]:.1f} / 100</b><br/>"
            "95% CI: [%{customdata[5]:.1f} - %{customdata[6]:.1f}]<br/>"
            "High-Pressure Balls: %{customdata[3]}<br/>"
            + ("HP Strike Rate: %{customdata[4]:.1f}<br/>" if is_batter else "HP Economy: %{customdata[4]:.2f} RPO<br/>")
            + "<extra></extra>"
        )
    ))
    
    # Highlight badge in title if player is focused
    title_text = f"Top {len(eligible)} {'Batters' if is_batter else 'Bowlers'} by Reliability Score"
    if selected_player:
        title_text += f" <span style='color:{RR_GOLD}; font-size:12px;'>[★ Focusing: {selected_player}]</span>"
        
    fig.update_layout(
        title=dict(text=title_text, font=dict(size=14, color=RR_WHITE)),
        xaxis=dict(title="Composite Reliability Score (0–100)", range=[0, 105]),
        yaxis=dict(title="", tickfont=dict(size=11, color=RR_WHITE)),
        height=380,
        margin=dict(l=120, r=40, t=45, b=35)
    )
    return apply_rr_theme(fig)


def build_pbi_scatter_chart(
    ranked_df: pd.DataFrame,
    is_batter: bool = True,
    selected_player: Optional[str] = None
) -> go.Figure:
    """
    Build 2D Pressure Performance scatter plot.
    Batters: HP Balls vs HP Strike Rate (bubble = HP runs).
    Bowlers: HP Balls vs HP Economy (inverted Y-axis, bubble = HP wickets).
    """
    if ranked_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No player data available", showarrow=False, font=dict(color=RR_MUTED, size=14))
        return apply_rr_theme(fig)

    eligible = ranked_df[ranked_df["is_eligible"]].copy()
    if len(eligible) < 5:
        eligible = ranked_df.head(20).copy()

    x_col = "hp_balls" if is_batter else "hp_legal_balls"
    y_col = "hp_strike_rate" if is_batter else "hp_economy"
    size_col = "hp_runs" if is_batter else "hp_wickets"
    
    # Custom hover formatting
    custom_data = np.stack((
        eligible["player_name"],
        eligible["reliability_score"],
        eligible[x_col],
        eligible[y_col],
        eligible[size_col],
        eligible["sr_delta"] if is_batter else eligible["econ_delta"]
    ), axis=-1)

    fig = go.Figure(go.Scatter(
        x=eligible[x_col],
        y=eligible[y_col],
        mode="markers",
        marker=dict(
            size=np.clip(eligible[size_col] * (0.12 if is_batter else 1.2) + 7, 7, 28),
            color=eligible["reliability_score"],
            colorscale=[[0, RR_BLUE], [0.5, RR_ELECTRIC], [1, RR_PINK]],
            showscale=True,
            colorbar=dict(
                title=dict(text="Score", font=dict(size=10, color=RR_MUTED)),
                thickness=10,
                len=0.7,
                tickfont=dict(size=9, color=RR_MUTED)
            ),
            line=dict(color=RR_CARD_BG, width=1)
        ),
        customdata=custom_data,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br/>"
            "Reliability Score: <b>%{customdata[1]:.1f}</b><br/>"
            f"{'HP Balls' if is_batter else 'HP Legal Balls'}: %{{customdata[2]}}<br/>"
            + (f"HP Strike Rate: %{{customdata[3]:.1f}}<br/>HP Runs: %{{customdata[4]}}<br/>SR Delta: %{{customdata[5]:+.1f}}"
               if is_batter else
               f"HP Economy: %{{customdata[3]:.2f}} RPO<br/>HP Wickets: %{{customdata[4]:.0f}}<br/>Econ Delta: %{{customdata[5]:+.2f}}")
            + "<extra></extra>"
        )
    ))

    # Invert Y-axis for bowling economy so lower economy (elite) is at top!
    if not is_batter:
        fig.update_yaxes(autorange="reversed")
        benchmark_y = 8.5
        benchmark_text = "Benchmark Econ (8.5 RPO)"
    else:
        benchmark_y = 150.0
        benchmark_text = "Benchmark SR (150.0)"

    fig.add_hline(
        y=benchmark_y,
        line_dash="dot",
        line_color=RR_MUTED,
        annotation_text=benchmark_text,
        annotation_font=dict(size=9, color=RR_MUTED)
    )

    # Accent selected player if present
    if selected_player and selected_player in eligible["player_name"].values:
        p_row = eligible[eligible["player_name"] == selected_player].iloc[0]
        fig.add_trace(go.Scatter(
            x=[p_row[x_col]],
            y=[p_row[y_col]],
            mode="markers+text",
            marker=dict(
                size=22,
                color=RR_GOLD,
                symbol="star",
                line=dict(color=RR_PINK, width=2.5)
            ),
            name="Selected Player",
            text=[f"★ {selected_player}"],
            textposition="top center",
            textfont=dict(color=RR_GOLD, size=11, family="Inter"),
            hoverinfo="skip",
            showlegend=False
        ))

    fig.update_layout(
        title=dict(
            text=f"Pressure Execution Matrix ({'Strike Rate vs HP Balls' if is_batter else 'Economy vs HP Balls'})",
            font=dict(size=14, color=RR_WHITE)
        ),
        xaxis=dict(title=f"High-Pressure Deliveries ({'Balls Faced' if is_batter else 'Legal Balls Bowled'})"),
        yaxis=dict(title=f"High-Pressure {'Strike Rate' if is_batter else 'Economy (Inverted: Top is Elite)'}"),
        height=380,
        margin=dict(l=50, r=40, t=45, b=35)
    )
    return apply_rr_theme(fig)


def build_pbi_heatmap_chart(
    deliv_df: pd.DataFrame,
    ranked_df: pd.DataFrame,
    is_batter: bool = True,
    selected_player: Optional[str] = None,
    top_n: int = 8
) -> go.Figure:
    """
    Build Pressure Band Heatmap:
    Rows = Selected / Top Players, Columns = 5 Pressure Bands.
    Metric: Strike Rate for Batters, Economy for Bowlers.
    """
    bins = [0, 50, 65, 75, 85, 100.1]
    labels = ["Low (<50)", "Moderate (50-64)", "High (65-74)", "Very High (75-84)", "Extreme (85+)"]
    
    # Choose players to display
    top_players = ranked_df.head(top_n)["player_name"].tolist() if not ranked_df.empty else []
    if selected_player and selected_player not in top_players:
        top_players = [selected_player] + top_players[:top_n - 1]
    elif selected_player and selected_player in top_players:
        # Move selected player to top
        top_players.remove(selected_player)
        top_players = [selected_player] + top_players

    if not top_players:
        fig = go.Figure()
        fig.add_annotation(text="No player data for heatmap", showarrow=False, font=dict(color=RR_MUTED, size=14))
        return apply_rr_theme(fig)

    player_col = "striker_name" if is_batter else "bowler_name"
    pressure_col = "pressure_batting" if is_batter else "pressure_bowling"
    
    sub = deliv_df[deliv_df[player_col].isin(top_players)].copy()
    if sub.empty:
        fig = go.Figure()
        fig.add_annotation(text="Insufficient deliveries for heatmap", showarrow=False, font=dict(color=RR_MUTED, size=14))
        return apply_rr_theme(fig)

    sub["band"] = pd.cut(sub[pressure_col], bins=bins, labels=labels, right=False)

    if is_batter:
        heat_data = sub.groupby([player_col, "band"], observed=False).agg(
            runs=("runs_batter", "sum"),
            balls=("is_ball_faced_batter", "sum")
        ).reset_index()
        heat_data["val"] = np.where(heat_data["balls"] > 0, (heat_data["runs"] / heat_data["balls"]) * 100.0, np.nan)
        metric_label = "Strike Rate"
        val_format = "{:.1f}"
        colorscale = [[0, RR_BLUE], [0.5, RR_ELECTRIC], [1, RR_PINK]]
    else:
        heat_data = sub.groupby([player_col, "band"], observed=False).agg(
            runs=("runs_bowler", "sum"),
            balls=("is_legal_ball_bowler", "sum")
        ).reset_index()
        heat_data["val"] = np.where(heat_data["balls"] >= 6, (heat_data["runs"] / (heat_data["balls"] / 6.0)), np.nan)
        metric_label = "Economy RPO"
        val_format = "{:.2f}"
        # For bowlers, lower economy is better (inverted colorscale: Blue is best)
        colorscale = [[0, RR_PINK], [0.5, RR_ELECTRIC], [1, RR_BLUE]]

    # Reindex to guarantee exact order
    pivot = heat_data.pivot(index=player_col, columns="band", values="val")
    pivot = pivot.reindex(index=top_players[::-1], columns=labels)  # Inverted for top-to-bottom display

    # Build annotations text and hover info
    text_matrix = []
    hover_matrix = []
    
    # Pre-aggregate balls for hover
    balls_pivot = heat_data.pivot(index=player_col, columns="band", values="balls").reindex(index=top_players[::-1], columns=labels).fillna(0)
    runs_pivot = heat_data.pivot(index=player_col, columns="band", values="runs").reindex(index=top_players[::-1], columns=labels).fillna(0)

    for p in top_players[::-1]:
        text_row = []
        hover_row = []
        for b in labels:
            val = pivot.loc[p, b] if p in pivot.index and b in pivot.columns else np.nan
            balls = balls_pivot.loc[p, b] if p in balls_pivot.index and b in balls_pivot.columns else 0
            runs = runs_pivot.loc[p, b] if p in runs_pivot.index and b in runs_pivot.columns else 0
            
            if pd.isna(val):
                text_row.append("—")
                hover_row.append(f"<b>{p}</b><br/>Band: {b}<br/>Deliveries: 0 (No sample)<extra></extra>")
            else:
                text_row.append(val_format.format(val))
                hover_row.append(
                    f"<b>{p}</b><br/>"
                    f"Band: {b}<br/>"
                    f"{metric_label}: <b>{val_format.format(val)}</b><br/>"
                    f"Runs: {int(runs)} | Deliveries: {int(balls)}"
                    "<extra></extra>"
                )
        text_matrix.append(text_row)
        hover_matrix.append(hover_row)

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=labels,
        y=top_players[::-1],
        colorscale=colorscale,
        showscale=True,
        colorbar=dict(
            title=dict(text=metric_label, font=dict(size=10, color=RR_MUTED)),
            thickness=10,
            len=0.7,
            tickfont=dict(size=9, color=RR_MUTED)
        ),
        text=text_matrix,
        texttemplate="%{text}",
        hoverinfo="text",
        hovertext=hover_matrix
    ))

    fig.update_layout(
        title=dict(text=f"Pressure Band Heatmap ({metric_label} Across Match States)", font=dict(size=14, color=RR_WHITE)),
        xaxis=dict(title="Match Pressure Band (0–100)", tickfont=dict(size=11, color=RR_WHITE)),
        yaxis=dict(title="", tickfont=dict(size=11, color=RR_WHITE)),
        height=380,
        margin=dict(l=120, r=40, t=45, b=35)
    )
    return apply_rr_theme(fig)


def build_pbi_comp_comparison_chart(
    deliv_df: pd.DataFrame,
    is_batter: bool = True
) -> go.Figure:
    """
    Build grouped bar chart comparing performance in IPL vs T20I vs Other T20.
    Normal (<65) vs High-Pressure (≥65).
    """
    pressure_col = "is_high_pressure_bat" if is_batter else "is_high_pressure_bowl"
    runs_col = "runs_batter" if is_batter else "runs_bowler"
    opp_col = "is_ball_faced_batter" if is_batter else "is_legal_ball_bowler"
    
    comp_metrics = deliv_df.groupby(["competition_type", pressure_col]).agg(
        runs=(runs_col, "sum"),
        balls=(opp_col, "sum")
    ).reset_index()
    
    if comp_metrics.empty:
        fig = go.Figure()
        fig.add_annotation(text="No competition data available", showarrow=False, font=dict(color=RR_MUTED, size=14))
        return apply_rr_theme(fig)

    if is_batter:
        comp_metrics["metric_val"] = (comp_metrics["runs"] / comp_metrics["balls"]) * 100.0
        y_title = "Batting Strike Rate"
        val_format = "{:.1f}"
    else:
        comp_metrics["metric_val"] = comp_metrics["runs"] / (comp_metrics["balls"] / 6.0)
        y_title = "Bowling Economy (RPO)"
        val_format = "{:.2f}"
        
    comp_metrics["situation"] = np.where(comp_metrics[pressure_col], "High Pressure (≥65)", "Normal (<65)")
    
    fig = px.bar(
        comp_metrics,
        x="competition_type",
        y="metric_val",
        color="situation",
        barmode="group",
        color_discrete_map={
            "High Pressure (≥65)": RR_PINK,
            "Normal (<65)": RR_BLUE
        },
        hover_data={"runs": True, "balls": True, "metric_val": ":.2f"}
    )
    
    fig.update_layout(
        title=dict(text=f"Competition Comparison ({y_title} by Match State)", font=dict(size=14, color=RR_WHITE)),
        xaxis=dict(title="Competition Scope"),
        yaxis=dict(title=y_title),
        legend=dict(
            title="",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10, color=RR_WHITE)
        ),
        height=380,
        margin=dict(l=50, r=40, t=55, b=35)
    )
    return apply_rr_theme(fig)


def build_pbi_distribution_chart(
    deliv_df: pd.DataFrame,
    is_batter: bool = True
) -> go.Figure:
    """
    Build donut chart showing Match Phase Breakdown under High Pressure
    (Death, Middle, Powerplay, Super Over).
    """
    pressure_col = "is_high_pressure_bat" if is_batter else "is_high_pressure_bowl"
    hp_df = deliv_df[deliv_df[pressure_col]].copy()
    
    if hp_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No high pressure deliveries in slice", showarrow=False, font=dict(color=RR_MUTED, size=14))
        return apply_rr_theme(fig)

    phase_counts = hp_df["phase"].value_counts().reset_index()
    phase_counts.columns = ["Phase", "Deliveries"]
    
    color_map = {
        "Death": RR_PINK,
        "Middle": RR_ELECTRIC,
        "Powerplay": RR_BLUE,
        "Super Over": RR_GOLD
    }
    
    fig = go.Figure(go.Pie(
        labels=phase_counts["Phase"],
        values=phase_counts["Deliveries"],
        hole=0.55,
        marker=dict(
            colors=[color_map.get(p, RR_MUTED) for p in phase_counts["Phase"]],
            line=dict(color=RR_CARD_BG, width=2)
        ),
        textinfo="label+percent",
        textfont=dict(size=11, color=RR_WHITE),
        hovertemplate="<b>%{label}</b><br/>High-Pressure Deliveries: %{value:,}<br/>Share: %{percent}<extra></extra>"
    ))
    
    fig.add_annotation(
        text=f"<b>{len(hp_df):,}</b><br/><span style='font-size:10px; color:{RR_MUTED};'>HP Balls</span>",
        x=0.5, y=0.5,
        font=dict(size=14, color=RR_WHITE),
        showarrow=False
    )
    
    fig.update_layout(
        title=dict(text="High-Pressure Phase Allocation (Match Distribution)", font=dict(size=14, color=RR_WHITE)),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(size=10, color=RR_MUTED)
        ),
        height=380,
        margin=dict(l=40, r=40, t=45, b=45)
    )
    return apply_rr_theme(fig)


def build_pbi_season_trends_chart(
    deliv_df: pd.DataFrame,
    is_batter: bool = True,
    selected_player: Optional[str] = None
) -> go.Figure:
    """
    Build multi-line chart showing season-by-season pressure performance trends (2022–2026).
    Compares cohort benchmark against the focused player if selected.
    """
    pressure_col = "is_high_pressure_bat" if is_batter else "is_high_pressure_bowl"
    runs_col = "runs_batter" if is_batter else "runs_bowler"
    opp_col = "is_ball_faced_batter" if is_batter else "is_legal_ball_bowler"
    
    hp_deliv = deliv_df[deliv_df[pressure_col]].copy()
    if hp_deliv.empty:
        fig = go.Figure()
        fig.add_annotation(text="No season trend data available", showarrow=False, font=dict(color=RR_MUTED, size=14))
        return apply_rr_theme(fig)

    # 1. Cohort baseline across seasons
    cohort_trend = hp_deliv.groupby("season").agg(
        runs=(runs_col, "sum"),
        balls=(opp_col, "sum")
    ).reset_index()
    
    if is_batter:
        cohort_trend["val"] = (cohort_trend["runs"] / cohort_trend["balls"]) * 100.0
        y_title = "High-Pressure Strike Rate"
        val_format = "{:.1f}"
    else:
        cohort_trend["val"] = cohort_trend["runs"] / (cohort_trend["balls"] / 6.0)
        y_title = "High-Pressure Economy (RPO)"
        val_format = "{:.2f}"
        
    fig = go.Figure()
    
    # Cohort Benchmark line
    fig.add_trace(go.Scatter(
        x=cohort_trend["season"],
        y=cohort_trend["val"],
        mode="lines+markers",
        name="Cohort Benchmark",
        line=dict(color=RR_ELECTRIC, width=2.5, dash="dot"),
        marker=dict(size=7, color=RR_ELECTRIC),
        hovertemplate="<b>Cohort Baseline (%{x})</b><br/>" + y_title + ": <b>%{y:.2f}</b><extra></extra>"
    ))
    
    # 2. Selected player trend line if active
    if selected_player:
        player_col = "striker_name" if is_batter else "bowler_name"
        p_sub = hp_deliv[hp_deliv[player_col] == selected_player]
        
        if not p_sub.empty:
            p_trend = p_sub.groupby("season").agg(
                runs=(runs_col, "sum"),
                balls=(opp_col, "sum")
            ).reset_index()
            
            if is_batter:
                p_trend["val"] = (p_trend["runs"] / p_trend["balls"]) * 100.0
            else:
                p_trend["val"] = p_trend["runs"] / (p_trend["balls"] / 6.0)
                
            fig.add_trace(go.Scatter(
                x=p_trend["season"],
                y=p_trend["val"],
                mode="lines+markers",
                name=f"★ {selected_player}",
                line=dict(color=RR_PINK, width=3.5),
                marker=dict(size=10, color=RR_GOLD, symbol="circle", line=dict(color=RR_WHITE, width=2)),
                hovertemplate=f"<b>{selected_player} (%{{x}})</b><br/>" + y_title + ": <b>%{{y:.2f}}</b><br/>Balls: %{text}<extra></extra>",
                text=p_trend["balls"]
            ))

    fig.update_layout(
        title=dict(text=f"Historical Season Trends (2022–2026 {y_title})", font=dict(size=14, color=RR_WHITE)),
        xaxis=dict(title="Cricket Season"),
        yaxis=dict(title=y_title),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10, color=RR_WHITE)
        ),
        height=380,
        margin=dict(l=50, r=40, t=55, b=35)
    )
    return apply_rr_theme(fig)


def build_player_spotlight_card_html(player_row: pd.Series, is_batter: bool = True) -> str:
    """Generate HTML card for the focused player with RR War Room styling."""
    p_name = player_row["player_name"]
    rank = player_row.get("rank", "N/A")
    score = player_row.get("reliability_score", 0.0)
    ci_lower = player_row.get("ci_lower", 0.0)
    ci_upper = player_row.get("ci_upper", 0.0)
    
    if is_batter:
        balls = player_row.get("hp_balls", 0)
        runs = player_row.get("hp_runs", 0)
        sr = player_row.get("hp_strike_rate", 0.0)
        avg = player_row.get("hp_average", 0.0)
        delta = player_row.get("sr_delta", 0.0)
        delta_str = f"{delta:+.1f} SR"
        primary_metric = f"HP SR: <b>{sr:.1f}</b>"
        secondary_metric = f"HP Avg: <b>{avg:.1f}</b>"
        accent_color = RR_PINK
    else:
        balls = player_row.get("hp_legal_balls", 0)
        runs = player_row.get("hp_runs_conceded", 0)
        econ = player_row.get("hp_economy", 0.0)
        wkts = player_row.get("hp_wickets", 0)
        delta = player_row.get("econ_delta", 0.0)
        delta_str = f"{delta:+.2f} Econ"
        primary_metric = f"HP Econ: <b>{econ:.2f} RPO</b>"
        secondary_metric = f"HP Wkts: <b>{int(wkts)}</b>"
        accent_color = RR_ELECTRIC

    return f"""
    <div style="background: linear-gradient(135deg, rgba(230,0,126,0.14) 0%, rgba(23,70,162,0.22) 100%); 
                border: 1px solid rgba(230,0,126,0.40); border-left: 5px solid {accent_color}; 
                border-radius: 12px; padding: 16px 22px; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(8,13,32,0.8);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <span class="rr-badge rr-badge-gold" style="font-size: 11px;">★ ACTIVE PLAYER SPOTLIGHT</span>
                <span class="rr-badge {'rr-badge-pink' if is_batter else 'rr-badge-blue'}" style="font-size: 11px;">RANK #{rank}</span>
                <div style="font-size: 22px; font-weight: 800; color: #F7F8FC; margin-top: 6px;">
                    {p_name}
                </div>
                <div style="font-size: 12px; color: #A8B3CC; margin-top: 2px;">
                    {primary_metric} | {secondary_metric} | HP Deliveries: <b>{int(balls)}</b> | Clutch Delta: <b style="color: {RR_GREEN if (is_batter and delta > 0) or (not is_batter and delta < 0) else RR_GOLD};">{delta_str}</b>
                </div>
            </div>
            <div style="text-align: right; margin-top: 4px;">
                <div style="font-size: 28px; font-weight: 900; color: {accent_color}; line-height: 1;">
                    {score:.1f}<span style="font-size: 14px; color: #A8B3CC;">/100</span>
                </div>
                <div style="font-size: 10px; font-weight: 700; color: #A8B3CC; letter-spacing: 0.8px;">
                    95% CI: [{ci_lower:.1f} – {ci_upper:.1f}]
                </div>
            </div>
        </div>
    </div>
    """
