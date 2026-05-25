import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(
    page_title="CGPA Calculator",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 CGPA Calculator")
st.write("Calculate semester-wise GPA, overall CGPA, percentage, and degree performance.")

# -----------------------------
# Helper Functions
# -----------------------------

def grade_from_gpa(gpa):
    if gpa >= 3.67:
        return "Excellent"
    elif gpa >= 3.00:
        return "Very Good"
    elif gpa >= 2.50:
        return "Good"
    elif gpa >= 2.00:
        return "Satisfactory"
    else:
        return "Needs Improvement"


def marks_to_grade_point(marks):
    """
    General grading scale.
    You can change this according to your university policy.
    """
    if marks >= 85:
        return 4.00
    elif marks >= 80:
        return 3.70
    elif marks >= 75:
        return 3.30
    elif marks >= 70:
        return 3.00
    elif marks >= 65:
        return 2.70
    elif marks >= 60:
        return 2.30
    elif marks >= 55:
        return 2.00
    elif marks >= 50:
        return 1.70
    else:
        return 0.00


def marks_to_letter_grade(marks):
    if marks >= 85:
        return "A"
    elif marks >= 80:
        return "A-"
    elif marks >= 75:
        return "B+"
    elif marks >= 70:
        return "B"
    elif marks >= 65:
        return "B-"
    elif marks >= 60:
        return "C+"
    elif marks >= 55:
        return "C"
    elif marks >= 50:
        return "D"
    else:
        return "F"


def cgpa_to_percentage(cgpa, method):
    if method == "CGPA × 25":
        return cgpa * 25
    elif method == "CGPA × 20 + 20":
        return (cgpa * 20) + 20
    elif method == "CGPA × 10":
        return cgpa * 10
    else:
        return cgpa * 25


def create_excel_report(course_df, semester_df, final_summary):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        course_df.to_excel(writer, index=False, sheet_name="Course Details")
        semester_df.to_excel(writer, index=False, sheet_name="Semester GPA")
        final_summary.to_excel(writer, index=False, sheet_name="Final Summary")

    output.seek(0)
    return output


# -----------------------------
# Sidebar Settings
# -----------------------------

st.sidebar.header("⚙️ Settings")

calculation_mode = st.sidebar.radio(
    "Select Calculation Method",
    ["Enter Marks", "Enter Grade Points Manually"]
)

percentage_method = st.sidebar.selectbox(
    "Percentage Formula",
    ["CGPA × 25", "CGPA × 20 + 20", "CGPA × 10"]
)

st.sidebar.info(
    "Note: Percentage formula varies by university. "
    "Select the formula according to your university policy."
)

num_semesters = st.sidebar.number_input(
    "Number of Semesters",
    min_value=1,
    max_value=12,
    value=8,
    step=1
)

st.divider()

all_courses = []
semester_results = []

# -----------------------------
# Input Area
# -----------------------------

for sem in range(1, num_semesters + 1):
    with st.expander(f"📘 Semester {sem}", expanded=(sem == 1)):
        num_courses = st.number_input(
            f"Number of Courses in Semester {sem}",
            min_value=1,
            max_value=15,
            value=5,
            step=1,
            key=f"num_courses_{sem}"
        )

        semester_quality_points = 0
        semester_credit_hours = 0

        for course in range(1, num_courses + 1):
            st.subheader(f"Course {course}")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                course_name = st.text_input(
                    "Course Name",
                    value=f"Course {course}",
                    key=f"course_name_{sem}_{course}"
                )

            with col2:
                credit_hours = st.number_input(
                    "Credit Hours",
                    min_value=1.0,
                    max_value=6.0,
                    value=3.0,
                    step=0.5,
                    key=f"credit_{sem}_{course}"
                )

            if calculation_mode == "Enter Marks":
                with col3:
                    marks = st.number_input(
                        "Marks",
                        min_value=0.0,
                        max_value=100.0,
                        value=75.0,
                        step=0.5,
                        key=f"marks_{sem}_{course}"
                    )

                grade_point = marks_to_grade_point(marks)
                letter_grade = marks_to_letter_grade(marks)

                with col4:
                    st.metric("Grade Point", grade_point)

            else:
                marks = None
                letter_grade = "Manual"

                with col3:
                    grade_point = st.number_input(
                        "Grade Point",
                        min_value=0.0,
                        max_value=4.0,
                        value=3.0,
                        step=0.01,
                        key=f"gp_{sem}_{course}"
                    )

                with col4:
                    st.metric("Quality Points", round(grade_point * credit_hours, 2))

            quality_points = grade_point * credit_hours

            semester_quality_points += quality_points
            semester_credit_hours += credit_hours

            all_courses.append({
                "Semester": sem,
                "Course Name": course_name,
                "Credit Hours": credit_hours,
                "Marks": marks if marks is not None else "Manual",
                "Letter Grade": letter_grade,
                "Grade Point": grade_point,
                "Quality Points": round(quality_points, 2)
            })

        semester_gpa = (
            semester_quality_points / semester_credit_hours
            if semester_credit_hours > 0
            else 0
        )

        semester_results.append({
            "Semester": sem,
            "Total Credit Hours": semester_credit_hours,
            "Total Quality Points": round(semester_quality_points, 2),
            "Semester GPA": round(semester_gpa, 2),
            "Performance": grade_from_gpa(semester_gpa)
        })

        st.success(f"Semester {sem} GPA: {semester_gpa:.2f}")

# -----------------------------
# Final Calculation
# -----------------------------

course_df = pd.DataFrame(all_courses)
semester_df = pd.DataFrame(semester_results)

total_credit_hours = course_df["Credit Hours"].sum()
total_quality_points = course_df["Quality Points"].sum()

overall_cgpa = (
    total_quality_points / total_credit_hours
    if total_credit_hours > 0
    else 0
)

percentage = cgpa_to_percentage(overall_cgpa, percentage_method)

if percentage > 100:
    percentage = 100

final_performance = grade_from_gpa(overall_cgpa)

st.divider()

st.header("📊 Final Degree Performance")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Credit Hours", round(total_credit_hours, 2))
col2.metric("Total Quality Points", round(total_quality_points, 2))
col3.metric("Overall CGPA", round(overall_cgpa, 2))
col4.metric("Percentage", f"{percentage:.2f}%")

st.success(f"Overall Performance: {final_performance}")

# -----------------------------
# Tables
# -----------------------------

st.subheader("📘 Semester-wise GPA Summary")
st.dataframe(semester_df, use_container_width=True)

st.subheader("📚 Complete Course Record")
st.dataframe(course_df, use_container_width=True)

# -----------------------------
# Final Summary Table
# -----------------------------

final_summary = pd.DataFrame([{
    "Total Semesters": num_semesters,
    "Total Credit Hours": round(total_credit_hours, 2),
    "Total Quality Points": round(total_quality_points, 2),
    "Overall CGPA": round(overall_cgpa, 2),
    "Percentage Formula": percentage_method,
    "Percentage": round(percentage, 2),
    "Final Performance": final_performance
}])

# -----------------------------
# Download Excel Report
# -----------------------------

excel_file = create_excel_report(course_df, semester_df, final_summary)

st.download_button(
    label="⬇️ Download Complete CGPA Report in Excel",
    data=excel_file,
    file_name="CGPA_Report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.divider()

st.info(
    "You can change the grading scale in the function named marks_to_grade_point() "
    "according to your university's official grading policy."
)