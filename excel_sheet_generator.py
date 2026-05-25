import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(
    page_title="Excel Workbook Sheet Generator",
    page_icon="📘",
    layout="centered"
)

st.title("📘 Excel Workbook Sheet Generator")
st.write("Create an Excel workbook with any number of sheets.")

# Input: Workbook file name
file_name = st.text_input(
    "Enter Excel file name:",
    value="generated_workbook"
)

# Input: Number of sheets
num_sheets = st.number_input(
    "How many sheets do you want to create?",
    min_value=1,
    max_value=100,
    value=3,
    step=1
)

st.subheader("Sheet Settings")

sheet_data = {}

for i in range(1, num_sheets + 1):
    st.markdown(f"### Sheet {i}")

    sheet_name = st.text_input(
        f"Enter name for Sheet {i}:",
        value=f"Sheet{i}",
        key=f"sheet_name_{i}"
    )

    rows = st.number_input(
        f"Number of rows for {sheet_name}:",
        min_value=1,
        max_value=1000,
        value=10,
        step=1,
        key=f"rows_{i}"
    )

    columns = st.number_input(
        f"Number of columns for {sheet_name}:",
        min_value=1,
        max_value=50,
        value=5,
        step=1,
        key=f"columns_{i}"
    )

    # Create empty data
    data = {}

    for col in range(1, columns + 1):
        column_name = f"Column {col}"
        data[column_name] = [""] * rows

    df = pd.DataFrame(data)

    sheet_data[sheet_name] = df

# Function to create Excel file
def create_excel_file(sheet_data):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in sheet_data.items():
            # Excel sheet name limit is 31 characters
            safe_sheet_name = sheet_name[:31]

            # Remove invalid characters from sheet name
            invalid_chars = ['\\', '/', '*', '[', ']', ':', '?']
            for char in invalid_chars:
                safe_sheet_name = safe_sheet_name.replace(char, "")

            if safe_sheet_name.strip() == "":
                safe_sheet_name = "Sheet"

            df.to_excel(writer, index=False, sheet_name=safe_sheet_name)

    output.seek(0)
    return output

# Generate button
if st.button("Generate Excel Workbook"):
    if file_name.strip() == "":
        st.error("Please enter a valid file name.")
    else:
        excel_file = create_excel_file(sheet_data)

        st.success("Excel workbook generated successfully!")

        st.download_button(
            label="📥 Download Excel Workbook",
            data=excel_file,
            file_name=f"{file_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )