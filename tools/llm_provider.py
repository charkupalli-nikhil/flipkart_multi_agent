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
                # Include full summary catalog matrix so Gemini can answer any specific question
                matrix_context = get_full_dataset_summary_matrix()
                
                combined_prompt = f"""
{system_prompt}

=== SYSTEM INSTRUCTIONS ===
1. You are the Executive AI for the Flipkart Sales Intelligence Multi-Agent System.
2. Directly, accurately, and thoroughly answer the user's question using the factual computed data below.
3. Quote specific verified numbers (Revenue, Units, Margins %, Discounts, Ratings).
4. Provide structured analysis with clear bullet points and markdown tables where appropriate.
5. If the user asks about trends or time periods, remind them that the data covers ~12 months (Feb 2024 to Feb 2025).

=== COMPUTED SPECIALIST AGENT FINDINGS ===
{tool_context}

=== FULL CATALOG & DIMENSIONAL GROUND TRUTH MATRIX ===
{matrix_context}

=== USER QUERY ===
{user_prompt}
"""
                response = self._gemini_client.models.generate_content(
                    model=self.model_name,
                    contents=combined_prompt
                )
                return response.text
            except Exception as e:
                print(f"[LLMProvider] Live Gemini call error: {e}. Generating via template.")

        # Default Mock / Grounded Template Synthesis
        return self._generate_mock_template(system_prompt, user_prompt, tool_context)

    def _generate_mock_template(self, system_prompt: str, user_prompt: str, tool_context: Optional[Dict[str, Any]]) -> str:
        """Template-based synthesis grounded in computed tool results."""
        if not tool_context:
            return "Analysis complete. Please refer to the computed summary metrics."

        lines = []
        lines.append("### Executive Intelligence Briefing\n")
        
        # Specific Entity Lookup Section
        if "specific_entity_lookup" in tool_context:
            ent = tool_context["specific_entity_lookup"]
            if ent.get("status") == "found":
                lines.append(f"#### 🎯 Filtered Entity Analysis ({', '.join([f'{k}: {v}' for k, v in ent.get('filters_applied', {}).items()])})")
                lines.append(f"- **Total Revenue:** ₹{ent.get('total_revenue_inr', 0):,.2f}")
                lines.append(f"- **Total Net Profit:** ₹{ent.get('total_profit_inr', 0):,.2f} (*Profit Margin: {ent.get('profit_margin_pct')}%*)")
                lines.append(f"- **Volume:** {ent.get('total_units_sold')} units across {ent.get('matched_orders_count')} orders (AOV: ₹{ent.get('average_order_value_inr', 0):,.2f})")
                lines.append(f"- **Customer Rating:** ★ {ent.get('average_customer_rating')} / 5.0 | **Avg Discount:** {ent.get('average_discount_pct')}%\n")
                if ent.get("top_products_in_subset"):
                    lines.append("**Top SKUs in this segment:**")
                    for p in ent["top_products_in_subset"]:
                        lines.append(f"- *{p.get('Product Name')}:* Sales ₹{p.get('sales', 0):,.2f}, Profit ₹{p.get('profit', 0):,.2f}, Units: {p.get('units')}")
                    lines.append("")

        # Summarize based on tool results
        if "kpis" in tool_context:
            k = tool_context["kpis"]
            lines.append("#### Overall Portfolio KPIs")
            lines.append(f"- **Total Sales Revenue:** ₹{k.get('total_revenue_inr', 0):,.2f}")
            lines.append(f"- **Total Net Profit:** ₹{k.get('total_profit_inr', 0):,.2f} (*Margin: {k.get('profit_margin_pct', 0):.2f}%*)")
            lines.append(f"- **Total Units Sold:** {k.get('total_units_sold', 0):,} across {k.get('total_orders', 0):,} orders")
            lines.append(f"- **Average Order Value (AOV):** ₹{k.get('average_order_value_inr', 0):,.2f}")
            lines.append(f"- **Average Customer Rating:** ★ {k.get('average_customer_rating', 0):.2f} / 5.0\n")

        if "sales_by_category" in tool_context:
            lines.append("#### Category Performance Breakdown")
            lines.append("| Category | Orders | Revenue (INR) | Profit (INR) | Margin % | Avg Rating |")
            lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for row in tool_context["sales_by_category"]:
                lines.append(f"| **{row.get('Category')}** | {row.get('orders')} | ₹{row.get('total_sales', 0):,.2f} | ₹{row.get('total_profit', 0):,.2f} | {row.get('profit_margin_pct', 0):.2f}% | {row.get('avg_rating', 0):.2f} |")
            lines.append("")

        if "top_products" in tool_context:
            lines.append("#### Top Ranked Products")
            lines.append("| Product Name | Category | Revenue (INR) | Units | Profit (INR) | Margin % |")
            lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for row in tool_context["top_products"]:
                lines.append(f"| **{row.get('Product Name')}** | {row.get('Category')} | ₹{row.get('total_sales', 0):,.2f} | {row.get('units_sold')} | ₹{row.get('total_profit', 0):,.2f} | {row.get('profit_margin_pct', 0):.2f}% |")
            lines.append("")

        if "profit_margins" in tool_context:
            lines.append("#### Profit Margins by Dimension")
            for row in tool_context["profit_margins"][:5]:
                dim_key = [k for k in row.keys() if k not in ["orders", "total_sales", "total_profit", "avg_discount", "avg_rating", "profit_margin_pct"]][0]
                lines.append(f"- **{row.get(dim_key)}:** Margin **{row.get('profit_margin_pct')}%** (Sales: ₹{row.get('total_sales', 0):,.2f}, Profit: ₹{row.get('total_profit', 0):,.2f})")
            lines.append("")

        if "discount_impact" in tool_context:
            lines.append("#### Discount Band Performance")
            lines.append("| Discount Band | Orders | Total Sales | Total Profit | Profit Margin % | Avg Rating |")
            lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for row in tool_context["discount_impact"]:
                lines.append(f"| **{row.get('Discount Band')}%** | {row.get('orders')} | ₹{row.get('total_sales', 0):,.2f} | ₹{row.get('total_profit', 0):,.2f} | {row.get('profit_margin_pct', 0):.2f}% | {row.get('avg_rating', 0):.2f} |")
            lines.append("")

        if "correlations" in tool_context:
            lines.append("#### Statistical Correlation Insights")
            corrs = tool_context["correlations"]
            if "discount_vs_profit" in corrs:
                lines.append(f"- **Discount vs Profit:** {corrs['discount_vs_profit']['relationship']}")
            if "discount_vs_margin" in corrs:
                lines.append(f"- **Discount vs Margin %:** {corrs['discount_vs_margin']['relationship']}")
            if "discount_vs_rating" in corrs:
                lines.append(f"- **Discount vs Rating:** {corrs['discount_vs_rating']['relationship']}")
            lines.append("")

        if "loss_pockets" in tool_context:
            lp = tool_context["loss_pockets"]
            lines.append("#### Loss Pockets & Vulnerabilities")
            lines.append(f"- **Total Loss Orders:** {lp.get('loss_orders_count')} ({lp.get('loss_percentage_of_all_orders')}% of total)")
            lines.append(f"- **Total Profit Loss:** ₹{abs(lp.get('total_negative_profit_inr', 0)):,.2f}")
            lines.append(f"- **Primary Root Cause:** {lp.get('key_driver')}\n")

        if "forecast" in tool_context:
            fc = tool_context["forecast"]
            lines.append("#### 3-Month Forward Forecast (Holt-Winters Model)")
            lines.append("| Period | Projected Revenue | Expected Profit | Projected Margin % | Uncertainty Range |")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")
            for f in fc.get("forecasts", []):
                lines.append(f"| **{f.get('period')}** | ₹{f.get('forecast_revenue_inr', 0):,.2f} | ₹{f.get('forecast_profit_inr', 0):,.2f} | {f.get('projected_profit_margin_pct', 0):.2f}% | ₹{f.get('forecast_revenue_lower_bound', 0):,.2f} - ₹{f.get('forecast_revenue_upper_bound', 0):,.2f} |")
            lines.append(f"\n> ⚠️ *{fc.get('uncertainty_disclosure')}*\n")

        if "clustering" in tool_context:
            cl = tool_context["clustering"]
            lines.append("#### KMeans Behavioral Customer/Order Archetypes")
            for p in cl.get("cluster_profiles", []):
                lines.append(f"- **Cluster {p.get('cluster_id')}: {p.get('segment_name')}** ({p.get('order_share_pct')}% of orders)")
                lines.append(f"  - *Avg Ticket:* ₹{p.get('avg_price_inr', 0):,.2f} | *Avg Qty:* {p.get('avg_quantity')} | *Avg Discount:* {p.get('avg_discount_pct')}% | *Avg Profit:* ₹{p.get('avg_profit_inr', 0):,.2f}")
                lines.append(f"  - *Strategy:* {p.get('strategic_description')}")
            lines.append("")

        if "rag" in tool_context:
            rag_info = tool_context["rag"].get("knowledge_base_retrieval", {})
            if "error" in rag_info:
                lines.append(f"#### 📚 Knowledge Base Retrieval Error\n{rag_info['error']}\n")
            elif rag_info.get("retrieved_information"):
                lines.append("#### 📚 Retrieved Knowledge Base Policies")
                for doc in rag_info["retrieved_information"]:
                    lines.append(f"> {doc}\n")
            else:
                lines.append("#### 📚 Knowledge Base Retrieval\nNo relevant policies found.\n")

        if "recommendations" in tool_context:
            lines.append("#### Prioritized Strategic Recommendations")
            for r in tool_context["recommendations"]:
                lines.append(f"1. **[{r.get('priority')}] {r.get('title')}**")
                lines.append(f"   - *Observation:* {r.get('observation')}")
                lines.append(f"   - *Action Plan:* {r.get('action')}")
                lines.append(f"   - *Impact:* {r.get('projected_impact')}")
            lines.append("")

        return "\n".join(lines)

# Global singleton
_GLOBAL_LLM_PROVIDER = None

def get_llm_provider() -> LLMProvider:
    global _GLOBAL_LLM_PROVIDER
    if _GLOBAL_LLM_PROVIDER is None:
        _GLOBAL_LLM_PROVIDER = LLMProvider()
    return _GLOBAL_LLM_PROVIDER
