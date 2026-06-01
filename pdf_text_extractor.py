import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from docx import Document
from io import BytesIO
import os


# ---------------------------------------
# Tesseract OCR Path for Windows
# ---------------------------------------
# Change this path only if Tesseract is installed somewhere else.
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ---------------------------------------
# Streamlit Page Settings
# ---------------------------------------
st.set_page_config(
    page_title="PDF Text Extractor",
    page_icon="📄",
    layout="centered"
)

st.title("📄 PDF Text Extractor App")
st.write(
    "Upload a PDF file. This app can extract text from both searchable PDFs "
    "and scanned image-based PDFs using OCR."
)


# ---------------------------------------
# Function 1: Extract Text from Searchable PDF
# ---------------------------------------
def extract_searchable_pdf_text(pdf_file):
    """
    This function extracts text directly from searchable PDFs.
    Searchable PDFs are those where text can be selected or copied.
    """
    extracted_text = ""

    pdf_bytes = pdf_file.read()
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

    for page_number in range(len(pdf_document)):
        page = pdf_document[page_number]
        page_text = page.get_text()

        extracted_text += f"\n\n--- Page {page_number + 1} ---\n\n"
        extracted_text += page_text

    pdf_document.close()
    return extracted_text.strip()


# ---------------------------------------
# Function 2: OCR for Scanned PDF
# ---------------------------------------
def extract_scanned_pdf_text(pdf_file, dpi=300, language="eng"):
    """
    This function converts each PDF page into an image
    and then uses OCR to extract text from it.
    This is useful for scanned PDFs.
    """
    extracted_text = ""

    pdf_bytes = pdf_file.read()
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    for page_number in range(len(pdf_document)):
        page = pdf_document[page_number]

        # Convert PDF page to image
        pix = page.get_pixmap(matrix=matrix)

        image = Image.frombytes(
            "RGB",
            [pix.width, pix.height],
            pix.samples
        )

        # OCR text extraction
        page_text = pytesseract.image_to_string(image, lang=language)

        extracted_text += f"\n\n--- Page {page_number + 1} ---\n\n"
        extracted_text += page_text

    pdf_document.close()
    return extracted_text.strip()


# ---------------------------------------
# Function 3: Auto Detect PDF Type
# ---------------------------------------
def auto_extract_pdf_text(pdf_file, dpi=300, language="eng"):
    """
    This function first tries direct extraction.
    If very little text is found, it uses OCR automatically.
    """
    pdf_bytes = pdf_file.read()
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

    direct_text = ""

    for page_number in range(len(pdf_document)):
        page = pdf_document[page_number]
        page_text = page.get_text()

        direct_text += f"\n\n--- Page {page_number + 1} ---\n\n"
        direct_text += page_text

    pdf_document.close()

    # If direct text is very small, use OCR
    if len(direct_text.strip()) < 50:
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        extracted_text = ""

        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)

        for page_number in range(len(pdf_document)):
            page = pdf_document[page_number]
            pix = page.get_pixmap(matrix=matrix)

            image = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples
            )

            page_text = pytesseract.image_to_string(image, lang=language)

            extracted_text += f"\n\n--- Page {page_number + 1} ---\n\n"
            extracted_text += page_text

        pdf_document.close()
        return extracted_text.strip(), "OCR mode was used because this PDF seems scanned."

    else:
        return direct_text.strip(), "Direct text extraction was used because this PDF seems searchable."


# ---------------------------------------
# Function 4: Convert Extracted Text to Word File
# ---------------------------------------
def create_word_file(text):
    """
    This function creates a Word document from extracted text.
    """
    document = Document()
    document.add_heading("Extracted PDF Text", level=1)

    pages = text.split("--- Page")

    for page in pages:
        page = page.strip()

        if page:
            document.add_paragraph("--- Page " + page)

    word_buffer = BytesIO()
    document.save(word_buffer)
    word_buffer.seek(0)

    return word_buffer


# ---------------------------------------
# Function 5: Convert Extracted Text to TXT File
# ---------------------------------------
def create_txt_file(text):
    """
    This function creates a TXT file from extracted text.
    """
    txt_buffer = BytesIO()
    txt_buffer.write(text.encode("utf-8"))
    txt_buffer.seek(0)

    return txt_buffer


# ---------------------------------------
# Sidebar Options
# ---------------------------------------
st.sidebar.header("⚙️ Extraction Settings")

extraction_mode = st.sidebar.radio(
    "Select extraction mode:",
    [
        "Auto Detect",
        "Searchable PDF Only",
        "Scanned PDF OCR Only"
    ]
)

output_type = st.sidebar.radio(
    "Select output file type:",
    [
        "TXT File",
        "Word File"
    ]
)

ocr_dpi = st.sidebar.slider(
    "OCR Image Quality DPI",
    min_value=150,
    max_value=400,
    value=300,
    step=50
)

ocr_language = st.sidebar.selectbox(
    "OCR Language",
    [
        "eng",
        "urd"
    ],
    index=0
)

st.sidebar.info(
    "Use 'eng' for English PDFs. Use 'urd' for Urdu PDFs only if Urdu OCR language is installed in Tesseract."
)


# ---------------------------------------
# File Upload Section
# ---------------------------------------
uploaded_pdf = st.file_uploader(
    "Upload your PDF file",
    type=["pdf"]
)


# ---------------------------------------
# Main App Logic
# ---------------------------------------
if uploaded_pdf is not None:
    st.success("PDF uploaded successfully.")

    if st.button("Extract Text"):
        with st.spinner("Extracting text from PDF... Please wait."):
            try:
                # Reset file pointer before extraction
                uploaded_pdf.seek(0)

                if extraction_mode == "Searchable PDF Only":
                    extracted_text = extract_searchable_pdf_text(uploaded_pdf)
                    message = "Direct text extraction completed."

                elif extraction_mode == "Scanned PDF OCR Only":
                    extracted_text = extract_scanned_pdf_text(
                        uploaded_pdf,
                        dpi=ocr_dpi,
                        language=ocr_language
                    )
                    message = "OCR text extraction completed."

                else:
                    extracted_text, message = auto_extract_pdf_text(
                        uploaded_pdf,
                        dpi=ocr_dpi,
                        language=ocr_language
                    )

                st.success(message)

                if extracted_text.strip() == "":
                    st.warning(
                        "No text was extracted. The PDF may be unclear, handwritten, "
                        "or OCR language may not be installed."
                    )
                else:
                    st.subheader("Extracted Text Preview")
                    st.text_area(
                        "Preview",
                        extracted_text[:5000],
                        height=300
                    )

                    # TXT Download
                    if output_type == "TXT File":
                        txt_file = create_txt_file(extracted_text)

                        st.download_button(
                            label="Download TXT File",
                            data=txt_file,
                            file_name="extracted_pdf_text.txt",
                            mime="text/plain"
                        )

                    # Word Download
                    elif output_type == "Word File":
                        word_file = create_word_file(extracted_text)

                        st.download_button(
                            label="Download Word File",
                            data=word_file,
                            file_name="extracted_pdf_text.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )

            except Exception as e:
                st.error("An error occurred while extracting text.")
                st.exception(e)

else:
    st.info("Please upload a PDF file to start.")