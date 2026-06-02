import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import date, datetime

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Teacher Diary Management System",
    page_icon="📘",
    layout="wide"
)

# -----------------------------
# DATABASE CONNECTION
# -----------------------------
DB_NAME = "teacher_diary.db"


def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


conn = get_connection()
cursor = conn.cursor()


# -----------------------------
# PASSWORD HASHING
# -----------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, hashed_password):
    return hash_password(password) == hashed_password


# -----------------------------
# DATABASE TABLES
# -----------------------------
def create_tables():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        school_name TEXT,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS diaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id INTEGER NOT NULL,
        teacher_name TEXT NOT NULL,
        school_name TEXT,
        diary_date TEXT NOT NULL,
        subject TEXT NOT NULL,
        class_name TEXT NOT NULL,
        topic TEXT NOT NULL,
        page_no TEXT,
        slos TEXT,
        lesson_summary TEXT,
        homework TEXT,
        remarks TEXT,
        created_at TEXT,
        FOREIGN KEY (teacher_id) REFERENCES users(id)
    )
    """)

    conn.commit()


def create_default_aeo():
    cursor.execute("SELECT * FROM users WHERE username = ?", ("aeo",))
    user = cursor.fetchone()

    if user is None:
        cursor.execute("""
        INSERT INTO users 
        (full_name, username, password, role, school_name, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "Area Education Officer",
            "aeo",
            hash_password("aeo123"),
            "AEO",
            "All Schools",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()


create_tables()
create_default_aeo()


# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def login_user(username, password):
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if user:
        stored_password = user[3]
        if verify_password(password, stored_password):
            return user

    return None


def add_user(full_name, username, password, role, school_name):
    try:
        cursor.execute("""
        INSERT INTO users 
        (full_name, username, password, role, school_name, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            full_name,
            username,
            hash_password(password),
            role,
            school_name,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        return True, "User added successfully."
    except sqlite3.IntegrityError:
        return False, "Username already exists. Please choose another username."


def update_user(user_id, full_name, username, role, school_name):
    try:
        cursor.execute("""
        UPDATE users
        SET full_name = ?, username = ?, role = ?, school_name = ?
        WHERE id = ?
        """, (full_name, username, role, school_name, user_id))
        conn.commit()
        return True, "User updated successfully."
    except sqlite3.IntegrityError:
        return False, "Username already exists. Please choose another username."


def delete_user(user_id):
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()


def change_own_account(user_id, new_full_name, new_username, new_password=None):
    try:
        if new_password:
            cursor.execute("""
            UPDATE users
            SET full_name = ?, username = ?, password = ?
            WHERE id = ?
            """, (
                new_full_name,
                new_username,
                hash_password(new_password),
                user_id
            ))
        else:
            cursor.execute("""
            UPDATE users
            SET full_name = ?, username = ?
            WHERE id = ?
            """, (
                new_full_name,
                new_username,
                user_id
            ))

        conn.commit()
        return True, "Account updated successfully. Please login again."
    except sqlite3.IntegrityError:
        return False, "Username already exists. Please choose another username."


def get_users():
    return pd.read_sql_query("""
    SELECT id, full_name, username, role, school_name, created_at
    FROM users
    ORDER BY role, full_name
    """, conn)


def get_school_users(school_name):
    return pd.read_sql_query("""
    SELECT id, full_name, username, role, school_name, created_at
    FROM users
    WHERE school_name = ?
    ORDER BY role, full_name
    """, conn, params=(school_name,))


def add_diary(
    teacher_id,
    teacher_name,
    school_name,
    diary_date,
    subject,
    class_name,
    topic,
    page_no,
    slos,
    lesson_summary,
    homework,
    remarks
):
    cursor.execute("""
    INSERT INTO diaries
    (teacher_id, teacher_name, school_name, diary_date, subject, class_name,
     topic, page_no, slos, lesson_summary, homework, remarks, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        teacher_id,
        teacher_name,
        school_name,
        diary_date,
        subject,
        class_name,
        topic,
        page_no,
        slos,
        lesson_summary,
        homework,
        remarks,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()


def update_diary(
    diary_id,
    diary_date,
    subject,
    class_name,
    topic,
    page_no,
    slos,
    lesson_summary,
    homework,
    remarks
):
    cursor.execute("""
    UPDATE diaries
    SET diary_date = ?, subject = ?, class_name = ?, topic = ?, page_no = ?,
        slos = ?, lesson_summary = ?, homework = ?, remarks = ?
    WHERE id = ?
    """, (
        diary_date,
        subject,
        class_name,
        topic,
        page_no,
        slos,
        lesson_summary,
        homework,
        remarks,
        diary_id
    ))
    conn.commit()


def delete_diary(diary_id):
    cursor.execute("DELETE FROM diaries WHERE id = ?", (diary_id,))
    conn.commit()


def get_teacher_diaries(teacher_id):
    return pd.read_sql_query("""
    SELECT id, diary_date, subject, class_name, topic, page_no, slos,
           lesson_summary, homework, remarks, created_at
    FROM diaries
    WHERE teacher_id = ?
    ORDER BY diary_date DESC
    """, conn, params=(teacher_id,))


def get_school_diaries(school_name):
    return pd.read_sql_query("""
    SELECT id, teacher_name, school_name, diary_date, subject, class_name,
           topic, page_no, slos, lesson_summary, homework, remarks, created_at
    FROM diaries
    WHERE school_name = ?
    ORDER BY diary_date DESC
    """, conn, params=(school_name,))


def get_all_diaries():
    return pd.read_sql_query("""
    SELECT id, teacher_name, school_name, diary_date, subject, class_name,
           topic, page_no, slos, lesson_summary, homework, remarks, created_at
    FROM diaries
    ORDER BY diary_date DESC
    """, conn)


# -----------------------------
# SESSION STATE
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None


# -----------------------------
# CUSTOM STYLE
# -----------------------------
st.markdown("""
<style>
.main-title {
    background: linear-gradient(90deg, #1e3c72, #2a5298);
    color: white;
    padding: 22px;
    border-radius: 12px;
    text-align: center;
    margin-bottom: 25px;
}
.card {
    background-color: #f8f9fa;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #ddd;
    margin-bottom: 12px;
}
.success-box {
    background-color: #e8f5e9;
    padding: 12px;
    border-radius: 8px;
    border-left: 5px solid #2e7d32;
}
.warning-box {
    background-color: #fff8e1;
    padding: 12px;
    border-radius: 8px;
    border-left: 5px solid #ff9800;
}
</style>
""", unsafe_allow_html=True)


# -----------------------------
# LOGIN PAGE
# -----------------------------
def login_page():
    st.markdown(
        "<h1 class='main-title'>📘 Teacher Diary Management System</h1>",
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 1.3, 1])

    with col2:
        st.subheader("🔐 Login")

        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login")

        if login_btn:
            user = login_user(username, password)

            if user:
                st.session_state.logged_in = True
                st.session_state.user = {
                    "id": user[0],
                    "full_name": user[1],
                    "username": user[2],
                    "role": user[4],
                    "school_name": user[5]
                }
                st.success("Login successful.")
                st.rerun()
            else:
                st.error("Invalid username or password.")

        st.info("Default AEO Login: username = aeo, password = aeo123")


# -----------------------------
# ACCOUNT SETTINGS
# -----------------------------
def account_settings():
    st.subheader("⚙️ My Account Settings")

    user = st.session_state.user

    with st.form("account_form"):
        new_full_name = st.text_input("Full Name", value=user["full_name"])
        new_username = st.text_input("Username", value=user["username"])
        new_password = st.text_input(
            "New Password",
            type="password",
            placeholder="Leave blank if you do not want to change password"
        )

        update_btn = st.form_submit_button("Update My Account")

    if update_btn:
        success, message = change_own_account(
            user["id"],
            new_full_name,
            new_username,
            new_password if new_password.strip() else None
        )

        if success:
            st.success(message)
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()
        else:
            st.error(message)


# -----------------------------
# USER MANAGEMENT
# -----------------------------
def user_management():
    st.subheader("👥 User Management")

    current_user = st.session_state.user

    if current_user["role"] == "Teacher":
        st.warning("Teachers are not allowed to manage users.")
        return

    st.markdown("### ➕ Add New User")

    with st.form("add_user_form"):
        full_name = st.text_input("Full Name")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if current_user["role"] == "AEO":
            role = st.selectbox("Role", ["Teacher", "Principal", "AEO"])
            school_name = st.text_input("School Name")
        else:
            role = st.selectbox("Role", ["Teacher"])
            school_name = current_user["school_name"]
            st.text_input("School Name", value=school_name, disabled=True)

        add_btn = st.form_submit_button("Add User")

    if add_btn:
        if full_name and username and password and role and school_name:
            success, message = add_user(full_name, username, password, role, school_name)
            if success:
                st.success(message)
            else:
                st.error(message)
        else:
            st.error("Please fill all required fields.")

    st.divider()

    st.markdown("### 📋 Existing Users")

    if current_user["role"] == "AEO":
        users_df = get_users()
    else:
        users_df = get_school_users(current_user["school_name"])

    st.dataframe(users_df, use_container_width=True)

    st.divider()

    st.markdown("### ✏️ Edit or Delete User")

    if not users_df.empty:
        user_options = {
            f"{row['id']} - {row['full_name']} ({row['role']})": row["id"]
            for _, row in users_df.iterrows()
        }

        selected_user_label = st.selectbox("Select User", list(user_options.keys()))
        selected_user_id = user_options[selected_user_label]

        cursor.execute("""
        SELECT id, full_name, username, role, school_name 
        FROM users 
        WHERE id = ?
        """, (selected_user_id,))
        selected_user = cursor.fetchone()

        if selected_user:
            with st.form("edit_user_form"):
                edit_full_name = st.text_input("Full Name", value=selected_user[1])
                edit_username = st.text_input("Username", value=selected_user[2])

                if current_user["role"] == "AEO":
                    edit_role = st.selectbox(
                        "Role",
                        ["Teacher", "Principal", "AEO"],
                        index=["Teacher", "Principal", "AEO"].index(selected_user[3])
                    )
                    edit_school_name = st.text_input("School Name", value=selected_user[4])
                else:
                    edit_role = selected_user[3]
                    edit_school_name = selected_user[4]
                    st.text_input("Role", value=edit_role, disabled=True)
                    st.text_input("School Name", value=edit_school_name, disabled=True)

                update_user_btn = st.form_submit_button("Update User")

            if update_user_btn:
                success, message = update_user(
                    selected_user_id,
                    edit_full_name,
                    edit_username,
                    edit_role,
                    edit_school_name
                )

                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

            st.warning("Deleting a user will remove the user login. Diary records will remain saved.")

            if selected_user_id == current_user["id"]:
                st.info("You cannot delete your own account from this panel.")
            else:
                if st.button("Delete Selected User"):
                    delete_user(selected_user_id)
                    st.success("User deleted successfully.")
                    st.rerun()


# -----------------------------
# TEACHER DIARY PAGE
# -----------------------------
def teacher_diary_page():
    st.subheader("📝 Daily Teacher Diary")

    user = st.session_state.user

    if user["role"] != "Teacher":
        st.warning("Only teachers can add personal diary entries from this page.")
        return

    st.markdown("### ➕ Add Daily Lesson Plan")

    with st.form("diary_form"):
        diary_date = st.date_input("Date", value=date.today())
        subject = st.text_input("Subject")
        class_name = st.text_input("Class")
        topic = st.text_input("Topic of Lesson")
        page_no = st.text_input("Page No.")
        slos = st.text_area("SLOs / Student Learning Outcomes")
        lesson_summary = st.text_area("Daily Lesson Plan Summary")
        homework = st.text_area("Homework")
        remarks = st.text_area("Remarks")

        save_diary_btn = st.form_submit_button("Save Diary")

    if save_diary_btn:
        if subject and class_name and topic:
            add_diary(
                user["id"],
                user["full_name"],
                user["school_name"],
                str(diary_date),
                subject,
                class_name,
                topic,
                page_no,
                slos,
                lesson_summary,
                homework,
                remarks
            )
            st.success("Diary entry saved successfully.")
        else:
            st.error("Subject, class, and topic are required.")

    st.divider()

    st.markdown("### 📚 My Diary Records")

    diary_df = get_teacher_diaries(user["id"])
    st.dataframe(diary_df, use_container_width=True)

    st.divider()

    st.markdown("### ✏️ Edit or Delete My Diary")

    if not diary_df.empty:
        diary_options = {
            f"{row['id']} - {row['diary_date']} - {row['subject']} - {row['topic']}": row["id"]
            for _, row in diary_df.iterrows()
        }

        selected_diary_label = st.selectbox("Select Diary Entry", list(diary_options.keys()))
        selected_diary_id = diary_options[selected_diary_label]

        cursor.execute("""
        SELECT id, diary_date, subject, class_name, topic, page_no, slos,
               lesson_summary, homework, remarks
        FROM diaries
        WHERE id = ? AND teacher_id = ?
        """, (selected_diary_id, user["id"]))

        diary = cursor.fetchone()

        if diary:
            with st.form("edit_diary_form"):
                edit_date = st.date_input(
                    "Date",
                    value=datetime.strptime(diary[1], "%Y-%m-%d").date()
                )
                edit_subject = st.text_input("Subject", value=diary[2])
                edit_class = st.text_input("Class", value=diary[3])
                edit_topic = st.text_input("Topic", value=diary[4])
                edit_page_no = st.text_input("Page No.", value=diary[5] if diary[5] else "")
                edit_slos = st.text_area("SLOs", value=diary[6] if diary[6] else "")
                edit_summary = st.text_area(
                    "Lesson Summary",
                    value=diary[7] if diary[7] else ""
                )
                edit_homework = st.text_area(
                    "Homework",
                    value=diary[8] if diary[8] else ""
                )
                edit_remarks = st.text_area(
                    "Remarks",
                    value=diary[9] if diary[9] else ""
                )

                update_diary_btn = st.form_submit_button("Update Diary")

            if update_diary_btn:
                update_diary(
                    selected_diary_id,
                    str(edit_date),
                    edit_subject,
                    edit_class,
                    edit_topic,
                    edit_page_no,
                    edit_slos,
                    edit_summary,
                    edit_homework,
                    edit_remarks
                )
                st.success("Diary updated successfully.")
                st.rerun()

            if st.button("Delete Selected Diary"):
                delete_diary(selected_diary_id)
                st.success("Diary deleted successfully.")
                st.rerun()
    else:
        st.info("No diary records found.")


# -----------------------------
# VIEW DIARIES
# -----------------------------
def view_diaries_page():
    st.subheader("📖 View Teacher Diaries")

    user = st.session_state.user

    if user["role"] == "Teacher":
        diaries_df = get_teacher_diaries(user["id"])
    elif user["role"] == "Principal":
        diaries_df = get_school_diaries(user["school_name"])
    else:
        diaries_df = get_all_diaries()

    if diaries_df.empty:
        st.info("No diary records found.")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        subject_filter = st.text_input("Filter by Subject")

    with col2:
        class_filter = st.text_input("Filter by Class")

    with col3:
        teacher_filter = st.text_input("Filter by Teacher Name")

    filtered_df = diaries_df.copy()

    if subject_filter:
        filtered_df = filtered_df[
            filtered_df["subject"].str.contains(subject_filter, case=False, na=False)
        ]

    if class_filter:
        filtered_df = filtered_df[
            filtered_df["class_name"].str.contains(class_filter, case=False, na=False)
        ]

    if teacher_filter and "teacher_name" in filtered_df.columns:
        filtered_df = filtered_df[
            filtered_df["teacher_name"].str.contains(teacher_filter, case=False, na=False)
        ]

    st.dataframe(filtered_df, use_container_width=True)

    csv = filtered_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="⬇️ Download Diary Records as CSV",
        data=csv,
        file_name="teacher_diary_records.csv",
        mime="text/csv"
    )


# -----------------------------
# DASHBOARD
# -----------------------------
def dashboard():
    user = st.session_state.user

    st.markdown(
        f"<h1 class='main-title'>📘 Welcome, {user['full_name']} ({user['role']})</h1>",
        unsafe_allow_html=True
    )

    if user["role"] == "Teacher":
        diary_df = get_teacher_diaries(user["id"])
        total_diaries = len(diary_df)

        col1, col2, col3 = st.columns(3)
        col1.metric("My Diary Entries", total_diaries)
        col2.metric("School", user["school_name"])
        col3.metric("Role", user["role"])

    elif user["role"] == "Principal":
        users_df = get_school_users(user["school_name"])
        diaries_df = get_school_diaries(user["school_name"])

        total_teachers = len(users_df[users_df["role"] == "Teacher"])
        total_diaries = len(diaries_df)

        col1, col2, col3 = st.columns(3)
        col1.metric("Teachers in School", total_teachers)
        col2.metric("Diary Entries", total_diaries)
        col3.metric("School", user["school_name"])

    else:
        users_df = get_users()
        diaries_df = get_all_diaries()

        total_users = len(users_df)
        total_schools = users_df["school_name"].nunique()
        total_diaries = len(diaries_df)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Users", total_users)
        col2.metric("Total Schools", total_schools)
        col3.metric("Total Diary Entries", total_diaries)

    st.divider()

    st.markdown("""
    <div class='success-box'>
    <b>System Purpose:</b> This app helps teachers prepare daily lesson diary records.
    Principals can monitor their school teachers, and AEO can monitor all schools.
    </div>
    """, unsafe_allow_html=True)


# -----------------------------
# MAIN APP
# -----------------------------
def main_app():
    user = st.session_state.user

    with st.sidebar:
        st.title("📘 Teacher Diary")
        st.write(f"**Name:** {user['full_name']}")
        st.write(f"**Role:** {user['role']}")
        st.write(f"**School:** {user['school_name']}")

        st.divider()

        menu = ["Dashboard", "My Account", "View Diaries"]

        if user["role"] == "Teacher":
            menu.insert(1, "Daily Diary")

        if user["role"] in ["Principal", "AEO"]:
            menu.insert(1, "User Management")

        choice = st.radio("Navigation", menu)

        st.divider()

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()

    if choice == "Dashboard":
        dashboard()

    elif choice == "Daily Diary":
        teacher_diary_page()

    elif choice == "User Management":
        user_management()

    elif choice == "View Diaries":
        view_diaries_page()

    elif choice == "My Account":
        account_settings()


# -----------------------------
# APP START
# -----------------------------
if st.session_state.logged_in:
    main_app()
else:
    login_page()