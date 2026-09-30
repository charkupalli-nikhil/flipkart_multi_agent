"""
Flipkart Sales Intelligence System - Streamlit UI Components
Provides reusable high-contrast visual elements for KPIs, agent traces, and charts.
"""

import json
import uuid
import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio
from tools.sales_tools import get_kpi_summary

def render_kpi_header(custom_df=None):
    """Renders high-contrast executive KPI header cards."""
    if custom_df is None:
        kpis = get_kpi_summary()
        rev_str = kpis['formatted_revenue']
        prof_str = kpis['formatted_profit']
        margin_pct = kpis['profit_margin_pct']
        orders_count = kpis['total_orders']
        units_count = kpis['total_units_sold']
        aov_str = kpis['formatted_aov']
        rating_val = kpis['average_customer_rating']
    else:
        tot_rev = float(custom_df["Total Sales (INR)"].sum())
        tot_prof = float(custom_df["Profit (INR)"].sum())
        margin_pct = round((tot_prof / tot_rev) * 100, 2) if tot_rev > 0 else 0.0
        orders_count = len(custom_df)
        units_count = int(custom_df["Quantity Sold"].sum())
        aov_str = f"₹{(tot_rev / orders_count):,.2f}" if orders_count > 0 else "₹0.00"
        rating_val = round(float(custom_df["Customer Rating"].mean()), 2)
        rev_str = f"₹{tot_rev:,.2f}"
        prof_str = f"₹{tot_prof:,.2f}"

    html = f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-label">Total Revenue</div>
            <div class="kpi-value">{rev_str}</div>
            <div class="kpi-subtext">Across Catalog</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Total Net Profit</div>
            <div class="kpi-value">{prof_str}</div>
            <div class="kpi-subtext">Margin: {margin_pct}%</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Gross Margin %</div>
            <div class="kpi-value">{margin_pct}%</div>
            <div class="kpi-subtext">Healthy Baseline</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Orders & Volume</div>
            <div class="kpi-value">{orders_count:,} <span style="font-size: 0.9rem; color: #94A3B8;">({units_count:,} units)</span></div>
            <div class="kpi-subtext">AOV: {aov_str}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Avg Customer Rating</div>
            <div class="kpi-value">★ {rating_val} <span style="font-size: 0.9rem; color: #94A3B8;">/ 5.0</span></div>
            <div class="kpi-subtext">Verified Reviews</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_reasoning_trace(tool_traces: list, routing_decision: list):
    """Renders an interactive reasoning trace expander showing agent execution steps."""
    if not tool_traces and not routing_decision:
        return
        
    badge_map = {
        "sales": ("📊 Sales Analytics", "badge-sales"),
        "profit": ("💰 Profit Optimization", "badge-profit"),
        "advisor": ("🔮 Business Advisor", "badge-advisor")
    }
    
    badges_html = " ".join([
        f'<span class="badge-pill {badge_map.get(r, ("Specialist Agent", "badge-sales"))[1]}">{badge_map.get(r, (r.title(), "badge-sales"))[0]}</span>'
        for r in routing_decision
    ])
    
    with st.expander(f"🔍 Multi-Agent Reasoning Trace ({len(tool_traces)} Tool Executions)", expanded=False):
        st.markdown(f"**Dispatched Specialist Agents:** {badges_html}", unsafe_allow_html=True)
        st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 10px 0;'>", unsafe_allow_html=True)
        
        for idx, trace in enumerate(tool_traces, 1):
            agent_name = trace.get("agent", "Specialist Agent")
            tool_name = trace.get("tool", "Unknown Tool")
            status = trace.get("status", "success")
            exec_time = trace.get("execution_time_sec", 0.0)
            status_icon = "🟢" if status == "success" else "🔴"
            
            st.markdown(
                f"**Step {idx}:** {status_icon} `<span style='color:#38BDF8; font-family:JetBrains Mono;'>{tool_name}</span>` &nbsp;|&nbsp; "
                f"**Agent:** <span style='color:#A5B4FC; font-weight:600;'>{agent_name}</span> &nbsp;|&nbsp; "
                f"⏱️ `<span style='color:#FDE68A;'>{exec_time}s</span>`",
                unsafe_allow_html=True
            )
            
            params = trace.get("parameters", {})
            if params.get("kwargs"):
                st.caption(f"Input Parameters: `{params['kwargs']}`")
            elif params.get("args"):
                st.caption(f"Input Parameters: `{params['args']}`")

def render_chart(chart_dict: dict, chart_key: str = None):
    """Renders a Plotly figure from chart metadata with unique key to prevent duplicate ID errors."""
    if not chart_dict:
        return
        
    unique_key = chart_key or f"chart_{uuid.uuid4().hex[:10]}"
    try:
        fig_json = chart_dict.get("figure_json")
        if fig_json:
            fig = pio.from_json(fig_json)
            st.plotly_chart(fig, use_container_width=True, key=unique_key)
        elif "file_path" in chart_dict and chart_dict["file_path"]:
            with open(chart_dict["file_path"], "r", encoding="utf-8") as f:
                fig = pio.from_json(f.read())
                st.plotly_chart(fig, use_container_width=True, key=unique_key)
    except Exception as e:
        st.warning(f"Unable to render chart visual: {e}")
