# Flipkart Sales Intelligence - Data Profile Report

## 1. Dataset Overview
- **Source File:** `data/flipkart_sales_enriched.csv`
- **Cleaned File:** `data/cleaned_flipkart.csv`
- **Total Records:** 1,000
- **Total Columns:** 18
- **Date Range:** 2024-02-12 to 2025-02-09 (~12 months)
- **Null Values:** 0 across all columns
- **Duplicate Records:** 0

## 2. Executive Key Performance Indicators (KPIs)
| Metric | Value |
| :--- | :--- |
| **Total Revenue (INR)** | ₹21,479,352.00 |
| **Total Profit (INR)** | ₹4,404,669.00 |
| **Overall Profit Margin** | 20.51% |
| **Total Units Sold** | 2,887 |
| **Total Orders** | 1,000 |
| **Average Customer Rating** | 4.05 / 5.0 |
| **Average Order Value (AOV)** | ₹21,479.35 |

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
| **Beauty** | 213 | ₹511,345.00 | ₹182,660.00 | 35.72% | 4.02 | 18.0% |
| **Books** | 192 | ₹386,135.00 | ₹122,929.00 | 31.84% | 4.08 | 18.0% |
| **Clothing** | 206 | ₹1,424,430.00 | ₹411,383.00 | 28.88% | 4.05 | 18.2% |
| **Electronics** | 185 | ₹14,487,672.00 | ₹2,541,733.00 | 17.54% | 4.11 | 17.7% |
| **Home & Kitchen** | 204 | ₹4,669,770.00 | ₹1,145,964.00 | 24.54% | 4.02 | 17.9% |

## 5. Discount Band Analysis
| Discount Band | Orders | Total Sales (INR) | Total Profit (INR) | Profit Margin % | Avg Rating |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **11-20%** | 395 | ₹8,487,342.00 | ₹1,858,537.00 | 21.90% | 4.07 |
| **21-30%** | 402 | ₹7,812,431.00 | ₹1,255,802.00 | 16.07% | 3.98 |
| **5-10%** | 203 | ₹5,179,579.00 | ₹1,290,330.00 | 24.91% | 4.17 |

## 6. Regional Distribution
| Region | Orders | Total Sales (INR) | Total Profit (INR) | Profit Margin % |
| :--- | :--- | :--- | :--- | :--- |
| **East** | 198 | ₹4,570,637.00 | ₹940,670.00 | 20.58% |
| **North** | 308 | ₹5,722,946.00 | ₹1,203,705.00 | 21.03% |
| **South** | 284 | ₹5,813,777.00 | ₹1,190,853.00 | 20.48% |
| **West** | 210 | ₹5,371,992.00 | ₹1,069,441.00 | 19.91% |

## 7. Known Dataset Properties & Limitations
1. **Synthetic Nature:** Transaction prices vary for the same product SKU depending on model configuration and time.
2. **Time Horizon:** Covers exactly 12 months (Feb 2024 - Feb 2025). 2025 contains ~1 month of data. Forecasting models should state this uncertainty clearly.
3. **No Review Text / User IDs:** Features requiring sentiment NLP on text or individual repeat customer profiling are out of scope.
