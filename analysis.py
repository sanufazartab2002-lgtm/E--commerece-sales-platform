"""
analysis.py
E-commerce Data Analysis: KPIs, sales trends, product performance,
customer segmentation (RFM), and visualizations.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams["figure.dpi"] = 110

# ---------------- Load data ----------------
orders = pd.read_csv("data/orders.csv", parse_dates=["order_date"])
customers = pd.read_csv("data/customers.csv", parse_dates=["signup_date"])
products = pd.read_csv("data/products.csv")

delivered = orders[orders["order_status"] == "Delivered"].copy()

report_lines = []
def log(line=""):
    print(line)
    report_lines.append(line)

log("=" * 60)
log("E-COMMERCE DATA ANALYSIS REPORT")
log("=" * 60)

# ---------------- 1. Core KPIs (Pandas + NumPy) ----------------
total_orders = len(orders)
total_revenue = delivered["revenue"].sum()
total_profit = delivered["profit"].sum()
avg_order_value = delivered["revenue"].mean()
cancel_rate = (orders["order_status"] == "Cancelled").mean() * 100
return_rate = (orders["order_status"] == "Returned").mean() * 100
unique_customers = orders["customer_id"].nunique()

log("\n--- CORE KPIs ---")
log(f"Total Orders            : {total_orders:,}")
log(f"Unique Customers        : {unique_customers:,}")
log(f"Total Revenue (Delivered): Rs {total_revenue:,.2f}")
log(f"Total Profit (Delivered) : Rs {total_profit:,.2f}")
log(f"Avg Order Value          : Rs {avg_order_value:,.2f}")
log(f"Cancellation Rate        : {cancel_rate:.2f}%")
log(f"Return Rate              : {return_rate:.2f}%")

# ---------------- 2. Monthly Revenue Trend ----------------
monthly = delivered.set_index("order_date").resample("ME")["revenue"].sum()

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(monthly.index, monthly.values, marker="o", color="#2563eb", linewidth=2)
ax.set_title("Monthly Revenue Trend", fontsize=13, fontweight="bold")
ax.set_ylabel("Revenue (Rs)")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1e5:.1f}L"))
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig("charts/01_monthly_revenue_trend.png")
plt.close(fig)

# ---------------- 3. Revenue by Category ----------------
cat_rev = delivered.groupby("category")["revenue"].sum().sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(8, 4.5))
bars = ax.bar(cat_rev.index, cat_rev.values, color="#0891b2")
ax.set_title("Revenue by Category", fontsize=13, fontweight="bold")
ax.set_ylabel("Revenue (Rs)")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1e5:.1f}L"))
plt.xticks(rotation=30, ha="right")
fig.tight_layout()
fig.savefig("charts/02_revenue_by_category.png")
plt.close(fig)

log("\n--- TOP CATEGORIES BY REVENUE ---")
for cat, rev in cat_rev.head(5).items():
    log(f"  {cat:<18}: Rs {rev:,.2f}")

# ---------------- 4. Top 10 Products ----------------
top_products = (delivered.groupby("product_name")["revenue"]
                 .sum().sort_values(ascending=False).head(10))

fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(top_products.index[::-1], top_products.values[::-1], color="#16a34a")
ax.set_title("Top 10 Products by Revenue", fontsize=13, fontweight="bold")
ax.set_xlabel("Revenue (Rs)")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1e3:.0f}K"))
fig.tight_layout()
fig.savefig("charts/03_top10_products.png")
plt.close(fig)

# ---------------- 5. Payment Method Distribution ----------------
pay_dist = orders["payment_method"].value_counts()

fig, ax = plt.subplots(figsize=(6, 6))
ax.pie(pay_dist.values, labels=pay_dist.index, autopct="%1.1f%%",
       colors=plt.cm.Set2.colors, startangle=90)
ax.set_title("Payment Method Distribution", fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig("charts/04_payment_methods.png")
plt.close(fig)

# ---------------- 6. Revenue by City ----------------
city_rev = (delivered.merge(customers[["customer_id", "city"]], on="customer_id")
            .groupby("city")["revenue"].sum().sort_values(ascending=False))

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.bar(city_rev.index, city_rev.values, color="#ea580c")
ax.set_title("Revenue by City", fontsize=13, fontweight="bold")
ax.set_ylabel("Revenue (Rs)")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1e5:.1f}L"))
plt.xticks(rotation=30, ha="right")
fig.tight_layout()
fig.savefig("charts/05_revenue_by_city.png")
plt.close(fig)

# ---------------- 7. RFM Customer Segmentation ----------------
snapshot_date = delivered["order_date"].max() + pd.Timedelta(days=1)

rfm = delivered.groupby("customer_id").agg(
    Recency=("order_date", lambda x: (snapshot_date - x.max()).days),
    Frequency=("order_id", "count"),
    Monetary=("revenue", "sum"),
).reset_index()

# NumPy-based quantile scoring (1-4)
def score_col(series, reverse=False):
    q = np.nanquantile(series, [0.25, 0.5, 0.75])
    def scorer(v):
        if v <= q[0]:
            return 4 if reverse else 1
        elif v <= q[1]:
            return 3 if reverse else 2
        elif v <= q[2]:
            return 2 if reverse else 3
        else:
            return 1 if reverse else 4
    return series.apply(scorer)

rfm["R_Score"] = score_col(rfm["Recency"], reverse=True)   # lower recency = better
rfm["F_Score"] = score_col(rfm["Frequency"])
rfm["M_Score"] = score_col(rfm["Monetary"])
rfm["RFM_Score"] = rfm["R_Score"] + rfm["F_Score"] + rfm["M_Score"]

def segment(row):
    if row["RFM_Score"] >= 10:
        return "Champions"
    elif row["RFM_Score"] >= 8:
        return "Loyal Customers"
    elif row["RFM_Score"] >= 6:
        return "Potential Loyalists"
    elif row["RFM_Score"] >= 4:
        return "At Risk"
    else:
        return "Lost / Inactive"

rfm["Segment"] = rfm.apply(segment, axis=1)
rfm.to_csv("data/rfm_segments.csv", index=False)

seg_counts = rfm["Segment"].value_counts()
seg_revenue = rfm.groupby("Segment")["Monetary"].sum().sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.bar(seg_counts.index, seg_counts.values, color="#9333ea")
ax.set_title("Customer Segments (RFM)", fontsize=13, fontweight="bold")
ax.set_ylabel("Number of Customers")
plt.xticks(rotation=20, ha="right")
fig.tight_layout()
fig.savefig("charts/06_customer_segments.png")
plt.close(fig)

log("\n--- CUSTOMER SEGMENTS (RFM ANALYSIS) ---")
for seg, cnt in seg_counts.items():
    rev = seg_revenue.get(seg, 0)
    log(f"  {seg:<22}: {cnt:>4} customers | Revenue: Rs {rev:,.2f}")

# ---------------- 8. Correlation: price vs quantity (NumPy) ----------------
corr = np.corrcoef(delivered["price"], delivered["quantity"])[0, 1]
log(f"\nCorrelation (Price vs Quantity ordered): {corr:.3f}")

# ---------------- Save text report ----------------
with open("ecommerce_analysis_report.txt", "w") as f:
    f.write("\n".join(report_lines))

log("\nAll charts saved to charts/. Full report saved to ecommerce_analysis_report.txt")
