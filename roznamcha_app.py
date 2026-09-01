import html
import sqlite3
import hashlib
from datetime import date, datetime, timedelta
from io import BytesIO
import pandas as pd
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
import streamlit as st

DB_FILE = "attendance.db"

# =========================================================
# DATABASE INITIALIZATION & HELPER FUNCTIONS
# =========================================================

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            display_name TEXT NOT NULL,
            school_name TEXT NOT NULL,
            must_change_password INTEGER DEFAULT 0
        )
    """)

    # Create Classes Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name TEXT NOT NULL,
            class_order INTEGER DEFAULT 0,
            boys_strength INTEGER DEFAULT 0,
            girls_strength INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )
    """)

    # Create Attendance Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attendance_date TEXT NOT NULL,
            class_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            boys_strength INTEGER DEFAULT 0,
            girls_strength INTEGER DEFAULT 0,
            boys_present INTEGER DEFAULT 0,
            girls_present INTEGER DEFAULT 0,
            FOREIGN KEY(class_id) REFERENCES classes(id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            UNIQUE(attendance_date, class_id)
        )
    """)

    # Insert default admin user if none exists
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO users (username, password, display_name, school_name, must_change_password)
            VALUES (?, ?, ?, ?, ?)
        """, ("admin", hash_password("adminpassword"), "School Admin", "Model High School", 0))

    # Insert default classes if none exist
    cursor.execute("SELECT COUNT(*) FROM classes")
    if cursor.fetchone()[0] == 0:
        default_classes = [
            ("Class 1", 1, 15, 15),
            ("Class 2", 2, 18, 12),
            ("Class 3", 3, 20, 20),
            ("Class 4", 4, 15, 10),
            ("Class 5", 5, 22, 18),
        ]
        cursor.executemany("""
            INSERT INTO classes (class_name, class_order, boys_strength, girls_strength)
            VALUES (?, ?, ?, ?)
        """, default_classes)

    conn.commit()
    conn.close()


def authenticate(username, password):
    conn = get_db_connection()
    hashed = hash_password(password)
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed)
    ).fetchone()
    conn.close()
    return dict(user) if user else None


def change_password(user_id, current_password, new_password):
    conn = get_db_connection()
    curr_hashed = hash_password(current_password)
    user = conn.execute(
        "SELECT id FROM users WHERE id = ? AND password = ?", (user_id, curr_hashed)
    ).fetchone()

    if not user:
        conn.close()
        return False, "Incorrect current password."

    conn.execute(
        "UPDATE users SET password = ?, must_change_password = 0 WHERE id = ?",
        (hash_password(new_password), user_id)
    )
    conn.commit()
    conn.close()
    return True, "Password successfully updated!"


def change_own_username(user_id, verify_password, new_username):
    conn = get_db_connection()
    curr_hashed = hash_password(verify_password)
    user = conn.execute(
        "SELECT id FROM users WHERE id = ? AND password = ?", (user_id, curr_hashed)
    ).fetchone()

    if not user:
        conn.close()
        return False, "Incorrect password verification."

    try:
        conn.execute(
            "UPDATE users SET username = ? WHERE id = ?", (new_username.strip(), user_id)
        )
        conn.commit()
        conn.close()
        return True, "Username successfully updated!"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Username is already taken."


# =========================================================
# CLASS MANAGEMENT FUNCTIONS
# =========================================================

def get_school_classes(active_only=True):
    conn = get_db_connection()
    query = "SELECT * FROM classes"
    if active_only:
        query += " WHERE is_active = 1"
    query += " ORDER BY class_order ASC"
    classes = conn.execute(query).fetchall()
    conn.close()
    return [dict(c) for c in classes]


def add_new_class(class_name, class_order, boys_strength, girls_strength):
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO classes (class_name, class_order, boys_strength, girls_strength, is_active)
        VALUES (?, ?, ?, ?, 1)
    """, (class_name.strip(), class_order, boys_strength, girls_strength))
    conn.commit()
    conn.close()


def update_class_status(class_id, is_active):
    conn = get_db_connection()
    conn.execute("UPDATE classes SET is_active = ? WHERE id = ?", (1 if is_active else 0, class_id))
    conn.commit()
    conn.close()


def update_class_details(class_id, class_name, class_order, boys_str, girls_str):
    conn = get_db_connection()
    conn.execute("""
        UPDATE classes 
        SET class_name = ?, class_order = ?, boys_strength = ?, girls_strength = ?
        WHERE id = ?
    """, (class_name.strip(), class_order, boys_str, girls_str, class_id))
    conn.commit()
    conn.close()


# =========================================================
# ATTENDANCE RECORD FUNCTIONS
# =========================================================

def get_existing_attendance(selected_date):
    conn = get_db_connection()
    records = conn.execute(
        "SELECT * FROM attendance WHERE attendance_date = ?", (selected_date.strftime("%Y-%m-%d"),)
    ).fetchall()
    conn.close()
    return {r["class_id"]: dict(r) for r in records}


def save_attendance(selected_date, user_id, entries):
    conn = get_db_connection()
    date_str = selected_date.strftime("%Y-%m-%d")

    for entry in entries:
        conn.execute("""
            INSERT INTO attendance (attendance_date, class_id, user_id, boys_strength, girls_strength, boys_present, girls_present)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(attendance_date, class_id) DO UPDATE SET
                user_id = excluded.user_id,
                boys_strength = excluded.boys_strength,
                girls_strength = excluded.girls_strength,
                boys_present = excluded.boys_present,
                girls_present = excluded.girls_present
        """, (
            date_str, entry["class_id"], user_id,
            entry["boys_strength"], entry["girls_strength"],
            entry["boys_present"], entry["girls_present"]
        ))

    conn.commit()
    conn.close()


def attendance_dataframe(start_date, end_date):
    conn = get_db_connection()
    query = """
        SELECT 
            a.attendance_date AS Date,
            c.class_name AS Class,
            c.class_order AS Class_Order,
            a.boys_strength AS "Boys Enrolled",
            a.girls_strength AS "Girls Enrolled",
            (a.boys_strength + a.girls_strength) AS "Total Enrolled",
            a.boys_present AS "Boys Present",
            a.girls_present AS "Girls Present",
            (a.boys_present + a.girls_present) AS "Total Present",
            ((a.boys_strength + a.girls_strength) - (a.boys_present + a.girls_present)) AS "Total Absent",
            CASE 
                WHEN (a.boys_strength + a.girls_strength) > 0 
                THEN ROUND(CAST((a.boys_present + a.girls_present) AS FLOAT) / (a.boys_strength + a.girls_strength) * 100, 2)
                ELSE 0 
            END AS "Attendance Percentage"
        FROM attendance a
        JOIN classes c ON a.class_id = c.id
        WHERE a.attendance_date BETWEEN ? AND ?
        ORDER BY a.attendance_date DESC, c.class_order ASC
    """
    df = pd.read_sql_query(query, conn, params=(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
    conn.close()
    return df


def summarize_attendance(df, grouping_columns):
    summary = df.groupby(grouping_columns).agg({
        "Boys Enrolled": "sum",
        "Girls Enrolled": "sum",
        "Total Enrolled": "sum",
        "Boys Present": "sum",
        "Girls Present": "sum",
        "Total Present": "sum",
        "Total Absent": "sum"
    }).reset_index()

    summary["Attendance Percentage"] = (
        (summary["Total Present"] / summary["Total Enrolled"]).fillna(0) * 100
    ).round(2)
    return summary


def render_roznamcha_table(df):
    st.dataframe(df.drop(columns=["Class_Order"], errors="ignore"), use_container_width=True)


# =========================================================
# EXCEL EXPORT HELPERS
# =========================================================

def style_excel_sheet(worksheet):
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Calibri", size=11)
    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9")
    )

    for col in worksheet.columns:
        max_len = 0
        col_letter = col[0].column_letter

        for cell in col:
            if cell.row == 1:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            else:
                cell.font = data_font
                cell.border = thin_border

            val_str = str(cell.value or "")
            max_len = max(max_len, len(val_str))

            heading = str(worksheet.cell(row=1, column=cell.column).value or "")
            if "Percentage" in heading or "%" in heading:
                cell.number_format = "0.00%"
                cell.alignment = Alignment(horizontal="right")
            elif isinstance(cell.value, (int, float)):
                cell.alignment = Alignment(horizontal="right")
            elif isinstance(cell.value, (date, datetime)):
                cell.number_format = "YYYY-MM-DD"
                cell.alignment = Alignment(horizontal="center")

        worksheet.column_dimensions[col_letter].width = max(max_len + 3, 12)


def build_excel_report(data):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        if not data.empty:
            export_df = data.drop(columns=["Class_Order"], errors="ignore")
            export_df.to_excel(writer, sheet_name="Raw Data", index=False)
            style_excel_sheet(writer.sheets["Raw Data"])

            if "Class" in data.columns:
                class_summary = summarize_attendance(data, grouping_columns=["Class"])
                class_summary.to_excel(writer, sheet_name="Class Summary", index=False)
                style_excel_sheet(writer.sheets["Class Summary"])
        else:
            pd.DataFrame({"Message": ["No data available"]}).to_excel(
                writer, sheet_name="Report", index=False
            )

    output.seek(0)
    return output.getvalue()


# =========================================================
# MODALS & ACCOUNT SETTINGS
# =========================================================

@st.dialog("Change Password")
def change_password_dialog(user):
    st.write("Please update your password to proceed.")
    with st.form("dialog_change_password_form"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        submit = st.form_submit_button("Update Password")

        if submit:
            if new_password != confirm_password:
                st.error("New passwords do not match.")
            else:
                success, message = change_password(
                    user["id"], current_password, new_password
                )
                if success:
                    st.session_state["user"]["must_change_password"] = 0
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)


def render_account_settings(user):
    st.subheader("Account Settings")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### Change Password")
        with st.form("settings_change_password_form"):
            curr_pass = st.text_input("Current Password", type="password", key="sec_curr")
            new_pass = st.text_input("New Password", type="password", key="sec_new")
            confirm_pass = st.text_input("Confirm Password", type="password", key="sec_conf")
            btn_pass = st.form_submit_button("Update Password")

            if btn_pass:
                if new_pass != confirm_pass:
                    st.error("New passwords do not match.")
                else:
                    ok, msg = change_password(user["id"], curr_pass, new_pass)
                    if ok:
                        st.session_state["user"]["must_change_password"] = 0
                        st.success(msg)
                    else:
                        st.error(msg)

    with col2:
        st.markdown("##### Change Username")
        with st.form("settings_change_username_form"):
            new_user = st.text_input("New Username", key="sec_uname")
            verify_pass = st.text_input("Current Password", type="password", key="sec_u_pass")
            btn_uname = st.form_submit_button("Update Username")

            if btn_uname:
                ok, msg = change_own_username(user["id"], verify_pass, new_user)
                if ok:
                    st.session_state["user"]["username"] = new_user.strip()
                    st.success(msg)
                else:
                    st.error(msg)


def render_manage_classes():
    st.subheader("Manage Classes")

    # Add New Class Form
    with st.expander("➕ Add New Class", expanded=True):
        with st.form("add_class_form"):
            c1, c2 = st.columns(2)
            c_name = c1.text_input("Class Name", placeholder="e.g. Class 6 or Nursery")
            c_order = c2.number_input("Display Order", min_value=1, value=6, help="Position in list")

            c3, c4 = st.columns(2)
            b_str = c3.number_input("Default Boys Enrolled", min_value=0, value=0)
            g_str = c4.number_input("Default Girls Enrolled", min_value=0, value=0)

            add_btn = st.form_submit_button("Add Class", use_container_width=True)

            if add_btn:
                if not c_name.strip():
                    st.error("Please enter a valid class name.")
                else:
                    add_new_class(c_name, c_order, b_str, g_str)
                    st.success(f"Class '{c_name}' added successfully!")
                    st.rerun()

    st.markdown("---")
    st.subheader("Existing Classes")

    all_classes = get_school_classes(active_only=False)

    for cls in all_classes:
        c_id = cls["id"]
        with st.expander(f"📌 {cls['class_name']} {'(Inactive)' if not cls['is_active'] else ''}"):
            with st.form(f"edit_class_{c_id}"):
                col1, col2 = st.columns(2)
                name_val = col1.text_input("Class Name", value=cls["class_name"], key=f"name_{c_id}")
                order_val = col2.number_input("Order", min_value=1, value=cls["class_order"], key=f"ord_{c_id}")

                col3, col4 = st.columns(2)
                b_val = col3.number_input("Default Boys Enrolled", min_value=0, value=cls["boys_strength"], key=f"b_{c_id}")
                g_val = col4.number_input("Default Girls Enrolled", min_value=0, value=cls["girls_strength"], key=f"g_{c_id}")

                is_active_val = st.checkbox("Active Class", value=bool(cls["is_active"]), key=f"act_{c_id}")

                save_btn = st.form_submit_button("Update Class Details")

                if save_btn:
                    update_class_details(c_id, name_val, order_val, b_val, g_val)
                    update_class_status(c_id, is_active_val)
                    st.success(f"Updated '{name_val}' successfully!")
                    st.rerun()


# =========================================================
# SCHOOL DASHBOARD & ENTRY
# =========================================================

def render_school_dashboard(user):
    school_name = user.get("school_name", "School Attendance System")

    st.sidebar.markdown(f"**Logged in as:** {user['display_name']}")
    page = st.sidebar.radio("Navigation", ["Mark Attendance", "Manage Classes", "View Records", "Account Settings"])

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    if page == "Mark Attendance":
        st.html(
            f"""
            <div class="dashboard-heading">
                <h2>{html.escape(school_name)}</h2>
                <p>Daily Student Attendance Entry</p>
            </div>
            """
        )

        selected_date = st.date_input("Attendance Date", value=date.today())
        classes = get_school_classes(active_only=True)
        existing_data = get_existing_attendance(selected_date)

        if not classes:
            st.warning("No active classes found in the system. Go to 'Manage Classes' to create one.")
            return

        st.info("Enter student counts for each class below:")

        entries = []
        with st.form("attendance_entry_form"):
            for cls in classes:
                c_id = cls["id"]
                c_name = cls["class_name"]
                c_prev = existing_data.get(c_id, {})

                st.markdown(f"#### Class: {c_name}")
                col1, col2, col3, col4 = st.columns(4)

                b_str = col1.number_input(
                    f"Boys Enrolled ({c_name})",
                    min_value=0,
                    value=c_prev.get("boys_strength", cls.get("boys_strength", 0)),
                    key=f"b_str_{c_id}"
                )
                g_str = col2.number_input(
                    f"Girls Enrolled ({c_name})",
                    min_value=0,
                    value=c_prev.get("girls_strength", cls.get("girls_strength", 0)),
                    key=f"g_str_{c_id}"
                )
                b_pres = col3.number_input(
                    f"Boys Present ({c_name})",
                    min_value=0,
                    max_value=b_str,
                    value=c_prev.get("boys_present", 0),
                    key=f"b_pres_{c_id}"
                )
                g_pres = col4.number_input(
                    f"Girls Present ({c_name})",
                    min_value=0,
                    max_value=g_str,
                    value=c_prev.get("girls_present", 0),
                    key=f"g_pres_{c_id}"
                )

                entries.append({
                    "class_id": c_id,
                    "boys_strength": b_str,
                    "girls_strength": g_str,
                    "boys_present": b_pres,
                    "girls_present": g_pres
                })
                st.divider()

            submit_btn = st.form_submit_button("Save Attendance Record", use_container_width=True)

        if submit_btn:
            save_attendance(selected_date, user["id"], entries)
            st.success(f"Attendance successfully saved for {selected_date.strftime('%Y-%m-%d')}!")

    elif page == "Manage Classes":
        render_manage_classes()

    elif page == "View Records":
        st.title("Attendance History")
        col1, col2 = st.columns(2)
        start_d = col1.date_input("Start Date", value=date.today() - timedelta(days=7))
        end_d = col2.date_input("End Date", value=date.today())

        df = attendance_dataframe(start_d, end_d)

        if not df.empty:
            st.markdown("### Roznamcha Summary View")
            render_roznamcha_table(df)

            st.markdown("### Download Data")
            excel_bytes = build_excel_report(df)
            st.download_button(
                label="📥 Export Excel Report",
                data=excel_bytes,
                file_name=f"Attendance_Report_{start_d}_to_{end_d}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("No attendance records found for the selected date range.")

    elif page == "Account Settings":
        render_account_settings(user)


# =========================================================
# LOGIN SCREEN & MAIN APP ROUTER
# =========================================================

def render_login():
    st.markdown(
        """
        <div style="text-align: center; padding: 2rem 0;">
            <h1>📘 School Attendance System</h1>
            <p>Please log in with your credentials to manage class attendance</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign In", use_container_width=True)

            if submit:
                user = authenticate(username, password)
                if user:
                    st.session_state["user"] = user
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")


def main():
    initialize_database()

    if "user" not in st.session_state:
        render_login()
    else:
        user = st.session_state["user"]

        if user.get("must_change_password") == 1:
            change_password_dialog(user)

        render_school_dashboard(user)


if __name__ == "__main__":
    main()