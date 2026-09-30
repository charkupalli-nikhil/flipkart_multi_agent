"""
Flipkart Sales Intelligence System - Tools Module
"""

from tools.base import load_sales_data, register_tool, execute_tool_with_trace, TOOL_REGISTRY
from tools.sales_tools import (
    get_kpi_summary,
    query_sales_by_dimension,
    get_top_bottom_products,
    get_monthly_sales_trend,
    generate_sales_chart,
)
from tools.profit_tools import (
    analyze_profit_margins,
    analyze_discount_impact,
    compute_correlations,
    identify_loss_pockets,
    payment_method_analysis,
    generate_profit_chart,
)
from tools.advisor_tools import (
    forecast_sales_and_profit,
    perform_kmeans_clustering,
    generate_strategic_recommendations,
)
from tools.query_tools import (
    lookup_entity_analytics,
    get_full_dataset_summary_matrix,
)
from tools.llm_provider import LLMProvider, get_llm_provider

__all__ = [
    "load_sales_data",
    "register_tool",
    "execute_tool_with_trace",
    "TOOL_REGISTRY",
    "get_kpi_summary",
    "query_sales_by_dimension",
    "get_top_bottom_products",
    "get_monthly_sales_trend",
    "generate_sales_chart",
    "analyze_profit_margins",
    "analyze_discount_impact",
    "compute_correlations",
    "identify_loss_pockets",
    "payment_method_analysis",
    "generate_profit_chart",
    "forecast_sales_and_profit",
    "perform_kmeans_clustering",
    "generate_strategic_recommendations",
    "lookup_entity_analytics",
    "get_full_dataset_summary_matrix",
    "LLMProvider",
    "get_llm_provider",
]
