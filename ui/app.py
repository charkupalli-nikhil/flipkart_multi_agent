"""
Flipkart Sales Intelligence System - Streamlit Multi-Agent Dashboard
Interactive, high-contrast AI assistant for e-commerce sales, discount optimization, and predictive intelligence.
"""

import os
import sys
import uuid
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ensure root directory is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.orchestrator import process_query
from ui.components import render_kpi_header, render_reasoning_trace, render_chart
from tools.base import load_sales_data
from tools.llm_provider import get_llm_provider
from tools.advisor_tools import forecast_sales_and_profit, perform_kmeans_clustering

# Page Configuration
st.set_page_config(
    page_title="Flipkart Sales Intelligence System",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Custom High-Contrast CSS
def load_css():
    css_file = os.path.join(os.path.dirname(__file__), "styles.css")
    if os.path.exists(css_file):
        with open(css_file, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Load Dataset for interactive exploration
df_data = load_sales_data()

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "### 👋 Welcome to the Flipkart Sales Intelligence Multi-Agent System!\n\n"
                "I am your executive AI copilot orchestrated via **LangGraph** and powered by **Google Gemini** with 3 specialist analytics agents:\n\n"
                "- 📊 **Sales Analytics Specialist:** Total revenue, order velocity, AOV, top/bottom SKUs, and category share.\n"
                "- 💰 **Profit & Optimization Specialist:** Gross margins, discount elasticity, correlation, and loss-making pockets.\n"
                "- 🔮 **Forecast & Business Advisor:** 3-month Holt-Winters projections, KMeans behavioral clustering, and prioritized strategy.\n\n"
                "**Try one of the quick sample queries below or type your own question in the chat input!**"
            ),
            "tool_traces": [],
            "routing_decision": [],
            "charts": []
        }
    ]

# Sidebar Controls
with st.sidebar:
    st.markdown("## ⚙️ System Status")
    
    llm = get_llm_provider()
    status = llm.get_status()
    
    if status["is_live_gemini"]:
        st.success(f"🟢 **LLM Engine:** Live Gemini AI (`{status['model_name']}`)")
    else:
        st.info("🔵 **LLM Engine:** Deterministic Mock Mode (Offline)")
        
    with st.expander("🔑 Gemini API Key Settings", expanded=False):
        st.markdown(
            "**Connected Model:** `gemini-3.8-flash`\n\n"
            "Key configured in `.env`. The system automatically validates connectivity on boot."
        )

    st.markdown("---")
    st.markdown("### 📁 Dataset Scope")
    st.caption("• **Records:** 1,000 verified orders\n• **Catalog:** 25 products across 5 categories\n• **Timeframe:** Feb 2024 – Feb 2025 (~12 mos)\n• **Scope:** No review text or customer PII")

    st.markdown("---")
    st.markdown("### 💡 Quick Prompt Chips")
    
    example_queries = [
        ("📊 Top 5 Revenue Products", "What are the top 5 revenue-generating products?"),
        ("💰 Category Profit Margins", "Analyze profit margin by category and discount band"),
        ("📈 3-Month Sales Forecast", "Forecast revenue and profit for the next 3 months"),
        ("🎯 Regional Strategy Plan", "Which region is least profitable and what should we do about it?"),
        ("⚠️ Guardrail Refusal Test", "Show customer review sentiment for mobile phones")
    ]
    
    selected_sidebar_query = None
    for label, query_text in example_queries:
        if st.button(label, use_container_width=True):
            selected_sidebar_query = query_text

# Main Page Header & Hero Banner
st.markdown("""
<div class="hero-banner">
    <div class="hero-title">🛍️ Flipkart Sales Intelligence System</div>
    <div class="hero-subtitle">
        Executive AI Multi-Agent Platform powered by LangGraph, Google Gemini AI, and Statistical Tool Calling
    </div>
</div>
""", unsafe_allow_html=True)

# Executive KPI Header
render_kpi_header()

# Main Interactive Navigation Tabs
tab_chat, tab_analytics, tab_simulator, tab_forecast, tab_data = st.tabs([
    "💬 Multi-Agent AI Chat",
    "📊 Dynamic Analytics Explorer",
    "🎛️ What-If Margin Simulator",
    "🔮 Forecast & Clusters",
    "📥 Data Hub & Reports"
])

# ==============================================================================
# TAB 1: MULTI-AGENT AI CHAT
# ==============================================================================
with tab_chat:
    st.markdown("#### 💬 Ask Multi-Agent Intelligence")
    
    # Render message history
    for msg_idx, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
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
    user_input = st.chat_input("Ask a question about sales revenue, discount bands, margins, or forecasts...")
    
    active_query = selected_sidebar_query or user_input
    
    if active_query:
        # Append User Message
        st.session_state.messages.append({
            "role": "user",
            "content": active_query
        })
        
        with st.chat_message("user"):
            st.markdown(f"**{active_query}**")
            
        with st.chat_message("assistant"):
            with st.spinner("🤖 Multi-agent system analyzing dataset and executing specialist tools..."):
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
# TAB 2: DYNAMIC ANALYTICS EXPLORER
# ==============================================================================
with tab_analytics:
    st.markdown("### 📊 Interactive Dimension & Filter Explorer")
    st.caption("Slice and dice transaction data in real time with dynamic KPI recalculation.")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        all_cats = sorted(df_data["Category"].unique().tolist())
        selected_cats = st.multiselect("Filter by Category:", options=all_cats, default=all_cats)
    with col_f2:
        all_regs = sorted(df_data["Region"].unique().tolist())
        selected_regs = st.multiselect("Filter by Region:", options=all_regs, default=all_regs)
    with col_f3:
        all_segs = sorted(df_data["Customer Segment"].unique().tolist())
        selected_segs = st.multiselect("Filter by Segment:", options=all_segs, default=all_segs)
        
    filtered_df = df_data[
        (df_data["Category"].isin(selected_cats)) &
        (df_data["Region"].isin(selected_regs)) &
        (df_data["Customer Segment"].isin(selected_segs))
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
            title="Revenue vs Profit by Category (Filtered)",
            template="plotly_dark",
            color_discrete_map={"Revenue": "#6366F1", "Profit": "#10B981"}
        )
        fig_cat.update_layout(font=dict(family="Plus Jakarta Sans, sans-serif"))
        st.plotly_chart(fig_cat, use_container_width=True, key="analytics_category_breakdown_bar")
        
    with col_c2:
        disc_agg = filtered_df.groupby("Discount Band").agg(
            Total_Sales=("Total Sales (INR)", "sum"),
            Total_Profit=("Profit (INR)", "sum")
        ).reset_index()
        disc_agg["Margin %"] = (disc_agg["Total_Profit"] / disc_agg["Total_Sales"]) * 100
        fig_disc = px.bar(
            disc_agg,
            x="Discount Band",
            y="Margin %",
            title="Profit Margin % by Discount Band",
            template="plotly_dark",
            color="Discount Band",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_disc.update_layout(font=dict(family="Plus Jakarta Sans, sans-serif"))
        st.plotly_chart(fig_disc, use_container_width=True, key="analytics_discount_band_bar")

    st.markdown("#### Filtered Transactions Table")
    st.dataframe(
        filtered_df[["Order ID", "Product Name", "Category", "Price (INR)", "Quantity Sold", "Total Sales (INR)", "Profit (INR)", "Discount %", "Region", "Payment Method"]],
        use_container_width=True,
        height=320
    )

# ==============================================================================
# TAB 3: WHAT-IF DISCOUNT & MARGIN SIMULATOR
# ==============================================================================
with tab_simulator:
    st.markdown("### 🎛️ Strategic 'What-If' Discount & Margin Simulator")
    st.markdown("Model the financial impact of adjusting discount strategies and volume elasticities across categories.")
    
    col_s1, col_s2 = st.columns([1, 2])
    
    with col_s1:
        st.markdown("#### Scenario Configuration")
        target_cat = st.selectbox("Select Target Category:", options=["All Categories"] + sorted(df_data["Category"].unique().tolist()))
        discount_reduction = st.slider("Discount Rate Reduction (% points):", min_value=0, max_value=15, value=5, step=1, help="e.g., Reducing 25% discount to 20% is a 5 point reduction")
        volume_retention_pct = st.slider("Expected Volume Retention (%):", min_value=80, max_value=105, value=96, step=1, help="Expected percentage of sales volume retained after discount adjustment")
        
    with col_s2:
        sim_df = df_data.copy()
        if target_cat != "All Categories":
            mask = sim_df["Category"] == target_cat
        else:
            mask = pd.Series(True, index=sim_df.index)
            
        # Current Metrics
        curr_sales = sim_df[mask]["Total Sales (INR)"].sum()
        curr_profit = sim_df[mask]["Profit (INR)"].sum()
        curr_margin = (curr_profit / curr_sales) * 100 if curr_sales > 0 else 0.0
        
        # Simulated Metrics
        # Reducing discount recovers unit margin
        recovered_margin_rate = (discount_reduction / 100.0) * 0.4
        sim_volume_factor = volume_retention_pct / 100.0
        
        sim_sales = curr_sales * sim_volume_factor
        sim_profit = (curr_profit + (curr_sales * recovered_margin_rate)) * sim_volume_factor
        sim_margin = (sim_profit / sim_sales) * 100 if sim_sales > 0 else 0.0
        
        profit_delta = sim_profit - curr_profit
        
        st.markdown("#### Projected Financial Impact")
        
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("Projected Total Profit", f"₹{sim_profit:,.2f}", f"{profit_delta:+,.2f} INR")
        c_m2.metric("New Profit Margin", f"{sim_margin:.2f}%", f"{sim_margin - curr_margin:+.2f}%")
        c_m3.metric("Annualized Profit Gain", f"₹{(profit_delta):,.2f}", "Net Margin Gain")
        
        # Comparison Bar Chart
        comp_df = pd.DataFrame([
            {"Scenario": "Current Baseline", "Sales (₹)": curr_sales, "Profit (₹)": curr_profit, "Margin %": curr_margin},
            {"Scenario": f"Simulated (-{discount_reduction}% Disc)", "Sales (₹)": sim_sales, "Profit (₹)": sim_profit, "Margin %": sim_margin},
        ])
        
        fig_comp = px.bar(
            comp_df,
            x="Scenario",
            y=["Profit (₹)", "Sales (₹)"],
            barmode="group",
            title=f"Baseline vs Simulated Strategy ({target_cat})",
            template="plotly_dark",
            color_discrete_map={"Profit (₹)": "#10B981", "Sales (₹)": "#6366F1"}
        )
        fig_comp.update_layout(font=dict(family="Plus Jakarta Sans, sans-serif"))
        st.plotly_chart(fig_comp, use_container_width=True, key="simulator_scenario_comparison_bar")

# ==============================================================================
# TAB 4: PREDICTIVE FORECAST & CLUSTERING
# ==============================================================================
with tab_forecast:
    st.markdown("### 🔮 Predictive Time Series & Customer Segmentation")
    
    col_fc1, col_fc2 = st.columns(2)
    
    with col_fc1:
        st.markdown("#### 📈 Forward Holt-Winters Forecast")
        horizon_months = st.slider("Forecast Horizon (Months):", min_value=1, max_value=6, value=3)
        fc_data = forecast_sales_and_profit(months=horizon_months)
        
        fc_table = pd.DataFrame(fc_data["forecasts"])
        fc_table["forecast_revenue_inr"] = fc_table["forecast_revenue_inr"].apply(lambda x: f"₹{x:,.2f}")
        fc_table["forecast_profit_inr"] = fc_table["forecast_profit_inr"].apply(lambda x: f"₹{x:,.2f}")
        fc_table["projected_profit_margin_pct"] = fc_table["projected_profit_margin_pct"].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(
            fc_table[["period", "forecast_revenue_inr", "forecast_profit_inr", "projected_profit_margin_pct"]],
            use_container_width=True
        )
        st.info(f"⚠️ **Note:** {fc_data['uncertainty_disclosure']}")
        
    with col_fc2:
        st.markdown("#### 🧬 KMeans Order Archetypes")
        num_clusters = st.selectbox("Number of Persona Clusters (K):", options=[2, 3, 4, 5], index=1)
        km_res = perform_kmeans_clustering(n_clusters=num_clusters)
        
        for p in km_res["cluster_profiles"]:
            st.markdown(f"**Cluster {p['cluster_id']}: {p['segment_name']}** ({p['order_share_pct']}% of orders)")
            st.caption(f"Avg Ticket: ₹{p['avg_price_inr']:,.2f} | Avg Discount: {p['avg_discount_pct']}% | Avg Margin: ₹{p['avg_profit_inr']:,.2f}")
            st.markdown(f"💡 *{p['strategic_description']}*")
            st.markdown("---")

# ==============================================================================
# TAB 5: DATA HUB & REPORTS
# ==============================================================================
with tab_data:
    st.markdown("### 📥 Data Profile & Export Center")
    
    col_d1, col_d2 = st.columns([3, 1])
    with col_d1:
        st.markdown("#### Cleaned & Enriched Dataset Overview (1,000 Records)")
    with col_d2:
        csv_bytes = df_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download Cleaned CSV",
            data=csv_bytes,
            file_name="cleaned_flipkart.csv",
            mime="text/csv",
            use_container_width=True
        )
        
    st.dataframe(df_data, use_container_width=True, height=420)
    
    with st.expander("📄 View Full Data Profile Markdown Document", expanded=False):
        if os.path.exists("outputs/data_profile.md"):
            with open("outputs/data_profile.md", "r", encoding="utf-8") as f:
                st.markdown(f.read())
