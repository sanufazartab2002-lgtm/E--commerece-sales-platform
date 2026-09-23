# Northstar Commerce Intelligence: Project Interview Guide

This guide is for onboarding a developer, analyst, reviewer, or AI agent. It explains the project from business purpose through data generation, API calculation, browser rendering, testing, and future production work.

## 1. What problem does the project solve?

Northstar Commerce Intelligence gives an e-commerce business one operational view of revenue quality, profitability, orders, customers, products, marketing efficiency, payments, returns, and inventory. It is a local analytics product backed by reproducible data rather than manually typed dashboard numbers.

The intended users are business owners, product managers, marketing teams, operations teams, and business analysts. Each chart should answer a decision question such as:

- Is revenue growing, and is the growth profitable?
- Which categories and products deserve more attention?
- Which acquisition channels produce efficient revenue?
- Are customers returning or becoming at risk?
- Where are returns, refunds, payment failures, and inventory risks concentrated?

## 2. What is the complete workflow?

```text
generate_data.py
	-> data/*.csv relational warehouse
	-> app.py loads tables and applies filters
	-> REST API aggregates business metrics
	-> dashboard.html fetches JSON
	-> Chart.js, KPI cards, tables, and insights render the result
```

The normal workflow is:

1. Generate or refresh the source data with `python generate_data.py`.
2. Start the API and static server with `python app.py`.
3. Open `http://localhost:8000`.
4. Change global filters such as year, month, category, city, or channel.
5. The browser requests new server-side aggregates.
6. KPI cards, charts, product tables, marketing metrics, and insights update from the response.
7. Export the currently filtered order ledger as CSV when an operational list is needed.

## 3. What does each project file own?

### `generate_data.py`

Creates reproducible multi-year synthetic data using NumPy and Pandas. It generates realistic price ranges, customer purchase concentration, seasonal demand, discounts, order statuses, payment outcomes, returns, marketing activity, and stock risk. The fixed random seed makes a run repeatable.

### `data/`

Acts as the local warehouse. The important relationships are:

```text
customers.customer_id -> orders.customer_id
orders.order_id -> order_items.order_id
products.product_id -> order_items.product_id
orders.order_id -> payments.order_id
orders.order_id -> returns.order_id
orders.marketing_channel -> marketing.channel
products.product_id -> inventory.product_id
```

### `app.py`

Loads CSVs once at startup, parses date columns, applies query filters, calculates aggregations, builds rule-based insights, and serves both API responses and the dashboard. This is the primary source of truth for dashboard analytics.

### `dashboard.html`

Contains the responsive presentation layer. It owns navigation, filters, API requests, Chart.js configuration, KPI formatting, tables, pagination, export actions, mobile navigation, empty states, and view switching. It should display API results rather than independently recomputing business metrics.

### `analysis.py`

Legacy offline analysis that creates matplotlib charts and a text report. It is useful for exploratory analysis, but new interactive dashboard behavior should normally be added to `app.py` and `dashboard.html`.

### `README.md`

Documents installation, architecture, dataset scale, endpoints, metrics, and future improvements.

## 4. How does one order become a dashboard metric?

An order header contains its customer, date, status, payment method, marketing channel, revenue, discount, cost, and profit. Its line items connect the order to one or more products and quantities.

For the overview:

1. `filter_orders()` limits orders by the active query parameters.
2. Cancelled orders are excluded from valid revenue and profit views.
3. The filtered orders are grouped by month, category, payment method, or channel.
4. Returns are matched by `order_id` to calculate refund exposure.
5. Customers with more than one valid order contribute to returning-customer and retention metrics.
6. Marketing spend is grouped by channel to calculate ROAS and CAC.
7. The API serializes the aggregate data as JSON.
8. The dashboard formats the values and renders charts and tables.

## 5. What are the core metric definitions?

- **Revenue:** valid order revenue after discounts and shipping revenue.
- **Profit:** revenue minus product cost in the generated order ledger.
- **Profit margin:** profit divided by revenue times 100.
- **AOV:** revenue divided by valid order count.
- **Return rate:** returned or refunded orders divided by all filtered orders.
- **Retention rate:** returning customers divided by active customers.
- **ROAS:** attributed channel revenue divided by marketing spend.
- **CAC:** channel spend divided by attributed customers.
- **Discount impact:** discount value compared with revenue and profit after discount.
- **Inventory value:** current stock multiplied by product cost price.

When changing a metric, update the calculation, its label or explanation in the UI, and the README definition together.

## 6. How do I run the project?

```powershell
python -m pip install pandas numpy
python generate_data.py
python app.py
```

Open `http://localhost:8000`. The server must remain running while using the dashboard. Regenerating data while the server is running requires restarting `app.py`, because the CSV tables are loaded at startup.

## 7. How do I debug a broken metric or chart?

Use this order so the problem is isolated quickly:

1. Confirm the source CSV contains the expected column and rows.
2. Call the endpoint directly, for example `Invoke-RestMethod http://localhost:8000/api/overview`.
3. Repeat the request with the same filter that fails, such as `?year=2025&category=Electronics`.
4. Check whether the JSON field is missing, zero, or incorrectly typed.
5. Trace the API field to the corresponding render function in `dashboard.html`.
6. Inspect the browser console and network response for JavaScript errors.
7. Fix the owning layer, then run the same endpoint and browser interaction again.

Useful checks:

```powershell
python -m py_compile app.py generate_data.py
Invoke-RestMethod http://localhost:8000/api/overview
Invoke-RestMethod "http://localhost:8000/api/orders?page=1&limit=5"
Invoke-RestMethod "http://localhost:8000/api/products?year=2025"
```

## 8. What should be checked before accepting a change?

### Data quality

- IDs referenced by orders exist in customers.
- IDs referenced by order items exist in products and orders.
- Monetary values are non-negative where expected.
- Dates fall within the generated period.
- Generated row counts remain above the documented minimums.

### Analytics quality

- Filtered totals change when filters change.
- Cancelled orders are treated consistently.
- AOV equals revenue divided by valid orders.
- Return and refund metrics use the returns table.
- ROAS and CAC come from actual spend and attributed records.
- Empty filters do not produce browser errors.

### Product quality

- The dashboard loads with a populated overview.
- Charts have labels that answer a business question.
- Tables remain usable on narrow screens.
- Pagination does not load every order into the browser.
- CSV export respects the active filters.
- API failures show a visible error state.

## 9. What are the main risks?

The main risks are hardcoded UI values, duplicate metric logic in the browser, inconsistent treatment of cancelled or returned orders, broken foreign-key relationships, stale data after regeneration, unbounded API responses, and filters that update only some parts of the page.

Another important risk is confusing generated demonstration data with production accounting. The application is suitable for portfolio demonstration and local analysis; it needs authentication, database transactions, audit trails, permissions, and validated finance definitions before handling real business decisions.

## 10. How should a new feature be added?

Start by naming the business question and identifying its source tables. Add or verify the server-side calculation in `app.py`, expose only the aggregate fields needed by the browser, add the smallest UI rendering change in `dashboard.html`, and document the metric in `README.md` if it changes the public behavior.

Avoid adding a chart without a decision purpose, duplicating a calculation in JavaScript, or downloading a full source table when an aggregate endpoint is sufficient.

## 11. What are the best next improvements?

- Replace CSV loading with PostgreSQL tables and indexed aggregate queries.
- Add a dedicated customer/RFM API and cohort-retention heatmap.
- Add geographic performance maps and state-level drilldowns.
- Add campaign-level conversion funnels from impressions, clicks, and conversions.
- Add authenticated workspaces, saved filters, permissions, and audit logs.
- Add PDF reports, scheduled email summaries, and background data refresh jobs.
- Add automated API tests for metric formulas, filters, pagination, and exports.
