import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO
from datetime import date, datetime

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="School LMS Dashboard",
    page_icon="🏫",
    layout="wide"
)

DB_NAME = "school_lms.db"


# =====================================================
# DATABASE CONNECTION
# =====================================================

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS schools (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        school_name TEXT UNIQUE,
        location TEXT,
        head_teacher TEXT,
        contact TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admission_no TEXT,
        student_name TEXT,
        father_name TEXT,
        gender TEXT,
        class_name TEXT,
        section TEXT,
        school_name TEXT,
        status TEXT DEFAULT 'Active'
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_name TEXT,
        designation TEXT,
        school_name TEXT,
        contact TEXT,
        status TEXT DEFAULT 'Active'
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS student_attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        attendance_date TEXT,
        school_name TEXT,
        class_name TEXT,
        section TEXT,
        admission_no TEXT,
        student_name TEXT,
        status TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS teacher_attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        attendance_date TEXT,
        school_name TEXT,
        teacher_name TEXT,
        status TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS nsb_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_date TEXT,
        school_name TEXT,
        financial_year TEXT,
        opening_balance REAL,
        receipt_amount REAL,
        expenditure_amount REAL,
        description TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS fee_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fee_date TEXT,
        school_name TEXT,
        admission_no TEXT,
        student_name TEXT,
        class_name TEXT,
        fee_month TEXT,
        total_fee REAL,
        paid_fee REAL,
        remaining_fee REAL,
        remarks TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS expense_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        expense_date TEXT,
        school_name TEXT,
        category TEXT,
        amount REAL,
        paid_to TEXT,
        description TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS vouchers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        voucher_date TEXT,
        school_name TEXT,
        voucher_no TEXT,
        bill_no TEXT,
        category TEXT,
        amount REAL,
        vendor_name TEXT,
        description TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def run_query(query, params=()):
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def execute_query(query, params=()):
    conn = get_connection()
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()


def read_uploaded_file(uploaded_file):
    if uploaded_file is None:
        return None

    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):
        return pd.read_csv(uploaded_file)

    if file_name.endswith(".xlsx") or file_name.endswith(".xls"):
        return pd.read_excel(uploaded_file)

    st.error("Only CSV or Excel files are allowed.")
    return None


def clean_columns(df):
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )
    return df


def to_excel_download(df, sheet_name="Report"):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()


def get_school_list():
    df = run_query("SELECT school_name FROM schools ORDER BY school_name")
    if df.empty:
        return []
    return df["school_name"].tolist()


def show_template(columns):
    template = pd.DataFrame(columns=columns)
    st.download_button(
        "⬇️ Download Sample Template",
        data=to_excel_download(template, "Template"),
        file_name="sample_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def insert_dataframe(df, table_name, required_columns):
    df = clean_columns(df)

    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        st.error(f"Missing columns: {missing}")
        st.info(f"Required columns are: {required_columns}")
        return

    df = df[required_columns]

    conn = get_connection()
    df.to_sql(table_name, conn, if_exists="append", index=False)
    conn.close()

    st.success(f"Data uploaded successfully into {table_name}.")


# =====================================================
# LOGIN SYSTEM
# =====================================================

def login_page():
    st.markdown("""
    <h1 style='text-align:center;'>🏫 School Attendance + NSB + Fee Dashboard</h1>
    <h4 style='text-align:center;color:gray;'>Advanced LMS for Schools, Academies and School Networks</h4>
    """, unsafe_allow_html=True)

    st.write("---")

    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        st.subheader("🔐 Admin Login")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login", use_container_width=True):
            if username == "admin" and password == "admin123":
                st.session_state["logged_in"] = True
                st.success("Login successful.")
                st.rerun()
            else:
                st.error("Invalid username or password.")

        st.info("Default Login: admin / admin123")


if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_page()
    st.stop()


# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.title("🏫 LMS Menu")

menu = st.sidebar.radio(
    "Select Section",
    [
        "Dashboard",
        "Schools",
        "Students",
        "Teachers",
        "Student Attendance",
        "Teacher Attendance",
        "NSB Records",
        "Fee Records",
        "Expenses",
        "Vouchers / Bills",
        "Reports",
        "Data Upload Center",
        "Logout"
    ]
)

if menu == "Logout":
    st.session_state["logged_in"] = False
    st.rerun()


# =====================================================
# DASHBOARD
# =====================================================

if menu == "Dashboard":
    st.title("📊 Main Dashboard")

    schools_df = run_query("SELECT * FROM schools")
    students_df = run_query("SELECT * FROM students")
    teachers_df = run_query("SELECT * FROM teachers")
    fee_df = run_query("SELECT * FROM fee_records")
    nsb_df = run_query("SELECT * FROM nsb_records")
    expense_df = run_query("SELECT * FROM expense_records")

    total_schools = len(schools_df)
    total_students = len(students_df)
    total_teachers = len(teachers_df)
    total_fee_received = fee_df["paid_fee"].sum() if not fee_df.empty else 0
    total_nsb_receipts = nsb_df["receipt_amount"].sum() if not nsb_df.empty else 0
    total_nsb_expenses = nsb_df["expenditure_amount"].sum() if not nsb_df.empty else 0
    total_expenses = expense_df["amount"].sum() if not expense_df.empty else 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Schools", total_schools)
    col2.metric("Total Students", total_students)
    col3.metric("Total Teachers", total_teachers)
    col4.metric("Fee Received", f"Rs. {total_fee_received:,.0f}")

    col5, col6, col7 = st.columns(3)

    col5.metric("NSB Receipts", f"Rs. {total_nsb_receipts:,.0f}")
    col6.metric("NSB Expenditure", f"Rs. {total_nsb_expenses:,.0f}")
    col7.metric("Other Expenses", f"Rs. {total_expenses:,.0f}")

    st.write("---")

    st.subheader("🏫 School-wise Student Strength")

    if not students_df.empty:
        school_strength = students_df.groupby("school_name")["id"].count().reset_index()
        school_strength.columns = ["School", "Students"]
        st.bar_chart(school_strength.set_index("School"))
        st.dataframe(school_strength, use_container_width=True)
    else:
        st.info("No student data available.")

    st.subheader("💰 School-wise Fee Collection")

    if not fee_df.empty:
        fee_summary = fee_df.groupby("school_name")[["total_fee", "paid_fee", "remaining_fee"]].sum().reset_index()
        st.dataframe(fee_summary, use_container_width=True)
        st.bar_chart(fee_summary.set_index("school_name")[["paid_fee", "remaining_fee"]])
    else:
        st.info("No fee data available.")

    st.subheader("🏦 NSB Balance Summary")

    if not nsb_df.empty:
        nsb_summary = nsb_df.groupby("school_name")[["receipt_amount", "expenditure_amount"]].sum().reset_index()
        nsb_summary["balance"] = nsb_summary["receipt_amount"] - nsb_summary["expenditure_amount"]
        st.dataframe(nsb_summary, use_container_width=True)
        st.bar_chart(nsb_summary.set_index("school_name")[["receipt_amount", "expenditure_amount", "balance"]])
    else:
        st.info("No NSB record available.")


# =====================================================
# SCHOOLS
# =====================================================

elif menu == "Schools":
    st.title("🏫 School Management")

    tab1, tab2 = st.tabs(["Manual Entry", "View Schools"])

    with tab1:
        st.subheader("Add School Manually")

        with st.form("school_form"):
            school_name = st.text_input("School Name")
            location = st.text_input("Location")
            head_teacher = st.text_input("Head Teacher")
            contact = st.text_input("Contact")

            submit = st.form_submit_button("Save School")

            if submit:
                if school_name.strip() == "":
                    st.warning("School name is required.")
                else:
                    try:
                        execute_query(
                            """
                            INSERT INTO schools 
                            (school_name, location, head_teacher, contact)
                            VALUES (?, ?, ?, ?)
                            """,
                            (school_name, location, head_teacher, contact)
                        )
                        st.success("School saved successfully.")
                    except:
                        st.error("This school already exists.")

    with tab2:
        df = run_query("SELECT * FROM schools ORDER BY school_name")
        st.dataframe(df, use_container_width=True)

        if not df.empty:
            st.download_button(
                "⬇️ Download Schools Excel",
                data=to_excel_download(df, "Schools"),
                file_name="schools_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


# =====================================================
# STUDENTS
# =====================================================

elif menu == "Students":
    st.title("👨‍🎓 Student Management")

    schools = get_school_list()

    tab1, tab2 = st.tabs(["Manual Entry", "View Students"])

    with tab1:
        st.subheader("Add Student Manually")

        with st.form("student_form"):
            admission_no = st.text_input("Admission No")
            student_name = st.text_input("Student Name")
            father_name = st.text_input("Father Name")
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            class_name = st.text_input("Class")
            section = st.text_input("Section")
            school_name = st.selectbox("School", schools) if schools else st.text_input("School Name")
            status = st.selectbox("Status", ["Active", "Left", "Dropout"])

            submit = st.form_submit_button("Save Student")

            if submit:
                execute_query(
                    """
                    INSERT INTO students 
                    (admission_no, student_name, father_name, gender, class_name, section, school_name, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (admission_no, student_name, father_name, gender, class_name, section, school_name, status)
                )
                st.success("Student saved successfully.")

    with tab2:
        df = run_query("SELECT * FROM students ORDER BY school_name, class_name, student_name")
        st.dataframe(df, use_container_width=True)

        if not df.empty:
            st.download_button(
                "⬇️ Download Students Excel",
                data=to_excel_download(df, "Students"),
                file_name="students_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


# =====================================================
# TEACHERS
# =====================================================

elif menu == "Teachers":
    st.title("👨‍🏫 Teacher Management")

    schools = get_school_list()

    tab1, tab2 = st.tabs(["Manual Entry", "View Teachers"])

    with tab1:
        st.subheader("Add Teacher Manually")

        with st.form("teacher_form"):
            teacher_name = st.text_input("Teacher Name")
            designation = st.text_input("Designation")
            school_name = st.selectbox("School", schools) if schools else st.text_input("School Name")
            contact = st.text_input("Contact")
            status = st.selectbox("Status", ["Active", "Left", "Transferred"])

            submit = st.form_submit_button("Save Teacher")

            if submit:
                execute_query(
                    """
                    INSERT INTO teachers 
                    (teacher_name, designation, school_name, contact, status)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (teacher_name, designation, school_name, contact, status)
                )
                st.success("Teacher saved successfully.")

    with tab2:
        df = run_query("SELECT * FROM teachers ORDER BY school_name, teacher_name")
        st.dataframe(df, use_container_width=True)

        if not df.empty:
            st.download_button(
                "⬇️ Download Teachers Excel",
                data=to_excel_download(df, "Teachers"),
                file_name="teachers_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


# =====================================================
# STUDENT ATTENDANCE
# =====================================================

elif menu == "Student Attendance":
    st.title("🧒 Student Attendance")

    schools = get_school_list()

    tab1, tab2, tab3 = st.tabs([
        "Absentees-only Marking",
        "Manual Single Entry",
        "Attendance View"
    ])

    with tab1:
        st.subheader("Mark Attendance by Selecting Absentees Only")

        if not schools:
            st.warning("Please add schools first.")
        else:
            attendance_date = st.date_input("Attendance Date", date.today())
            school_name = st.selectbox("Select School", schools)

            classes_df = run_query(
                "SELECT DISTINCT class_name FROM students WHERE school_name=? AND status='Active'",
                (school_name,)
            )

            class_list = classes_df["class_name"].dropna().tolist()

            if class_list:
                class_name = st.selectbox("Select Class", class_list)

                sections_df = run_query(
                    """
                    SELECT DISTINCT section FROM students 
                    WHERE school_name=? AND class_name=? AND status='Active'
                    """,
                    (school_name, class_name)
                )

                section_list = sections_df["section"].dropna().tolist()
                section = st.selectbox("Select Section", section_list) if section_list else ""

                students = run_query(
                    """
                    SELECT admission_no, student_name 
                    FROM students 
                    WHERE school_name=? AND class_name=? AND section=? AND status='Active'
                    ORDER BY student_name
                    """,
                    (school_name, class_name, section)
                )

                if not students.empty:
                    student_options = [
                        f"{row['admission_no']} - {row['student_name']}"
                        for _, row in students.iterrows()
                    ]

                    absent_students = st.multiselect(
                        "Select Absent Students Only",
                        student_options
                    )

                    if st.button("Save Attendance", use_container_width=True):
                        execute_query(
                            """
                            DELETE FROM student_attendance 
                            WHERE attendance_date=? AND school_name=? AND class_name=? AND section=?
                            """,
                            (str(attendance_date), school_name, class_name, section)
                        )

                        for _, row in students.iterrows():
                            label = f"{row['admission_no']} - {row['student_name']}"
                            status = "Absent" if label in absent_students else "Present"

                            execute_query(
                                """
                                INSERT INTO student_attendance 
                                (attendance_date, school_name, class_name, section, admission_no, student_name, status)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    str(attendance_date),
                                    school_name,
                                    class_name,
                                    section,
                                    row["admission_no"],
                                    row["student_name"],
                                    status
                                )
                            )

                        st.success("Attendance saved successfully.")
                else:
                    st.info("No active students found.")
            else:
                st.info("No class data found.")

    with tab2:
        st.subheader("Manual Single Student Attendance Entry")

        with st.form("student_attendance_form"):
            attendance_date = st.date_input("Date", date.today())
            school_name = st.selectbox("School", schools) if schools else st.text_input("School")
            class_name = st.text_input("Class")
            section = st.text_input("Section")
            admission_no = st.text_input("Admission No")
            student_name = st.text_input("Student Name")
            status = st.selectbox("Status", ["Present", "Absent", "Leave"])

            submit = st.form_submit_button("Save Entry")

            if submit:
                execute_query(
                    """
                    INSERT INTO student_attendance
                    (attendance_date, school_name, class_name, section, admission_no, student_name, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (str(attendance_date), school_name, class_name, section, admission_no, student_name, status)
                )
                st.success("Attendance entry saved.")

    with tab3:
        st.subheader("Student Attendance Record")

        df = run_query("SELECT * FROM student_attendance ORDER BY attendance_date DESC")

        if not df.empty:
            st.dataframe(df, use_container_width=True)

            summary = df.groupby(["school_name", "status"])["id"].count().reset_index()
            st.subheader("Attendance Summary")
            st.dataframe(summary, use_container_width=True)

            st.download_button(
                "⬇️ Download Student Attendance Excel",
                data=to_excel_download(df, "Student Attendance"),
                file_name="student_attendance_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("No attendance record available.")


# =====================================================
# TEACHER ATTENDANCE
# =====================================================

elif menu == "Teacher Attendance":
    st.title("👨‍🏫 Teacher Attendance")

    schools = get_school_list()

    tab1, tab2, tab3 = st.tabs([
        "Absentees-only Marking",
        "Manual Single Entry",
        "View Attendance"
    ])

    with tab1:
        st.subheader("Mark Teacher Attendance by Selecting Absentees Only")

        if not schools:
            st.warning("Please add schools first.")
        else:
            attendance_date = st.date_input("Attendance Date", date.today())
            school_name = st.selectbox("School", schools)

            teachers = run_query(
                """
                SELECT teacher_name 
                FROM teachers 
                WHERE school_name=? AND status='Active'
                ORDER BY teacher_name
                """,
                (school_name,)
            )

            if not teachers.empty:
                teacher_list = teachers["teacher_name"].tolist()

                absent_teachers = st.multiselect(
                    "Select Absent Teachers Only",
                    teacher_list
                )

                if st.button("Save Teacher Attendance", use_container_width=True):
                    execute_query(
                        """
                        DELETE FROM teacher_attendance 
                        WHERE attendance_date=? AND school_name=?
                        """,
                        (str(attendance_date), school_name)
                    )

                    for teacher in teacher_list:
                        status = "Absent" if teacher in absent_teachers else "Present"

                        execute_query(
                            """
                            INSERT INTO teacher_attendance 
                            (attendance_date, school_name, teacher_name, status)
                            VALUES (?, ?, ?, ?)
                            """,
                            (str(attendance_date), school_name, teacher, status)
                        )

                    st.success("Teacher attendance saved successfully.")
            else:
                st.info("No active teachers found.")

    with tab2:
        st.subheader("Manual Teacher Attendance Entry")

        with st.form("teacher_attendance_form"):
            attendance_date = st.date_input("Date", date.today())
            school_name = st.selectbox("School", schools) if schools else st.text_input("School")
            teacher_name = st.text_input("Teacher Name")
            status = st.selectbox("Status", ["Present", "Absent", "Leave"])

            submit = st.form_submit_button("Save Entry")

            if submit:
                execute_query(
                    """
                    INSERT INTO teacher_attendance 
                    (attendance_date, school_name, teacher_name, status)
                    VALUES (?, ?, ?, ?)
                    """,
                    (str(attendance_date), school_name, teacher_name, status)
                )
                st.success("Teacher attendance saved.")

    with tab3:
        df = run_query("SELECT * FROM teacher_attendance ORDER BY attendance_date DESC")
        st.dataframe(df, use_container_width=True)

        if not df.empty:
            st.download_button(
                "⬇️ Download Teacher Attendance Excel",
                data=to_excel_download(df, "Teacher Attendance"),
                file_name="teacher_attendance_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


# =====================================================
# NSB RECORDS
# =====================================================

elif menu == "NSB Records":
    st.title("🏦 NSB Receipt and Expenditure Record")

    schools = get_school_list()

    tab1, tab2 = st.tabs(["Manual Entry", "View NSB Records"])

    with tab1:
        with st.form("nsb_form"):
            record_date = st.date_input("Date", date.today())
            school_name = st.selectbox("School", schools) if schools else st.text_input("School")
            financial_year = st.text_input("Financial Year", value="2025-2026")
            opening_balance = st.number_input("Opening Balance", min_value=0.0, step=100.0)
            receipt_amount = st.number_input("Receipt Amount", min_value=0.0, step=100.0)
            expenditure_amount = st.number_input("Expenditure Amount", min_value=0.0, step=100.0)
            description = st.text_area("Description")

            submit = st.form_submit_button("Save NSB Record")

            if submit:
                execute_query(
                    """
                    INSERT INTO nsb_records
                    (record_date, school_name, financial_year, opening_balance, receipt_amount, expenditure_amount, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(record_date),
                        school_name,
                        financial_year,
                        opening_balance,
                        receipt_amount,
                        expenditure_amount,
                        description
                    )
                )
                st.success("NSB record saved.")

    with tab2:
        df = run_query("SELECT * FROM nsb_records ORDER BY record_date DESC")

        if not df.empty:
            df["balance"] = df["opening_balance"] + df["receipt_amount"] - df["expenditure_amount"]
            st.dataframe(df, use_container_width=True)

            summary = df.groupby("school_name")[["receipt_amount", "expenditure_amount"]].sum().reset_index()
            summary["balance"] = summary["receipt_amount"] - summary["expenditure_amount"]

            st.subheader("School-wise NSB Summary")
            st.dataframe(summary, use_container_width=True)

            st.download_button(
                "⬇️ Download NSB Excel",
                data=to_excel_download(df, "NSB Records"),
                file_name="nsb_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("No NSB record available.")


# =====================================================
# FEE RECORDS
# =====================================================

elif menu == "Fee Records":
    st.title("💵 Student Fee Records")

    schools = get_school_list()

    tab1, tab2 = st.tabs(["Manual Entry", "View Fee Records"])

    with tab1:
        with st.form("fee_form"):
            fee_date = st.date_input("Fee Date", date.today())
            school_name = st.selectbox("School", schools) if schools else st.text_input("School")
            admission_no = st.text_input("Admission No")
            student_name = st.text_input("Student Name")
            class_name = st.text_input("Class")
            fee_month = st.text_input("Fee Month", value=datetime.now().strftime("%B"))
            total_fee = st.number_input("Total Fee", min_value=0.0, step=100.0)
            paid_fee = st.number_input("Paid Fee", min_value=0.0, step=100.0)
            remaining_fee = total_fee - paid_fee
            st.info(f"Remaining Fee: Rs. {remaining_fee:,.0f}")
            remarks = st.text_area("Remarks")

            submit = st.form_submit_button("Save Fee Record")

            if submit:
                execute_query(
                    """
                    INSERT INTO fee_records
                    (fee_date, school_name, admission_no, student_name, class_name, fee_month, total_fee, paid_fee, remaining_fee, remarks)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(fee_date),
                        school_name,
                        admission_no,
                        student_name,
                        class_name,
                        fee_month,
                        total_fee,
                        paid_fee,
                        remaining_fee,
                        remarks
                    )
                )
                st.success("Fee record saved.")

    with tab2:
        df = run_query("SELECT * FROM fee_records ORDER BY fee_date DESC")

        if not df.empty:
            st.dataframe(df, use_container_width=True)

            summary = df.groupby("school_name")[["total_fee", "paid_fee", "remaining_fee"]].sum().reset_index()

            st.subheader("School-wise Fee Summary")
            st.dataframe(summary, use_container_width=True)

            st.download_button(
                "⬇️ Download Fee Excel",
                data=to_excel_download(df, "Fee Records"),
                file_name="fee_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("No fee record available.")


# =====================================================
# EXPENSES
# =====================================================

elif menu == "Expenses":
    st.title("💸 Expense Records")

    schools = get_school_list()

    tab1, tab2 = st.tabs(["Manual Entry", "View Expenses"])

    with tab1:
        with st.form("expense_form"):
            expense_date = st.date_input("Expense Date", date.today())
            school_name = st.selectbox("School", schools) if schools else st.text_input("School")
            category = st.selectbox(
                "Expense Category",
                [
                    "Stationery",
                    "Repair",
                    "Electricity",
                    "Furniture",
                    "Cleaning",
                    "Salary",
                    "Transport",
                    "Other"
                ]
            )
            amount = st.number_input("Amount", min_value=0.0, step=100.0)
            paid_to = st.text_input("Paid To")
            description = st.text_area("Description")

            submit = st.form_submit_button("Save Expense")

            if submit:
                execute_query(
                    """
                    INSERT INTO expense_records
                    (expense_date, school_name, category, amount, paid_to, description)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(expense_date),
                        school_name,
                        category,
                        amount,
                        paid_to,
                        description
                    )
                )
                st.success("Expense saved.")

    with tab2:
        df = run_query("SELECT * FROM expense_records ORDER BY expense_date DESC")

        if not df.empty:
            st.dataframe(df, use_container_width=True)

            summary = df.groupby(["school_name", "category"])["amount"].sum().reset_index()
            st.subheader("Expense Summary")
            st.dataframe(summary, use_container_width=True)

            st.download_button(
                "⬇️ Download Expenses Excel",
                data=to_excel_download(df, "Expenses"),
                file_name="expense_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("No expense record available.")


# =====================================================
# VOUCHERS / BILLS
# =====================================================

elif menu == "Vouchers / Bills":
    st.title("🧾 Voucher and Bill Records")

    schools = get_school_list()

    tab1, tab2 = st.tabs(["Manual Entry", "View Vouchers"])

    with tab1:
        with st.form("voucher_form"):
            voucher_date = st.date_input("Voucher Date", date.today())
            school_name = st.selectbox("School", schools) if schools else st.text_input("School")
            voucher_no = st.text_input("Voucher No")
            bill_no = st.text_input("Bill No")
            category = st.text_input("Category")
            amount = st.number_input("Amount", min_value=0.0, step=100.0)
            vendor_name = st.text_input("Vendor Name")
            description = st.text_area("Description")

            submit = st.form_submit_button("Save Voucher")

            if submit:
                execute_query(
                    """
                    INSERT INTO vouchers
                    (voucher_date, school_name, voucher_no, bill_no, category, amount, vendor_name, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(voucher_date),
                        school_name,
                        voucher_no,
                        bill_no,
                        category,
                        amount,
                        vendor_name,
                        description
                    )
                )
                st.success("Voucher saved.")

    with tab2:
        df = run_query("SELECT * FROM vouchers ORDER BY voucher_date DESC")

        if not df.empty:
            st.dataframe(df, use_container_width=True)

            st.download_button(
                "⬇️ Download Vouchers Excel",
                data=to_excel_download(df, "Vouchers"),
                file_name="voucher_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("No voucher record available.")


# =====================================================
# REPORTS
# =====================================================

elif menu == "Reports":
    st.title("📁 Reports Center")

    report_type = st.selectbox(
        "Select Report",
        [
            "Schools",
            "Students",
            "Teachers",
            "Student Attendance",
            "Teacher Attendance",
            "NSB Records",
            "Fee Records",
            "Expenses",
            "Vouchers"
        ]
    )

    table_map = {
        "Schools": "schools",
        "Students": "students",
        "Teachers": "teachers",
        "Student Attendance": "student_attendance",
        "Teacher Attendance": "teacher_attendance",
        "NSB Records": "nsb_records",
        "Fee Records": "fee_records",
        "Expenses": "expense_records",
        "Vouchers": "vouchers"
    }

    table_name = table_map[report_type]

    df = run_query(f"SELECT * FROM {table_name}")

    if not df.empty:
        st.dataframe(df, use_container_width=True)

        st.download_button(
            "⬇️ Download Excel Report",
            data=to_excel_download(df, report_type),
            file_name=f"{table_name}_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        csv_data = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇️ Download CSV Report",
            data=csv_data,
            file_name=f"{table_name}_report.csv",
            mime="text/csv"
        )
    else:
        st.info("No data available for this report.")


# =====================================================
# DATA UPLOAD CENTER
# =====================================================

elif menu == "Data Upload Center":
    st.title("📤 Excel / CSV Upload Center")

    st.info(
        "You can upload old data from Excel or CSV files. "
        "Download the sample template first, fill your data, then upload it."
    )

    upload_type = st.selectbox(
        "Select Data Category",
        [
            "Schools",
            "Students",
            "Teachers",
            "Student Attendance",
            "Teacher Attendance",
            "NSB Records",
            "Fee Records",
            "Expenses",
            "Vouchers"
        ]
    )

    required_columns_map = {
        "Schools": [
            "school_name",
            "location",
            "head_teacher",
            "contact"
        ],
        "Students": [
            "admission_no",
            "student_name",
            "father_name",
            "gender",
            "class_name",
            "section",
            "school_name",
            "status"
        ],
        "Teachers": [
            "teacher_name",
            "designation",
            "school_name",
            "contact",
            "status"
        ],
        "Student Attendance": [
            "attendance_date",
            "school_name",
            "class_name",
            "section",
            "admission_no",
            "student_name",
            "status"
        ],
        "Teacher Attendance": [
            "attendance_date",
            "school_name",
            "teacher_name",
            "status"
        ],
        "NSB Records": [
            "record_date",
            "school_name",
            "financial_year",
            "opening_balance",
            "receipt_amount",
            "expenditure_amount",
            "description"
        ],
        "Fee Records": [
            "fee_date",
            "school_name",
            "admission_no",
            "student_name",
            "class_name",
            "fee_month",
            "total_fee",
            "paid_fee",
            "remaining_fee",
            "remarks"
        ],
        "Expenses": [
            "expense_date",
            "school_name",
            "category",
            "amount",
            "paid_to",
            "description"
        ],
        "Vouchers": [
            "voucher_date",
            "school_name",
            "voucher_no",
            "bill_no",
            "category",
            "amount",
            "vendor_name",
            "description"
        ]
    }

    table_map = {
        "Schools": "schools",
        "Students": "students",
        "Teachers": "teachers",
        "Student Attendance": "student_attendance",
        "Teacher Attendance": "teacher_attendance",
        "NSB Records": "nsb_records",
        "Fee Records": "fee_records",
        "Expenses": "expense_records",
        "Vouchers": "vouchers"
    }

    required_columns = required_columns_map[upload_type]
    table_name = table_map[upload_type]

    st.subheader("Required Columns")
    st.write(required_columns)

    show_template(required_columns)

    uploaded_file = st.file_uploader(
        "Upload Excel or CSV File",
        type=["xlsx", "xls", "csv"]
    )

    if uploaded_file is not None:
        df = read_uploaded_file(uploaded_file)

        if df is not None:
            st.subheader("Preview Uploaded Data")
            st.dataframe(df.head(20), use_container_width=True)

            if st.button("Upload Data to Database", use_container_width=True):
                insert_dataframe(df, table_name, required_columns)