 # Northstar Commerce Intelligence

Production-style e-commerce BI dashboard with a relational synthetic dataset, server-side Pandas analytics, responsive Chart.js visualizations, filters, insights, exports, product performance, order ledger, marketing efficiency, and inventory risk.

## Run locally

```bash
python -m pip install pandas numpy
python generate_data.py
python app.py
```

Open `http://localhost:8000`.

## Architecture

```text
data/*.csv -> app.py analytics API -> dashboard.html + Chart.js
```

The API caches CSV tables in memory, applies year/month/category/city/channel filters, and returns aggregates or paginated rows rather than loading the whole warehouse into the browser.

## Dataset

The generator creates reproducible data from 2022 through August 2026 with seasonal demand, multi-line orders, customer repeat behavior, discounts, payment failures, returns, marketing spend, and inventory statuses.

| Table | Rows | Purpose |
|---|---:|---|
| `customers.csv` | 5,200 | Profiles and geography |
| `products.csv` | 600 | Catalog, prices, costs, ratings |
| `orders.csv` | 26,000 | Order headers and economics |
| `order_items.csv` | 44,544 | Line items and discounts |
| `payments.csv` | 26,000 | Payment method and status |
| `returns.csv` | 2,572 | Return reasons and refunds |
| `marketing.csv` | 6,000 | Spend, reach, clicks, conversions |
| `inventory.csv` | 600 | Stock and reorder risk |

## API

- `GET /api/overview` returns KPIs, monthly series, category economics, payment mix, channel performance, filters, and calculated insights.
- `GET /api/orders?page=1&limit=12&search=...` returns paginated order records.
- `GET /api/products` returns product aggregates for active filters.
- `GET /api/export` downloads the filtered order ledger as CSV.

Global query filters include `year`, `month`, `category`, `location`, and `channel`.

## Key data concepts

Revenue is valid order revenue after discounts. Profit is revenue minus product cost. Margin is profit divided by revenue. AOV is revenue divided by orders. ROAS is channel revenue divided by spend. CAC is spend divided by acquired customers. Retention is returning customers divided by active customers. Return rate is returned/refunded orders divided by all orders. RFM analysis can be derived from customer recency, order frequency, and monetary value.

## Future improvements

Move CSV tables to PostgreSQL with indexed aggregate queries, add authenticated workspaces, customer cohort/RFM endpoints, geographic maps, PDF exports, scheduled reports, and background refresh jobs.
