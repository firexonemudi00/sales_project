import pandas as pd
from app import validate_data, preprocess_data, get_kpis, statistical_summary

def test_cleaning_and_kpis():
    raw = pd.DataFrame({
        "Order ID": ["A", "A", "B"],
        "Sales": ["100", "100", "50"],
        "Profit": ["20", "20", "5"],
        "Quantity": ["2", "2", "1"],
        "Order Date": ["2025-01-01", "2025-01-01", "bad-date"],
        "Category": [" Tech ", " Tech ", None],
    })
    report = validate_data(raw)
    assert report["rows"] == 3
    assert report["duplicates"] == 1
    cleaned, removed = preprocess_data(raw)
    assert removed == 1
    assert pd.api.types.is_numeric_dtype(cleaned["Sales"])
    assert pd.api.types.is_datetime64_any_dtype(cleaned["Order Date"])
    sales, profit, orders, qty, margin = get_kpis(cleaned)
    assert sales == 150
    assert profit == 25
    assert orders == 2
    assert qty == 3
    assert round(margin, 2) == 16.67
    assert not statistical_summary(cleaned).empty

if __name__ == "__main__":
    test_cleaning_and_kpis()
    print("Smoke tests passed.")
