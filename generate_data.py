"""Generate a realistic, relational e-commerce dataset for the analytics app."""
from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(2026)
ROOT = Path(__file__).parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

START = pd.Timestamp("2022-01-01")
END = pd.Timestamp("2026-08-31")
CATEGORIES = {
    "Electronics": (1800, 90000), "Fashion": (350, 9500),
    "Beauty": (180, 4200), "Home & Kitchen": (250, 18000),
    "Sports": (300, 12000), "Grocery": (60, 2500),
    "Books": (120, 2200), "Accessories": (150, 6500),
}
CITIES = {
    "Mumbai": "Maharashtra", "Pune": "Maharashtra", "Delhi": "Delhi",
    "Bengaluru": "Karnataka", "Hyderabad": "Telangana", "Chennai": "Tamil Nadu",
    "Kolkata": "West Bengal", "Ahmedabad": "Gujarat", "Jaipur": "Rajasthan",
    "Lucknow": "Uttar Pradesh", "Kochi": "Kerala", "Indore": "Madhya Pradesh",
}
BRANDS = ["Northstar", "Aster & Co.", "Mosaic", "Luma", "Cedar Lane", "Orbit", "Solace", "Pioneer"]


def date_series(size: int) -> pd.Series:
    days = (END - START).days
    return pd.Series(START + pd.to_timedelta(RNG.integers(0, days + 1, size), unit="D"))


def generate_products() -> pd.DataFrame:
    rows = []
    names = ["Pro", "Essential", "Studio", "Everyday", "Max", "Select", "Classic", "Plus"]
    for index in range(600):
        category = list(CATEGORIES)[index % len(CATEGORIES)]
        low, high = CATEGORIES[category]
        price = round(float(np.exp(RNG.uniform(np.log(low), np.log(high)))), 2)
        rows.append({
            "product_id": f"P{index + 1:05d}",
            "product_name": f"{BRANDS[index % len(BRANDS)]} {category} {names[index % len(names)]} {index + 1:03d}",
            "category": category, "brand": BRANDS[index % len(BRANDS)],
            "selling_price": price, "cost_price": round(price * RNG.uniform(.48, .76), 2),
            "rating": round(float(np.clip(RNG.normal(4.2, .45), 2.7, 5)), 1),
            "reorder_level": int(RNG.integers(15, 75)),
        })
    return pd.DataFrame(rows)


def generate_customers() -> pd.DataFrame:
    cities = RNG.choice(list(CITIES), 5200, p=[.16, .09, .14, .14, .09, .09, .07, .07, .05, .04, .03, .03])
    first = ["Aarav", "Diya", "Kabir", "Meera", "Arjun", "Anaya", "Rohan", "Ishita", "Vihaan", "Sara"]
    last = ["Sharma", "Patel", "Khan", "Iyer", "Mehta", "Reddy", "Singh", "Nair", "Das", "Kapoor"]
    return pd.DataFrame({
        "customer_id": [f"C{i:06d}" for i in range(1, 5201)],
        "name": [f"{RNG.choice(first)} {RNG.choice(last)}" for _ in range(5200)],
        "age": RNG.integers(18, 68, 5200),
        "gender": RNG.choice(["Female", "Male", "Non-binary"], 5200, p=[.48, .49, .03]),
        "city": cities, "state": [CITIES[city] for city in cities], "country": "India",
        "signup_date": date_series(5200).dt.strftime("%Y-%m-%d"),
    })


def generate_orders(products: pd.DataFrame, customers: pd.DataFrame):
    n_orders = 26000
    dates = date_series(n_orders)
    month_boost = np.where(dates.dt.month.isin([10, 11, 12]), 1.28, 1.0)
    weights = RNG.pareto(2.2, len(customers)) + .2
    customer_ids = RNG.choice(customers.customer_id, n_orders, p=weights / weights.sum())
    statuses = RNG.choice(["Completed", "Processing", "Cancelled", "Returned", "Refunded"], n_orders, p=[.77, .08, .06, .055, .035])
    payment = RNG.choice(["Credit Card", "Debit Card", "UPI", "PayPal", "Cash on Delivery", "Wallet"], n_orders, p=[.25, .17, .27, .10, .13, .08])
    channels = RNG.choice(["Google Ads", "Meta Ads", "Instagram", "Email", "Organic Search", "Direct", "Affiliate", "Referral"], n_orders, p=[.16, .16, .08, .13, .17, .14, .08, .08])
    rows, item_rows = [], []
    for i in range(n_orders):
        order_id = f"O{i + 1:07d}"
        item_count = int(RNG.choice([1, 2, 3, 4], p=[.52, .3, .13, .05]))
        selected = products.iloc[RNG.choice(len(products), item_count, replace=False)]
        discount_rate = float(np.clip(RNG.normal(.11, .07), 0, .35))
        subtotal = 0.0
        cost = 0.0
        for _, product in selected.iterrows():
            quantity = int(RNG.integers(1, 4))
            line_revenue = product.selling_price * quantity * month_boost[i]
            subtotal += line_revenue
            cost += product.cost_price * quantity
            item_rows.append({"order_id": order_id, "product_id": product.product_id, "quantity": quantity,
                              "unit_price": product.selling_price, "discount": round(line_revenue * discount_rate, 2),
                              "line_revenue": round(line_revenue * (1 - discount_rate), 2), "cost": round(product.cost_price * quantity, 2)})
        shipping = 0 if subtotal > 2500 else 99
        discount = subtotal * discount_rate
        revenue = max(0, subtotal - discount + shipping)
        rows.append({"order_id": order_id, "customer_id": customer_ids[i], "order_date": dates[i].strftime("%Y-%m-%d"),
                     "payment_method": payment[i], "marketing_channel": channels[i], "order_status": statuses[i],
                     "subtotal": round(subtotal, 2), "discount": round(discount, 2), "shipping_revenue": shipping,
                     "revenue": round(revenue, 2), "cost": round(cost, 2), "profit": round(revenue - cost, 2)})
    return pd.DataFrame(rows), pd.DataFrame(item_rows)


def main():
    products = generate_products()
    customers = generate_customers()
    orders, items = generate_orders(products, customers)
    completed = orders[orders.order_status.isin(["Completed", "Processing", "Returned", "Refunded"])]
    returns = completed.sample(frac=.105, random_state=7).copy()
    returns = returns.assign(return_id=lambda d: [f"R{i:06d}" for i in range(1, len(d) + 1)],
                            return_date=lambda d: pd.to_datetime(d.order_date) + pd.to_timedelta(RNG.integers(1, 30, len(d)), unit="D"),
                            return_reason=RNG.choice(["Damaged Product", "Wrong Product", "Size Issue", "Customer Changed Mind", "Late Delivery", "Quality Issue"], len(returns)),
                            refund_amount=lambda d: (d.revenue * RNG.uniform(.65, 1, len(d))).round(2))
    returns = returns[["return_id", "order_id", "customer_id", "return_date", "return_reason", "refund_amount"]]
    payments = orders[["order_id", "payment_method", "revenue"]].copy()
    payments.insert(0, "payment_id", [f"PAY{i:07d}" for i in range(1, len(payments) + 1)])
    payments["payment_status"] = np.where(orders.order_status.eq("Cancelled"), "Failed", RNG.choice(["Successful", "Successful", "Successful", "Failed"], len(orders)))
    payments["transaction_date"] = orders.order_date
    spend = pd.DataFrame({"marketing_id": [f"M{i:06d}" for i in range(1, 6001)], "date": date_series(6000).dt.strftime("%Y-%m-%d"),
                          "channel": RNG.choice(["Google Ads", "Meta Ads", "Instagram", "Email", "Organic Search", "Direct", "Affiliate", "Referral"], 6000),
                          "spend": RNG.uniform(600, 42000, 6000).round(2), "impressions": RNG.integers(3000, 300000, 6000),
                          "clicks": RNG.integers(120, 14000, 6000), "conversions": RNG.integers(2, 260, 6000)})
    stock = RNG.integers(0, 420, len(products))
    inventory = products[["product_id", "product_name", "category", "cost_price", "reorder_level"]].copy()
    inventory["current_stock"] = stock
    inventory["inventory_value"] = (stock * inventory.cost_price).round(2)
    inventory["stock_status"] = np.select([stock == 0, stock < inventory.reorder_level, stock > 300], ["Out of Stock", "Low Stock", "Overstocked"], default="In Stock")
    for frame, name in [(customers, "customers"), (products, "products"), (orders, "orders"), (items, "order_items"), (payments, "payments"), (returns, "returns"), (spend, "marketing"), (inventory, "inventory")]:
        frame.to_csv(DATA / f"{name}.csv", index=False)
    print(f"Generated {len(customers):,} customers, {len(products):,} products, {len(orders):,} orders, {len(items):,} order items, {len(returns):,} returns, and {len(payments):,} payments.")


if __name__ == "__main__":
    main()
