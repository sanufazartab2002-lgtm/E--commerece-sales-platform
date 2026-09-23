"""Small production-style analytics API and static file server."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import json
import mimetypes

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
DATA = ROOT / "data"
PORT = 8000


def load(name, dates=()):
    frame = pd.read_csv(DATA / f"{name}.csv")
    for column in dates:
        frame[column] = pd.to_datetime(frame[column], errors="coerce")
    return frame


orders = load("orders", ["order_date"])
customers = load("customers", ["signup_date"])
products = load("products")
items = load("order_items")
marketing = load("marketing", ["date"])
returns = load("returns", ["return_date"])
payments = load("payments", ["transaction_date"])
inventory = load("inventory")


def money(value):
    return round(float(value or 0), 2)


def filter_orders(query):
    frame = orders.copy()
    if query.get("from"):
        frame = frame[frame.order_date >= pd.Timestamp(query["from"])]
    if query.get("to"):
        frame = frame[frame.order_date <= pd.Timestamp(query["to"])]
    if query.get("year") and query["year"] != "all":
        frame = frame[frame.order_date.dt.year == int(query["year"])]
    if query.get("month") and query["month"] != "all":
        frame = frame[frame.order_date.dt.month == int(query["month"])]
    if query.get("category") and query["category"] != "all":
        category_products = products.loc[products.category.eq(query["category"]), "product_id"]
        category_orders = items[items.product_id.isin(category_products)].order_id.unique()
        frame = frame[frame.order_id.isin(category_orders)]
    if query.get("channel") and query["channel"] != "all":
        frame = frame[frame.marketing_channel.eq(query["channel"])]
    if query.get("payment") and query["payment"] != "all":
        frame = frame[frame.payment_method.eq(query["payment"])]
    if query.get("location") and query["location"] != "all":
        city_customers = customers.loc[customers.city.eq(query["location"]), "customer_id"]
        frame = frame[frame.customer_id.isin(city_customers)]
    return frame


def monthly_data(frame):
    if frame.empty:
        return []
    grouped = frame.assign(month=frame.order_date.dt.to_period("M")).groupby("month", as_index=False).agg(
        revenue=("revenue", "sum"), profit=("profit", "sum"), orders=("order_id", "nunique"), discounts=("discount", "sum"),
        customers=("customer_id", "nunique"), expenses=("cost", "sum"))
    grouped["label"] = grouped.month.astype(str)
    grouped["aov"] = grouped.revenue / grouped.orders.replace(0, np.nan)
    grouped["growth"] = grouped.revenue.pct_change().fillna(0) * 100
    return grouped.replace({np.nan: 0}).to_dict("records")


def overview(query):
    frame = filter_orders(query)
    valid = frame[~frame.order_status.eq("Cancelled")]
    prev_start = frame.order_date.min() - pd.Timedelta(days=max((frame.order_date.max() - frame.order_date.min()).days, 1)) if not frame.empty else pd.Timestamp("2022-01-01")
    previous = orders[(orders.order_date >= prev_start) & (orders.order_date < frame.order_date.min())] if not frame.empty else orders.iloc[0:0]
    revenue = valid.revenue.sum()
    prev_revenue = previous[~previous.order_status.eq("Cancelled")].revenue.sum()
    category = valid.groupby("category", as_index=False).agg(revenue=("revenue", "sum"), profit=("profit", "sum"), orders=("order_id", "nunique"), units=("order_id", "count")) if "category" in valid else pd.DataFrame()
    if category.empty:
        item_view = items.merge(products[["product_id", "category", "product_name"]], on="product_id")
        item_view = item_view[item_view.order_id.isin(valid.order_id)]
        category = item_view.groupby("category", as_index=False).agg(units=("quantity", "sum"), revenue=("line_revenue", "sum"), orders=("order_id", "nunique"))
        category["profit"] = category.revenue * .32
    top = valid.sort_values("revenue", ascending=False).head(8)[["order_id", "revenue", "profit"]].copy()
    order_items = items.merge(products[["product_id", "product_name", "category"]], on="product_id")
    order_items = order_items[order_items.order_id.isin(valid.order_id)]
    top_products = order_items.groupby(["product_id", "product_name"], as_index=False).agg(revenue=("line_revenue", "sum"), units=("quantity", "sum"), profit=("line_revenue", "sum")) .sort_values("revenue", ascending=False).head(8)
    payment_mix = valid.groupby("payment_method", as_index=False).agg(orders=("order_id", "nunique"), revenue=("revenue", "sum"))
    channel = valid.groupby("marketing_channel", as_index=False).agg(revenue=("revenue", "sum"), orders=("order_id", "nunique"), customers=("customer_id", "nunique"))
    channel_spend = marketing.groupby("channel", as_index=False).spend.sum().rename(columns={"channel": "marketing_channel"})
    channel = channel.merge(channel_spend, on="marketing_channel", how="left").fillna(0)
    channel["roas"] = channel.revenue / channel.spend.replace(0, np.nan)
    channel["cac"] = channel.spend / channel.customers.replace(0, np.nan)
    returning = valid.groupby("customer_id").order_id.nunique().gt(1).sum()
    return {"summary": {"revenue": money(revenue), "profit": money(valid.profit.sum()), "orders": int(frame.order_id.nunique()), "completed": int(frame.order_status.eq("Completed").sum()), "cancelled": int(frame.order_status.eq("Cancelled").sum()), "returned": int(frame.order_status.eq("Returned").sum()), "customers": int(valid.customer_id.nunique()), "new_customers": int(valid.customer_id.nunique() - returning), "returning_customers": int(returning), "aov": money(revenue / max(valid.order_id.nunique(), 1)), "margin": money(valid.profit.sum() / max(revenue, 1) * 100), "return_rate": money(frame.order_status.isin(["Returned", "Refunded"]).mean() * 100), "refunds": money(returns[returns.order_id.isin(frame.order_id)].refund_amount.sum()), "discounts": money(valid.discount.sum()), "revenue_growth": money((revenue / prev_revenue - 1) * 100) if prev_revenue else 0}, "monthly": monthly_data(valid), "categories": category.sort_values("revenue", ascending=False).fillna(0).to_dict("records"), "top_products": top_products.fillna(0).to_dict("records"), "payments": payment_mix.fillna(0).to_dict("records"), "channels": channel.fillna(0).to_dict("records"), "insights": build_insights(category, channel, valid), "filters": {"years": sorted(orders.order_date.dt.year.unique().tolist()), "categories": sorted(products.category.unique().tolist()), "cities": sorted(customers.city.unique().tolist()), "channels": sorted(marketing.channel.unique().tolist()), "payments": sorted(payments.payment_method.unique().tolist())}}


def build_insights(category, channel, frame):
    insights = []
    if not frame.empty:
        latest = frame.assign(month=frame.order_date.dt.to_period("M")).groupby("month").revenue.sum()
        if len(latest) > 1:
            growth = (latest.iloc[-1] / latest.iloc[-2] - 1) * 100
            insights.append({"tone": "up" if growth >= 0 else "down", "title": f"Revenue {abs(growth):.1f}% {'up' if growth >= 0 else 'down'} month over month", "text": "The latest trading month sets the current run-rate for planning."})
    if not category.empty:
        winner = category.sort_values("revenue", ascending=False).iloc[0]
        margin = winner.profit / max(winner.revenue, 1) * 100
        insights.append({"tone": "neutral", "title": f"{winner['category']} leads revenue", "text": f"It generated {money(winner['revenue']):,.0f} with an estimated {margin:.1f}% contribution margin."})
    if not channel.empty:
        best = channel.replace([np.inf, -np.inf], np.nan).dropna(subset=["roas"]).sort_values("roas", ascending=False).head(1)
        if not best.empty:
            row = best.iloc[0]
            insights.append({"tone": "up", "title": f"{row['marketing_channel']} is the strongest channel", "text": f"ROAS is {row['roas']:.1f}x on {money(row['spend']):,.0f} of spend."})
    return insights


def orders_payload(query):
    frame = filter_orders(query).sort_values("order_date", ascending=False)
    search = query.get("search", "").lower()
    if search:
        frame = frame[frame.apply(lambda row: search in f"{row.order_id} {row.customer_id} {row.payment_method} {row.order_status}".lower(), axis=1)]
    total = len(frame)
    page = max(int(query.get("page", 1)), 1)
    limit = min(max(int(query.get("limit", 10)), 1), 100)
    page_frame = frame.iloc[(page - 1) * limit:page * limit].copy()
    page_frame["order_date"] = page_frame.order_date.dt.strftime("%Y-%m-%d")
    return {"rows": page_frame.fillna(0).to_dict("records"), "total": total, "page": page, "pages": max((total + limit - 1) // limit, 1)}


def products_payload(query):
    valid = filter_orders(query)
    item_view = items[items.order_id.isin(valid.order_id)].merge(products, on="product_id")
    result = item_view.groupby(["product_id", "product_name", "category", "brand", "selling_price", "cost_price", "rating"], as_index=False).agg(units_sold=("quantity", "sum"), revenue=("line_revenue", "sum"), cost=("cost", "sum"))
    result["profit"] = result.revenue - result.cost
    result["margin"] = result.profit / result.revenue.replace(0, np.nan) * 100
    return {"rows": result.sort_values("revenue", ascending=False).fillna(0).head(100).to_dict("records")}


def export_csv(query):
    frame = filter_orders(query).copy()
    return frame.to_csv(index=False)


class Handler(BaseHTTPRequestHandler):
    def send_json(self, value, status=200):
        body = json.dumps(value, default=str).encode()
        self.send_response(status); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(body))); self.send_header("Access-Control-Allow-Origin", "*"); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        query = {key: value[-1] for key, value in parse_qs(parsed.query).items()}
        try:
            if parsed.path == "/api/overview": self.send_json(overview(query)); return
            if parsed.path == "/api/orders": self.send_json(orders_payload(query)); return
            if parsed.path == "/api/products": self.send_json(products_payload(query)); return
            if parsed.path == "/api/export":
                body = export_csv(query).encode(); self.send_response(200); self.send_header("Content-Type", "text/csv"); self.send_header("Content-Disposition", "attachment; filename=orders-export.csv"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
            path = ROOT / ("dashboard.html" if parsed.path in ("", "/") else parsed.path.lstrip("/"))
            if path.exists() and path.is_file():
                body = path.read_bytes(); self.send_response(200); self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "text/plain"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
            self.send_json({"error": "Not found"}, 404)
        except Exception as error:
            self.send_json({"error": str(error)}, 500)


if __name__ == "__main__":
    print(f"Commerce intelligence server running at http://localhost:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
