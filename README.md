# Sales Data Analysis Dashboard

An interactive Streamlit application for uploading, validating, preprocessing, analyzing, and visualizing sales datasets.

## Features

- Upload CSV, Excel (`.xlsx`), and JSON files.
- Inspect dimensions, column names, data types, missing values, unique values, and duplicate records.
- Clean whitespace and common missing-value tokens; convert Sales, Profit, Quantity, and Discount to numeric values; parse Order Date and Ship Date.
- Choose whether to keep missing values, fill numeric columns with their median and text columns with their mode, or drop incomplete rows.
- Optionally remove duplicate rows.
- Interactive filters for Region, Category, Segment, Ship Mode, State, and Order Date (filters appear when the columns exist).
- Five dynamically updating KPIs: Total Sales, Total Profit, Total Orders (unique Order IDs), Total Quantity Sold, and Profit Margin.
- Interactive Plotly charts: Sales by Category, Profit by Region, Monthly Sales Trend, and Sales vs Profit.
- Statistical summaries and cleaned CSV download.

## Run locally

Python 3.9+ is recommended.

```bash
# 1. Create and activate a virtual environment (Windows PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the app
streamlit run app.py
```

The bundled `sample_data.csv` is loaded when no file is uploaded. Upload your own file from the sidebar to analyze it.

## GitHub upload

1. Create a new, empty repository on GitHub (for example, `sales-data-analysis-dashboard`).
2. Open a terminal in this project folder.
3. Run:

```bash
git init
git add app.py requirements.txt README.md sample_data.csv
git commit -m "Build interactive sales analytics dashboard"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/sales-data-analysis-dashboard.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username and use the repository URL shown by GitHub.

## Deploy on Streamlit Community Cloud

1. Push the project files to GitHub.
2. Sign in at https://share.streamlit.io/ using GitHub.
3. Select **Create app** and choose your repository, branch (`main`), and main file path (`app.py`).
4. Select **Deploy**.
5. When deployment completes, open the generated app URL and verify that the sample data loads, upload each supported format, test filters, and download the cleaned CSV.

No secrets or API keys are required by this application.

## Data notes

- KPI totals are calculated from the currently filtered and preprocessed rows.
- Total Orders counts distinct non-null Order IDs.
- Profit Margin = (Total Profit / Total Sales) × 100; it is shown as 0% when total sales is zero.
- Missing/invalid dates remain missing rather than being replaced with fabricated dates.
- The application only converts conventional sales field names (`Sales`, `Profit`, `Quantity`, `Discount`) and recognizes `Order Date` and `Ship Date`. Rename source columns to these names if needed.
