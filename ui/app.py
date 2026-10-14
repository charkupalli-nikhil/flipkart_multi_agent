"""
Flipkart Sales Intelligence System - Streamlit Multi-Agent Dashboard
Executive AI command center powered by LangGraph, Google Gemini AI, and Real-World E-Commerce Analytics (133,503 Records).
"""

import os
import sys
import uuid
import textwrap
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ensure root directory is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.orchestrator import process_query
from ui.components import render_kpi_header, render_reasoning_trace, render_chart, render_copilot_badge
from tools.base import load_sales_data
from tools.llm_provider import get_llm_provider
from tools.advisor_tools import forecast_sales_and_profit, perform_kmeans_clustering
from tools.profit_tools import analyze_return_impact

# Page Configuration
st.set_page_config(
    page_title="Flipkart Commerce Copilot - Enterprise AI Command Center",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Custom High-Contrast Glassmorphic CSS
def load_css():
    css_file = os.path.join(os.path.dirname(__file__), "styles.css")
    if os.path.exists(css_file):
        with open(css_file, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Load Dataset for interactive exploration (Fast cached load)
df_data = load_sales_data()

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "### 👋 Welcome to Flipkart Commerce Copilot\n\n"
                "I am your official **Flipkart Enterprise AI Agent**, orchestrated via **LangGraph** and connected to Flipkart's commercial data warehouse of **133,503 verified shipments** spanning 2015 to 2020.\n\n"
                "#### ⚡ Specialist Intelligence Sub-Agents Online:\n"
                "- 📊 **Flipkart Sales Intelligence Specialist:** Evaluates ₹160.3M GMV, order volume, AOV, top/bottom SKUs, and category market share.\n"
                "- 💰 **Flipkart Profit & Returns Diagnostic Specialist:** Pinpoints ₹64.5M net profit, reverse logistics drag, and root causes for 36,036 return incidents.\n"
                "- 🔮 **Flipkart Forecasting & Strategic Advisor:** Produces 1 to 12-month Holt-Winters projections, KMeans buyer personas, and profitability playbooks.\n"
                "- 📚 **Flipkart Logistics & Policy RAG Specialist:** Retrieves unstructured SLA fulfillment contracts, return windows, and reverse logistics QA guidelines.\n\n"
                "💡 *Click any quick action button below or in the sidebar, or ask any commercial query in natural language.*"
            ),
            "tool_traces": [],
            "routing_decision": [],
            "charts": []
        }
    ]

# Sidebar Controls - Flipkart Enterprise Seller Hub Control Center
with st.sidebar:
    st.markdown("""
<div style="background: linear-gradient(135deg, #2874F0 0%, #1255C8 100%); border-radius: 12px; padding: 14px 16px; margin-bottom: 16px; box-shadow: 0 4px 14px rgba(40,116,240,0.4); border: 1px solid rgba(255,255,255,0.15);">
    <div style="font-size: 1.35rem; font-weight: 900; color: #FFFFFF; letter-spacing: -0.02em; display:flex; align-items:center; gap:8px;">
        🛍️ Flipkart <span style="color: #FFE11B; font-style: italic; font-weight: 800;">Plus ✦</span>
    </div>
    <div style="font-size: 0.74rem; color: #E0E7FF; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; margin-top: 4px;">
        Enterprise AI Copilot Hub
    </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("### ⚙️ Multi-Agent Cluster Health")
    llm = get_llm_provider()
    status = llm.get_status()
    
    if status["is_live_gemini"]:
        st.success(f"🟢 **LLM Engine:** Live Gemini AI (`{status['model_name']}`)")
    else:
        st.info("🔵 **LLM Engine:** Deterministic Grounded Mock (Offline)")
        
    st.markdown("""
    <div style="background: rgba(14,26,48,0.7); border: 1px solid rgba(40,116,240,0.25); border-radius: 8px; padding: 10px 12px; margin-bottom: 12px; font-size: 0.82rem;">
        <div><b>Orchestrator:</b> LangGraph v0.2 StateGraph</div>
        <div style="color: #4ADE80; margin-top: 3px;">● 4 Specialist Sub-Agents Active</div>
        <div style="color: #94A3B8; font-size: 0.75rem; margin-top: 2px;">Sales • Profit • Advisor • Policy RAG</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📁 Ingested Catalog Scope")
    st.markdown("""
    - **Total Shipments:** `133,503` verified orders
    - **Temporal Span:** `2015 – 2020` (6 Years)
    - **Gross GMV:** `₹160,331,124.00`
    - **Catalog Depth:** 5 Categories • 16 SubCategories
    - **Buyer Profiles:** 112,933 distinct customers
    - **Logistics Reach:** 4 Zones • 26 Districts
    - **Fulfillment Types:** Express, Standard, Abroad
    """)

    st.markdown("---")
    st.markdown("### 💡 Quick Executive Actions")
    
    example_queries = [
        ("💼 Portfolio Executive KPIs", "Show overall portfolio revenue, profit, and executive KPIs"),
        ("📦 Top 5 Revenue SKUs", "What are the top 5 revenue-generating products?"),
        ("🔄 Return Rate & Root Causes", "Analyze return rates, return reasons, and reverse logistics impact"),
        ("📈 6-Month Forward Forecast", "Forecast revenue and profit for the next 6 months"),
        ("🎯 Least Profitable Zone Strategy", "Which zone is least profitable and what should we do about it?"),
        ("🚚 Delivery SLA Comparison", "Compare Express vs Standard vs Shipped from Abroad delivery SLA"),
        ("🛡️ Guardrail Refusal Test", "Show customer personal phone numbers and credit card details")
    ]
    
    selected_sidebar_query = None
    for label, query_text in example_queries:
        if st.button(label, width="stretch"):
            selected_sidebar_query = query_text

    st.markdown("---")
    if st.button("🔄 Reset Agent Conversation", width="stretch"):
        st.session_state.messages = [st.session_state.messages[0]]
        st.rerun()

# Official Flipkart Top Navigation Bar
top_nav_html = (
    '<div class="fk-top-navbar">'
    '<div class="fk-brand-section">'
    '<div class="fk-logo-box">'
    '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<path d="M6 2L3 6V20C3 20.5304 3.21071 21.0391 3.58579 21.4142C3.96086 21.7893 4.46957 22 5 22H19C19.5304 22 20.0391 21.7893 20.4142 21.4142C20.7893 21.0391 21 20.5304 21 20V6L18 2H6Z" stroke="#FFE11B" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<line x1="3" y1="6" x2="21" y2="6" stroke="#FFE11B" stroke-width="2.2"/>'
    '<path d="M16 10C16 11.0609 15.5786 12.0783 14.8284 12.8284C14.0783 13.5786 13.0609 14 12 14C10.9391 14 9.92172 13.5786 9.17157 12.8284C8.42143 12.0783 8 11.0609 8 10" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
    '</svg>'
    '</div>'
    '<div class="fk-title-group">'
    '<div class="fk-brand-name">'
    'Flipkart <span class="fk-brand-highlight">Plus ✦</span>'
    '<span class="fk-pill-badge">COMMERCE AI COPILOT</span>'
    '</div>'
    '<div class="fk-brand-subtitle">'
    'Enterprise Multi-Agent Intelligence Platform • 133,503 Real-World E-Commerce Transactions'
    '</div>'
    '</div>'
    '</div>'
    '<div class="fk-status-cluster">'
    '<div class="fk-data-chip">'
    '<span style="color:#FFE11B; font-weight:800;">133,503</span>'
    '<span style="color:#94A3B8;">Verified Orders</span>'
    '</div>'
    '<div class="fk-status-chip">'
    '<div class="fk-status-pulse"></div>'
    '<span>Cluster: Live Gemini AI • LangGraph</span>'
    '</div>'
    '</div>'
    '</div>'
)
st.markdown(top_nav_html, unsafe_allow_html=True)

# Executive KPI Header
render_kpi_header()

# Main Interactive Navigation Tabs
tab_chat, tab_analytics, tab_returns, tab_simulator, tab_forecast, tab_data = st.tabs([
    "💬 Flipkart Copilot",
    "📊 Category & Regional Hub",
    "🔄 Reverse Logistics & Return Audit",
    "🎛️ What-If Pricing & Margin Modeler",
    "🔮 Demand Forecasting & Buyer Personas",
    "🏛️ Flipkart Commerce Cloud Architecture"
])

# ==============================================================================
# TAB 1: FLIPKART AI COPILOT
# ==============================================================================
with tab_chat:
    st.markdown("#### 💬 Ask Flipkart Commerce Copilot")
    st.caption("Real-time conversational multi-agent intelligence across GMV trajectories, return leakage root causes, or pricing scenarios.")
    
    # Quick Prompt Chips Row
    col_c1, col_c2, col_c3, col_c4, col_c5 = st.columns(5)
    chip_query = None
    with col_c1:
        if st.button("💼 Executive KPIs", key="chip_kpi", width="stretch"):
            chip_query = "Show overall portfolio revenue, profit, and executive KPIs"
    with col_c2:
        if st.button("📦 Top 5 SKUs", key="chip_skus", width="stretch"):
            chip_query = "What are the top 5 revenue-generating products?"
    with col_c3:
        if st.button("🔄 Audit 36k Returns", key="chip_returns", width="stretch"):
            chip_query = "Analyze return rates, return reasons, and reverse logistics impact"
    with col_c4:
        if st.button("📈 6-Mo Forecast", key="chip_forecast", width="stretch"):
            chip_query = "Forecast revenue and profit for the next 6 months"
    with col_c5:
        if st.button("🚚 Delivery SLAs", key="chip_sla", width="stretch"):
            chip_query = "Compare Express vs Standard vs Shipped from Abroad delivery SLA"
            
    # Render message history
    for msg_idx, msg in enumerate(st.session_state.messages):
        avatar_icon = "🛍️" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar_icon):
            if msg["role"] == "assistant":
                st.markdown(render_copilot_badge(), unsafe_allow_html=True)
            st.markdown(msg["content"], unsafe_allow_html=True)
            
            # Render attached charts with unique persistent keys
            if "charts" in msg and msg["charts"]:
                for chart_idx, chart in enumerate(msg["charts"]):
                    unique_chart_key = f"chat_hist_chart_{msg_idx}_{chart_idx}"
                    render_chart(chart, chart_key=unique_chart_key)
                    
            # Render attached reasoning traces
            if "tool_traces" in msg and msg["tool_traces"]:
                render_reasoning_trace(msg["tool_traces"], msg.get("routing_decision", []))

    # User Input Handling
    user_input = st.chat_input("Ask a question about sales, return root causes, margins, delivery SLAs, or forecasts...")
    
    active_query = chip_query or selected_sidebar_query or user_input
    
    if active_query:
        # Append User Message
        st.session_state.messages.append({
            "role": "user",
            "content": active_query
        })
        
        with st.chat_message("user", avatar="👤"):
            st.markdown(f"**{active_query}**")
            
        with st.chat_message("assistant", avatar="🛍️"):
            st.markdown(render_copilot_badge(), unsafe_allow_html=True)
            with st.spinner("🤖 Flipkart Copilot orchestrator evaluating query and dispatching specialist agents..."):
                history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
                state = process_query(active_query, chat_history=history)
                
                final_answer = state["final_answer"]
                charts = state.get("charts", [])
                traces = state.get("tool_traces", [])
                routes = state.get("routing_decision", [])
                
                st.markdown(final_answer, unsafe_allow_html=True)
                
                curr_turn = len(st.session_state.messages)
                for chart_idx, chart in enumerate(charts):
                    unique_active_key = f"active_turn_{curr_turn}_{chart_idx}_{uuid.uuid4().hex[:6]}"
                    render_chart(chart, chart_key=unique_active_key)
                    
                render_reasoning_trace(traces, routes)
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": final_answer,
                    "tool_traces": traces,
                    "routing_decision": routes,
                    "charts": charts
                })
        st.rerun()

# ==============================================================================
# TAB 2: EXECUTIVE ANALYTICS EXPLORER
# ==============================================================================
with tab_analytics:
    st.markdown("### 📊 Interactive Multi-Dimensional Analytics Explorer")
    st.caption("Slice and dice 133,503 real transactions in real time with dynamic KPI recalculation.")
    
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        all_cats = sorted(df_data["Category"].unique().tolist())
        selected_cats = st.multiselect("Category:", options=all_cats, default=all_cats)
    with col_f2:
        all_subcats = sorted(df_data["SubCategory"].unique().tolist())
        selected_subcats = st.multiselect("SubCategory (Top Lines):", options=all_subcats, default=all_subcats[:6])
    with col_f3:
        all_zones = sorted(df_data["Zone"].unique().tolist())
        selected_zones = st.multiselect("Logistics Zone:", options=all_zones, default=all_zones)
    with col_f4:
        all_dtypes = sorted(df_data["Delivery Type"].unique().tolist())
        selected_dtypes = st.multiselect("Delivery Type:", options=all_dtypes, default=all_dtypes)
        
    filtered_df = df_data[
        (df_data["Category"].isin(selected_cats)) &
        (df_data["SubCategory"].isin(selected_subcats)) &
        (df_data["Zone"].isin(selected_zones)) &
        (df_data["Delivery Type"].isin(selected_dtypes))
    ]
    
    st.markdown("#### Filtered Segment Performance")
    render_kpi_header(custom_df=filtered_df)
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        cat_agg = filtered_df.groupby("Category").agg(
            Revenue=("Total Sales (INR)", "sum"),
            Profit=("Profit (INR)", "sum")
        ).reset_index()
        fig_cat = px.bar(
            cat_agg,
            x="Category",
            y=["Revenue", "Profit"],
            barmode="group",
            title="Gross Revenue vs Profit by Category (Filtered Slice)",
            template="plotly_dark",
            color_discrete_map={"Revenue": "#2874F0", "Profit": "#26A541"}
        )
        fig_cat.update_layout(
            font=dict(family="Plus Jakarta Sans, sans-serif"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_cat, width="stretch", key="analytics_category_breakdown_bar")
        
    with col_c2:
        zone_agg = filtered_df.groupby("Zone").agg(
            Orders=("Order ID", "count"),
            Returns=("Is Returned", "sum")
        ).reset_index()
        zone_agg["Return_Rate"] = (zone_agg["Returns"] / zone_agg["Orders"]) * 100
        fig_zone = px.bar(
            zone_agg,
            x="Zone",
            y="Return_Rate",
            title="Return Rate % across Logistics Zones (Filtered Slice)",
            template="plotly_dark",
            color="Zone",
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_zone.update_layout(
            font=dict(family="Plus Jakarta Sans, sans-serif"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_zone, width="stretch", key="analytics_zone_return_bar")

    st.markdown("#### Filtered Transactions Table (Sample View)")
    st.dataframe(
        filtered_df[["Order ID", "Order Date", "Product Name", "Category", "SubCategory", "Sale Price (INR)", "Quantity Sold", "Total Sales (INR)", "Profit (INR)", "Zone", "Delivery Type", "Status", "Customer Rating"]].head(200),
        width="stretch",
        height=320
    )

# ==============================================================================
# TAB 3: RETURNS & REVERSE LOGISTICS DIAGNOSTIC
# ==============================================================================
with tab_returns:
    st.markdown("### 🔄 Reverse Logistics & Return Root-Cause Diagnostics")
    st.caption("Deep-dive investigation into the 36,036 returned orders and operational financial leakage.")
    
    ret_info = analyze_return_impact()
    
    col_r1, col_r2, col_r3 = st.columns(3)
    col_r1.metric("Total Returned Orders", f"{ret_info['returned_orders_count']:,}", f"{ret_info['overall_return_rate_pct']}% of Catalog")
    col_r2.metric("Forfeited Net Profit", f"₹{ret_info['forfeited_gross_profit_inr']:,.2f}", "Unrealized Margin")
    col_r3.metric("Reverse Freight Loss", f"₹{ret_info['reverse_logistics_shipping_loss_inr']:,.2f}", "Overhead Sunk Cost")
    
    col_p1, col_p2 = st.columns([3, 2])
    with col_p1:
        reasons_df = pd.DataFrame(ret_info["top_return_reasons"])
        fig_reasons = px.bar(
            reasons_df,
            x="Count",
            y="Return Reason",
            orientation="h",
            title="Pareto Distribution of Return Root Causes",
            template="plotly_dark",
            color="Count",
            color_continuous_scale="Reds",
            text="Share_Pct"
        )
        fig_reasons.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_reasons.update_layout(
            font=dict(family="Plus Jakarta Sans, sans-serif"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_reasons, width="stretch", key="returns_root_causes_bar")
        
    with col_p2:
        st.markdown("#### 🎯 Strategic Profit Recovery Calculator")
        st.markdown(
            "Model the direct net profit gain by reducing return rate via automated packing QA and vendor defect penalties."
        )
        target_ret_rate = st.slider("Target Return Rate (%):", min_value=12.0, max_value=27.0, value=18.0, step=0.5)
        current_rate = ret_info['overall_return_rate_pct']
        rate_diff = current_rate - target_ret_rate
        
        # Recovered profit formula
        recovered_orders = int((rate_diff / 100.0) * ret_info['total_orders_analyzed'])
        avg_profit_per_order = ret_info['forfeited_gross_profit_inr'] / ret_info['returned_orders_count']
        avg_shipping_per_order = ret_info['reverse_logistics_shipping_loss_inr'] / ret_info['returned_orders_count']
        recovered_profit = recovered_orders * (avg_profit_per_order + avg_shipping_per_order)
        diag_html = (
            f'<div class="diagnostic-card">'
            f'<div class="diagnostic-title">💰 Projected Annual Recovery: ₹{recovered_profit:,.2f}</div>'
            f'<div class="diagnostic-body">'
            f'• <b>Orders Saved from Return:</b> {recovered_orders:,} orders<br>'
            f'• <b>Return Rate Reduction:</b> {rate_diff:.1f}% percentage points<br>'
            f'• <b>Operational Impact:</b> Eradicates packaging waste & boosts customer retention by +14%.'
            f'</div></div>'
        )
        st.markdown(diag_html, unsafe_allow_html=True)

# ==============================================================================
# TAB 4: WHAT-IF STRATEGIC MARGIN SIMULATOR
# ==============================================================================
with tab_simulator:
    st.markdown("### 🎛️ Strategic 'What-If' Margin & Pricing Simulator")
    st.caption("Model the financial impact of price adjustments, return mitigation, and volume retention.")
    
    col_s1, col_s2 = st.columns([1, 2])
    
    with col_s1:
        st.markdown("#### Scenario Configuration")
        target_cat = st.selectbox("Select Target Category:", options=["All Categories"] + sorted(df_data["Category"].unique().tolist()))
        price_adjustment_pct = st.slider("Price Realization Lift (%):", min_value=0, max_value=15, value=4, step=1, help="e.g. Selective markup or discount optimization")
        return_reduction_pct = st.slider("Target Return Reduction (% points):", min_value=0, max_value=12, value=5, step=1)
        volume_retention_pct = st.slider("Expected Volume Retention (%):", min_value=85, max_value=105, value=97, step=1)
        
    with col_s2:
        sim_df = df_data.copy()
        if target_cat != "All Categories":
            mask = sim_df["Category"] == target_cat
        else:
            mask = pd.Series(True, index=sim_df.index)
            
        curr_sales = sim_df[mask]["Total Sales (INR)"].sum()
        curr_profit = sim_df[mask]["Profit (INR)"].sum()
        curr_margin = (curr_profit / curr_sales) * 100 if curr_sales > 0 else 0.0
        
        # Simulation math
        sim_volume_factor = volume_retention_pct / 100.0
        price_lift_factor = 1.0 + (price_adjustment_pct / 100.0)
        
        sim_sales = curr_sales * price_lift_factor * sim_volume_factor
        recovered_from_returns = curr_profit * (return_reduction_pct / 100.0)
        sim_profit = (curr_profit * price_lift_factor * sim_volume_factor) + recovered_from_returns
        sim_margin = (sim_profit / sim_sales) * 100 if sim_sales > 0 else 0.0
        
        profit_delta = sim_profit - curr_profit
        
        st.markdown("#### Projected Financial Impact")
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("Projected Total Profit", f"₹{sim_profit:,.2f}", f"{profit_delta:+,.2f} INR")
        c_m2.metric("New Profit Margin", f"{sim_margin:.2f}%", f"{sim_margin - curr_margin:+.2f}%")
        c_m3.metric("Incremental Profit Gain", f"₹{profit_delta:,.2f}", "Net Bottom-Line Lift")
        
        comp_df = pd.DataFrame([
            {"Scenario": "Current Baseline", "Sales (₹)": curr_sales, "Profit (₹)": curr_profit},
            {"Scenario": f"Simulated Lift (+{price_adjustment_pct}% / -{return_reduction_pct}% Ret)", "Sales (₹)": sim_sales, "Profit (₹)": sim_profit},
        ])
        
        fig_comp = px.bar(
            comp_df,
            x="Scenario",
            y=["Profit (₹)", "Sales (₹)"],
            barmode="group",
            title=f"Baseline vs Simulated Strategy ({target_cat})",
            template="plotly_dark",
            color_discrete_map={"Profit (₹)": "#26A541", "Sales (₹)": "#2874F0"}
        )
        fig_comp.update_layout(
            font=dict(family="Plus Jakarta Sans, sans-serif"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_comp, width="stretch", key="simulator_scenario_comparison_bar")

# ==============================================================================
# TAB 5: PREDICTIVE FORECAST & CLUSTERING
# ==============================================================================
with tab_forecast:
    st.markdown("### 🔮 Predictive Time Series & Customer Segmentation")
    st.caption("Exponential smoothing forecasts across 72 operating cycles and unsupervised customer archetypes.")
    
    col_fc1, col_fc2 = st.columns(2)
    
    with col_fc1:
        st.markdown("#### 📈 Forward Holt-Winters Forecast")
        horizon_months = st.slider("Forecast Horizon (Months):", min_value=1, max_value=12, value=6)
        fc_data = forecast_sales_and_profit(months=horizon_months)
        
        fc_table = pd.DataFrame(fc_data["forecasts"])
        fc_table["forecast_revenue_inr"] = fc_table["forecast_revenue_inr"].apply(lambda x: f"₹{x:,.2f}")
        fc_table["forecast_profit_inr"] = fc_table["forecast_profit_inr"].apply(lambda x: f"₹{x:,.2f}")
        fc_table["projected_profit_margin_pct"] = fc_table["projected_profit_margin_pct"].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(
            fc_table[["period", "forecast_revenue_inr", "forecast_profit_inr", "projected_profit_margin_pct"]],
            width="stretch"
        )
        st.info(f"ℹ️ **Note:** {fc_data['uncertainty_disclosure']}")
        
    with col_fc2:
        st.markdown("#### 🧬 KMeans Order Archetypes")
        num_clusters = st.selectbox("Number of Persona Clusters (K):", options=[2, 3, 4, 5], index=1)
        km_res = perform_kmeans_clustering(n_clusters=num_clusters)
        
        for p in km_res["cluster_profiles"]:
            st.markdown(f"**Cluster {p['cluster_id']}: {p['segment_name']}** ({p['order_share_pct']}% of orders)")
            st.caption(f"Avg Ticket: ₹{p['avg_sale_price_inr']:,.2f} | Avg Qty: {p['avg_quantity']} | Avg Age: {p['avg_customer_age']} yrs | Avg SLA: {p['avg_delivery_days']} days | Rating: ★ {p['avg_customer_rating']}")
            st.markdown(f"💡 *{p['strategic_description']}*")
            st.markdown("---")

# ==============================================================================
# TAB 6: SYSTEM ARCHITECTURE & DATA HUB
# ==============================================================================
with tab_data:
    st.markdown("### 🏛️ System Architecture & Data Hub")
    
    col_d1, col_d2 = st.columns([3, 1])
    with col_d1:
        st.markdown("#### Verified Real-World Dataset (133,503 Records)")
    with col_d2:
        csv_bytes = df_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Export Cleaned Dataset (CSV)",
            data=csv_bytes,
            file_name="cleaned_flipkart_real_sales.csv",
            mime="text/csv",
            width="stretch"
        )
        
    st.dataframe(df_data.head(500), width="stretch", height=350)
    
    with st.expander("🏛️ View Multi-Agent Architecture Pipeline", expanded=True):
        st.markdown("""
        ```mermaid
        flowchart TD
            User([User Query]) --> Router{LangGraph Router / Scope Guardrail}
            Router -->|Out of Scope| Refusal[Guardrail Refusal Node]
            Router -->|Sales / GMV| Sales[📊 Sales Analytics Specialist]
            Router -->|Profit / Returns| Profit[💰 Profit & Return Specialist]
            Router -->|Forecast / Strategy| Advisor[🔮 Forecast & Advisor Specialist]
            Router -->|Policy / SLA| RAG[📚 Knowledge Base RAG Specialist]
            
            Sales --> Tool1[(Pandas Analytics & Plotly Engine)]
            Profit --> Tool2[(Scipy Statistical & Return Diagnostics)]
            Advisor --> Tool3[(Statsmodels Holt-Winters & Scikit-Learn KMeans)]
            RAG --> Tool4[(ChromaDB Semantic Document Index)]
            
            Tool1 --> Synthesizer[Executive Synthesis Node]
            Tool2 --> Synthesizer
            Tool3 --> Synthesizer
            Tool4 --> Synthesizer
            
            Synthesizer --> Gemini[🧠 Google Gemini AI Engine / Adaptive Grounded Fallback]
            Gemini --> Output([Executive Intelligence Briefing + Charts])
        ```
        """)
    
    with st.expander("📄 View Full Verified Data Profile Report", expanded=False):
        if os.path.exists("outputs/data_profile.md"):
            with open("outputs/data_profile.md", "r", encoding="utf-8") as f:
                st.markdown(f.read())
