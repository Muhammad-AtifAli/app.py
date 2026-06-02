import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime

# -----------------------------
# PAGE SETTINGS
# -----------------------------
st.set_page_config(
    page_title="Personal Diary App",
    page_icon="📔",
    layout="wide"
)

# -----------------------------
# DATABASE CONNECTION
# -----------------------------
conn = sqlite3.connect("personal_diary.db", check_same_thread=False)
cursor = conn.cursor()

# -----------------------------
# CREATE TABLES
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS diary_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    title TEXT,
    entry TEXT,
    mood TEXT,
    entry_date TEXT,
    created_at TEXT
)
""")

conn.commit()

# -----------------------------
# PASSWORD SECURITY
# -----------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(password, hashed_password):
    return hash_password(password) == hashed_password

# -----------------------------
# USER FUNCTIONS
# -----------------------------
def register_user(username, password):
    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hash_password(password))
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(username, password):
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()

    if result:
        stored_password = result[0]
        if check_password(password, stored_password):
            return True
    return False

# -----------------------------
# DIARY FUNCTIONS
# -----------------------------
def add_entry(username, title, entry, mood, entry_date):
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO diary_entries 
    (username, title, entry, mood, entry_date, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (username, title, entry, mood, entry_date, created_at))
    conn.commit()

def get_entries(username):
    cursor.execute("""
    SELECT id, title, entry, mood, entry_date, created_at 
    FROM diary_entries 
    WHERE username = ?
    ORDER BY entry_date DESC, created_at DESC
    """, (username,))
    return cursor.fetchall()

def search_entries(username, keyword):
    cursor.execute("""
    SELECT id, title, entry, mood, entry_date, created_at 
    FROM diary_entries
    WHERE username = ? 
    AND (title LIKE ? OR entry LIKE ? OR mood LIKE ? OR entry_date LIKE ?)
    ORDER BY entry_date DESC
    """, (
        username,
        f"%{keyword}%",
        f"%{keyword}%",
        f"%{keyword}%",
        f"%{keyword}%"
    ))
    return cursor.fetchall()

def update_entry(entry_id, new_title, new_entry, new_mood, new_date):
    cursor.execute("""
    UPDATE diary_entries 
    SET title = ?, entry = ?, mood = ?, entry_date = ?
    WHERE id = ?
    """, (new_title, new_entry, new_mood, new_date, entry_id))
    conn.commit()

def delete_entry(entry_id):
    cursor.execute("DELETE FROM diary_entries WHERE id = ?", (entry_id,))
    conn.commit()

def entries_to_dataframe(entries):
    return pd.DataFrame(
        entries,
        columns=["ID", "Title", "Entry", "Mood", "Date", "Created At"]
    )

# -----------------------------
# SESSION STATE
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

# -----------------------------
# CUSTOM CSS
# -----------------------------
st.markdown("""
<style>
.main-title {
    text-align: center;
    color: #4B0082;
    font-size: 42px;
    font-weight: bold;
}
.subtitle {
    text-align: center;
    color: #555555;
    font-size: 18px;
}
.diary-card {
    background-color: #f8f4ff;
    padding: 18px;
    border-radius: 12px;
    border-left: 6px solid #6a0dad;
    margin-bottom: 15px;
}
.small-text {
    color: gray;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# LOGIN / REGISTER PAGE
# -----------------------------
def login_register_page():
    st.markdown('<div class="main-title">📔 Personal Diary App</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Write your thoughts, feelings, memories, and daily reflections safely.</div>', unsafe_allow_html=True)

    st.write("")
    st.write("")

    tab1, tab2 = st.tabs(["Login", "Create Account"])

    with tab1:
        st.subheader("Login to Your Diary")

        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            if username.strip() == "" or password.strip() == "":
                st.warning("Please enter both username and password.")
            elif login_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

    with tab2:
        st.subheader("Create New Account")

        new_username = st.text_input("Choose Username", key="register_username")
        new_password = st.text_input("Choose Password", type="password", key="register_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")

        if st.button("Register"):
            if new_username.strip() == "" or new_password.strip() == "":
                st.warning("Please fill all fields.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            elif len(new_password) < 4:
                st.warning("Password should be at least 4 characters long.")
            else:
                success = register_user(new_username, new_password)
                if success:
                    st.success("Account created successfully. Now login.")
                else:
                    st.error("Username already exists. Try another username.")

# -----------------------------
# MAIN DIARY PAGE
# -----------------------------
def diary_page():
    st.sidebar.title("📔 Diary Menu")
    st.sidebar.write(f"Logged in as: **{st.session_state.username}**")

    menu = st.sidebar.radio(
        "Choose Option",
        [
            "Write New Entry",
            "View My Diary",
            "Search Diary",
            "Edit/Delete Entry",
            "Mood Summary",
            "Export Diary"
        ]
    )

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    st.markdown('<div class="main-title">My Personal Diary</div>', unsafe_allow_html=True)

    username = st.session_state.username

    # -----------------------------
    # WRITE NEW ENTRY
    # -----------------------------
    if menu == "Write New Entry":
        st.subheader("✍️ Write New Diary Entry")

        title = st.text_input("Entry Title")
        entry_date = st.date_input("Entry Date", datetime.today())
        mood = st.selectbox(
            "How are you feeling today?",
            ["Happy 😊", "Sad 😢", "Excited 🤩", "Angry 😠", "Relaxed 😌", "Confused 🤔", "Grateful 🙏", "Tired 😴"]
        )
        entry = st.text_area("Write your diary entry here", height=250)

        if st.button("Save Entry"):
            if title.strip() == "" or entry.strip() == "":
                st.warning("Please write title and diary entry.")
            else:
                add_entry(username, title, entry, mood, str(entry_date))
                st.success("Diary entry saved successfully!")

    # -----------------------------
    # VIEW DIARY
    # -----------------------------
    elif menu == "View My Diary":
        st.subheader("📖 My Diary Entries")

        entries = get_entries(username)

        if len(entries) == 0:
            st.info("No diary entries found. Start writing your first entry.")
        else:
            for entry in entries:
                entry_id, title, text, mood, entry_date, created_at = entry

                st.markdown(f"""
                <div class="diary-card">
                    <h3>{title}</h3>
                    <p><b>Date:</b> {entry_date}</p>
                    <p><b>Mood:</b> {mood}</p>
                    <p>{text}</p>
                    <p class="small-text">Created at: {created_at}</p>
                </div>
                """, unsafe_allow_html=True)

    # -----------------------------
    # SEARCH DIARY
    # -----------------------------
    elif menu == "Search Diary":
        st.subheader("🔍 Search Diary Entries")

        keyword = st.text_input("Search by title, mood, date, or words inside entry")

        if keyword:
            results = search_entries(username, keyword)

            if len(results) == 0:
                st.warning("No matching diary entries found.")
            else:
                st.success(f"{len(results)} result(s) found.")

                for entry in results:
                    entry_id, title, text, mood, entry_date, created_at = entry

                    st.markdown(f"""
                    <div class="diary-card">
                        <h3>{title}</h3>
                        <p><b>Date:</b> {entry_date}</p>
                        <p><b>Mood:</b> {mood}</p>
                        <p>{text}</p>
                        <p class="small-text">Created at: {created_at}</p>
                    </div>
                    """, unsafe_allow_html=True)

    # -----------------------------
    # EDIT / DELETE ENTRY
    # -----------------------------
    elif menu == "Edit/Delete Entry":
        st.subheader("🛠️ Edit or Delete Diary Entry")

        entries = get_entries(username)

        if len(entries) == 0:
            st.info("No entries available to edit or delete.")
        else:
            entry_options = {
                f"{entry[1]} | {entry[4]} | ID: {entry[0]}": entry
                for entry in entries
            }

            selected_entry_label = st.selectbox(
                "Select an entry",
                list(entry_options.keys())
            )

            selected_entry = entry_options[selected_entry_label]

            entry_id, title, text, mood, entry_date, created_at = selected_entry

            new_title = st.text_input("Edit Title", value=title)
            new_date = st.date_input(
                "Edit Date",
                datetime.strptime(entry_date, "%Y-%m-%d")
            )

            mood_options = ["Happy 😊", "Sad 😢", "Excited 🤩", "Angry 😠", "Relaxed 😌", "Confused 🤔", "Grateful 🙏", "Tired 😴"]

            if mood in mood_options:
                mood_index = mood_options.index(mood)
            else:
                mood_index = 0

            new_mood = st.selectbox(
                "Edit Mood",
                mood_options,
                index=mood_index
            )

            new_text = st.text_area("Edit Entry", value=text, height=250)

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Update Entry"):
                    if new_title.strip() == "" or new_text.strip() == "":
                        st.warning("Title and entry cannot be empty.")
                    else:
                        update_entry(entry_id, new_title, new_text, new_mood, str(new_date))
                        st.success("Entry updated successfully!")
                        st.rerun()

            with col2:
                if st.button("Delete Entry"):
                    delete_entry(entry_id)
                    st.success("Entry deleted successfully!")
                    st.rerun()

    # -----------------------------
    # MOOD SUMMARY
    # -----------------------------
    elif menu == "Mood Summary":
        st.subheader("📊 Mood Summary")

        entries = get_entries(username)

        if len(entries) == 0:
            st.info("No entries available for mood summary.")
        else:
            df = entries_to_dataframe(entries)

            mood_count = df["Mood"].value_counts().reset_index()
            mood_count.columns = ["Mood", "Total Entries"]

            st.dataframe(mood_count, use_container_width=True)

            st.bar_chart(mood_count.set_index("Mood"))

    # -----------------------------
    # EXPORT DIARY
    # -----------------------------
    elif menu == "Export Diary":
        st.subheader("⬇️ Export Diary")

        entries = get_entries(username)

        if len(entries) == 0:
            st.info("No entries available to export.")
        else:
            df = entries_to_dataframe(entries)

            st.dataframe(df, use_container_width=True)

            csv = df.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="Download Diary as CSV",
                data=csv,
                file_name=f"{username}_personal_diary.csv",
                mime="text/csv"
            )

# -----------------------------
# APP START
# -----------------------------
if st.session_state.logged_in:
    diary_page()
else:
    login_register_page()