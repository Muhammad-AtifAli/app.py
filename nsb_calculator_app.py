import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime, timedelta
from pathlib import Path


# ============================================================
# NSB CALCULATOR STREAMLIT APP
# ============================================================

DB_FILE = "nsb_calculator.db"
BILL_FOLDER = Path("uploaded_bills")
BILL_FOLDER.mkdir(exist_ok=True)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


conn = get_connection()
cur = conn.cursor()


# ============================================================
# CREATE TABLES
# ============================================================

def create_tables():
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            school_name TEXT,
            financial_year TEXT,
            fy_start TEXT,
            fy_end TEXT,
            opening_balance REAL DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt_date TEXT NOT NULL,
            receipt_no TEXT,
            income_details TEXT,
            source TEXT,
            amount REAL NOT NULL,
            remarks TEXT,
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenditures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voucher_no TEXT,
            purchase_date TEXT NOT NULL,
            bill_date TEXT,
            vendor_name TEXT,
            category TEXT,
            item_details TEXT,
            amount REAL NOT NULL,
            bill_file_path TEXT,
            remarks TEXT,
            created_at TEXT
        )
    """)

    conn.commit()


create_tables()


# ============================================================
# OLD DATABASE FIX / MIGRATION
# ============================================================

def column_exists(table_name, column_name):
    cur.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cur.fetchall()]
    return column_name in columns


def fix_old_database():
    if not column_exists("settings", "financial_year"):
        cur.execute("ALTER TABLE settings ADD COLUMN financial_year TEXT")

    if not column_exists("settings", "fy_start"):
        cur.execute("ALTER TABLE settings ADD COLUMN fy_start TEXT")

    if not column_exists("settings", "fy_end"):
        cur.execute("ALTER TABLE settings ADD COLUMN fy_end TEXT")

    if not column_exists("receipts", "income_details"):
        cur.execute("ALTER TABLE receipts ADD COLUMN income_details TEXT")

    if not column_exists("receipts", "remarks"):
        cur.execute("ALTER TABLE receipts ADD COLUMN remarks TEXT")

    if not column_exists("expenditures", "vendor_name"):
        cur.execute("ALTER TABLE expenditures ADD COLUMN vendor_name TEXT")

    if not column_exists("expenditures", "item_details"):
        cur.execute("ALTER TABLE expenditures ADD COLUMN item_details TEXT")

    if not column_exists("expenditures", "remarks"):
        cur.execute("ALTER TABLE expenditures ADD COLUMN remarks TEXT")

    conn.commit()


fix_old_database()


# ============================================================
# BASIC DATABASE FUNCTIONS
# ============================================================

def run_query(query, params=()):
    cur.execute(query, params)
    conn.commit()


def get_df(query, params=()):
    return pd.read_sql_query(query, conn, params=params)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def money(value):
    try:
        return f"Rs. {float(value):,.0f}"
    except:
        return "Rs. 0"


def get_fy_dates(financial_year):
    start_year = int(financial_year.split("-")[0])
    end_year = int(financial_year.split("-")[1])
    fy_start = date(start_year, 7, 1)
    fy_end = date(end_year, 6, 30)
    return fy_start, fy_end


def get_settings():
    df = get_df("SELECT * FROM settings WHERE id = 1")
    if df.empty:
        return None
    return df.iloc[0].to_dict()


def save_settings(school_name, financial_year, opening_balance):
    fy_start, fy_end = get_fy_dates(financial_year)

    run_query("""
        INSERT INTO settings
        (id, school_name, financial_year, fy_start, fy_end, opening_balance)
        VALUES (1, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            school_name = excluded.school_name,
            financial_year = excluded.financial_year,
            fy_start = excluded.fy_start,
            fy_end = excluded.fy_end,
            opening_balance = excluded.opening_balance
    """, (
        school_name,
        financial_year,
        str(fy_start),
        str(fy_end),
        opening_balance
    ))


def save_uploaded_bill(uploaded_file, voucher_no):
    if uploaded_file is None:
        return ""

    safe_voucher = voucher_no.strip() if voucher_no else "without_voucher"
    safe_voucher = safe_voucher.replace("/", "_").replace("\\", "_").replace(" ", "_")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{safe_voucher}_{uploaded_file.name}"
    file_path = BILL_FOLDER / filename

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return str(file_path)


def month_name_from_number(month_number):
    names = {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
        10: "October",
        11: "November",
        12: "December"
    }
    return names.get(month_number, "")


def create_month_rows(financial_year):
    start_year = int(financial_year.split("-")[0])
    end_year = int(financial_year.split("-")[1])

    months = [
        (7, start_year),
        (8, start_year),
        (9, start_year),
        (10, start_year),
        (11, start_year),
        (12, start_year),
        (1, end_year),
        (2, end_year),
        (3, end_year),
        (4, end_year),
        (5, end_year),
        (6, end_year),
    ]

    rows = []

    for sr, (month_no, year_no) in enumerate(months, start=1):
        rows.append({
            "Sr No.": sr,
            "Month No": month_no,
            "Year": year_no,
            "Month": f"{month_name_from_number(month_no)} ({year_no})"
        })

    return pd.DataFrame(rows)


# ============================================================
# CORRECTED LAST MONTH / TILL LAST MONTH FUNCTIONS
# These calculate according to latest entered record,
# not according to computer's current date.
# ============================================================

def get_latest_transaction_date(fy_start, fy_end):
    receipt_df = get_df("""
        SELECT MAX(receipt_date) AS latest_date
        FROM receipts
        WHERE receipt_date BETWEEN ? AND ?
    """, (str(fy_start), str(fy_end)))

    exp_df = get_df("""
        SELECT MAX(purchase_date) AS latest_date
        FROM expenditures
        WHERE purchase_date BETWEEN ? AND ?
    """, (str(fy_start), str(fy_end)))

    dates = []

    if not receipt_df.empty and receipt_df.iloc[0]["latest_date"]:
        dates.append(datetime.strptime(receipt_df.iloc[0]["latest_date"], "%Y-%m-%d").date())

    if not exp_df.empty and exp_df.iloc[0]["latest_date"]:
        dates.append(datetime.strptime(exp_df.iloc[0]["latest_date"], "%Y-%m-%d").date())

    if not dates:
        return None

    return max(dates)


def get_previous_month_range_from_latest_record(fy_start, fy_end):
    latest_date = get_latest_transaction_date(fy_start, fy_end)

    if latest_date is None:
        return None, None

    first_day_latest_month = date(latest_date.year, latest_date.month, 1)
    previous_month_end = first_day_latest_month - timedelta(days=1)

    if previous_month_end < fy_start:
        return None, None

    previous_month_start = date(previous_month_end.year, previous_month_end.month, 1)

    if previous_month_start < fy_start:
        previous_month_start = fy_start

    if previous_month_end > fy_end:
        previous_month_end = fy_end

    return previous_month_start, previous_month_end


def get_receipts_till_last_month(fy_start, fy_end):
    latest_date = get_latest_transaction_date(fy_start, fy_end)

    if latest_date is None:
        return 0

    first_day_latest_month = date(latest_date.year, latest_date.month, 1)
    previous_month_end = first_day_latest_month - timedelta(days=1)

    if previous_month_end < fy_start:
        return 0

    if previous_month_end > fy_end:
        previous_month_end = fy_end

    df = get_df("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM receipts
        WHERE receipt_date BETWEEN ? AND ?
    """, (str(fy_start), str(previous_month_end)))

    return float(df.iloc[0]["total"])


def get_expenditures_till_last_month(fy_start, fy_end):
    latest_date = get_latest_transaction_date(fy_start, fy_end)

    if latest_date is None:
        return 0

    first_day_latest_month = date(latest_date.year, latest_date.month, 1)
    previous_month_end = first_day_latest_month - timedelta(days=1)

    if previous_month_end < fy_start:
        return 0

    if previous_month_end > fy_end:
        previous_month_end = fy_end

    df = get_df("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM expenditures
        WHERE purchase_date BETWEEN ? AND ?
    """, (str(fy_start), str(previous_month_end)))

    return float(df.iloc[0]["total"])


def get_last_month_receipts(fy_start, fy_end):
    previous_month_start, previous_month_end = get_previous_month_range_from_latest_record(fy_start, fy_end)

    if previous_month_start is None or previous_month_end is None:
        return 0

    df = get_df("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM receipts
        WHERE receipt_date BETWEEN ? AND ?
    """, (str(previous_month_start), str(previous_month_end)))

    return float(df.iloc[0]["total"])


def get_last_month_expenditures(fy_start, fy_end):
    previous_month_start, previous_month_end = get_previous_month_range_from_latest_record(fy_start, fy_end)

    if previous_month_start is None or previous_month_end is None:
        return 0

    df = get_df("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM expenditures
        WHERE purchase_date BETWEEN ? AND ?
    """, (str(previous_month_start), str(previous_month_end)))

    return float(df.iloc[0]["total"])


# ============================================================
# TOTAL FUNCTIONS
# ============================================================

def get_total_receipts(fy_start, fy_end):
    df = get_df("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM receipts
        WHERE receipt_date BETWEEN ? AND ?
    """, (str(fy_start), str(fy_end)))

    return float(df.iloc[0]["total"])


def get_total_expenditures(fy_start, fy_end):
    df = get_df("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM expenditures
        WHERE purchase_date BETWEEN ? AND ?
    """, (str(fy_start), str(fy_end)))

    return float(df.iloc[0]["total"])


def prepare_monthly_balance_sheet(financial_year, opening_balance):
    fy_start, fy_end = get_fy_dates(financial_year)
    month_df = create_month_rows(financial_year)

    receipts = get_df("""
        SELECT 
            strftime('%m', receipt_date) AS month_no,
            strftime('%Y', receipt_date) AS year_no,
            GROUP_CONCAT(income_details, ', ') AS income_details,
            SUM(amount) AS receipt_amount
        FROM receipts
        WHERE receipt_date BETWEEN ? AND ?
        GROUP BY year_no, month_no
    """, (str(fy_start), str(fy_end)))

    expenses = get_df("""
        SELECT 
            strftime('%m', purchase_date) AS month_no,
            strftime('%Y', purchase_date) AS year_no,
            SUM(amount) AS expenditure
        FROM expenditures
        WHERE purchase_date BETWEEN ? AND ?
        GROUP BY year_no, month_no
    """, (str(fy_start), str(fy_end)))

    if not receipts.empty:
        receipts["Month No"] = receipts["month_no"].astype(int)
        receipts["Year"] = receipts["year_no"].astype(int)
        receipts = receipts[["Month No", "Year", "income_details", "receipt_amount"]]
    else:
        receipts = pd.DataFrame(columns=["Month No", "Year", "income_details", "receipt_amount"])

    if not expenses.empty:
        expenses["Month No"] = expenses["month_no"].astype(int)
        expenses["Year"] = expenses["year_no"].astype(int)
        expenses = expenses[["Month No", "Year", "expenditure"]]
    else:
        expenses = pd.DataFrame(columns=["Month No", "Year", "expenditure"])

    final_df = month_df.merge(receipts, on=["Month No", "Year"], how="left")
    final_df = final_df.merge(expenses, on=["Month No", "Year"], how="left")

    final_df["income_details"] = final_df["income_details"].fillna("N/A")
    final_df["receipt_amount"] = final_df["receipt_amount"].fillna(0)
    final_df["expenditure"] = final_df["expenditure"].fillna(0)

    balances = []
    running_balance = opening_balance

    for _, row in final_df.iterrows():
        running_balance = running_balance + row["receipt_amount"] - row["expenditure"]
        balances.append(running_balance)

    final_df["remaining_balance"] = balances

    final_df = final_df.rename(columns={
        "income_details": "Income Details",
        "receipt_amount": "Amount",
        "expenditure": "Expenditure",
        "remaining_balance": "Remaining Balance"
    })

    final_df = final_df[[
        "Sr No.",
        "Month",
        "Income Details",
        "Amount",
        "Expenditure",
        "Remaining Balance"
    ]]

    return final_df


# ============================================================
# STREAMLIT PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="NSB Calculator",
    page_icon="🏫",
    layout="wide"
)

st.title("🏫 NSB Calculator")
st.caption("Government receipt, expenditure, voucher, bill and monthly balance sheet management system")


# ============================================================
# SIDEBAR SETTINGS
# ============================================================

st.sidebar.header("⚙️ Main Settings")

settings = get_settings()
current_year = date.today().year

if settings:
    default_school_name = settings.get("school_name", "")
    default_fy = settings.get("financial_year") or f"{current_year}-{current_year + 1}"
    default_opening_balance = float(settings.get("opening_balance", 0))
else:
    default_school_name = ""
    default_fy = f"{current_year}-{current_year + 1}"
    default_opening_balance = 0.0

with st.sidebar.form("settings_form"):
    school_name = st.text_input("School Name", value=default_school_name)

    financial_year = st.text_input(
        "Financial Year",
        value=default_fy,
        help="Write like this: 2026-2027"
    )

    opening_balance = st.number_input(
        "Balance on 30th June",
        min_value=0.0,
        value=default_opening_balance,
        step=1000.0
    )

    save_btn = st.form_submit_button("💾 Save Settings")

    if save_btn:
        try:
            get_fy_dates(financial_year)
            save_settings(school_name, financial_year, opening_balance)
            st.success("Settings saved successfully.")
            st.rerun()
        except:
            st.error("Financial Year must be written like this: 2026-2027")


settings = get_settings()

if settings is None:
    st.warning("First save settings from the left sidebar.")
    st.stop()


school_name = settings.get("school_name", "")
financial_year = settings.get("financial_year") or f"{current_year}-{current_year + 1}"
opening_balance = float(settings.get("opening_balance", 0))

fy_start, fy_end = get_fy_dates(financial_year)

st.subheader(school_name if school_name else "School NSB Record")
st.info(f"Financial Year: {financial_year} | From {fy_start.strftime('%d-%m-%Y')} to {fy_end.strftime('%d-%m-%Y')}")


# ============================================================
# MAIN CALCULATIONS
# ============================================================

total_receipts = get_total_receipts(fy_start, fy_end)
total_expenditures = get_total_expenditures(fy_start, fy_end)
current_balance = opening_balance + total_receipts - total_expenditures

last_month_receipts = get_last_month_receipts(fy_start, fy_end)
last_month_expenditures = get_last_month_expenditures(fy_start, fy_end)

receipts_till_last_month = get_receipts_till_last_month(fy_start, fy_end)
expenditures_till_last_month = get_expenditures_till_last_month(fy_start, fy_end)


# ============================================================
# DASHBOARD
# ============================================================

st.header("📊 Dashboard")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Balance 30th June", money(opening_balance))
c2.metric("Total Received", money(total_receipts))
c3.metric("Total Expenditures", money(total_expenditures))
c4.metric("Remaining Balance", money(current_balance))

c5, c6, c7, c8 = st.columns(4)

c5.metric("Last Month Received", money(last_month_receipts))
c6.metric("Last Month Expenditures", money(last_month_expenditures))
c7.metric("Received Till Last Month", money(receipts_till_last_month))
c8.metric("Expenditures Till Last Month", money(expenditures_till_last_month))


# ============================================================
# TABS
# ============================================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "➕ Add Receipt",
    "➖ Add Expenditure / Bill",
    "📄 Balance Sheet",
    "🧾 Bills / Vouchers",
    "📈 Summary",
    "⬇️ Export / Delete"
])


# ============================================================
# ADD RECEIPT
# ============================================================

with tab1:
    st.header("➕ Add Government Receipt / Income")

    with st.form("add_receipt_form"):
        col1, col2 = st.columns(2)

        with col1:
            receipt_date = st.date_input("Date of Income Receipt", value=date.today())
            receipt_no = st.text_input("Receipt No. / Letter No.")
            income_details = st.text_input(
                "Income Details",
                placeholder="Example: 1st Grant, 2nd Grant, Salary ASP"
            )

        with col2:
            source = st.text_input("Source", value="Government")
            receipt_amount = st.number_input("Amount Received", min_value=0.0, step=1000.0)
            receipt_remarks = st.text_area("Remarks")

        receipt_submit = st.form_submit_button("✅ Save Receipt")

        if receipt_submit:
            if receipt_amount <= 0:
                st.error("Amount must be greater than 0.")
            elif receipt_date < fy_start or receipt_date > fy_end:
                st.error("Receipt date is outside the selected financial year.")
            else:
                run_query("""
                    INSERT INTO receipts
                    (receipt_date, receipt_no, income_details, source, amount, remarks, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(receipt_date),
                    receipt_no,
                    income_details,
                    source,
                    receipt_amount,
                    receipt_remarks,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

                st.success("Receipt saved successfully.")
                st.rerun()


# ============================================================
# ADD EXPENDITURE
# ============================================================

with tab2:
    st.header("➖ Add Expenditure / Bill")

    with st.form("add_expenditure_form"):
        col1, col2 = st.columns(2)

        with col1:
            voucher_no = st.text_input("Voucher No.")
            purchase_date = st.date_input("Date of Purchasing", value=date.today())
            bill_date = st.date_input("Bill Date", value=date.today())
            vendor_name = st.text_input("Vendor / Shop / Person Name")

        with col2:
            category = st.selectbox(
                "Category",
                [
                    "Stationery",
                    "Repair & Maintenance",
                    "Furniture",
                    "Electricity",
                    "Internet / IT",
                    "Cleaning",
                    "Sports",
                    "Lab Material",
                    "Printing",
                    "Transport",
                    "Miscellaneous"
                ]
            )

            item_details = st.text_input(
                "Item / Bill Details",
                placeholder="Example: White board markers, repair work, fan, register"
            )

            expenditure_amount = st.number_input("Expenditure Amount", min_value=0.0, step=500.0)

            bill_file = st.file_uploader(
                "Upload Bill Image/PDF Optional",
                type=["jpg", "jpeg", "png", "pdf"]
            )

            expenditure_remarks = st.text_area("Remarks")

        exp_submit = st.form_submit_button("✅ Save Expenditure")

        if exp_submit:
            if expenditure_amount <= 0:
                st.error("Amount must be greater than 0.")
            elif purchase_date < fy_start or purchase_date > fy_end:
                st.error("Purchase date is outside the selected financial year.")
            else:
                bill_path = save_uploaded_bill(bill_file, voucher_no)

                run_query("""
                    INSERT INTO expenditures
                    (
                        voucher_no,
                        purchase_date,
                        bill_date,
                        vendor_name,
                        category,
                        item_details,
                        amount,
                        bill_file_path,
                        remarks,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    voucher_no,
                    str(purchase_date),
                    str(bill_date),
                    vendor_name,
                    category,
                    item_details,
                    expenditure_amount,
                    bill_path,
                    expenditure_remarks,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

                st.success("Expenditure saved successfully.")
                st.rerun()


# ============================================================
# BALANCE SHEET
# ============================================================

with tab3:
    st.header(f"📄 NSB Balance Sheet ({financial_year})")

    st.write(f"**Balance 30th June:** {money(opening_balance)}")

    balance_sheet = prepare_monthly_balance_sheet(financial_year, opening_balance)
    display_sheet = balance_sheet.copy()

    for col in ["Amount", "Expenditure", "Remaining Balance"]:
        display_sheet[col] = display_sheet[col].apply(money)

    st.dataframe(display_sheet, use_container_width=True, hide_index=True)

    total_row_col1, total_row_col2, total_row_col3 = st.columns(3)

    total_row_col1.metric("Total Received", money(total_receipts))
    total_row_col2.metric("Total Expenditure", money(total_expenditures))
    total_row_col3.metric("Final Remaining Balance", money(current_balance))


# ============================================================
# BILLS / VOUCHERS
# ============================================================

with tab4:
    st.header("🧾 Bills and Voucher Records")

    voucher_search = st.text_input("Search by Voucher No., Vendor, Category, or Item")

    if voucher_search.strip():
        exp_records = get_df("""
            SELECT 
                id,
                voucher_no,
                purchase_date,
                bill_date,
                vendor_name,
                category,
                item_details,
                amount,
                bill_file_path,
                remarks
            FROM expenditures
            WHERE purchase_date BETWEEN ? AND ?
            AND (
                voucher_no LIKE ?
                OR vendor_name LIKE ?
                OR category LIKE ?
                OR item_details LIKE ?
            )
            ORDER BY purchase_date DESC, id DESC
        """, (
            str(fy_start),
            str(fy_end),
            f"%{voucher_search}%",
            f"%{voucher_search}%",
            f"%{voucher_search}%",
            f"%{voucher_search}%"
        ))
    else:
        exp_records = get_df("""
            SELECT 
                id,
                voucher_no,
                purchase_date,
                bill_date,
                vendor_name,
                category,
                item_details,
                amount,
                bill_file_path,
                remarks
            FROM expenditures
            WHERE purchase_date BETWEEN ? AND ?
            ORDER BY purchase_date DESC, id DESC
        """, (str(fy_start), str(fy_end)))

    if exp_records.empty:
        st.info("No bill or voucher record found.")
    else:
        exp_records_display = exp_records.copy()
        exp_records_display["amount"] = exp_records_display["amount"].apply(money)

        st.dataframe(exp_records_display, use_container_width=True, hide_index=True)


# ============================================================
# SUMMARY
# ============================================================

with tab5:
    st.header("📈 NSB Summary")

    summary_data = {
        "Particular": [
            "Previous Balance / Balance 30th June",
            "Total Received",
            "Total Income",
            "Total Expenses",
            "Remaining Balance",
            "Last Month Received",
            "Last Month Expenditures",
            "Received Till Last Month",
            "Expenditures Till Last Month"
        ],
        "Amount": [
            opening_balance,
            total_receipts,
            opening_balance + total_receipts,
            total_expenditures,
            current_balance,
            last_month_receipts,
            last_month_expenditures,
            receipts_till_last_month,
            expenditures_till_last_month
        ]
    }

    summary_df = pd.DataFrame(summary_data)
    summary_show = summary_df.copy()
    summary_show["Amount"] = summary_show["Amount"].apply(money)

    st.dataframe(summary_show, use_container_width=True, hide_index=True)

    st.subheader("📊 Monthly Chart")

    chart_df = prepare_monthly_balance_sheet(financial_year, opening_balance)
    chart_data = chart_df[["Month", "Amount", "Expenditure", "Remaining Balance"]].copy()
    chart_data = chart_data.set_index("Month")

    st.line_chart(chart_data)


# ============================================================
# EXPORT / DELETE
# ============================================================

with tab6:
    st.header("⬇️ Export / Delete Records")

    st.subheader("Download Records")

    receipt_records = get_df("""
        SELECT 
            id,
            receipt_date,
            receipt_no,
            income_details,
            source,
            amount,
            remarks,
            created_at
        FROM receipts
        WHERE receipt_date BETWEEN ? AND ?
        ORDER BY receipt_date DESC, id DESC
    """, (str(fy_start), str(fy_end)))

    expenditure_records = get_df("""
        SELECT 
            id,
            voucher_no,
            purchase_date,
            bill_date,
            vendor_name,
            category,
            item_details,
            amount,
            bill_file_path,
            remarks,
            created_at
        FROM expenditures
        WHERE purchase_date BETWEEN ? AND ?
        ORDER BY purchase_date DESC, id DESC
    """, (str(fy_start), str(fy_end)))

    balance_sheet_export = prepare_monthly_balance_sheet(financial_year, opening_balance)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            "Download Balance Sheet CSV",
            data=balance_sheet_export.to_csv(index=False).encode("utf-8"),
            file_name=f"nsb_balance_sheet_{financial_year}.csv",
            mime="text/csv"
        )

    with col2:
        st.download_button(
            "Download Receipts CSV",
            data=receipt_records.to_csv(index=False).encode("utf-8"),
            file_name=f"nsb_receipts_{financial_year}.csv",
            mime="text/csv"
        )

    with col3:
        st.download_button(
            "Download Expenditures CSV",
            data=expenditure_records.to_csv(index=False).encode("utf-8"),
            file_name=f"nsb_expenditures_{financial_year}.csv",
            mime="text/csv"
        )

    st.divider()

    st.subheader("🗑️ Delete Wrong Entry")

    d1, d2 = st.columns(2)

    with d1:
        st.markdown("### Delete Receipt")

        receipt_delete_id = st.number_input(
            "Enter Receipt ID",
            min_value=0,
            step=1,
            key="receipt_delete_id"
        )

        if st.button("Delete Receipt"):
            if receipt_delete_id > 0:
                run_query("DELETE FROM receipts WHERE id = ?", (receipt_delete_id,))
                st.success("Receipt deleted if ID existed.")
                st.rerun()
            else:
                st.error("Please enter a valid Receipt ID.")

    with d2:
        st.markdown("### Delete Expenditure")

        exp_delete_id = st.number_input(
            "Enter Expenditure ID",
            min_value=0,
            step=1,
            key="exp_delete_id"
        )

        if st.button("Delete Expenditure"):
            if exp_delete_id > 0:
                run_query("DELETE FROM expenditures WHERE id = ?", (exp_delete_id,))
                st.success("Expenditure deleted if ID existed.")
                st.rerun()
            else:
                st.error("Please enter a valid Expenditure ID.")


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Important: Keep backup of nsb_calculator.db and uploaded_bills folder. "
    "These files contain your saved NSB records and uploaded bills."
)