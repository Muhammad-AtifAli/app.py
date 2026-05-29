import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime, date
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

st.set_page_config(
    page_title="Banquet Booking & Management System",
    page_icon="🏛️",
    layout="wide"
)

DB = "banquet_system.db"

st.markdown("""
<style>
.big-title{
    font-size:40px;
    font-weight:800;
    text-align:center;
    color:#2c3e50;
}
.sub-title{
    text-align:center;
    font-size:19px;
    color:#555;
}
.box{
    background:white;
    padding:18px;
    border-radius:14px;
    box-shadow:0 3px 12px rgba(0,0,0,.08);
    margin-bottom:12px;
}
</style>
""", unsafe_allow_html=True)


# =====================================================
# DATABASE FUNCTIONS
# =====================================================

def con():
    return sqlite3.connect(DB, check_same_thread=False)


def hpw(password):
    return hashlib.sha256(password.encode()).hexdigest()


def q(sql, params=(), fetch=False):
    c = con()
    cur = c.cursor()
    cur.execute(sql, params)
    data = cur.fetchall() if fetch else None
    c.commit()
    c.close()
    return data


def df(sql, params=()):
    c = con()
    data = pd.read_sql_query(sql, c, params=params)
    c.close()
    return data


def column_exists(table_name, column_name):
    c = con()
    cur = c.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cur.fetchall()]
    c.close()
    return column_name in columns


def init_db():
    c = con()
    cur = c.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        full_name TEXT,
        email TEXT,
        phone TEXT,
        role TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS packages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        package_name TEXT UNIQUE,
        price_per_guest REAL,
        hall_rent REAL,
        description TEXT,
        status TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bookings(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id TEXT UNIQUE,
        customer_name TEXT,
        phone TEXT,
        email TEXT,
        event_type TEXT,
        event_date TEXT,
        time_slot TEXT,
        guests INTEGER,
        package_id INTEGER,
        estimated_cost REAL,
        status TEXT,
        payment_status TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id TEXT,
        amount REAL,
        payment_method TEXT,
        payment_date TEXT,
        remarks TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS expenses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        expense_title TEXT,
        category TEXT,
        amount REAL,
        expense_date TEXT,
        remarks TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS staff(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        staff_name TEXT,
        duty TEXT,
        phone TEXT,
        salary REAL,
        status TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS feedback(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT,
        rating INTEGER,
        comments TEXT,
        created_at TEXT
    )
    """)

    c.commit()
    c.close()

    # Safe migration for older versions where staff table had "role" instead of "duty"
    if not column_exists("staff", "duty"):
        q("ALTER TABLE staff ADD COLUMN duty TEXT DEFAULT ''")

    c = con()
    cur = c.cursor()

    cur.execute("SELECT COUNT(*) FROM packages")
    if cur.fetchone()[0] == 0:
        cur.executemany("""
        INSERT INTO packages(package_name, price_per_guest, hall_rent, description, status)
        VALUES(?,?,?,?,?)
        """, [
            ("Basic", 1200, 30000, "Simple menu, basic decoration, standard seating.", "Active"),
            ("Standard", 1800, 50000, "Better menu, improved decoration, sound system.", "Active"),
            ("Premium", 2500, 80000, "Premium food, luxury decoration, photography support.", "Active"),
            ("Luxury", 3500, 120000, "Full luxury setup, VIP seating, premium services.", "Active")
        ])

    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.executemany("""
        INSERT INTO users(username, password, full_name, email, phone, role, created_at)
        VALUES(?,?,?,?,?,?,?)
        """, [
            ("superadmin", hpw("admin123"), "Super Admin", "superadmin@banquet.com", "03000000000", "Super Admin", now),
            ("manager", hpw("manager123"), "Banquet Manager", "manager@banquet.com", "03000000001", "Banquet Manager", now),
            ("accountant", hpw("account123"), "Accountant", "accountant@banquet.com", "03000000002", "Accountant", now),
            ("customer", hpw("customer123"), "Demo Customer", "customer@gmail.com", "03000000003", "Customer", now)
        ])

    c.commit()
    c.close()


init_db()


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def booking_id():
    return "BK-" + datetime.now().strftime("%Y%m%d%H%M%S")


def login(username, password):
    result = q("""
    SELECT id, username, full_name, email, phone, role
    FROM users
    WHERE username=? AND password=?
    """, (username, hpw(password)), True)

    return result[0] if result else None


def cost(package_id, guests):
    result = q("""
    SELECT price_per_guest, hall_rent
    FROM packages
    WHERE id=?
    """, (package_id,), True)

    if not result:
        return 0

    price_per_guest, hall_rent = result[0]
    return float(price_per_guest) * int(guests) + float(hall_rent)


def available(event_date, slot, ignore_booking_id=None):
    if ignore_booking_id:
        result = q("""
        SELECT COUNT(*)
        FROM bookings
        WHERE event_date=?
        AND time_slot=?
        AND status IN('Pending','Confirmed')
        AND booking_id!=?
        """, (str(event_date), slot, ignore_booking_id), True)
    else:
        result = q("""
        SELECT COUNT(*)
        FROM bookings
        WHERE event_date=?
        AND time_slot=?
        AND status IN('Pending','Confirmed')
        """, (str(event_date), slot), True)

    return result[0][0] == 0


def recalc_payment(booking_id_value):
    booking = df("""
    SELECT estimated_cost
    FROM bookings
    WHERE booking_id=?
    """, (booking_id_value,))

    if booking.empty:
        return

    total = float(booking.iloc[0]["estimated_cost"])

    payment = df("""
    SELECT SUM(amount) AS paid
    FROM payments
    WHERE booking_id=?
    """, (booking_id_value,))

    paid = payment.iloc[0]["paid"]

    if pd.isna(paid):
        paid = 0

    paid = float(paid)

    if paid >= total and total > 0:
        status = "Fully Paid"
    elif paid > 0:
        status = "Advance Paid"
    else:
        status = "Unpaid"

    q("""
    UPDATE bookings
    SET payment_status=?
    WHERE booking_id=?
    """, (status, booking_id_value))


def excel(data):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        data.to_excel(writer, index=False, sheet_name="Report")

    output.seek(0)
    return output


def receipt_pdf(row):
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=A4)
    y = A4[1] - 70

    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(140, y, "Banquet Booking Receipt")

    y -= 50
    pdf.setFont("Helvetica", 12)

    receipt_items = [
        ("Booking ID", row.get("booking_id", "")),
        ("Customer", row.get("customer_name", "")),
        ("Phone", row.get("phone", "")),
        ("Email", row.get("email", "")),
        ("Event", row.get("event_type", "")),
        ("Date", row.get("event_date", "")),
        ("Time Slot", row.get("time_slot", "")),
        ("Guests", row.get("guests", "")),
        ("Package", row.get("package_name", "")),
        ("Cost", f"Rs. {float(row.get('estimated_cost', 0)):,.0f}"),
        ("Status", row.get("status", "")),
        ("Payment", row.get("payment_status", ""))
    ]

    for label, value in receipt_items:
        pdf.drawString(80, y, f"{label}:")
        pdf.drawString(220, y, str(value))
        y -= 25

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(80, y - 20, "Thank you for choosing our banquet hall!")

    pdf.save()
    output.seek(0)
    return output


def logout():
    st.session_state.logged_in = False
    st.session_state.user = None
    st.rerun()


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None


# =====================================================
# PASSWORD CHANGE PAGE FOR EVERY USER
# =====================================================

def change_my_password():
    st.header("🔑 Change My Password")
    st.info("This option is available for every logged-in person: owner, manager, accountant, and customer.")

    user = st.session_state.user

    with st.form("change_password_form"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")

        submit = st.form_submit_button("Change Password")

        if submit:
            if not current_password or not new_password or not confirm_password:
                st.error("Please fill all password fields.")
                return

            if len(new_password) < 6:
                st.error("New password should be at least 6 characters long.")
                return

            if new_password != confirm_password:
                st.error("New password and confirm password do not match.")
                return

            result = q("""
            SELECT password
            FROM users
            WHERE id=?
            """, (user["id"],), True)

            if not result:
                st.error("User account not found.")
                return

            old_hash = result[0][0]

            if old_hash != hpw(current_password):
                st.error("Current password is incorrect.")
                return

            q("""
            UPDATE users
            SET password=?
            WHERE id=?
            """, (hpw(new_password), user["id"]))

            st.success("Password changed successfully. Please login again with your new password.")

            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()


# =====================================================
# PUBLIC PAGES
# =====================================================

def home():
    st.markdown('<div class="big-title">🏛️ Banquet Booking & Management System</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">For owners, managers, accountants, and customers</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    col1.markdown("""
    <div class="box">
    <h3>🎉 Customer Booking</h3>
    <p>View packages, check date, calculate cost and submit booking.</p>
    </div>
    """, unsafe_allow_html=True)

    col2.markdown("""
    <div class="box">
    <h3>🛠️ Owner Control</h3>
    <p>Edit/delete packages, bookings, users, staff and feedback.</p>
    </div>
    """, unsafe_allow_html=True)

    col3.markdown("""
    <div class="box">
    <h3>💰 Finance</h3>
    <p>Record payments, expenses, income, profit and reports.</p>
    </div>
    """, unsafe_allow_html=True)

    st.info("Package edit/delete is available only after login as Super Admin or Banquet Manager.")


def customer_panel():
    st.header("👤 Customer Booking Panel")
    st.info("Customers can only view packages. Owners/managers can edit/delete packages from the Packages menu after login.")

    packages = df("""
    SELECT *
    FROM packages
    WHERE status='Active'
    ORDER BY id
    """)

    if packages.empty:
        st.warning("No active package available.")
        return

    st.subheader("📦 Available Packages")
    st.dataframe(
        packages[["package_name", "price_per_guest", "hall_rent", "description"]],
        use_container_width=True
    )

    with st.form("booking_form"):
        st.subheader("📝 Submit Booking Request")

        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Customer Name")
            phone = st.text_input("Phone")
            email = st.text_input("Email")
            event_type = st.selectbox(
                "Event Type",
                ["Wedding", "Walima", "Birthday", "Engagement", "Corporate Event", "Seminar", "Other"]
            )

        with col2:
            event_date = st.date_input("Event Date", min_value=date.today())
            slot = st.selectbox("Time Slot", ["Morning", "Afternoon", "Evening", "Night"])
            guests = st.number_input("Guests", min_value=1, step=1)
            package_name = st.selectbox("Package", packages["package_name"].tolist())

        package_id_value = int(packages[packages.package_name == package_name].iloc[0]["id"])
        total = cost(package_id_value, guests)

        st.success(f"Estimated Cost: Rs. {total:,.0f}")

        if st.form_submit_button("Check Availability & Submit"):
            if not name or not phone:
                st.error("Name and phone are required.")
            elif not available(event_date, slot):
                st.error("This date/time slot is already booked or pending.")
            else:
                new_booking_id = booking_id()

                q("""
                INSERT INTO bookings(
                    booking_id, customer_name, phone, email, event_type,
                    event_date, time_slot, guests, package_id, estimated_cost,
                    status, payment_status, created_at
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    new_booking_id, name, phone, email, event_type,
                    str(event_date), slot, guests, package_id_value, total,
                    "Pending", "Unpaid", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

                st.success(f"Booking submitted. Booking ID: {new_booking_id}")

    with st.form("feedback_form"):
        st.subheader("⭐ Feedback")

        fb_name = st.text_input("Your Name")
        rating = st.slider("Rating", 1, 5, 5)
        comments = st.text_area("Comments")

        if st.form_submit_button("Submit Feedback"):
            if fb_name and comments:
                q("""
                INSERT INTO feedback(customer_name, rating, comments, created_at)
                VALUES(?,?,?,?)
                """, (
                    fb_name,
                    rating,
                    comments,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

                st.success("Feedback submitted.")
            else:
                st.error("Name and comments are required.")


def register():
    st.header("🆕 Customer Registration")

    with st.form("registration_form"):
        full_name = st.text_input("Full Name")
        username = st.text_input("Username")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        if st.form_submit_button("Create Account"):
            if not full_name or not username or not password:
                st.error("Full name, username and password are required.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            elif len(password) < 6:
                st.error("Password should be at least 6 characters long.")
            else:
                try:
                    q("""
                    INSERT INTO users(username, password, full_name, email, phone, role, created_at)
                    VALUES(?,?,?,?,?,?,?)
                    """, (
                        username,
                        hpw(password),
                        full_name,
                        email,
                        phone,
                        "Customer",
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ))

                    st.success("Account created. Please login.")
                except sqlite3.IntegrityError:
                    st.error("Username already exists.")


def login_page():
    st.header("🔐 Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.form_submit_button("Login"):
            user = login(username, password)

            if user:
                st.session_state.logged_in = True
                st.session_state.user = {
                    "id": user[0],
                    "username": user[1],
                    "full_name": user[2],
                    "email": user[3],
                    "phone": user[4],
                    "role": user[5]
                }
                st.rerun()
            else:
                st.error("Invalid username or password.")

    st.info("""
    Default accounts:

    Super Admin: `superadmin` / `admin123`  
    Banquet Manager: `manager` / `manager123`  
    Accountant: `accountant` / `account123`  
    Customer: `customer` / `customer123`
    """)


# =====================================================
# DASHBOARD
# =====================================================

def dashboard():
    st.header("📊 Dashboard")

    bookings = df("SELECT * FROM bookings")
    payments = df("SELECT * FROM payments")
    expenses = df("SELECT * FROM expenses")

    income = 0 if payments.empty else payments.amount.sum()
    expense = 0 if expenses.empty else expenses.amount.sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Bookings", len(bookings))
    col2.metric("Pending", 0 if bookings.empty else len(bookings[bookings.status == "Pending"]))
    col3.metric("Confirmed", 0 if bookings.empty else len(bookings[bookings.status == "Confirmed"]))
    col4.metric("Cancelled", 0 if bookings.empty else len(bookings[bookings.status == "Cancelled"]))

    col5, col6, col7 = st.columns(3)

    col5.metric("Income", f"Rs. {income:,.0f}")
    col6.metric("Expenses", f"Rs. {expense:,.0f}")
    col7.metric("Profit/Loss", f"Rs. {income - expense:,.0f}")

    st.subheader("📅 Upcoming Events")

    upcoming = df("""
    SELECT b.booking_id, b.customer_name, b.event_type, b.event_date,
           b.time_slot, b.guests, p.package_name, b.status
    FROM bookings b
    LEFT JOIN packages p ON b.package_id=p.id
    WHERE b.event_date>=?
    ORDER BY b.event_date
    """, (date.today().strftime("%Y-%m-%d"),))

    st.dataframe(upcoming, use_container_width=True)


# =====================================================
# PACKAGE MANAGEMENT
# =====================================================

def manage_packages():
    st.header("📦 Package Management")
    st.success("Here owner/management can add, edit, deactivate, and delete packages.")

    data = df("SELECT * FROM packages ORDER BY id")
    st.dataframe(data, use_container_width=True)

    with st.expander("➕ Add New Package", expanded=True):
        with st.form("add_package_form", clear_on_submit=True):
            package_name = st.text_input("Package Name")
            price = st.number_input("Price Per Guest", min_value=0.0, step=100.0)
            rent = st.number_input("Hall Rent", min_value=0.0, step=1000.0)
            description = st.text_area("Description")
            status = st.selectbox("Status", ["Active", "Inactive"])

            if st.form_submit_button("Add Package"):
                if not package_name:
                    st.error("Package name is required.")
                else:
                    try:
                        q("""
                        INSERT INTO packages(package_name, price_per_guest, hall_rent, description, status)
                        VALUES(?,?,?,?,?)
                        """, (package_name, price, rent, description, status))

                        st.success("Package added.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Package name already exists.")

    st.subheader("✏️ Edit / Delete Package")

    data = df("SELECT * FROM packages ORDER BY id")

    if data.empty:
        st.warning("No package found.")
        return

    selected_id = st.selectbox("Select Package ID", data.id.tolist(), key="package_select")
    row = data[data.id == selected_id].iloc[0]

    with st.form("edit_package_form"):
        package_name = st.text_input("Package Name", row.package_name)
        price = st.number_input("Price Per Guest", value=float(row.price_per_guest), min_value=0.0, step=100.0)
        rent = st.number_input("Hall Rent", value=float(row.hall_rent), min_value=0.0, step=1000.0)
        description = st.text_area("Description", row.description)
        status = st.selectbox("Status", ["Active", "Inactive"], index=0 if row.status == "Active" else 1)

        if st.form_submit_button("Update Package"):
            try:
                q("""
                UPDATE packages
                SET package_name=?, price_per_guest=?, hall_rent=?, description=?, status=?
                WHERE id=?
                """, (package_name, price, rent, description, status, selected_id))

                st.success("Package updated.")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Another package has this name.")

    st.warning("Deleting a package does not delete old bookings.")

    if st.button("🗑️ Delete Selected Package"):
        q("DELETE FROM packages WHERE id=?", (selected_id,))
        st.success("Package deleted.")
        st.rerun()


# =====================================================
# BOOKING MANAGEMENT
# =====================================================

def manage_bookings():
    st.header("📋 Booking Management")

    data = df("""
    SELECT b.*, p.package_name
    FROM bookings b
    LEFT JOIN packages p ON b.package_id=p.id
    ORDER BY b.id DESC
    """)

    st.dataframe(data, use_container_width=True)

    if not data.empty:
        st.download_button(
            "Download Bookings Excel",
            excel(data),
            "bookings.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    packages = df("SELECT * FROM packages WHERE status='Active' ORDER BY id")

    if not packages.empty:
        with st.expander("➕ Add Booking by Management"):
            with st.form("add_booking_form"):
                col1, col2 = st.columns(2)

                with col1:
                    name = st.text_input("Customer Name")
                    phone = st.text_input("Phone")
                    email = st.text_input("Email")
                    event_type = st.selectbox(
                        "Event Type",
                        ["Wedding", "Walima", "Birthday", "Engagement", "Corporate Event", "Seminar", "Other"]
                    )

                with col2:
                    event_date = st.date_input("Event Date", value=date.today())
                    slot = st.selectbox("Time Slot", ["Morning", "Afternoon", "Evening", "Night"])
                    guests = st.number_input("Guests", min_value=1, step=1)
                    package_name = st.selectbox("Package", packages.package_name.tolist())
                    status = st.selectbox("Status", ["Pending", "Confirmed", "Rejected", "Cancelled"])

                package_id_value = int(packages[packages.package_name == package_name].iloc[0].id)
                total = cost(package_id_value, guests)

                st.success(f"Cost: Rs. {total:,.0f}")

                if st.form_submit_button("Add Booking"):
                    if not name or not phone:
                        st.error("Name and phone required.")
                    elif not available(event_date, slot):
                        st.error("Date/time already booked.")
                    else:
                        new_booking_id = booking_id()

                        q("""
                        INSERT INTO bookings(
                            booking_id, customer_name, phone, email, event_type,
                            event_date, time_slot, guests, package_id, estimated_cost,
                            status, payment_status, created_at
                        )
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                        """, (
                            new_booking_id, name, phone, email, event_type,
                            str(event_date), slot, guests, package_id_value, total,
                            status, "Unpaid", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ))

                        st.success("Booking added.")
                        st.rerun()

    st.subheader("✏️ Edit / Delete Booking")

    data = df("""
    SELECT b.*, p.package_name
    FROM bookings b
    LEFT JOIN packages p ON b.package_id=p.id
    ORDER BY b.id DESC
    """)

    if data.empty or packages.empty:
        return

    selected_booking_id = st.selectbox("Select Booking ID", data.booking_id.tolist(), key="booking_select")
    row = data[data.booking_id == selected_booking_id].iloc[0]

    package_names = packages.package_name.tolist()
    package_index = package_names.index(row.package_name) if row.package_name in package_names else 0

    with st.form("edit_booking_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Customer Name", row.customer_name)
            phone = st.text_input("Phone", row.phone)
            email = st.text_input("Email", row.email)

            event_options = ["Wedding", "Walima", "Birthday", "Engagement", "Corporate Event", "Seminar", "Other"]
            event_type = st.selectbox(
                "Event Type",
                event_options,
                index=event_options.index(row.event_type) if row.event_type in event_options else 0
            )

        with col2:
            event_date = st.date_input("Event Date", value=pd.to_datetime(row.event_date).date())

            slots = ["Morning", "Afternoon", "Evening", "Night"]
            slot = st.selectbox(
                "Time Slot",
                slots,
                index=slots.index(row.time_slot) if row.time_slot in slots else 0
            )

            guests = st.number_input("Guests", min_value=1, value=int(row.guests), step=1)
            package_name = st.selectbox("Package", package_names, index=package_index)

            status_options = ["Pending", "Confirmed", "Rejected", "Cancelled"]
            status = st.selectbox(
                "Status",
                status_options,
                index=status_options.index(row.status) if row.status in status_options else 0
            )

        package_id_value = int(packages[packages.package_name == package_name].iloc[0].id)
        total = cost(package_id_value, guests)

        st.success(f"Updated Cost: Rs. {total:,.0f}")

        if st.form_submit_button("Update Booking"):
            if not available(event_date, slot, selected_booking_id):
                st.error("Date/time booked by another booking.")
            else:
                q("""
                UPDATE bookings
                SET customer_name=?, phone=?, email=?, event_type=?, event_date=?,
                    time_slot=?, guests=?, package_id=?, estimated_cost=?, status=?
                WHERE booking_id=?
                """, (
                    name, phone, email, event_type, str(event_date),
                    slot, guests, package_id_value, total, status,
                    selected_booking_id
                ))

                recalc_payment(selected_booking_id)
                st.success("Booking updated.")
                st.rerun()

    col1, col2 = st.columns(2)

    if col1.button("🗑️ Delete Selected Booking"):
        q("DELETE FROM payments WHERE booking_id=?", (selected_booking_id,))
        q("DELETE FROM bookings WHERE booking_id=?", (selected_booking_id,))
        st.success("Booking deleted.")
        st.rerun()

    receipt_data = df("""
    SELECT b.*, p.package_name
    FROM bookings b
    LEFT JOIN packages p ON b.package_id=p.id
    WHERE b.booking_id=?
    """, (selected_booking_id,))

    if not receipt_data.empty:
        pdf_file = receipt_pdf(receipt_data.iloc[0].to_dict())
        col2.download_button(
            "🧾 Receipt PDF",
            pdf_file,
            f"{selected_booking_id}_receipt.pdf",
            "application/pdf"
        )


# =====================================================
# PAYMENT MANAGEMENT
# =====================================================

def manage_payments():
    st.header("💳 Payment Management")

    bookings = df("""
    SELECT booking_id, customer_name, estimated_cost, payment_status
    FROM bookings
    ORDER BY id DESC
    """)

    if bookings.empty:
        st.warning("No bookings found.")
        return

    with st.form("add_payment_form", clear_on_submit=True):
        booking = st.selectbox("Booking ID", bookings.booking_id.tolist())
        amount = st.number_input("Amount", min_value=0.0, step=1000.0)
        method = st.selectbox("Method", ["Cash", "Bank Transfer", "JazzCash", "EasyPaisa", "Card", "Other"])
        payment_date = st.date_input("Payment Date", value=date.today())
        remarks = st.text_area("Remarks")

        if st.form_submit_button("Add Payment"):
            if amount <= 0:
                st.error("Amount must be greater than zero.")
            else:
                q("""
                INSERT INTO payments(booking_id, amount, payment_method, payment_date, remarks)
                VALUES(?,?,?,?,?)
                """, (booking, amount, method, str(payment_date), remarks))

                recalc_payment(booking)
                st.success("Payment added.")
                st.rerun()

    data = df("SELECT * FROM payments ORDER BY id DESC")
    st.dataframe(data, use_container_width=True)

    if data.empty:
        return

    selected_id = st.selectbox("Select Payment ID to Edit/Delete", data.id.tolist())
    row = data[data.id == selected_id].iloc[0]

    booking_ids = bookings.booking_id.tolist()
    index = booking_ids.index(row.booking_id) if row.booking_id in booking_ids else 0

    with st.form("edit_payment_form"):
        new_booking = st.selectbox("Booking ID", booking_ids, index=index)
        amount = st.number_input("Amount", value=float(row.amount), min_value=0.0, step=1000.0)

        methods = ["Cash", "Bank Transfer", "JazzCash", "EasyPaisa", "Card", "Other"]
        method = st.selectbox(
            "Method",
            methods,
            index=methods.index(row.payment_method) if row.payment_method in methods else 0
        )

        payment_date = st.date_input("Payment Date", value=pd.to_datetime(row.payment_date).date())
        remarks = st.text_area("Remarks", row.remarks)

        if st.form_submit_button("Update Payment"):
            old_booking = row.booking_id

            q("""
            UPDATE payments
            SET booking_id=?, amount=?, payment_method=?, payment_date=?, remarks=?
            WHERE id=?
            """, (new_booking, amount, method, str(payment_date), remarks, selected_id))

            recalc_payment(old_booking)
            recalc_payment(new_booking)

            st.success("Payment updated.")
            st.rerun()

    if st.button("🗑️ Delete Selected Payment"):
        old_booking = row.booking_id

        q("DELETE FROM payments WHERE id=?", (selected_id,))
        recalc_payment(old_booking)

        st.success("Payment deleted.")
        st.rerun()


# =====================================================
# EXPENSE MANAGEMENT
# =====================================================

def manage_expenses():
    st.header("💸 Expense Management")

    categories = ["Decoration", "Electricity", "Staff", "Food", "Maintenance", "Rent", "Marketing", "Other"]

    with st.form("add_expense_form", clear_on_submit=True):
        title = st.text_input("Expense Title")
        category = st.selectbox("Category", categories)
        amount = st.number_input("Amount", min_value=0.0, step=500.0)
        expense_date = st.date_input("Expense Date", value=date.today())
        remarks = st.text_area("Remarks")

        if st.form_submit_button("Add Expense"):
            if not title or amount <= 0:
                st.error("Title and amount required.")
            else:
                q("""
                INSERT INTO expenses(expense_title, category, amount, expense_date, remarks)
                VALUES(?,?,?,?,?)
                """, (title, category, amount, str(expense_date), remarks))

                st.success("Expense added.")
                st.rerun()

    data = df("SELECT * FROM expenses ORDER BY id DESC")
    st.dataframe(data, use_container_width=True)

    if data.empty:
        return

    selected_id = st.selectbox("Select Expense ID", data.id.tolist())
    row = data[data.id == selected_id].iloc[0]

    with st.form("edit_expense_form"):
        title = st.text_input("Expense Title", row.expense_title)
        category = st.selectbox(
            "Category",
            categories,
            index=categories.index(row.category) if row.category in categories else 0
        )
        amount = st.number_input("Amount", value=float(row.amount), min_value=0.0, step=500.0)
        expense_date = st.date_input("Expense Date", value=pd.to_datetime(row.expense_date).date())
        remarks = st.text_area("Remarks", row.remarks)

        if st.form_submit_button("Update Expense"):
            q("""
            UPDATE expenses
            SET expense_title=?, category=?, amount=?, expense_date=?, remarks=?
            WHERE id=?
            """, (title, category, amount, str(expense_date), remarks, selected_id))

            st.success("Expense updated.")
            st.rerun()

    if st.button("🗑️ Delete Selected Expense"):
        q("DELETE FROM expenses WHERE id=?", (selected_id,))
        st.success("Expense deleted.")
        st.rerun()


# =====================================================
# STAFF MANAGEMENT
# =====================================================

def manage_staff():
    st.header("👨‍🍳 Staff Management")

    with st.form("add_staff_form", clear_on_submit=True):
        name = st.text_input("Staff Name")
        duty = st.text_input("Duty/Role")
        phone = st.text_input("Phone")
        salary = st.number_input("Salary", min_value=0.0, step=1000.0)
        status = st.selectbox("Status", ["Active", "Inactive"])

        if st.form_submit_button("Add Staff"):
            if not name:
                st.error("Name required.")
            else:
                q("""
                INSERT INTO staff(staff_name, duty, phone, salary, status)
                VALUES(?,?,?,?,?)
                """, (name, duty, phone, salary, status))

                st.success("Staff added.")
                st.rerun()

    data = df("SELECT * FROM staff ORDER BY id DESC")
    st.dataframe(data, use_container_width=True)

    if data.empty:
        return

    selected_id = st.selectbox("Select Staff ID", data.id.tolist())
    row = data[data.id == selected_id].iloc[0]

    with st.form("edit_staff_form"):
        name = st.text_input("Staff Name", row.staff_name)
        duty = st.text_input("Duty/Role", row.duty)
        phone = st.text_input("Phone", row.phone)
        salary = st.number_input("Salary", value=float(row.salary), min_value=0.0, step=1000.0)
        status = st.selectbox("Status", ["Active", "Inactive"], index=0 if row.status == "Active" else 1)

        if st.form_submit_button("Update Staff"):
            q("""
            UPDATE staff
            SET staff_name=?, duty=?, phone=?, salary=?, status=?
            WHERE id=?
            """, (name, duty, phone, salary, status, selected_id))

            st.success("Staff updated.")
            st.rerun()

    if st.button("🗑️ Delete Selected Staff"):
        q("DELETE FROM staff WHERE id=?", (selected_id,))
        st.success("Staff deleted.")
        st.rerun()


# =====================================================
# USER MANAGEMENT
# =====================================================

def manage_users():
    st.header("🔐 Users & Roles")

    roles = ["Super Admin", "Banquet Manager", "Accountant", "Customer"]

    data = df("""
    SELECT id, username, full_name, email, phone, role, created_at
    FROM users
    ORDER BY id
    """)

    st.dataframe(data, use_container_width=True)

    st.info("Every user can change his/her own password from the 'Change Password' menu. Super Admin can also reset any user's password here.")

    with st.form("add_user_form", clear_on_submit=True):
        st.subheader("➕ Add User")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        full_name = st.text_input("Full Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        role = st.selectbox("Role", roles)

        if st.form_submit_button("Add User"):
            if not username or not password or not full_name:
                st.error("Username, password and full name required.")
            elif len(password) < 6:
                st.error("Password should be at least 6 characters long.")
            else:
                try:
                    q("""
                    INSERT INTO users(username, password, full_name, email, phone, role, created_at)
                    VALUES(?,?,?,?,?,?,?)
                    """, (
                        username,
                        hpw(password),
                        full_name,
                        email,
                        phone,
                        role,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ))

                    st.success("User added.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Username already exists.")

    if data.empty:
        return

    st.subheader("✏️ Edit User / Reset Password")

    selected_id = st.selectbox("Select User ID", data.id.tolist())
    row = data[data.id == selected_id].iloc[0]

    with st.form("edit_user_form"):
        username = st.text_input("Username", row.username)
        full_name = st.text_input("Full Name", row.full_name)
        email = st.text_input("Email", row.email)
        phone = st.text_input("Phone", row.phone)
        role = st.selectbox(
            "Role",
            roles,
            index=roles.index(row.role) if row.role in roles else 3
        )

        new_password = st.text_input(
            "Reset Password - leave blank if you do not want to change this user's password",
            type="password"
        )

        if st.form_submit_button("Update User"):
            try:
                if new_password:
                    if len(new_password) < 6:
                        st.error("New password should be at least 6 characters long.")
                        return

                    q("""
                    UPDATE users
                    SET username=?, password=?, full_name=?, email=?, phone=?, role=?
                    WHERE id=?
                    """, (
                        username,
                        hpw(new_password),
                        full_name,
                        email,
                        phone,
                        role,
                        selected_id
                    ))
                else:
                    q("""
                    UPDATE users
                    SET username=?, full_name=?, email=?, phone=?, role=?
                    WHERE id=?
                    """, (
                        username,
                        full_name,
                        email,
                        phone,
                        role,
                        selected_id
                    ))

                st.success("User updated.")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Username already exists.")

    if st.button("🗑️ Delete Selected User"):
        if row.username == "superadmin":
            st.error("Main superadmin cannot be deleted.")
        else:
            q("DELETE FROM users WHERE id=?", (selected_id,))
            st.success("User deleted.")
            st.rerun()


# =====================================================
# FEEDBACK MANAGEMENT
# =====================================================

def manage_feedback():
    st.header("⭐ Feedback Management")

    data = df("SELECT * FROM feedback ORDER BY id DESC")
    st.dataframe(data, use_container_width=True)

    if data.empty:
        return

    selected_id = st.selectbox("Select Feedback ID", data.id.tolist())
    row = data[data.id == selected_id].iloc[0]

    with st.form("edit_feedback_form"):
        name = st.text_input("Customer Name", row.customer_name)
        rating = st.slider("Rating", 1, 5, int(row.rating))
        comments = st.text_area("Comments", row.comments)

        if st.form_submit_button("Update Feedback"):
            q("""
            UPDATE feedback
            SET customer_name=?, rating=?, comments=?
            WHERE id=?
            """, (name, rating, comments, selected_id))

            st.success("Feedback updated.")
            st.rerun()

    if st.button("🗑️ Delete Selected Feedback"):
        q("DELETE FROM feedback WHERE id=?", (selected_id,))
        st.success("Feedback deleted.")
        st.rerun()


# =====================================================
# CUSTOMERS AND REPORTS
# =====================================================

def customers():
    st.header("👥 Customer Records")

    data = df("""
    SELECT customer_name, phone, email,
           COUNT(*) total_bookings,
           SUM(estimated_cost) total_business
    FROM bookings
    GROUP BY customer_name, phone, email
    ORDER BY total_bookings DESC
    """)

    st.dataframe(data, use_container_width=True)

    if not data.empty:
        st.download_button(
            "Download Customers Excel",
            excel(data),
            "customers.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.info("Edit customer information from the related booking record.")


def reports():
    st.header("📁 Reports & Backup")

    tables = {
        "Bookings": df("""
            SELECT b.*, p.package_name
            FROM bookings b
            LEFT JOIN packages p ON b.package_id=p.id
        """),
        "Payments": df("SELECT * FROM payments"),
        "Expenses": df("SELECT * FROM expenses"),
        "Packages": df("SELECT * FROM packages"),
        "Staff": df("SELECT * FROM staff"),
        "Feedback": df("SELECT * FROM feedback"),
        "Users": df("""
            SELECT id, username, full_name, email, phone, role, created_at
            FROM users
        """)
    }

    col1, col2, col3 = st.columns(3)

    col1.download_button(
        "Bookings Excel",
        excel(tables["Bookings"]),
        "bookings.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    col2.download_button(
        "Payments Excel",
        excel(tables["Payments"]),
        "payments.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    col3.download_button(
        "Expenses Excel",
        excel(tables["Expenses"]),
        "expenses.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, table in tables.items():
            table.to_excel(writer, index=False, sheet_name=name)

    output.seek(0)

    st.download_button(
        "⬇️ Full Backup Excel",
        output,
        "banquet_full_backup.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# =====================================================
# CUSTOMER ACCOUNT
# =====================================================

def my_account():
    user = st.session_state.user

    st.header(f"👤 Welcome, {user['full_name']}")

    st.info("Use the 'Change Password' menu from the sidebar if you want to change your password.")

    data = df("""
    SELECT b.*, p.package_name
    FROM bookings b
    LEFT JOIN packages p ON b.package_id=p.id
    WHERE b.email=? OR b.phone=?
    ORDER BY b.id DESC
    """, (user["email"], user["phone"]))

    st.dataframe(data, use_container_width=True)

    if not data.empty:
        selected_booking = st.selectbox("Select Booking ID for Receipt", data.booking_id.tolist())
        pdf_file = receipt_pdf(data[data.booking_id == selected_booking].iloc[0].to_dict())

        st.download_button(
            "Download Receipt",
            pdf_file,
            f"{selected_booking}_receipt.pdf",
            "application/pdf"
        )


# =====================================================
# ROLE BASED ROUTING
# =====================================================

def logged_in():
    user = st.session_state.user
    role = user["role"]

    st.sidebar.success(f"Logged in as: {user['full_name']}")
    st.sidebar.info(f"Role: {role}")

    if st.sidebar.button("Logout"):
        logout()

    if role == "Super Admin":
        menu = st.sidebar.radio("Menu", [
            "Dashboard",
            "Bookings",
            "Packages",
            "Payments",
            "Expenses",
            "Customers",
            "Staff",
            "Users & Roles",
            "Feedback",
            "Reports & Backup",
            "Change Password"
        ])

        pages = {
            "Dashboard": dashboard,
            "Bookings": manage_bookings,
            "Packages": manage_packages,
            "Payments": manage_payments,
            "Expenses": manage_expenses,
            "Customers": customers,
            "Staff": manage_staff,
            "Users & Roles": manage_users,
            "Feedback": manage_feedback,
            "Reports & Backup": reports,
            "Change Password": change_my_password
        }

        pages[menu]()

    elif role == "Banquet Manager":
        menu = st.sidebar.radio("Menu", [
            "Dashboard",
            "Bookings",
            "Packages",
            "Customers",
            "Staff",
            "Feedback",
            "Change Password"
        ])

        pages = {
            "Dashboard": dashboard,
            "Bookings": manage_bookings,
            "Packages": manage_packages,
            "Customers": customers,
            "Staff": manage_staff,
            "Feedback": manage_feedback,
            "Change Password": change_my_password
        }

        pages[menu]()

    elif role == "Accountant":
        menu = st.sidebar.radio("Menu", [
            "Dashboard",
            "Payments",
            "Expenses",
            "Reports & Backup",
            "Change Password"
        ])

        pages = {
            "Dashboard": dashboard,
            "Payments": manage_payments,
            "Expenses": manage_expenses,
            "Reports & Backup": reports,
            "Change Password": change_my_password
        }

        pages[menu]()

    else:
        menu = st.sidebar.radio("Menu", [
            "My Account",
            "New Booking",
            "Change Password"
        ])

        pages = {
            "My Account": my_account,
            "New Booking": customer_panel,
            "Change Password": change_my_password
        }

        pages[menu]()


# =====================================================
# MAIN APP
# =====================================================

def main():
    st.sidebar.title("🏛️ Banquet System")

    if st.session_state.logged_in:
        logged_in()
    else:
        menu = st.sidebar.radio("Navigation", [
            "Home",
            "Customer Panel",
            "Register",
            "Login"
        ])

        pages = {
            "Home": home,
            "Customer Panel": customer_panel,
            "Register": register,
            "Login": login_page
        }

        pages[menu]()


if __name__ == "__main__":
    main()