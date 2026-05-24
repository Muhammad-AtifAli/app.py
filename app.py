import streamlit as st
import pdfplumber
import pandas as pd
from io import BytesIO


st.set_page_config(
    page_title="PDF to Excel Converter",
    page_icon="📄",
    layout="centered"
)

st.title("PDF to Excel Converter")
st.write("Upload a PDF file. This app will extract all tables and combine them into one Excel sheet.")


def clean_table(table):
    cleaned_rows = []

    for row in table:
        if row is None:
            continue

        cleaned_row = []

        for cell in row:
            if cell is None:
                cleaned_row.append("")
            else:
                cleaned_row.append(str(cell).strip())

        if any(cell != "" for cell in cleaned_row):
            cleaned_rows.append(cleaned_row)

    return cleaned_rows


def convert_pdf_to_excel(uploaded_file):
    all_rows = []
    tables_found = 0

    with pdfplumber.open(uploaded_file) as pdf:

        for page_number, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()

            for table_number, table in enumerate(tables, start=1):
                cleaned_table = clean_table(table)

                if len(cleaned_table) == 0:
                    continue

                # Add page/table information before each table
                all_rows.append([f"Page {page_number} - Table {table_number}"])
                all_rows.extend(cleaned_table)
                all_rows.append([])

                tables_found += 1

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        if tables_found > 0:
            df = pd.DataFrame(all_rows)
            df.to_excel(
                writer,
                sheet_name="All_Data",
                index=False,
                header=False
            )
        else:
            df = pd.DataFrame({
                "Message": [
                    "No tables were found in this PDF.",
                    "This may be a scanned PDF or the table structure may not be clear."
                ]
            })
            df.to_excel(writer, sheet_name="All_Data", index=False)

    output.seek(0)
    return output, tables_found


uploaded_pdf = st.file_uploader("Upload your PDF file", type=["pdf"])

if uploaded_pdf is not None:
    st.success("PDF uploaded successfully!")

    if st.button("Convert PDF to Excel"):
        with st.spinner("Converting PDF to Excel..."):
            excel_file, total_tables = convert_pdf_to_excel(uploaded_pdf)

        if total_tables > 0:
            st.success(f"Conversion completed! {total_tables} table(s) combined into one sheet.")
        else:
            st.warning("No tables were found in this PDF.")

        st.download_button(
            label="Download Excel File",
            data=excel_file,
            file_name="converted_pdf_one_sheet.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )