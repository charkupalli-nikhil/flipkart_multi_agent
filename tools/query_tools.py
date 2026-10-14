"""
Flipkart Sales Intelligence System - Flexible Custom Query & Entity Lookup Tools
Allows dynamic filtering, entity lookups, and multidimensional aggregation across all 133,503 records.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from tools.base import load_sales_data, register_tool

@register_tool(
    name="lookup_entity_analytics",
    description="Lookup detailed sales, profit, margin, returns, and rating metrics for specific products, categories, subcategories, zones, locations, delivery types, or demographics."
)
def lookup_entity_analytics(
    product_name: Optional[str] = None,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    zone: Optional[str] = None,
    location: Optional[str] = None,
    region: Optional[str] = None,
    delivery_type: Optional[str] = None,
    status: Optional[str] = None,
    customer_gender: Optional[str] = None,
    age_group: Optional[str] = None,
    year_month: Optional[str] = None
) -> Dict[str, Any]:
    df = load_sales_data()
    subset = df.copy()
    
    filters_applied = {}
    if product_name:
        matched_prods = [p for p in df["Product Name"].unique() if product_name.lower() in p.lower()]
        if matched_prods:
            subset = subset[subset["Product Name"].isin(matched_prods)]
            filters_applied["Product Name"] = matched_prods[:3]
    if category:
        matched_cats = [c for c in df["Category"].unique() if category.lower() in c.lower()]
        if matched_cats:
            subset = subset[subset["Category"].isin(matched_cats)]
            filters_applied["Category"] = matched_cats
    if subcategory:
        matched_subcats = [sc for sc in df["SubCategory"].unique() if subcategory.lower() in sc.lower()]
        if matched_subcats:
            subset = subset[subset["SubCategory"].isin(matched_subcats)]
            filters_applied["SubCategory"] = matched_subcats
    if zone:
        matched_zones = [z for z in df["Zone"].unique() if zone.lower() in z.lower()]
        if matched_zones:
            subset = subset[subset["Zone"].isin(matched_zones)]
            filters_applied["Zone"] = matched_zones
    target_loc = location or region
    if target_loc:
        matched_locs = [l for l in df["Location"].unique() if target_loc.lower() in l.lower()]
        if matched_locs:
            subset = subset[subset["Location"].isin(matched_locs)]
            filters_applied["Location"] = matched_locs
    if delivery_type:
        matched_dt = [d for d in df["Delivery Type"].unique() if delivery_type.lower() in d.lower()]
        if matched_dt:
            subset = subset[subset["Delivery Type"].isin(matched_dt)]
            filters_applied["Delivery Type"] = matched_dt
    if status:
        matched_st = [s for s in df["Status"].unique() if status.lower() in s.lower()]
        if matched_st:
            subset = subset[subset["Status"].isin(matched_st)]
            filters_applied["Status"] = matched_st
    if customer_gender:
        matched_g = [g for g in df["Customer Gender"].unique() if customer_gender.upper() == g.upper() or customer_gender.lower() in ("male" if g=="M" else "female")]
        if matched_g:
            subset = subset[subset["Customer Gender"].isin(matched_g)]
            filters_applied["Customer Gender"] = matched_g
    if age_group and "Age Group" in df.columns:
        matched_ag = [a for a in df["Age Group"].unique() if age_group.lower() in a.lower()]
        if matched_ag:
            subset = subset[subset["Age Group"].isin(matched_ag)]
            filters_applied["Age Group"] = matched_ag
    if year_month and "Year-Month" in df.columns:
        matched_ym = [ym for ym in df["Year-Month"].unique() if year_month in ym]
        if matched_ym:
            subset = subset[subset["Year-Month"].isin(matched_ym)]
            filters_applied["Year-Month"] = matched_ym

    if len(subset) == 0:
        return {
            "status": "not_found",
            "filters_applied": filters_applied,
            "message": "No transactions found matching specified criteria."
        }
        
    tot_sales = float(subset["Total Sales (INR)"].sum())
    tot_profit = float(subset["Profit (INR)"].sum())
    orders = len(subset)
    units = int(subset["Quantity Sold"].sum())
    margin = round((tot_profit / tot_sales) * 100, 2) if tot_sales > 0 else 0.0
    aov = round(tot_sales / orders, 2) if orders > 0 else 0.0
    avg_rating = round(float(subset["Customer Rating"].mean()), 2)
    
    is_ret = subset["Is Returned"] if "Is Returned" in subset.columns else (subset["Status"] == "Returned")
    return_orders_count = int(is_ret.sum())
    return_rate_pct = round((return_orders_count / orders) * 100, 2) if orders > 0 else 0.0
    
    top_products_in_subset = subset.groupby("Product Name").agg(
        sales=("Total Sales (INR)", "sum"),
        profit=("Profit (INR)", "sum"),
        units=("Quantity Sold", "sum")
    ).reset_index().sort_values("sales", ascending=False).head(5).to_dict(orient="records")
    
    return {
        "status": "found",
        "filters_applied": filters_applied,
        "matched_orders_count": orders,
        "total_revenue_inr": tot_sales,
        "total_profit_inr": tot_profit,
        "profit_margin_pct": margin,
        "total_units_sold": units,
        "returned_orders_count": return_orders_count,
        "return_rate_pct": return_rate_pct,
        "average_order_value_inr": aov,
        "average_customer_rating": avg_rating,
        "top_products_in_subset": top_products_in_subset
    }

@register_tool(
    name="get_full_dataset_summary_matrix",
    description="Returns complete summary matrices for 5 categories, 16 subcategories, 4 zones, 3 delivery types, and demographics across 133,503 records."
)
def get_full_dataset_summary_matrix() -> Dict[str, Any]:
    df = load_sales_data()
    is_ret = df["Is Returned"] if "Is Returned" in df.columns else (df["Status"] == "Returned")
    df["_tmp_ret"] = is_ret.astype(int)
    
    def agg_dim(col):
        g = df.groupby(col).agg(
            orders=("Order ID", "count"),
            units=("Quantity Sold", "sum"),
            revenue=("Total Sales (INR)", "sum"),
            profit=("Profit (INR)", "sum"),
            returns=("_tmp_ret", "sum"),
            avg_rating=("Customer Rating", "mean")
        ).reset_index()
        g["margin_pct"] = np.round((g["profit"] / g["revenue"]) * 100, 2)
        g["return_rate_pct"] = np.round((g["returns"] / g["orders"]) * 100, 2)
        g["avg_rating"] = np.round(g["avg_rating"], 2)
        return g.to_dict(orient="records")

    return {
        "categories_matrix": agg_dim("Category"),
        "subcategories_matrix": agg_dim("SubCategory"),
        "zones_matrix": agg_dim("Zone"),
        "delivery_types_matrix": agg_dim("Delivery Type"),
        "status_matrix": agg_dim("Status"),
        "customer_gender_matrix": agg_dim("Customer Gender"),
    }
