# Flipkart Sales Intelligence - Real-World Dataset Profile & Architecture Report

## 1. Executive Summary & Verification
- **Data Source:** Verified Real-World E-Commerce Transactions (`flipkart_sales_new.xlsx`)
- **Total Transactions:** **133,503** verified orders
- **Total Catalog Units Sold:** **712,502** units
- **Unique Customers:** **112,933** distinct customer profiles
- **Temporal Horizon:** **2015-01-01** to **2020-12-31** (6 Full Calendar Years: 2015–2020)
- **Data Integrity:** 0 null values across transactional features; 100% verified order reconciliation

---

## 2. Executive Key Performance Indicators (KPIs)
| Executive Metric | Gross Baseline | Realized (Post-Returns) | Business Significance |
| :--- | :--- | :--- | :--- |
| **Total Revenue (INR)** | **₹160,331,124.00** | **₹117,034,317.00** | ~₹16.03 Cr Gross GMV across 6 years |
| **Total Profit (INR)** | **₹89,167,379.00** | **₹64,733,881.00** | Operating Net Profit generated |
| **Profit Margin %** | **55.61%** | **55.31%** | Healthy structural unit margins |
| **Average Order Value (AOV)** | **₹1,200.96** | — | Average gross basket size |
| **Total Orders** | **133,503** | **97,467** delivered | 133.5k total logistics movements |
| **Return Rate** | **26.99%** | **36,036 returns** | Primary lever for profit optimization |
| **Average Customer Rating** | **★ 2.73 / 5.0** | — | Post-delivery satisfaction index |
| **Average Delivery Time** | **9.5 days** | — | Express (~3.5d), Standard (~10d), Overseas (~15d) |

---

## 3. Product Category Intelligence
| Category | Total Orders | Units Sold | Total Revenue (INR) | Total Profit (INR) | Margin % | Return Rate % | Avg Rating |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Electronics** | 12,187 | 42,842 | ₹9,643,093.00 | ₹5,334,830.00 | 55.32% | 26.50% | ★ 2.73 |
| **Fashion** | 39,432 | 217,285 | ₹48,841,540.00 | ₹27,148,692.00 | 55.59% | 27.02% | ★ 2.73 |
| **Health and beauty** | 42,447 | 234,340 | ₹52,815,725.00 | ₹29,449,771.00 | 55.76% | 27.36% | ★ 2.72 |
| **Home and Office** | 18,193 | 100,771 | ₹22,650,440.00 | ₹12,598,004.00 | 55.62% | 27.49% | ★ 2.73 |
| **Phones and Tablet** | 21,244 | 117,264 | ₹26,380,326.00 | ₹14,636,082.00 | 55.48% | 26.07% | ★ 2.75 |

---

## 4. Regional Zone & Fulfillment Distribution
| Zone | Orders | Total Revenue (INR) | Total Profit (INR) | Margin % | Return Rate % | Avg Delivery Days |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Zone 1** | 33,575 | ₹40,369,738.00 | ₹22,427,382.00 | 55.55% | 26.63% | 9.5 days |
| **Zone 2** | 24,611 | ₹29,440,230.00 | ₹16,345,042.00 | 55.52% | 26.75% | 9.5 days |
| **Zone 3** | 57,607 | ₹69,359,321.00 | ₹38,656,968.00 | 55.73% | 26.83% | 9.5 days |
| **Zone 4** | 17,710 | ₹21,161,835.00 | ₹11,737,987.00 | 55.47% | 28.55% | 9.6 days |

---

## 5. Reverse Logistics & Return Root-Cause Diagnostics
Total Returned Orders: **36,036** (26.99% of catalog orders)

| Return Reason | Incident Count | Share of Returns % | Operational Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Delivey - Missing item/part** | 7,125 | 19.77% | Fulfillment audit, automated visual SKU QA, supplier packaging penalty |
| **Quality-Defective item** | 7,114 | 19.74% | Fulfillment audit, automated visual SKU QA, supplier packaging penalty |
| **Delivery-Wrong item** | 6,955 | 19.30% | Fulfillment audit, automated visual SKU QA, supplier packaging penalty |
| **Onsite -Description mismatch** | 6,895 | 19.13% | Fulfillment audit, automated visual SKU QA, supplier packaging penalty |
| **Product - Not fitting expectation** | 6,892 | 19.13% | Fulfillment audit, automated visual SKU QA, supplier packaging penalty |
| **Not Applicable / Delivered** | 1,055 | 2.93% | Fulfillment audit, automated visual SKU QA, supplier packaging penalty |

---

## 6. Schema & Dimension Catalog
| Feature | Type | Definition & Domain |
| :--- | :--- | :--- |
| `Order ID` | String | Unique transactional order identifier |
| `Order Date` | Datetime | Transaction placement timestamp (2015-01-01 to 2020-12-31) |
| `Delivery Date` | Datetime | Final customer delivery or return processing timestamp |
| `Customer ID` | String | Unique identifier across 112,933 distinct customers |
| `Customer Age` | Integer | Demographics (17 to 79 years, mean: 35.4) |
| `Customer Gender` | String | Male (51%) and Female (49%) customer representation |
| `Age Group` | String | Categorized into Gen Z, Millennial, Gen X, and Senior |
| `Category` | String | 5 major departments: Health and beauty, Fashion, Phones and Tablet, Home and Office, Electronics |
| `SubCategory` | String | 16 specialized merchandise subcategories |
| `Product Name` | String | Verified catalog product descriptions |
| `Unit Price (INR)` | Float | Cost of Goods Sold (COGS) per merchandise unit |
| `Sale Price (INR)` | Float | Actual selling transaction price per merchandise unit |
| `Quantity Sold` | Integer | Units purchased in order (1 to 10 units) |
| `Total Sales (INR)` | Float | Gross order revenue: `Sale Price * Quantity Sold` |
| `Profit (INR)` | Float | Gross order profit: `(Sale Price - Unit Price) * Quantity Sold` |
| `Profit Margin %` | Float | Structurally computed margin percentage |
| `Shipping Fee (INR)` | Float | Freight handling fee charged/incurred |
| `Status` | String | Order fulfillment state: `Delivered` vs `Returned` |
| `Return Reason` | String | Specific root cause for returned merchandise |
| `Customer Rating` | Integer | Post-purchase satisfaction score (1 to 5 stars) |
| `Location` / `Region` | String | 26 primary metropolitan districts and regions |
| `Zone` | String | Logistics hub zones (Zone 1, Zone 2, Zone 3, Zone 4) |
| `Delivery Type` | String | Express, Standard Delivery, Shipped from Abroad |
| `Delivery Days` | Integer | Measured fulfillment lead time in business days |
| `Year-Month` | String | `YYYY-MM` format across 72 monthly operating cycles |
