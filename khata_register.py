import streamlit as st
import sqlite3
import pandas as pd
import qrcode
from io import BytesIO
from datetime import datetime

# ---------------- PAGE SETUP ----------------
st.set_page_config(
    page_title="Karyana Shop Management App",
    page_icon="🛒",
    layout="wide"
)

DB_NAME = "karyana_shop.db"


# ---------------- DATABASE CONNECTION ----------------
def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_code TEXT UNIQUE,
        item_name TEXT NOT NULL,
        category TEXT,
        unit TEXT,
        purchase_price REAL DEFAULT 0,
        sale_price REAL DEFAULT 0,
        stock_quantity REAL DEFAULT 0,
        low_stock_limit REAL DEFAULT 5,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_code TEXT,
        item_name TEXT,
        quantity REAL,
        purchase_price REAL,
        total_amount REAL,
        purchase_date TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_code TEXT,
        item_name TEXT,
        quantity REAL,
        sale_price REAL,
        total_amount REAL,
        profit REAL,
        sale_date TEXT
    )
    """)

    conn.commit()
    conn.close()


create_tables()


# ---------------- HELPER FUNCTIONS ----------------
def generate_item_code():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM products")
    count = cur.fetchone()[0] + 1
    conn.close()
    return f"KRY{count:05d}"


def generate_qr_code(data):
    qr = qrcode.make(data)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def get_all_products():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM products ORDER BY id DESC", conn)
    conn.close()
    return df


def get_product_by_code(item_code):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE item_code = ?", (item_code,))
    product = cur.fetchone()
    conn.close()
    return product


def add_product(item_name, category, unit, purchase_price, sale_price, opening_stock, low_stock_limit):
    conn = get_connection()
    cur = conn.cursor()

    item_code = generate_item_code()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cur.execute("""
    INSERT INTO products 
    (item_code, item_name, category, unit, purchase_price, sale_price, stock_quantity, low_stock_limit, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        item_code,
        item_name,
        category,
        unit,
        purchase_price,
        sale_price,
        opening_stock,
        low_stock_limit,
        created_at
    ))

    conn.commit()
    conn.close()
    return item_code


def update_stock_after_purchase(item_code, quantity, purchase_price):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    UPDATE products
    SET stock_quantity = stock_quantity + ?,
        purchase_price = ?
    WHERE item_code = ?
    """, (quantity, purchase_price, item_code))

    conn.commit()
    conn.close()


def update_stock_after_sale(item_code, quantity):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    UPDATE products
    SET stock_quantity = stock_quantity - ?
    WHERE item_code = ?
    """, (quantity, item_code))

    conn.commit()
    conn.close()


def record_purchase(item_code, item_name, quantity, purchase_price):
    total_amount = quantity * purchase_price
    purchase_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO purchases 
    (item_code, item_name, quantity, purchase_price, total_amount, purchase_date)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (item_code, item_name, quantity, purchase_price, total_amount, purchase_date))

    conn.commit()
    conn.close()

    update_stock_after_purchase(item_code, quantity, purchase_price)


def record_sale(item_code, item_name, quantity, sale_price, purchase_price):
    total_amount = quantity * sale_price
    profit = (sale_price - purchase_price) * quantity
    sale_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO sales
    (item_code, item_name, quantity, sale_price, total_amount, profit, sale_date)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (item_code, item_name, quantity, sale_price, total_amount, profit, sale_date))

    conn.commit()
    conn.close()

    update_stock_after_sale(item_code, quantity)


def get_purchases():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM purchases ORDER BY id DESC", conn)
    conn.close()
    return df


def get_sales():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM sales ORDER BY id DESC", conn)
    conn.close()
    return df


def low_stock_items():
    conn = get_connection()
    df = pd.read_sql_query("""
    SELECT item_code, item_name, category, unit, stock_quantity, low_stock_limit
    FROM products
    WHERE stock_quantity <= low_stock_limit
    ORDER BY stock_quantity ASC
    """, conn)
    conn.close()
    return df


def delete_product(item_code):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE item_code = ?", (item_code,))
    conn.commit()
    conn.close()


# ---------------- SIDEBAR ----------------
st.sidebar.title("🛒 Karyana Shop App")

menu = st.sidebar.radio(
    "Select Option",
    [
        "Dashboard",
        "Add New Item",
        "Stock List",
        "Purchase Entry",
        "Sell Item / Billing",
        "Low Stock Alert",
        "Reports",
        "QR / Barcode Label",
        "Delete Item"
    ]
)


# ---------------- DASHBOARD ----------------
if menu == "Dashboard":
    st.title("📊 Karyana Shop Dashboard")

    products_df = get_all_products()
    sales_df = get_sales()
    purchases_df = get_purchases()
    low_df = low_stock_items()

    total_items = len(products_df)

    if not products_df.empty:
        total_stock_value = (products_df["stock_quantity"] * products_df["purchase_price"]).sum()
    else:
        total_stock_value = 0

    total_sales = sales_df["total_amount"].sum() if not sales_df.empty else 0
    total_profit = sales_df["profit"].sum() if not sales_df.empty else 0
    total_purchase = purchases_df["total_amount"].sum() if not purchases_df.empty else 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Items", total_items)
    col2.metric("Stock Value", f"Rs. {total_stock_value:,.0f}")
    col3.metric("Total Sales", f"Rs. {total_sales:,.0f}")
    col4.metric("Total Profit", f"Rs. {total_profit:,.0f}")

    st.markdown("---")

    col5, col6 = st.columns(2)

    with col5:
        st.subheader("⚠️ Low Stock Items")
        if low_df.empty:
            st.success("No low stock item.")
        else:
            st.dataframe(low_df, use_container_width=True)

    with col6:
        st.subheader("🧾 Recent Sales")
        if sales_df.empty:
            st.info("No sales yet.")
        else:
            st.dataframe(sales_df.head(10), use_container_width=True)


# ---------------- ADD NEW ITEM ----------------
elif menu == "Add New Item":
    st.title("➕ Add New Item")

    with st.form("add_item_form"):
        item_name = st.text_input("Item Name", placeholder="Example: Sugar, Rice, Tea, Soap")
        category = st.text_input("Category", placeholder="Example: Grocery, Drinks, Cleaning")
        unit = st.selectbox("Unit", ["Piece", "Kg", "Gram", "Liter", "Packet", "Box", "Dozen"])
        purchase_price = st.number_input("Purchase Price", min_value=0.0, step=1.0)
        sale_price = st.number_input("Sale Price", min_value=0.0, step=1.0)
        opening_stock = st.number_input("Opening Stock Quantity", min_value=0.0, step=1.0)
        low_stock_limit = st.number_input("Low Stock Alert Limit", min_value=0.0, step=1.0, value=5.0)

        submit = st.form_submit_button("Save Item")

    if submit:
        if item_name.strip() == "":
            st.error("Please enter item name.")
        elif sale_price < purchase_price:
            st.warning("Sale price is less than purchase price. Please check.")
        else:
            code = add_product(
                item_name,
                category,
                unit,
                purchase_price,
                sale_price,
                opening_stock,
                low_stock_limit
            )
            st.success(f"Item added successfully. Item Code: {code}")

            qr_buffer = generate_qr_code(code)
            st.image(qr_buffer, caption=f"QR / Barcode Code: {code}", width=200)
            st.download_button(
                "Download QR Code",
                data=qr_buffer,
                file_name=f"{code}_qr.png",
                mime="image/png"
            )


# ---------------- STOCK LIST ----------------
elif menu == "Stock List":
    st.title("📦 Stock List")

    df = get_all_products()

    search = st.text_input("Search item by name, category, or code")

    if not df.empty and search:
        search = search.lower()
        df = df[
            df["item_name"].str.lower().str.contains(search, na=False) |
            df["category"].str.lower().str.contains(search, na=False) |
            df["item_code"].str.lower().str.contains(search, na=False)
        ]

    if df.empty:
        st.info("No stock item found.")
    else:
        st.dataframe(df, use_container_width=True)

        excel_data = BytesIO()
        df.to_excel(excel_data, index=False)
        excel_data.seek(0)

        st.download_button(
            "Download Stock List in Excel",
            data=excel_data,
            file_name="stock_list.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


# ---------------- PURCHASE ENTRY ----------------
elif menu == "Purchase Entry":
    st.title("🛍️ Purchase Entry")

    products_df = get_all_products()

    if products_df.empty:
        st.warning("Please add items first.")
    else:
        item_options = products_df["item_code"] + " - " + products_df["item_name"]

        selected_item = st.selectbox("Select Item", item_options)
        item_code = selected_item.split(" - ")[0]

        product = get_product_by_code(item_code)

        if product:
            item_name = product[2]
            old_purchase_price = product[5]

            st.info(f"Selected Item: {item_name}")

            quantity = st.number_input("Purchase Quantity", min_value=0.0, step=1.0)
            purchase_price = st.number_input(
                "Purchase Price Per Unit",
                min_value=0.0,
                step=1.0,
                value=float(old_purchase_price)
            )

            total = quantity * purchase_price
            st.subheader(f"Total Purchase Amount: Rs. {total:,.0f}")

            if st.button("Save Purchase"):
                if quantity <= 0:
                    st.error("Quantity must be greater than zero.")
                else:
                    record_purchase(item_code, item_name, quantity, purchase_price)
                    st.success("Purchase saved and stock updated successfully.")
                    st.rerun()


# ---------------- SELL ITEM / BILLING ----------------
elif menu == "Sell Item / Billing":
    st.title("🧾 Sell Item / Billing")

    st.info(
        "You can type item code manually or use a barcode scanner. "
        "Most barcode scanners work like keyboard input."
    )

    item_code = st.text_input("Scan / Enter Item Code", placeholder="Example: KRY00001")

    if item_code:
        product = get_product_by_code(item_code)

        if product is None:
            st.error("Item not found. Please check code.")
        else:
            product_id = product[0]
            code = product[1]
            item_name = product[2]
            category = product[3]
            unit = product[4]
            purchase_price = product[5]
            sale_price = product[6]
            stock_quantity = product[7]

            col1, col2, col3 = st.columns(3)
            col1.metric("Item", item_name)
            col2.metric("Available Stock", f"{stock_quantity} {unit}")
            col3.metric("Sale Price", f"Rs. {sale_price}")

            quantity = st.number_input("Selling Quantity", min_value=0.0, step=1.0)

            total_bill = quantity * sale_price
            profit = (sale_price - purchase_price) * quantity

            st.subheader(f"Total Bill: Rs. {total_bill:,.0f}")

            if quantity > stock_quantity:
                st.error("Not enough stock available.")
            else:
                if st.button("Sell Item"):
                    if quantity <= 0:
                        st.error("Quantity must be greater than zero.")
                    else:
                        record_sale(code, item_name, quantity, sale_price, purchase_price)
                        st.success("Sale completed successfully.")
                        st.write(f"Profit on this sale: Rs. {profit:,.0f}")
                        st.rerun()


# ---------------- LOW STOCK ALERT ----------------
elif menu == "Low Stock Alert":
    st.title("⚠️ Low Stock Alert")

    df = low_stock_items()

    if df.empty:
        st.success("All items have sufficient stock.")
    else:
        st.warning("The following items are low in stock.")
        st.dataframe(df, use_container_width=True)


# ---------------- REPORTS ----------------
elif menu == "Reports":
    st.title("📑 Reports")

    report_type = st.selectbox(
        "Select Report",
        ["Sales Report", "Purchase Report", "Stock Report", "Profit Report"]
    )

    if report_type == "Sales Report":
        df = get_sales()
        st.subheader("Sales Report")

    elif report_type == "Purchase Report":
        df = get_purchases()
        st.subheader("Purchase Report")

    elif report_type == "Stock Report":
        df = get_all_products()
        st.subheader("Stock Report")

    else:
        df = get_sales()
        st.subheader("Profit Report")

        if not df.empty:
            total_sales = df["total_amount"].sum()
            total_profit = df["profit"].sum()

            col1, col2 = st.columns(2)
            col1.metric("Total Sales", f"Rs. {total_sales:,.0f}")
            col2.metric("Total Profit", f"Rs. {total_profit:,.0f}")

    if df.empty:
        st.info("No data available.")
    else:
        st.dataframe(df, use_container_width=True)

        excel_data = BytesIO()
        df.to_excel(excel_data, index=False)
        excel_data.seek(0)

        st.download_button(
            "Download Report in Excel",
            data=excel_data,
            file_name=f"{report_type.replace(' ', '_').lower()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


# ---------------- QR / BARCODE LABEL ----------------
elif menu == "QR / Barcode Label":
    st.title("🏷️ QR / Barcode Label Generator")

    products_df = get_all_products()

    if products_df.empty:
        st.warning("Please add items first.")
    else:
        item_options = products_df["item_code"] + " - " + products_df["item_name"]
        selected_item = st.selectbox("Select Item", item_options)

        item_code = selected_item.split(" - ")[0]
        product = get_product_by_code(item_code)

        if product:
            item_name = product[2]
            sale_price = product[6]

            st.subheader(item_name)
            st.write(f"Item Code: {item_code}")
            st.write(f"Sale Price: Rs. {sale_price}")

            qr_buffer = generate_qr_code(item_code)

            st.image(qr_buffer, caption=f"{item_name} - {item_code}", width=250)

            st.download_button(
                "Download QR / Barcode Label",
                data=qr_buffer,
                file_name=f"{item_code}_label.png",
                mime="image/png"
            )


# ---------------- DELETE ITEM ----------------
elif menu == "Delete Item":
    st.title("🗑️ Delete Item")

    products_df = get_all_products()

    if products_df.empty:
        st.info("No item available.")
    else:
        item_options = products_df["item_code"] + " - " + products_df["item_name"]
        selected_item = st.selectbox("Select Item to Delete", item_options)

        item_code = selected_item.split(" - ")[0]

        st.warning("Be careful. This will delete the item from stock list.")

        confirm = st.checkbox("Yes, I want to delete this item")

        if st.button("Delete Item"):
            if confirm:
                delete_product(item_code)
                st.success("Item deleted successfully.")
                st.rerun()
            else:
                st.error("Please confirm before deleting.")