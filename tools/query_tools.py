"""
Flipkart Sales Intelligence System - Flexible Custom Query & Entity Lookup Tools
Allows dynamic filtering, entity lookups, and multidimensional aggregation across all 1,000 records.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from tools.base import load_sales_data, register_tool

@register_tool(name="lookup_entity_analytics", description="Lookup detailed sales, profit, margin, and rating metrics for specific products, categories, regions, or payment methods.")
def lookup_entity_analytics(
    product_name: Optional[str] = None,
    category: Optional[str] = None,
    region: Optional[str] = None,
    segment: Optional[str] = None,
    payment_method: Optional[str] = None,
    year_month: Optional[str] = None
) -> Dict[str, Any]:
    df = load_sales_data()
    subset = df.copy()
    
    filters_applied = {}
    if product_name:
        # Case insensitive substring match
        matched_prods = [p for p in df["Product Name"].unique() if product_name.lower() in p.lower()]
        if matched_prods:
            subset = subset[subset["Product Name"].isin(matched_prods)]
            filters_applied["Product Name"] = matched_prods
    if category:
        matched_cats = [c for c in df["Category"].unique() if category.lower() in c.lower()]
        if matched_cats:
            subset = subset[subset["Category"].isin(matched_cats)]
            filters_applied["Category"] = matched_cats
    if region:
        matched_regs = [r for r in df["Region"].unique() if region.lower() in r.lower()]
        if matched_regs:
            subset = subset[subset["Region"].isin(matched_regs)]
            filters_applied["Region"] = matched_regs
    if segment:
        matched_segs = [s for s in df["Customer Segment"].unique() if segment.lower() in s.lower()]
        if matched_segs:
            subset = subset[subset["Customer Segment"].isin(matched_segs)]
            filters_applied["Customer Segment"] = matched_segs
    if payment_method:
        matched_pays = [p for p in df["Payment Method"].unique() if payment_method.lower() in p.lower()]
        if matched_pays:
            subset = subset[subset["Payment Method"].isin(matched_pays)]
            filters_applied["Payment Method"] = matched_pays
    if year_month:
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
    avg_disc = round(float(subset["Discount %"].mean()), 1)
    
    # Sub-breakdowns if applicable
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
        "average_order_value_inr": aov,
        "average_customer_rating": avg_rating,
        "average_discount_pct": avg_disc,
        "top_products_in_subset": top_products_in_subset
    }

@register_tool(name="get_full_dataset_summary_matrix", description="Returns complete summary matrices for all 25 products, 5 categories, 4 regions, 6 payment methods, and 3 segments.")
def get_full_dataset_summary_matrix() -> Dict[str, Any]:
    df = load_sales_data()
    
    def agg_dim(col):
        g = df.groupby(col).agg(
            orders=("Order ID", "count"),
            units=("Quantity Sold", "sum"),
            revenue=("Total Sales (INR)", "sum"),
            profit=("Profit (INR)", "sum"),
            avg_rating=("Customer Rating", "mean"),
            avg_discount=("Discount %", "mean")
        ).reset_index()
        g["margin_pct"] = np.round((g["profit"] / g["revenue"]) * 100, 2)
        g["avg_rating"] = np.round(g["avg_rating"], 2)
        g["avg_discount"] = np.round(g["avg_discount"], 1)
        return g.to_dict(orient="records")
        
    # Product Matrix
    prod_g = df.groupby(["Product Name", "Category"]).agg(
        orders=("Order ID", "count"),
        units=("Quantity Sold", "sum"),
        revenue=("Total Sales (INR)", "sum"),
        profit=("Profit (INR)", "sum"),
        avg_price=("Price (INR)", "mean"),
        avg_rating=("Customer Rating", "mean"),
        avg_discount=("Discount %", "mean")
    ).reset_index()
    prod_g["margin_pct"] = np.round((prod_g["profit"] / prod_g["revenue"]) * 100, 2)
    prod_g["avg_price"] = np.round(prod_g["avg_price"], 2)
    prod_g["avg_rating"] = np.round(prod_g["avg_rating"], 2)
    prod_g["avg_discount"] = np.round(prod_g["avg_discount"], 1)

    return {
        "products_catalog_matrix": prod_g.sort_values("revenue", ascending=False).to_dict(orient="records"),
        "categories_matrix": agg_dim("Category"),
        "regions_matrix": agg_dim("Region"),
        "segments_matrix": agg_dim("Customer Segment"),
        "payment_methods_matrix": agg_dim("Payment Method"),
        "discount_bands_matrix": agg_dim("Discount Band"),
    }
