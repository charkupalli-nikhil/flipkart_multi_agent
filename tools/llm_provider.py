"""
Flipkart Sales Intelligence System - Dual LLM Provider Engine
Provides seamless Google Gemini API integration with rich context ground truth and deterministic Mock Mode fallback.
"""

import os
import re
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from tools.query_tools import get_full_dataset_summary_matrix

load_dotenv()

class LLMProvider:
    def __init__(self):
        self.mode = os.getenv("LLM_MODE", "mock").lower().strip()
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        self._gemini_client = None
        self._init_client()

    def _init_client(self):
        if self.mode == "gemini" and self.api_key:
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=self.api_key)
                self.mode = "gemini"
            except Exception as e:
                print(f"[LLMProvider] Gemini initialization failed: {e}. Falling back to 'mock' mode.")
                self.mode = "mock"
        else:
            self.mode = "mock"

    def is_gemini_active(self) -> bool:
        return self.mode == "gemini" and self._gemini_client is not None

    def get_status(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "has_api_key": bool(self.api_key),
            "model_name": self.model_name,
            "is_live_gemini": self.is_gemini_active(),
            "config_note": "To enable live Gemini AI, set LLM_MODE=gemini and GEMINI_API_KEY=your_key in .env"
        }

    def generate_response(self, system_prompt: str, user_prompt: str, tool_context: Optional[Dict[str, Any]] = None) -> str:
        if self.is_gemini_active():
            try:
                matrix_context = get_full_dataset_summary_matrix()
                
                combined_prompt = f"""
{system_prompt}

=== SYSTEM INSTRUCTIONS ===
1. You are the Executive AI Copilot for the Flipkart Sales Intelligence Multi-Agent System.
2. Directly, accurately, and thoroughly answer the user's question using the factual computed data below.
3. Quote specific verified numbers (Revenue, Units, Gross Margins %, Realized Margins %, Returns, Ratings, SLAs).
4. Provide structured executive briefings with clear bullet points, bold KPIs, and markdown tables where appropriate.
5. If the user asks about time horizons, remind them that the data covers 133,503 real transactions across 6 calendar years (2015 to 2020).

=== COMPUTED SPECIALIST AGENT FINDINGS ===
{tool_context}

=== FULL CATALOG & DIMENSIONAL GROUND TRUTH MATRIX ===
{matrix_context}

=== USER QUERY ===
{user_prompt}
"""
                import concurrent.futures
                
                def _do_gemini_call():
                    res = self._gemini_client.models.generate_content(
                        model=self.model_name,
                        contents=combined_prompt
                    )
                    return res.text

                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    fut = executor.submit(_do_gemini_call)
                    return fut.result(timeout=6.0)
            except Exception as e:
                print(f"[LLMProvider] Live Gemini call error or timeout: {e}. Generating via grounded template fallback.")

        # Default Mock / Grounded Template Synthesis
        return self._generate_mock_template(system_prompt, user_prompt, tool_context)

    def _generate_mock_template(self, system_prompt: str, user_prompt: str, tool_context: Optional[Dict[str, Any]]) -> str:
        """Template-based synthesis grounded in computed tool results."""
        if not tool_context:
            return "Analysis complete. Please refer to the computed summary metrics."

        lines = []
        lines.append("### 📊 Executive Intelligence Briefing\n")
        
        # Specific Entity Lookup Section
        if "specific_entity_lookup" in tool_context:
            ent = tool_context["specific_entity_lookup"]
            if ent.get("status") == "found":
                lines.append(f"#### 🎯 Filtered Entity Analysis ({', '.join([f'{k}: {v}' for k, v in ent.get('filters_applied', {}).items()])})")
                lines.append(f"- **Total Revenue:** ₹{ent.get('total_revenue_inr', 0):,.2f}")
                lines.append(f"- **Total Net Profit:** ₹{ent.get('total_profit_inr', 0):,.2f} (*Profit Margin: {ent.get('profit_margin_pct')}%*)")
                lines.append(f"- **Volume:** {ent.get('total_units_sold', 0):,} units across {ent.get('matched_orders_count', 0):,} orders (AOV: ₹{ent.get('average_order_value_inr', 0):,.2f})")
                lines.append(f"- **Return Rate:** {ent.get('return_rate_pct')}% ({ent.get('returned_orders_count', 0):,} returned orders)")
                lines.append(f"- **Customer Rating:** ★ {ent.get('average_customer_rating')} / 5.0\n")
                if ent.get("top_products_in_subset"):
                    lines.append("**Top SKUs in this segment:**")
                    for p in ent["top_products_in_subset"]:
                        lines.append(f"- *{p.get('Product Name')}:* Sales ₹{p.get('sales', 0):,.2f}, Profit ₹{p.get('profit', 0):,.2f}, Units: {p.get('units')}")
                    lines.append("")

        # Summarize KPIs
        if "kpis" in tool_context:
            k = tool_context["kpis"]
            lines.append("#### 🏆 Portfolio Key Performance Indicators (KPIs)")
            lines.append(f"- **Total Gross Revenue:** ₹{k.get('total_revenue_inr', 0):,.2f} (~₹16.03 Cr GMV across 2015–2020)")
            lines.append(f"- **Total Gross Profit:** ₹{k.get('total_profit_inr', 0):,.2f} (*Gross Margin: {k.get('profit_margin_pct', 0):.2f}%*)")
            lines.append(f"- **Net Realized Profit (Delivered):** ₹{k.get('realized_profit_inr', 0):,.2f} (*Realized Margin: {k.get('realized_margin_pct', 0):.2f}%*)")
            lines.append(f"- **Total Logistics Orders:** {k.get('total_orders', 0):,} ({k.get('total_units_sold', 0):,} units sold)")
            lines.append(f"- **Fulfillment Performance:** {k.get('delivered_orders', 0):,} Delivered | {k.get('returned_orders', 0):,} Returned (**{k.get('return_rate_pct', 0):.2f}% Return Rate**)")
            lines.append(f"- **Average Order Value (AOV):** ₹{k.get('average_order_value_inr', 0):,.2f}")
            lines.append(f"- **Average Delivery SLA:** {k.get('average_delivery_days', 9.5)} business days | **Avg Rating:** ★ {k.get('average_customer_rating', 0):.2f} / 5.0\n")

        # Category Breakdown
        for key in tool_context:
            if key.startswith("sales_by_"):
                dim_title = key.replace("sales_by_", "").replace("_", " ").title()
                rows = tool_context[key]
                lines.append(f"#### 📦 Performance Breakdown by {dim_title}")
                first_col = [col for col in rows[0].keys() if col not in ["orders", "total_sales", "total_profit", "units_sold", "avg_price", "avg_rating", "return_orders", "profit_margin_pct", "avg_order_value", "return_rate_pct", "avg_delivery_days"]][0] if rows else "Dimension"
                lines.append(f"| {first_col} | Orders | Revenue (INR) | Profit (INR) | Margin % | Return Rate % | Avg Rating |")
                lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
                for r in rows[:10]:
                    lines.append(f"| **{r.get(first_col)}** | {r.get('orders', 0):,} | ₹{r.get('total_sales', 0):,.2f} | ₹{r.get('total_profit', 0):,.2f} | {r.get('profit_margin_pct', 0):.2f}% | {r.get('return_rate_pct', 0):.2f}% | ★ {r.get('avg_rating', 0):.2f} |")
                lines.append("")

        # Top/Bottom Products
        if "top_bottom_products" in tool_context:
            lines.append("#### 🥇 Ranked Merchandise SKUs")
            lines.append("| Product Name | Category | Revenue (INR) | Units | Profit (INR) | Margin % | Return Rate % |")
            lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
            for row in tool_context["top_bottom_products"]:
                lines.append(f"| **{row.get('Product Name')[:40]}** | {row.get('Category')} | ₹{row.get('total_sales', 0):,.2f} | {row.get('units_sold', 0):,} | ₹{row.get('total_profit', 0):,.2f} | {row.get('profit_margin_pct', 0):.2f}% | {row.get('return_rate_pct', 0):.2f}% |")
            lines.append("")

        # Return Diagnostics
        if "return_diagnostics" in tool_context:
            rd = tool_context["return_diagnostics"]
            lines.append("#### 🔄 Reverse Logistics & Return Root-Cause Diagnostics")
            lines.append(f"- **Total Return Volume:** **{rd.get('returned_orders_count', 0):,} orders** ({rd.get('overall_return_rate_pct')}% of all transactions)")
            lines.append(f"- **Forfeited Gross Profit:** ₹{rd.get('forfeited_gross_profit_inr', 0):,.2f}")
            lines.append(f"- **Reverse Logistics Freight Overhead:** ₹{rd.get('reverse_logistics_shipping_loss_inr', 0):,.2f}")
            lines.append(f"- **Total Financial Drag:** **₹{rd.get('total_financial_drag_inr', 0):,.2f}**")
            lines.append(f"\n**Root Causes Breakdown:**")
            for reason in rd.get("top_return_reasons", []):
                lines.append(f"- **{reason.get('Return Reason')}:** {reason.get('Count', 0):,} incidents (*{reason.get('Share_Pct')}% of returns*)")
            lines.append(f"\n💡 *Strategic Recovery:* {rd.get('strategic_takeaway')}\n")

        # Profit Margins by Dimension
        if "profit_margins" in tool_context:
            lines.append("#### 💰 Margin Performance Breakdown")
            for row in tool_context["profit_margins"][:6]:
                dim_key = [k for k in row.keys() if k not in ["orders", "total_sales", "total_profit", "return_orders", "avg_price", "avg_rating", "profit_margin_pct", "return_rate_pct"]][0]
                lines.append(f"- **{row.get(dim_key)}:** Margin **{row.get('profit_margin_pct')}%** (Sales: ₹{row.get('total_sales', 0):,.2f}, Profit: ₹{row.get('total_profit', 0):,.2f}, Return Rate: {row.get('return_rate_pct')}%)")
            lines.append("")

        # Correlations
        if "correlations" in tool_context:
            lines.append("#### 📈 Statistical Correlation Insights")
            corrs = tool_context["correlations"]
            for k, val in corrs.items():
                lines.append(f"- **{val.get('feature_x')} vs {val.get('feature_y')}:** {val.get('relationship')}")
            lines.append("")

        # Loss Pockets
        if "loss_pockets" in tool_context:
            lp = tool_context["loss_pockets"]
            lines.append("#### ⚠️ Low Margin Pockets & Vulnerabilities")
            lines.append(f"- **Margin Floor:** < {lp.get('margin_threshold_pct')}%")
            lines.append(f"- **Primary Operational Driver:** {lp.get('key_driver')}\n")

        # Forecast
        if "forecast" in tool_context:
            fc = tool_context["forecast"]
            lines.append(f"#### 🔮 Forward Time-Series Forecast ({fc.get('forecast_horizon_months')} Months Projection)")
            lines.append("| Period | Projected Revenue | Expected Profit | Projected Margin % | 80% Confidence Interval |")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")
            for f in fc.get("forecasts", []):
                lines.append(f"| **{f.get('period')}** | ₹{f.get('forecast_revenue_inr', 0):,.2f} | ₹{f.get('forecast_profit_inr', 0):,.2f} | {f.get('projected_profit_margin_pct', 0):.2f}% | ₹{f.get('forecast_revenue_lower_bound', 0):,.2f} – ₹{f.get('forecast_revenue_upper_bound', 0):,.2f} |")
            lines.append(f"\n> ℹ️ *{fc.get('uncertainty_disclosure')}*\n")

        # Clustering
        if "clustering" in tool_context:
            cl = tool_context["clustering"]
            lines.append("#### 🧬 KMeans Behavioral Customer & Order Archetypes")
            for p in cl.get("cluster_profiles", []):
                lines.append(f"- **Cluster {p.get('cluster_id')}: {p.get('segment_name')}** ({p.get('order_share_pct')}% sample share)")
                lines.append(f"  - *Avg Price:* ₹{p.get('avg_sale_price_inr', 0):,.2f} | *Avg Qty:* {p.get('avg_quantity')} | *Avg Age:* {p.get('avg_customer_age')} yrs | *Avg Delivery SLA:* {p.get('avg_delivery_days')} days | *Avg Rating:* ★ {p.get('avg_customer_rating')}")
                lines.append(f"  - *Strategic Playbook:* {p.get('strategic_description')}")
            lines.append("")

        # RAG Knowledge Base
        if "rag" in tool_context:
            rag_info = tool_context["rag"].get("knowledge_base_retrieval", {})
            if "error" in rag_info:
                lines.append(f"#### 📚 Knowledge Base Retrieval Error\n{rag_info['error']}\n")
            elif rag_info.get("retrieved_information"):
                lines.append("#### 📚 Retrieved Operational Policies & SLAs")
                for doc in rag_info["retrieved_information"]:
                    lines.append(f"> {doc}\n")
            else:
                lines.append("#### 📚 Knowledge Base Retrieval\nNo relevant policies retrieved.\n")

        # Strategic Recommendations
        if "recommendations" in tool_context:
            lines.append("#### 💡 Prioritized Strategic Recommendations")
            for r in tool_context["recommendations"]:
                lines.append(f"1. **[{r.get('priority')}] {r.get('title')}**")
                lines.append(f"   - **Observation:** {r.get('observation')}")
                lines.append(f"   - **Action Plan:** {r.get('action')}")
                lines.append(f"   - **Projected Impact:** {r.get('projected_impact')}")
            lines.append("")

        return "\n".join(lines)

# Global singleton
_GLOBAL_LLM_PROVIDER = None

def get_llm_provider() -> LLMProvider:
    global _GLOBAL_LLM_PROVIDER
    if _GLOBAL_LLM_PROVIDER is None:
        _GLOBAL_LLM_PROVIDER = LLMProvider()
    return _GLOBAL_LLM_PROVIDER
