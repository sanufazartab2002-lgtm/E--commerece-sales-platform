# E-commerce Data Analyst Project (Python + NumPy + Pandas + Matplotlib)

Ek complete, portfolio-ready e-commerce data analysis project. Real-world jaisa
synthetic dataset generate karke, usme KPIs, sales trends, product/category
performance, aur RFM-based customer segmentation kiya gaya hai.

## Project Structure
```
ecommerce_project/
├── generate_data.py          # Synthetic dataset banata hai (customers, products, orders)
├── analysis.py                # Main analysis + charts + RFM segmentation
├── data/
│   ├── customers.csv          # 2,000 customers
│   ├── products.csv           # 56 products (7 categories)
│   ├── orders.csv             # 15,000 order records
│   └── rfm_segments.csv       # Customer-wise RFM scores & segments
├── charts/
│   ├── 01_monthly_revenue_trend.png
│   ├── 02_revenue_by_category.png
│   ├── 03_top10_products.png
│   ├── 04_payment_methods.png
│   ├── 05_revenue_by_city.png
│   └── 06_customer_segments.png
├── ecommerce_analysis_report.txt   # Text summary of all findings
├── dashboard.html              # Interactive analytics dashboard (open in browser)
└── README.md
```

## How to Run
```bash
pip install numpy pandas matplotlib
python generate_data.py   # Step 1: dataset banao
python analysis.py        # Step 2: analysis + charts generate karo
```

## Interactive Dashboard (UI)
`dashboard.html` ko seedha double-click karke browser me khol sakte ho — isme
KPIs, monthly revenue trend, category/product/city charts, payment method
split aur RFM customer segment table sab ek hi page par interactive charts
(Chart.js) ke saath hain. Ye file self-contained hai, koi server chalane ki
zarurat nahi.

## Kya-Kya Analysis Hua Hai

1. **Core KPIs** – Total orders, revenue, profit, avg order value, cancellation
   & return rate (Pandas aggregations)
2. **Monthly Revenue Trend** – Time-series resampling se seasonal patterns
   (festive months Oct-Nov me spike)
3. **Revenue by Category** – Kaunsi category sabse zyada revenue laati hai
4. **Top 10 Products** – Best-selling products by revenue
5. **Payment Method Distribution** – UPI, Card, COD, etc. ka share
6. **Revenue by City** – Geographic performance
7. **RFM Customer Segmentation** – Recency, Frequency, Monetary ke NumPy
   quantile-based scores se customers ko 5 segments me baata gaya:
   Champions, Loyal Customers, Potential Loyalists, At Risk, Lost/Inactive
8. **Correlation Analysis** – NumPy se price vs quantity correlation

## Key Insights (is sample run se)
- Total Revenue: ~₹19.7 Cr (15,000 orders me se ~88% delivered)
- Electronics category sabse zyada revenue deti hai (~₹13.5 Cr)
- 512 "Champion" customers hi total revenue ka bada hissa (~73%) generate
  karte hain — classic Pareto (80/20) pattern
- Cancellation rate 7.1%, return rate 4.6%

## Tech Stack
- **Pandas** – data loading, groupby aggregations, merges, resampling
- **NumPy** – quantile scoring, correlation, random data generation
- **Matplotlib** – line, bar, horizontal bar, and pie charts

## Next Steps (aap extend kar sakte hain)
- Real dataset (Kaggle/company data) se replace karein
- Scikit-learn se actual K-Means clustering RFM ki jagah
- Streamlit/Dash se interactive dashboard banayein
- Cohort retention analysis add karein
