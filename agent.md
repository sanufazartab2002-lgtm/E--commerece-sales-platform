# Project Analysis Agent

## Mission
Analyze the complete Northstar Commerce Intelligence project before making changes. Preserve existing behavior, use the actual generated data model, and prefer small, testable improvements.

## Project Map

- `generate_data.py`: reproducible multi-year relational CSV generator.
- `data/`: customers, products, orders, order items, payments, returns, marketing, and inventory tables.
- `app.py`: Pandas-backed REST API and static file server on `http://localhost:8000`.
- `dashboard.html`: responsive Chart.js analytics dashboard consuming API aggregates.
- `analysis.py`: legacy offline analysis and chart generation.
- `README.md`: setup, architecture, dataset, metrics, and API documentation.

## Analysis Workflow

1. Read `README.md`, then inspect the relevant source file and its data columns.
2. Identify the controlling code path before editing.
3. Trace metrics from source CSVs through `app.py` into dashboard rendering.
4. Check for data consistency, filter behavior, API errors, calculation errors, and responsive UI regressions.
5. Make the smallest focused change that fixes the root cause.
6. Validate with `python -m py_compile app.py generate_data.py` and a live API request when relevant.
7. Do not rewrite generated data unless the task requires a new dataset.

## Important Rules

- Never hardcode analytics values in the UI; derive them from API responses.
- Keep relationships intact: IDs must match across customers, products, orders, items, payments, returns, and inventory.
- Treat cancelled orders consistently when calculating revenue and profit.
- Keep API filtering server-side and avoid loading the full warehouse into the browser.
- Preserve the existing visual language and responsive behavior.
- Do not introduce a database or frontend build system without a clear requirement.
- Update `README.md` when commands, APIs, schemas, or architecture change.

## Useful Checks

```powershell
python -m py_compile app.py generate_data.py
python generate_data.py
python app.py
Invoke-RestMethod http://localhost:8000/api/overview
Invoke-RestMethod "http://localhost:8000/api/orders?page=1&limit=5"
```
