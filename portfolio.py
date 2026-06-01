import streamlit as st
import pandas as pd

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Muhammad Atif | Streamlit Apps Portfolio",
    page_icon="💼",
    layout="wide"
)

# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>
.main {
    background-color: #f8fafc;
}

.big-title {
    font-size: 44px;
    font-weight: 800;
    color: #0f172a;
    text-align: center;
}

.subtitle {
    font-size: 20px;
    color: #475569;
    text-align: center;
    margin-bottom: 30px;
}

.section-title {
    font-size: 30px;
    font-weight: 700;
    color: #1e293b;
    margin-top: 35px;
    margin-bottom: 15px;
}

.card {
    background-color: white;
    padding: 22px;
    border-radius: 18px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.08);
    margin-bottom: 20px;
    border: 1px solid #e2e8f0;
}

.card-title {
    font-size: 22px;
    font-weight: 700;
    color: #0f172a;
}

.card-text {
    font-size: 16px;
    color: #475569;
}

.badge {
    display: inline-block;
    background-color: #e0f2fe;
    color: #0369a1;
    padding: 5px 10px;
    border-radius: 12px;
    font-size: 13px;
    margin-top: 8px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)


# ---------------- PROJECT DATA ----------------
projects = [
    {
        "title": "Invoice & Receipt App",
        "category": "Business Apps",
        "description": "Create invoices, receipts, customer records, printable bills, and business records.",
        "features": "Invoice generation, receipt printing, customer record, total calculation",
        "demo": "https://your-invoice-app.streamlit.app",
        "code": "https://github.com/yourusername/invoice-app"
    },
    {
        "title": "School Attendance System",
        "category": "School Apps",
        "description": "Manage student attendance, teacher attendance, reports, and school dashboard.",
        "features": "Attendance entry, monthly reports, absent students, Excel download",
        "demo": "https://your-attendance-app.streamlit.app",
        "code": "https://github.com/yourusername/attendance-app"
    },
    {
        "title": "Karyana Stock Manager",
        "category": "Business Apps",
        "description": "Manage stock, sales, purchases, barcode records, and low-stock alerts.",
        "features": "Stock entry, sales record, purchase record, low stock warning",
        "demo": "https://your-karyana-app.streamlit.app",
        "code": "https://github.com/yourusername/karyana-app"
    },
    {
        "title": "Corpus Text Analysis App",
        "category": "Research Apps",
        "description": "Analyze text data for word frequency, keyword search, concordance, and n-grams.",
        "features": "Upload TXT files, frequency list, KWIC, n-gram analysis",
        "demo": "https://your-corpus-app.streamlit.app",
        "code": "https://github.com/yourusername/corpus-app"
    },
    {
        "title": "PDF Text Extractor App",
        "category": "Utility Apps",
        "description": "Extract text from searchable and scanned PDFs with output options.",
        "features": "PDF upload, OCR support, TXT output, Word output",
        "demo": "https://your-pdf-app.streamlit.app",
        "code": "https://github.com/yourusername/pdf-extractor"
    },
    {
        "title": "Kids Urdu Learning App",
        "category": "Kids Learning Apps",
        "description": "An Urdu learning app for children with activities and problem-solving exercises.",
        "features": "Urdu activities, quizzes, learning games, child-friendly interface",
        "demo": "https://your-kids-app.streamlit.app",
        "code": "https://github.com/yourusername/kids-learning-app"
    },
    {
        "title": "CGPA Calculator",
        "category": "Student Apps",
        "description": "Calculate semester-wise GPA, total CGPA, and percentage.",
        "features": "Semester GPA, total CGPA, percentage calculation, result summary",
        "demo": "https://your-cgpa-app.streamlit.app",
        "code": "https://github.com/yourusername/cgpa-calculator"
    },
    {
        "title": "BMI Calculator",
        "category": "Health Apps",
        "description": "Calculate BMI using weight in kg and height in feet and inches.",
        "features": "BMI calculation, health category, user-friendly interface",
        "demo": "https://your-bmi-app.streamlit.app",
        "code": "https://github.com/yourusername/bmi-calculator"
    }
]


# ---------------- SIDEBAR ----------------
st.sidebar.title("💼 Portfolio Menu")

page = st.sidebar.radio(
    "Go to",
    ["Home", "Projects", "Services", "About Me", "Contact"]
)

st.sidebar.markdown("---")
st.sidebar.info("Portfolio of Python and Streamlit apps by Muhammad Atif.")


# ---------------- HOME PAGE ----------------
if page == "Home":
    st.markdown('<div class="big-title">Muhammad Atif</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Python & Streamlit App Developer | School, Business, Research and Utility Apps</div>',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Projects", "8+")
    with col2:
        st.metric("Categories", "6")
    with col3:
        st.metric("Technology", "Python + Streamlit")

    st.markdown('<div class="section-title">Welcome to My Portfolio</div>', unsafe_allow_html=True)

    st.write("""
    I create useful Python and Streamlit applications for schools, shops, offices, researchers,
    students, and small businesses. This portfolio contains my completed and demo projects.
    """)

    st.success("You can use this portfolio link to show your work to clients and customers.")

    st.markdown('<div class="section-title">My Main Skills</div>', unsafe_allow_html=True)

    skill_col1, skill_col2, skill_col3, skill_col4 = st.columns(4)

    with skill_col1:
        st.info("Python")
    with skill_col2:
        st.info("Streamlit")
    with skill_col3:
        st.info("Excel Automation")
    with skill_col4:
        st.info("Data Apps")


# ---------------- PROJECTS PAGE ----------------
elif page == "Projects":
    st.markdown('<div class="big-title">My Projects</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">A collection of my Python and Streamlit applications</div>',
        unsafe_allow_html=True
    )

    categories = ["All"] + sorted(list(set(project["category"] for project in projects)))

    selected_category = st.selectbox("Filter projects by category", categories)

    search_text = st.text_input("Search project by name or keyword")

    filtered_projects = projects

    if selected_category != "All":
        filtered_projects = [
            project for project in filtered_projects
            if project["category"] == selected_category
        ]

    if search_text:
        filtered_projects = [
            project for project in filtered_projects
            if search_text.lower() in project["title"].lower()
            or search_text.lower() in project["description"].lower()
            or search_text.lower() in project["features"].lower()
        ]

    st.write(f"Showing **{len(filtered_projects)}** project(s).")

    for project in filtered_projects:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)

            st.markdown(
                f'<div class="card-title">{project["title"]}</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                f'<div class="badge">{project["category"]}</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                f'<div class="card-text">{project["description"]}</div>',
                unsafe_allow_html=True
            )

            st.write("**Main Features:**", project["features"])

            col1, col2 = st.columns(2)

            with col1:
                st.link_button("Open Demo", project["demo"])

            with col2:
                st.link_button("View Code", project["code"])

            st.markdown('</div>', unsafe_allow_html=True)


# ---------------- SERVICES PAGE ----------------
elif page == "Services":
    st.markdown('<div class="big-title">My Services</div>', unsafe_allow_html=True)

    st.write("""
    I can create custom web apps using Python and Streamlit for different fields.
    """)

    service_col1, service_col2 = st.columns(2)

    with service_col1:
        st.markdown("""
        ### 🏫 School Apps
        - Attendance system
        - Fee management system
        - Result card generator
        - LMS dashboard
        - Student record system

        ### 🛒 Business Apps
        - Invoice app
        - Stock management system
        - Sales and purchase dashboard
        - Customer record system
        """)

    with service_col2:
        st.markdown("""
        ### 📚 Research Apps
        - Corpus text analysis
        - Word frequency app
        - PDF text extractor
        - Excel data cleaning app

        ### 👨‍👩‍👧 Kids Learning Apps
        - Urdu learning app
        - Typing tutor
        - Quiz app
        - Problem-solving activities
        """)

    st.success("Clients can contact me for custom apps according to their needs.")


# ---------------- ABOUT PAGE ----------------
elif page == "About Me":
    st.markdown('<div class="big-title">About Me</div>', unsafe_allow_html=True)

    st.write("""
    My name is **Muhammad Atif**. I am learning and developing Python and Streamlit apps.
    My aim is to create practical applications that solve real problems in schools,
    businesses, research, offices, and daily life.
    """)

    st.markdown("### My Development Focus")

    st.write("""
    - Easy-to-use apps
    - Beautiful user interface
    - Useful dashboards
    - Excel and PDF automation
    - School and business management systems
    - Research and corpus analysis tools
    """)

    st.markdown("### Technologies I Use")

    tech_data = {
        "Technology": ["Python", "Streamlit", "Pandas", "Excel", "PDF Tools", "Data Analysis"],
        "Use": [
            "Main programming language",
            "Web app frontend",
            "Data handling",
            "Reports and records",
            "Text extraction",
            "Dashboards and summaries"
        ]
    }

    df = pd.DataFrame(tech_data)
    st.table(df)


# ---------------- CONTACT PAGE ----------------
elif page == "Contact":
    st.markdown('<div class="big-title">Contact Me</div>', unsafe_allow_html=True)

    st.write("""
    You can contact me for custom Python and Streamlit apps.
    """)

    st.markdown("""
    ### Contact Details

    **Name:** Muhammad Atif  
    **Email:** your-email@example.com  
    **WhatsApp:** +92-300-0000000  
    **GitHub:** https://github.com/yourusername  
    **Fiverr:** https://fiverr.com/yourusername  
    """)

    st.markdown("### Send Project Request")

    with st.form("contact_form"):
        name = st.text_input("Your Name")
        email = st.text_input("Your Email or WhatsApp")
        project_type = st.selectbox(
            "Project Type",
            [
                "School App",
                "Business App",
                "Research App",
                "Kids Learning App",
                "Utility App",
                "Other"
            ]
        )
        message = st.text_area("Write your project details")

        submitted = st.form_submit_button("Submit Request")

        if submitted:
            st.success("Your request has been recorded. Please connect this form with email or database later.")
            st.write("Name:", name)
            st.write("Contact:", email)
            st.write("Project Type:", project_type)
            st.write("Message:", message)


# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:gray;'>© 2026 Muhammad Atif | Python & Streamlit Apps Portfolio</p>",
    unsafe_allow_html=True
)