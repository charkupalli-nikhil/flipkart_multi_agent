"""
Flipkart Sales Intelligence System - Streamlit UI Components
Provides reusable executive visual elements for KPIs, multi-agent traces, and Plotly charts.
"""

import json
import uuid
import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio
from tools.sales_tools import get_kpi_summary

def format_compact_inr(val: float) -> str:
    """Formats large monetary numbers cleanly for high-density executive cards."""
    if abs(val) >= 1e6:
        return f"₹{val/1e6:.2f}M"
    elif abs(val) >= 1e3:
        return f"₹{val/1e3:.1f}K"
    return f"₹{val:,.2f}"

def render_kpi_header(custom_df=None):
    """Renders executive KPI header cards with real-world metrics without Markdown escaping issues."""
    if custom_df is None:
        kpis = get_kpi_summary()
        tot_rev = kpis['total_revenue_inr']
        tot_prof = kpis.get('realized_profit_inr', kpis['total_profit_inr'])
        margin_pct = kpis['profit_margin_pct']
        orders_count = kpis['total_orders']
        units_count = kpis['total_units_sold']
        return_rate = kpis.get('return_rate_pct', 27.0)
        returned_orders = kpis.get('returned_orders', 36036)
        aov_str = kpis['formatted_aov']
        rating_val = kpis['average_customer_rating']
        sla_val = kpis.get('average_delivery_days', 9.5)
    else:
        tot_rev = float(custom_df["Total Sales (INR)"].sum())
        tot_prof_raw = float(custom_df["Profit (INR)"].sum())
        margin_pct = round((tot_prof_raw / tot_rev) * 100, 2) if tot_rev > 0 else 0.0
        orders_count = len(custom_df)
        units_count = int(custom_df["Quantity Sold"].sum())
        aov_str = f"₹{(tot_rev / orders_count):,.2f}" if orders_count > 0 else "₹0.00"
        rating_val = round(float(custom_df["Customer Rating"].mean()), 2)
        
        is_ret = custom_df["Is Returned"] if "Is Returned" in custom_df.columns else (custom_df["Status"] == "Returned")
        returned_orders = int(is_ret.sum())
        return_rate = round((returned_orders / orders_count) * 100, 2) if orders_count > 0 else 0.0
        
        tot_prof = float(custom_df["Realized Profit (INR)"].sum()) if "Realized Profit (INR)" in custom_df.columns else tot_prof_raw * (1 - return_rate/100)
        sla_val = round(float(custom_df["Delivery Days"].mean()), 1) if "Delivery Days" in custom_df.columns else 9.5

    rev_compact = format_compact_inr(tot_rev)
    prof_compact = format_compact_inr(tot_prof)
    exact_rev = f"₹{tot_rev:,.2f}"
    exact_prof = f"₹{tot_prof:,.2f}"

    # Build continuous HTML without blank lines or 4-space indents
    cards = [
        f'<div class="fk-kpi-card" title="Exact GMV: {exact_rev}"><div class="fk-card-bar bar-blue"></div><div class="fk-kpi-header"><span class="fk-kpi-title">Gross Revenue (GMV)</span><span class="fk-kpi-icon">💰</span></div><div class="fk-kpi-val">{rev_compact}</div><div class="fk-kpi-meta"><span class="fk-tag-pill tag-blue">6-Year Total</span><span>2015–2020</span></div></div>',
        f'<div class="fk-kpi-card" title="Exact Realized Profit: {exact_prof}"><div class="fk-card-bar bar-green"></div><div class="fk-kpi-header"><span class="fk-kpi-title">Realized Net Profit</span><span class="fk-kpi-icon">📈</span></div><div class="fk-kpi-val">{prof_compact}</div><div class="fk-kpi-meta"><span class="fk-tag-pill tag-green">Margin {margin_pct}%</span><span>Delivered</span></div></div>',
        f'<div class="fk-kpi-card"><div class="fk-card-bar bar-yellow"></div><div class="fk-kpi-header"><span class="fk-kpi-title">Orders & Volume</span><span class="fk-kpi-icon">📦</span></div><div class="fk-kpi-val">{orders_count:,}</div><div class="fk-kpi-meta"><span class="fk-tag-pill tag-yellow">{units_count:,} Units</span><span>AOV {aov_str}</span></div></div>',
        f'<div class="fk-kpi-card"><div class="fk-card-bar bar-orange"></div><div class="fk-kpi-header"><span class="fk-kpi-title">Return Rate</span><span class="fk-kpi-icon">🔄</span></div><div class="fk-kpi-val">{return_rate}%</div><div class="fk-kpi-meta"><span class="fk-tag-pill tag-red">{returned_orders:,} Returns</span><span>Leakage Lever</span></div></div>',
        f'<div class="fk-kpi-card"><div class="fk-card-bar bar-cyan"></div><div class="fk-kpi-header"><span class="fk-kpi-title">Avg Delivery SLA</span><span class="fk-kpi-icon">⏱️</span></div><div class="fk-kpi-val">{sla_val} <span style="font-size: 0.85rem; font-weight: 500; color: #94A3B8;">days</span></div><div class="fk-kpi-meta"><span class="fk-tag-pill tag-blue">Express: 3.5d</span><span>Std: 10d</span></div></div>',
        f'<div class="fk-kpi-card"><div class="fk-card-bar bar-purple"></div><div class="fk-kpi-header"><span class="fk-kpi-title">Customer Rating</span><span class="fk-kpi-icon">★</span></div><div class="fk-kpi-val">★ {rating_val} <span style="font-size: 0.85rem; font-weight: 500; color: #94A3B8;">/ 5.0</span></div><div class="fk-kpi-meta"><span class="fk-tag-pill tag-green">112k+ Buyers</span><span>Verified</span></div></div>'
    ]
    html = f'<div class="fk-kpi-grid">{"".join(cards)}</div>'
    st.markdown(html, unsafe_allow_html=True)

def render_copilot_badge():
    """Renders the official Flipkart AI Copilot response header."""
    header_html = (
        '<div class="fk-agent-msg-header">'
        '<div class="fk-agent-title-row">'
        '<div class="fk-agent-avatar">'
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
        '<path d="M6 2L3 6V20C3 20.5304 3.21071 21.0391 3.58579 21.4142C3.96086 21.7893 4.46957 22 5 22H19C19.5304 22 20.0391 21.7893 20.4142 21.4142C20.7893 21.0391 21 20.5304 21 20V6L18 2H6Z" stroke="#FFE11B" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
        '<line x1="3" y1="6" x2="21" y2="6" stroke="#FFE11B" stroke-width="2.2"/>'
        '<path d="M16 10C16 11.0609 15.5786 12.0783 14.8284 12.8284C14.0783 13.5786 13.0609 14 12 14C10.9391 14 9.92172 13.5786 9.17157 12.8284C8.42143 12.0783 8 11.0609 8 10" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
        '</svg>'
        '</div>'
        '<span class="fk-agent-name">Flipkart Commerce Copilot</span>'
        '<span class="fk-verified-badge">✓ Verified Flipkart AI</span>'
        '</div>'
        '<div class="fk-agent-meta">LangGraph • Gemini AI • 133,503 Records</div>'
        '</div>'
    )
    return header_html

def render_reasoning_trace(tool_traces: list, routing_decision: list):
    """Renders interactive multi-agent reasoning trace showing LangGraph execution steps."""
    if not tool_traces and not routing_decision:
        return
        
    badge_map = {
        "sales": ("📊 Flipkart Sales Specialist", "badge-sales"),
        "profit": ("💰 Flipkart Profit & Returns Specialist", "badge-profit"),
        "advisor": ("🔮 Flipkart Forecast & Strategy Advisor", "badge-advisor"),
        "rag": ("📚 Flipkart Policy & SLA RAG Specialist", "badge-rag")
    }
    
    badges_html = " ".join([
        f'<span class="agent-badge-pill {badge_map.get(r, ("Specialist Agent", "badge-sales"))[1]}">{badge_map.get(r, (r.title(), "badge-sales"))[0]}</span>'
        for r in routing_decision
    ])
    
    with st.expander(f"🧠 Multi-Agent Orchestration & Reasoning Trace ({len(tool_traces)} Tool Invocations)", expanded=False):
        st.markdown(f"**Dispatched Specialist Agents:** {badges_html}", unsafe_allow_html=True)
        st.markdown("<hr style='border-color: rgba(40,116,240,0.25); margin: 10px 0;'>", unsafe_allow_html=True)
        
        for idx, trace in enumerate(tool_traces, 1):
            agent_name = trace.get("agent", "Specialist Agent")
            tool_name = trace.get("tool", "Unknown Tool")
            status = trace.get("status", "success")
            exec_time = trace.get("execution_time_sec", 0.0)
            status_icon = "🟢" if status == "success" else "🔴"
            
            step_html = (
                f'<div class="trace-step-pill">'
                f'<span style="font-weight: 700; color: #FFFFFF;">Step {idx}:</span> {status_icon} '
                f'<span style="color:#38BDF8; font-family:\'JetBrains Mono\', monospace; font-weight:600;">{tool_name}</span> '
                f'&nbsp;|&nbsp; '
                f'<span style="color:#FFE11B; font-weight:600;">{agent_name}</span> '
                f'&nbsp;|&nbsp; '
                f'<span style="color:#A5B4FC; font-family:\'JetBrains Mono\', monospace;">⏱️ {exec_time}s</span>'
                f'</div>'
            )
            st.markdown(step_html, unsafe_allow_html=True)
            
            params = trace.get("parameters", {})
            if params.get("kwargs"):
                st.caption(f"Input Parameters: `{params['kwargs']}`")
            elif params.get("args"):
                st.caption(f"Input Parameters: `{params['args']}`")

def render_chart(chart_dict: dict, chart_key: str = None):
    """Renders Plotly chart from metadata with unique persistent keys."""
    if not chart_dict:
        return
        
    unique_key = chart_key or f"chart_{uuid.uuid4().hex[:10]}"
    try:
        fig_json = chart_dict.get("figure_json")
        if fig_json:
            fig = pio.from_json(fig_json)
            st.plotly_chart(fig, width="stretch", key=unique_key)
        elif "file_path" in chart_dict and chart_dict["file_path"]:
            with open(chart_dict["file_path"], "r", encoding="utf-8") as f:
                fig = pio.from_json(f.read())
                st.plotly_chart(fig, width="stretch", key=unique_key)
    except Exception as e:
        st.warning(f"Unable to render chart visual: {e}")
