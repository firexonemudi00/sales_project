import io
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Sales Analytics Dashboard", page_icon="📊", layout="wide")

NUMERIC_CANDIDATES = ["Sales", "Profit", "Quantity", "Discount"]
DATE_CANDIDATES = ["Order Date", "Ship Date"]

def load_data(uploaded_file):
    """Load CSV, Excel, or JSON data into a DataFrame."""
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(uploaded_file)
    if suffix == ".xlsx":
        return pd.read_excel(uploaded_file, engine="openpyxl")
    if suffix == ".json":
        raw = uploaded_file.getvalue()
        try:
            return pd.read_json(io.BytesIO(raw))
        except ValueError:
            return pd.read_json(io.BytesIO(raw), lines=True)
    raise ValueError("Unsupported file type. Please upload CSV, XLSX, or JSON.")

def validate_data(df):
    """Return a validation report for the raw, unmodified dataset."""
    report = pd.DataFrame({
        "Column": df.columns.astype(str),
        "Data Type": df.dtypes.astype(str).values,
        "Missing Values": df.isna().sum().values,
        "Missing (%)": (df.isna().mean().values * 100).round(2),
        "Unique Values": df.nunique(dropna=True).values,
    })
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "duplicates": int(df.duplicated().sum()),
        "missing_cells": int(df.isna().sum().sum()),
        "report": report,
    }

def preprocess_data(df, missing_strategy="Keep missing values", remove_duplicates=True):
    """Clean strings, convert known numeric/date fields, and handle missing values."""
    clean = df.copy()
    clean.columns = [str(c).strip() for c in clean.columns]

    # Standardize text fields without changing genuine missing values.
    for col in clean.select_dtypes(include=["object", "string"]).columns:
        clean[col] = clean[col].map(
            lambda x: x.strip() if isinstance(x, str) else x
        )
        clean[col] = clean[col].replace({"": pd.NA, "NA": pd.NA, "N/A": pd.NA, "null": pd.NA})

    for col in NUMERIC_CANDIDATES:
        if col in clean.columns:
            clean[col] = pd.to_numeric(
                clean[col].astype("string").str.replace(",", "", regex=False),
                errors="coerce"
            )
            # Treat positive/negative infinity as invalid numeric values.
            clean[col] = clean[col].replace([float("inf"), float("-inf")], float("nan"))

    for col in DATE_CANDIDATES:
        if col in clean.columns:
            clean[col] = pd.to_datetime(clean[col], errors="coerce")

    duplicates_removed = int(clean.duplicated().sum()) if remove_duplicates else 0
    if remove_duplicates:
        clean = clean.drop_duplicates().copy()

    if missing_strategy == "Drop rows with missing values":
        clean = clean.dropna().copy()
    elif missing_strategy == "Fill numeric with median; text with mode":
        for col in clean.columns:
            if pd.api.types.is_numeric_dtype(clean[col]):
                if clean[col].isna().any():
                    median = clean[col].median()
                    clean[col] = clean[col].fillna(median)
            elif pd.api.types.is_datetime64_any_dtype(clean[col]):
                # Keep invalid/missing dates visible rather than inventing dates.
                continue
            elif clean[col].isna().any():
                modes = clean[col].mode(dropna=True)
                if not modes.empty:
                    clean[col] = clean[col].fillna(modes.iloc[0])

    return clean, duplicates_removed

def statistical_summary(df):
    """Reusable descriptive-statistics function for numeric columns."""
    numeric = df.select_dtypes(include="number")
    if numeric.empty:
        return pd.DataFrame()
    return numeric.describe().T.rename_axis("Column").reset_index()

def get_kpis(df):
    """Calculate dashboard KPIs, using safe defaults when fields are absent."""
    sales = pd.to_numeric(df["Sales"], errors="coerce").fillna(0) if "Sales" in df else pd.Series(dtype=float)
    profit = pd.to_numeric(df["Profit"], errors="coerce").fillna(0) if "Profit" in df else pd.Series(dtype=float)
    quantity = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0) if "Quantity" in df else pd.Series(dtype=float)
    orders = df["Order ID"].nunique() if "Order ID" in df else len(df)
    total_sales = float(sales.sum()) if len(sales) else 0.0
    total_profit = float(profit.sum()) if len(profit) else 0.0
    total_quantity = float(quantity.sum()) if len(quantity) else 0.0
    margin = (total_profit / total_sales * 100) if total_sales else 0.0
    return total_sales, total_profit, int(orders), total_quantity, margin

def filter_data(df, selections, date_range):
    """Apply all active dashboard filters."""
    result = df.copy()
    for column, selected in selections.items():
        if column in result.columns and selected:
            result = result[result[column].isin(selected)]
    if "Order Date" in result.columns and date_range and len(date_range) == 2:
        dates = pd.to_datetime(result["Order Date"], errors="coerce")
        start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
        result = result[dates.between(start, end)]
    return result

def money(value):
    return f"${value:,.2f}"

st.title("📊 Sales Data Analysis Dashboard")
st.caption("Upload, validate, clean, explore and visualize your sales data.")

with st.sidebar:
    st.header("Data source")
    uploaded = st.file_uploader("Upload a data file", type=["csv", "xlsx", "json"])
    st.caption("Supported formats: CSV, Excel (.xlsx), JSON (.json)")
    st.divider()
    st.header("Preprocessing options")
    missing_strategy = st.selectbox(
        "Missing-value treatment",
        ["Keep missing values", "Fill numeric with median; text with mode", "Drop rows with missing values"]
    )
    remove_duplicates = st.checkbox("Remove duplicate records", value=True)

try:
    if uploaded is not None:
        raw_df = load_data(uploaded)
        source_name = uploaded.name
    else:
        sample_path = Path(__file__).parent / "sample_data.csv"
        if sample_path.exists():
            raw_df = pd.read_csv(sample_path)
            source_name = "Bundled sample_data.csv"
            st.info("Showing the bundled sample dataset. Upload your own CSV, XLSX, or JSON file from the sidebar.")
        else:
            st.info("Upload a CSV, XLSX, or JSON file using the sidebar to begin.")
            st.stop()

    if raw_df.empty:
        st.error("The uploaded file contains no rows.")
        st.stop()
    if len(raw_df.columns) == 0:
        st.error("The uploaded file contains no columns.")
        st.stop()

    validation = validate_data(raw_df)
    st.subheader("1. Data validation")
    st.caption(f"Source: {source_name}")
    a, b, c, d = st.columns(4)
    a.metric("Rows", f"{validation['rows']:,}")
    b.metric("Columns", f"{validation['columns']:,}")
    c.metric("Duplicate records", f"{validation['duplicates']:,}")
    d.metric("Missing cells", f"{validation['missing_cells']:,}")

    with st.expander("Column-level validation details", expanded=True):
        st.dataframe(validation["report"], use_container_width=True, hide_index=True)
        st.write("Raw data preview")
        st.dataframe(raw_df.head(10), use_container_width=True)

    clean_df, duplicates_removed = preprocess_data(
        raw_df, missing_strategy=missing_strategy, remove_duplicates=remove_duplicates
    )
    st.subheader("2. Preprocessed data")
    x1, x2, x3 = st.columns(3)
    x1.metric("Rows after cleaning", f"{len(clean_df):,}")
    x2.metric("Duplicates removed", f"{duplicates_removed:,}")
    x3.metric("Remaining missing cells", f"{int(clean_df.isna().sum().sum()):,}")
    with st.expander("Cleaned data preview"):
        st.dataframe(clean_df.head(20), use_container_width=True)

    st.subheader("3. Interactive filters")
    filter_columns = ["Region", "Category", "Segment", "Ship Mode", "State"]
    available_filters = [col for col in filter_columns if col in clean_df.columns]
    selections = {}
    filter_cols = st.columns(min(3, max(1, len(available_filters))))
    for idx, col in enumerate(available_filters):
        options = sorted(clean_df[col].dropna().astype(str).unique().tolist())
        with filter_cols[idx % len(filter_cols)]:
            selected = st.multiselect(f"Filter by {col}", options, default=options, key=f"filter_{col}")
        selections[col] = selected

    date_range = None
    if "Order Date" in clean_df.columns:
        valid_dates = pd.to_datetime(clean_df["Order Date"], errors="coerce").dropna()
        if not valid_dates.empty:
            min_date, max_date = valid_dates.min().date(), valid_dates.max().date()
            date_range = st.date_input("Order date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

    filtered = filter_data(clean_df, selections, date_range)
    st.subheader("4. Key performance indicators")
    sales, profit, orders, quantity, margin = get_kpis(filtered)
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Sales", money(sales))
    k2.metric("Total Profit", money(profit))
    k3.metric("Total Orders", f"{orders:,}")
    k4.metric("Total Quantity Sold", f"{quantity:,.0f}")
    k5.metric("Profit Margin", f"{margin:.2f}%")

    st.subheader("5. Interactive visualizations")
    if filtered.empty:
        st.warning("No records match the selected filters. Change or clear your filters.")
    else:
        chart1, chart2 = st.columns(2)
        if "Category" in filtered.columns and "Sales" in filtered.columns:
            category_data = filtered.groupby("Category", dropna=False)["Sales"].sum().reset_index()
            fig = px.bar(category_data, x="Category", y="Sales", color="Category",
                         title="Sales by Category", hover_data={"Sales": ":,.2f"})
            chart1.plotly_chart(fig, use_container_width=True)
        if "Region" in filtered.columns and "Profit" in filtered.columns:
            region_data = filtered.groupby("Region", dropna=False)["Profit"].sum().reset_index()
            fig = px.bar(region_data, x="Region", y="Profit", color="Region",
                         title="Profit by Region", hover_data={"Profit": ":,.2f"})
            chart2.plotly_chart(fig, use_container_width=True)

        chart3, chart4 = st.columns(2)
        if "Order Date" in filtered.columns and "Sales" in filtered.columns:
            monthly = filtered.dropna(subset=["Order Date"]).copy()
            monthly["Month"] = monthly["Order Date"].dt.to_period("M").astype(str)
            monthly = monthly.groupby("Month", as_index=False)["Sales"].sum()
            fig = px.line(monthly, x="Month", y="Sales", markers=True, title="Monthly Sales Trend")
            chart3.plotly_chart(fig, use_container_width=True)
        if {"Sales", "Profit", "Category"}.issubset(filtered.columns):
            fig = px.scatter(filtered, x="Sales", y="Profit", color="Category",
                             size="Quantity" if "Quantity" in filtered.columns else None,
                             hover_data=[c for c in ["Order ID", "Product Name", "Region"] if c in filtered.columns],
                             title="Sales vs Profit")
            chart4.plotly_chart(fig, use_container_width=True)

    st.subheader("6. Statistical analysis")
    summary = statistical_summary(filtered)
    if summary.empty:
        st.info("No numeric columns are available for statistical summaries.")
    else:
        st.dataframe(summary, use_container_width=True, hide_index=True)

    st.subheader("7. Download cleaned data")
    csv_bytes = clean_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download cleaned dataset (CSV)", data=csv_bytes,
                       file_name="cleaned_sales_data.csv", mime="text/csv")

except Exception as exc:
    st.error(f"Unable to process this file: {exc}")
    st.info("Check that the file is a valid CSV, XLSX, or JSON file with a tabular structure.")
