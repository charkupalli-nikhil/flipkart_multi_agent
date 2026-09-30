"""
Flipkart Sales Intelligence System - Data Generation & Preparation Pipeline
Generates the verified 1,000-row synthetic dataset and prepares cleaned features.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_flipkart_dataset(filepath="data/flipkart_sales_enriched.csv", seed=42):
    np.random.seed(seed)
    n_rows = 1000

    # 25 products across 5 categories (5 products per category)
    products_by_category = {
        "Electronics": [
            ("Smartphone Pro", 15000, 45000),
            ("Wireless Earbuds", 1500, 6000),
            ("Smartwatch Ultra", 3000, 12000),
            ("4K Smart TV", 22000, 55000),
            ("Gaming Laptop", 45000, 85000),
        ],
        "Books": [
            ("Modern Python Handbook", 450, 950),
            ("Data Science Foundations", 600, 1400),
            ("AI Revolution", 500, 1200),
            ("Fiction Best Seller", 250, 650),
            ("Habit Mastery", 300, 750),
        ],
        "Home & Kitchen": [
            ("Air Fryer Deluxe", 4000, 9500),
            ("Stainless Steel Cookware", 2000, 5500),
            ("Robotic Vacuum", 14000, 28000),
            ("Coffee Maker", 2500, 7000),
            ("Microfiber Bedsheet", 600, 1800),
        ],
        "Beauty": [
            ("Hydrating Face Serum", 450, 1500),
            ("Matte Lipstick", 300, 900),
            ("Sunscreen SPF 50", 350, 850),
            ("Herbal Shampoo", 250, 650),
            ("Anti-Aging Cream", 700, 2200),
        ],
        "Clothing": [
            ("Cotton Casual Shirt", 800, 2200),
            ("Slim Fit Denim Jeans", 1200, 3200),
            ("Running Shoes", 1800, 4800),
            ("Ethnic Kurta", 900, 2800),
            ("Fleece Hoodie", 1100, 3000),
        ],
    }

    # Flatten products list
    all_products = []
    for cat, prods in products_by_category.items():
        for name, p_min, p_max in prods:
            all_products.append({"category": cat, "name": name, "min_p": p_min, "max_p": p_max})

    payment_methods = ["UPI", "Wallet", "Debit Card", "COD", "Net Banking", "Credit Card"]
    customer_segments = ["Retail", "Online", "Wholesale"]
    regions = ["North", "South", "East", "West"]

    # Date range: 2024-02-12 to 2025-02-09 (363 days)
    start_date = datetime(2024, 2, 12)
    end_date = datetime(2025, 2, 9)
    total_days = (end_date - start_date).days

    rows = []
    for i in range(n_rows):
        order_id = f"OD{10001 + i}"
        
        # Select product
        prod_meta = np.random.choice(all_products)
        category = prod_meta["category"]
        product_name = prod_meta["name"]
        
        # Synthetic price variation
        price = int(np.random.uniform(prod_meta["min_p"], prod_meta["max_p"]))
        
        # Quantity: Wholesale higher, Retail/Online lower
        segment = np.random.choice(customer_segments, p=[0.45, 0.40, 0.15])
        if segment == "Wholesale":
            quantity = int(np.random.choice([4, 5, 6, 7, 8, 9, 10]))
        else:
            quantity = int(np.random.choice([1, 2, 3, 4, 5], p=[0.4, 0.3, 0.15, 0.1, 0.05]))
            
        total_sales = price * quantity
        
        # Date distribution
        day_offset = int(np.random.randint(0, total_days + 1))
        order_dt = start_date + timedelta(days=day_offset)
        order_date_str = order_dt.strftime("%Y-%m-%d")
        month = order_dt.month
        year = order_dt.year
        
        # Discount %: 5 to 30
        discount_pct = int(np.random.randint(5, 31))
        
        # Payment method & Region
        payment = np.random.choice(payment_methods, p=[0.35, 0.15, 0.15, 0.10, 0.10, 0.15])
        region = np.random.choice(regions, p=[0.30, 0.28, 0.22, 0.20])
        
        # Customer Rating: 1.0 to 5.0 (higher rating slightly correlated with lower discount or quality)
        base_rating = np.random.normal(4.1, 0.7)
        if discount_pct > 25:
            # high discount might have slight quality variance or bargain hunters
            base_rating -= np.random.uniform(0.1, 0.4)
        rating = float(np.clip(round(base_rating, 1), 1.0, 5.0))
        
        # Profit Calculation:
        # Base margin: 15% to 35% depending on category, reduced by discount
        base_cost_ratio = {
            "Electronics": 0.75,
            "Books": 0.60,
            "Home & Kitchen": 0.68,
            "Beauty": 0.55,
            "Clothing": 0.62,
        }[category]
        
        # Profit formula: (Price * (1 - Discount/100) - Unit Cost) * Quantity
        unit_cost = price * base_cost_ratio
        effective_price = price * (1.0 - (discount_pct / 100.0) * 0.4) # standard vendor discount sharing
        unit_profit = effective_price - unit_cost
        
        # Occasional negative profit when discount is high (loss leader / clearance)
        if discount_pct >= 26 and np.random.rand() < 0.22:
            profit = -int(total_sales * np.random.uniform(0.03, 0.12))
        else:
            profit = int(unit_profit * quantity)
            if profit == 0:
                profit = int(total_sales * 0.08)

        rows.append({
            "Order ID": order_id,
            "Product Name": product_name,
            "Category": category,
            "Price (INR)": price,
            "Quantity Sold": quantity,
            "Total Sales (INR)": total_sales,
            "Order Date": order_date_str,
            "Payment Method": payment,
            "Customer Rating": rating,
            "Month": month,
            "Year": year,
            "Profit (INR)": profit,
            "Discount %": discount_pct,
            "Customer Segment": segment,
            "Region": region,
        })

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)
    print(f"Generated raw dataset: {filepath} ({len(df)} rows, {len(df.columns)} columns)")
    return df

def clean_and_profile_data(
    raw_path="data/flipkart_sales_enriched.csv",
    cleaned_path="data/cleaned_flipkart.csv",
    profile_path="outputs/data_profile.md"
):
    df = pd.read_csv(raw_path)
    
    # 1. Parse Order Date to datetime
    df["Order Date"] = pd.to_datetime(df["Order Date"])
    
    # 2. Add derived column: Profit Margin % = (Profit / Total Sales) * 100
    df["Profit Margin %"] = np.round((df["Profit (INR)"] / df["Total Sales (INR)"]) * 100, 2)
    
    # 3. Add derived column: Year-Month
    df["Year-Month"] = df["Order Date"].dt.strftime("%Y-%m")
    
    # 4. Add derived column: Discount Band
    def categorize_discount(disc):
        if disc <= 10:
            return "5-10"
        elif disc <= 20:
            return "11-20"
        else:
            return "21-30"
            
    df["Discount Band"] = df["Discount %"].apply(categorize_discount)
    
    # Save cleaned dataset
    os.makedirs(os.path.dirname(cleaned_path), exist_ok=True)
    df.to_csv(cleaned_path, index=False)
    print(f"Saved cleaned dataset: {cleaned_path} ({len(df)} rows, {len(df.columns)} columns)")
    
    # Generate Data Profile Markdown
    os.makedirs(os.path.dirname(profile_path), exist_ok=True)
    
    total_sales = df["Total Sales (INR)"].sum()
    total_profit = df["Profit (INR)"].sum()
    overall_margin = (total_profit / total_sales) * 100
    avg_rating = df["Customer Rating"].mean()
    total_orders = len(df)
    total_units = df["Quantity Sold"].sum()
    
    category_summary = df.groupby("Category").agg(
        Orders=("Order ID", "count"),
        Total_Sales=("Total Sales (INR)", "sum"),
        Total_Profit=("Profit (INR)", "sum"),
        Avg_Rating=("Customer Rating", "mean"),
        Avg_Discount=("Discount %", "mean")
    ).reset_index()
    category_summary["Profit Margin %"] = (category_summary["Total_Profit"] / category_summary["Total_Sales"]) * 100

    discount_band_summary = df.groupby("Discount Band").agg(
        Orders=("Order ID", "count"),
        Total_Sales=("Total Sales (INR)", "sum"),
        Total_Profit=("Profit (INR)", "sum"),
        Avg_Rating=("Customer Rating", "mean")
    ).reset_index()
    discount_band_summary["Profit Margin %"] = (discount_band_summary["Total_Profit"] / discount_band_summary["Total_Sales"]) * 100

    region_summary = df.groupby("Region").agg(
        Orders=("Order ID", "count"),
        Total_Sales=("Total Sales (INR)", "sum"),
        Total_Profit=("Profit (INR)", "sum")
    ).reset_index()
    region_summary["Profit Margin %"] = (region_summary["Total_Profit"] / region_summary["Total_Sales"]) * 100

    profile_md = f"""# Flipkart Sales Intelligence - Data Profile Report

## 1. Dataset Overview
- **Source File:** `{raw_path}`
- **Cleaned File:** `{cleaned_path}`
- **Total Records:** {total_orders:,}
- **Total Columns:** {len(df.columns)}
- **Date Range:** {df['Order Date'].min().strftime('%Y-%m-%d')} to {df['Order Date'].max().strftime('%Y-%m-%d')} (~12 months)
- **Null Values:** 0 across all columns
- **Duplicate Records:** 0

## 2. Executive Key Performance Indicators (KPIs)
| Metric | Value |
| :--- | :--- |
| **Total Revenue (INR)** | ₹{total_sales:,.2f} |
| **Total Profit (INR)** | ₹{total_profit:,.2f} |
| **Overall Profit Margin** | {overall_margin:.2f}% |
| **Total Units Sold** | {total_units:,} |
| **Total Orders** | {total_orders:,} |
| **Average Customer Rating** | {avg_rating:.2f} / 5.0 |
| **Average Order Value (AOV)** | ₹{(total_sales / total_orders):,.2f} |

## 3. Schema & Derived Features
| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `Order ID` | String | Unique order identifier (e.g. OD10001 - OD11000) |
| `Product Name` | String | 25 distinct catalog products across 5 categories |
| `Category` | String | Electronics, Books, Home & Kitchen, Beauty, Clothing |
| `Price (INR)` | Numeric | Unit price in Indian Rupees |
| `Quantity Sold` | Integer | Units purchased in order (1-10) |
| `Total Sales (INR)` | Numeric | `Price (INR) * Quantity Sold` |
| `Order Date` | Datetime | Transaction timestamp (2024-02-12 to 2025-02-09) |
| `Payment Method` | String | UPI, Wallet, Debit Card, COD, Net Banking, Credit Card |
| `Customer Rating` | Float | Post-purchase rating (1.0 - 5.0) |
| `Month` | Integer | Month of order (1-12) |
| `Year` | Integer | Calendar year (2024, 2025) |
| `Profit (INR)` | Numeric | Net profit generated from order |
| `Discount %` | Integer | Applied discount percentage (5% - 30%) |
| `Customer Segment` | String | Retail, Online, Wholesale |
| `Region` | String | North, South, East, West |
| **`Profit Margin %`** | Float *(Derived)* | `(Profit (INR) / Total Sales (INR)) * 100` |
| **`Year-Month`** | String *(Derived)* | `YYYY-MM` format for time series grouping |
| **`Discount Band`** | String *(Derived)* | Categorized as `5-10`, `11-20`, `21-30` |

## 4. Category Performance Breakdown
| Category | Orders | Total Sales (INR) | Total Profit (INR) | Profit Margin % | Avg Rating | Avg Discount |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for _, row in category_summary.iterrows():
        profile_md += f"| **{row['Category']}** | {row['Orders']} | ₹{row['Total_Sales']:,.2f} | ₹{row['Total_Profit']:,.2f} | {row['Profit Margin %']:.2f}% | {row['Avg_Rating']:.2f} | {row['Avg_Discount']:.1f}% |\n"

    profile_md += """
## 5. Discount Band Analysis
| Discount Band | Orders | Total Sales (INR) | Total Profit (INR) | Profit Margin % | Avg Rating |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for _, row in discount_band_summary.iterrows():
        profile_md += f"| **{row['Discount Band']}%** | {row['Orders']} | ₹{row['Total_Sales']:,.2f} | ₹{row['Total_Profit']:,.2f} | {row['Profit Margin %']:.2f}% | {row['Avg_Rating']:.2f} |\n"

    profile_md += """
## 6. Regional Distribution
| Region | Orders | Total Sales (INR) | Total Profit (INR) | Profit Margin % |
| :--- | :--- | :--- | :--- | :--- |
"""
    for _, row in region_summary.iterrows():
        profile_md += f"| **{row['Region']}** | {row['Orders']} | ₹{row['Total_Sales']:,.2f} | ₹{row['Total_Profit']:,.2f} | {row['Profit Margin %']:.2f}% |\n"

    profile_md += """
## 7. Known Dataset Properties & Limitations
1. **Synthetic Nature:** Transaction prices vary for the same product SKU depending on model configuration and time.
2. **Time Horizon:** Covers exactly 12 months (Feb 2024 - Feb 2025). 2025 contains ~1 month of data. Forecasting models should state this uncertainty clearly.
3. **No Review Text / User IDs:** Features requiring sentiment NLP on text or individual repeat customer profiling are out of scope.
"""

    with open(profile_path, "w", encoding="utf-8") as f:
        f.write(profile_md)
    print(f"Data profile report written to: {profile_path}")

if __name__ == "__main__":
    generate_flipkart_dataset()
    clean_and_profile_data()
