"""
Flipkart Sales Intelligence System - Real-World Sales Analytics Tools
Provides tools for revenue, unit volume, order velocity, AOV, return rates,
top/bottom merchandise rankings, multi-dimensional slicing, and interactive Plotly visuals.
"""

import os
import json
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional
from tools.base import load_sales_data, register_tool

@register_tool(
    name="get_kpi_summary",
    description="Calculate executive KPIs: Gross Revenue, Net Realized Revenue, Gross Profit, Realized Profit, Margins, Orders, Return Rate, Units Sold, Rating, and AOV across the real 133,503 dataset."
)
def get_kpi_summary() -> Dict[str, Any]:
    df = load_sales_data()
    total_sales = float(df["Total Sales (INR)"].sum())
    total_profit = float(df["Profit (INR)"].sum())
    total_units = int(df["Quantity Sold"].sum())
    total_orders = int(len(df))
    
    # Realized metrics accounting for returns
    if "Is Returned" in df.columns:
        is_returned = df["Is Returned"]
    elif "Status" in df.columns:
        is_returned = (df["Status"] == "Returned")
    else:
        is_returned = pd.Series(False, index=df.index)
    returned_orders = int(is_returned.sum())
    return_rate = round((returned_orders / total_orders) * 100, 2) if total_orders > 0 else 0.0
    
    realized_sales = float(df["Realized Revenue (INR)"].sum()) if "Realized Revenue (INR)" in df.columns else total_sales * (1 - return_rate/100)
    realized_profit = float(df["Realized Profit (INR)"].sum()) if "Realized Profit (INR)" in df.columns else total_profit * (1 - return_rate/100)
    
    avg_rating = float(np.round(df["Customer Rating"].mean(), 2))
    aov = float(np.round(total_sales / total_orders, 2)) if total_orders > 0 else 0.0
    overall_margin = float(np.round((total_profit / total_sales) * 100, 2)) if total_sales > 0 else 0.0
    realized_margin = float(np.round((realized_profit / realized_sales) * 100, 2)) if realized_sales > 0 else 0.0
    
    avg_delivery_days = float(np.round(df["Delivery Days"].mean(), 1)) if "Delivery Days" in df.columns else 9.5
    unique_customers = int(df["CustomerID"].nunique()) if "CustomerID" in df.columns else total_orders

    return {
        "total_revenue_inr": total_sales,
        "total_profit_inr": total_profit,
        "profit_margin_pct": overall_margin,
        "realized_revenue_inr": realized_sales,
        "realized_profit_inr": realized_profit,
        "realized_margin_pct": realized_margin,
        "total_units_sold": total_units,
        "total_orders": total_orders,
        "returned_orders": returned_orders,
        "return_rate_pct": return_rate,
        "delivered_orders": total_orders - returned_orders,
        "average_customer_rating": avg_rating,
        "average_order_value_inr": aov,
        "average_delivery_days": avg_delivery_days,
        "unique_customers": unique_customers,
        "formatted_revenue": f"₹{total_sales:,.2f}",
        "formatted_profit": f"₹{total_profit:,.2f}",
        "formatted_realized_revenue": f"₹{realized_sales:,.2f}",
        "formatted_realized_profit": f"₹{realized_profit:,.2f}",
        "formatted_aov": f"₹{aov:,.2f}",
    }

@register_tool(
    name="query_sales_by_dimension",
    description="Aggregate sales and performance metrics grouped by any dimension (Category, SubCategory, Zone, Location, Delivery Type, Customer Gender, Age Group, Product Name, Status, Year, Year-Month)."
)
def query_sales_by_dimension(dimension: str = "Category") -> List[Dict[str, Any]]:
    df = load_sales_data()
    valid_dims = {
        "category": "Category",
        "subcategory": "SubCategory",
        "sub-category": "SubCategory",
        "zone": "Zone",
        "region": "Region",
        "location": "Location",
        "delivery type": "Delivery Type",
        "delivery": "Delivery Type",
        "gender": "Customer Gender",
        "customer gender": "Customer Gender",
        "age group": "Age Group",
        "segment": "Customer Segment",
        "customer segment": "Customer Segment",
        "product": "Product Name",
        "product name": "Product Name",
        "status": "Status",
        "year": "Year",
        "month": "Month",
        "year-month": "Year-Month",
        "margin band": "Margin Band",
        "discount band": "Discount Band",
        "payment": "Payment Method",
        "payment method": "Payment Method"
    }
    col = valid_dims.get(dimension.lower().strip(), dimension)
    if col not in df.columns:
        # Fallback to Category
        col = "Category"
        
    is_ret = df["Is Returned"] if "Is Returned" in df.columns else (df["Status"] == "Returned")
    df["_tmp_ret"] = is_ret.astype(int)

    grouped = df.groupby(col).agg(
        orders=("Order ID", "count"),
        total_sales=("Total Sales (INR)", "sum"),
        total_profit=("Profit (INR)", "sum"),
        units_sold=("Quantity Sold", "sum"),
        avg_price=("Sale Price (INR)", "mean"),
        avg_rating=("Customer Rating", "mean"),
        return_orders=("_tmp_ret", "sum"),
        avg_delivery_days=("Delivery Days", "mean") if "Delivery Days" in df.columns else ("Order ID", "count")
    ).reset_index()
    
    grouped["profit_margin_pct"] = np.round((grouped["total_profit"] / grouped["total_sales"]) * 100, 2)
    grouped["avg_order_value"] = np.round(grouped["total_sales"] / grouped["orders"], 2)
    grouped["avg_rating"] = np.round(grouped["avg_rating"], 2)
    grouped["return_rate_pct"] = np.round((grouped["return_orders"] / grouped["orders"]) * 100, 2)
    if "Delivery Days" in df.columns:
        grouped["avg_delivery_days"] = np.round(grouped["avg_delivery_days"], 1)
    
    # Sort by total_sales descending
    grouped = grouped.sort_values(by="total_sales", ascending=False)
    
    records = grouped.to_dict(orient="records")
    return records

@register_tool(
    name="get_top_bottom_products",
    description="Retrieve top or bottom N products ranked by Total Sales, Profit, Units Sold, Rating, or Return Rate."
)
def get_top_bottom_products(n: int = 5, metric: str = "Total Sales (INR)", ascending: bool = False) -> List[Dict[str, Any]]:
    df = load_sales_data()
    
    is_ret = df["Is Returned"] if "Is Returned" in df.columns else (df["Status"] == "Returned")
    df["_tmp_ret"] = is_ret.astype(int)

    grouped = df.groupby(["Product Name", "Category"]).agg(
        orders=("Order ID", "count"),
        total_sales=("Total Sales (INR)", "sum"),
        total_profit=("Profit (INR)", "sum"),
        units_sold=("Quantity Sold", "sum"),
        avg_rating=("Customer Rating", "mean"),
        return_orders=("_tmp_ret", "sum")
    ).reset_index()
    
    grouped["profit_margin_pct"] = np.round((grouped["total_profit"] / grouped["total_sales"]) * 100, 2)
    grouped["return_rate_pct"] = np.round((grouped["return_orders"] / grouped["orders"]) * 100, 2)
    grouped["avg_rating"] = np.round(grouped["avg_rating"], 2)
    
    metric_lower = metric.lower().strip()
    if "profit" in metric_lower:
        sort_col = "total_profit"
    elif "quantity" in metric_lower or "units" in metric_lower:
        sort_col = "units_sold"
    elif "rating" in metric_lower:
        sort_col = "avg_rating"
    elif "return" in metric_lower:
        sort_col = "return_rate_pct"
    else:
        sort_col = "total_sales"
        
    sorted_df = grouped.sort_values(by=sort_col, ascending=ascending).head(n)
    return sorted_df.to_dict(orient="records")

@register_tool(
    name="get_monthly_sales_trend",
    description="Calculate chronological monthly sales, profit, order count, and return rate across 6 years (2015-2020)."
)
def get_monthly_sales_trend() -> List[Dict[str, Any]]:
    df = load_sales_data()
    is_ret = df["Is Returned"] if "Is Returned" in df.columns else (df["Status"] == "Returned")
    df["_tmp_ret"] = is_ret.astype(int)

    monthly = df.groupby("Year-Month").agg(
        orders=("Order ID", "count"),
        total_sales=("Total Sales (INR)", "sum"),
        total_profit=("Profit (INR)", "sum"),
        units_sold=("Quantity Sold", "sum"),
        return_orders=("_tmp_ret", "sum"),
        avg_rating=("Customer Rating", "mean")
    ).reset_index().sort_values("Year-Month")
    
    monthly["profit_margin_pct"] = np.round((monthly["total_profit"] / monthly["total_sales"]) * 100, 2)
    monthly["avg_order_value"] = np.round(monthly["total_sales"] / monthly["orders"], 2)
    monthly["return_rate_pct"] = np.round((monthly["return_orders"] / monthly["orders"]) * 100, 2)
    monthly["avg_rating"] = np.round(monthly["avg_rating"], 2)
    monthly["sales_growth_pct"] = np.round(monthly["total_sales"].pct_change() * 100, 2).fillna(0.0)
    
    return monthly.to_dict(orient="records")

@register_tool(
    name="generate_sales_chart",
    description="Generate an interactive Plotly chart (bar, line, pie, donut) and save to outputs/charts/."
)
def generate_sales_chart(chart_type: str = "bar", dimension: str = "Category", metric: str = "Total Sales (INR)", title: Optional[str] = None) -> Dict[str, Any]:
    df = load_sales_data()
    os.makedirs("outputs/charts", exist_ok=True)
    
    valid_dims = {
        "category": "Category",
        "subcategory": "SubCategory",
        "zone": "Zone",
        "region": "Region",
        "location": "Location",
        "delivery type": "Delivery Type",
        "delivery": "Delivery Type",
        "gender": "Customer Gender",
        "age group": "Age Group",
        "product": "Product Name",
        "month": "Year-Month",
        "status": "Status",
        "margin band": "Margin Band"
    }
    dim_col = valid_dims.get(dimension.lower().strip(), "Category")
    
    if chart_type == "bar":
        agg_df = df.groupby(dim_col)["Total Sales (INR)"].sum().reset_index().sort_values("Total Sales (INR)", ascending=False).head(15)
        fig = px.bar(
            agg_df,
            x=dim_col,
            y="Total Sales (INR)",
            title=title or f"Total Sales (INR) by {dim_col}",
            color=dim_col,
            template="plotly_dark",
            labels={"Total Sales (INR)": "Revenue (₹)", dim_col: dim_col},
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig.update_layout(
            showlegend=False,
            font=dict(family="Plus Jakarta Sans, sans-serif"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        
    elif chart_type == "line":
        agg_df = df.groupby("Year-Month").agg(
            Revenue=("Total Sales (INR)", "sum"),
            Profit=("Profit (INR)", "sum")
        ).reset_index().sort_values("Year-Month")
        fig = px.line(
            agg_df,
            x="Year-Month",
            y=["Revenue", "Profit"],
            title=title or "Chronological Monthly Revenue & Profit Trajectory (2015-2020)",
            template="plotly_dark",
            markers=True,
            color_discrete_map={"Revenue": "#6366F1", "Profit": "#10B981"}
        )
        fig.update_layout(
            font=dict(family="Plus Jakarta Sans, sans-serif"),
            yaxis_title="Amount in INR (₹)",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        
    elif chart_type in ["pie", "donut"]:
        agg_df = df.groupby(dim_col)["Total Sales (INR)"].sum().reset_index().sort_values("Total Sales (INR)", ascending=False).head(10)
        fig = px.pie(
            agg_df,
            names=dim_col,
            values="Total Sales (INR)",
            hole=0.45 if chart_type == "donut" else 0.0,
            title=title or f"Revenue Distribution by {dim_col}",
            template="plotly_dark",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_layout(
            font=dict(family="Plus Jakarta Sans, sans-serif"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
    else:
        # Default bar
        agg_df = df.groupby(dim_col)["Total Sales (INR)"].sum().reset_index().sort_values("Total Sales (INR)", ascending=False)
        fig = px.bar(
            agg_df,
            x=dim_col,
            y="Total Sales (INR)",
            title=title or f"Total Revenue by {dim_col}",
            color=dim_col,
            template="plotly_dark"
        )
        fig.update_layout(
            font=dict(family="Plus Jakarta Sans, sans-serif"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        
    filename = f"chart_{dim_col.lower().replace(' ', '_')}_{chart_type}.json"
    file_path = os.path.join("outputs/charts", filename)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(fig.to_json())
        
    return {
        "chart_type": chart_type,
        "title": title or f"Sales Chart by {dim_col}",
        "file_path": file_path,
        "figure_json": fig.to_json()
    }
