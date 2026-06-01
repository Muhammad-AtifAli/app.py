import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from docx import Document
from io import BytesIO
import re


# =========================================================
# TESSERACT PATH FOR WINDOWS
# =========================================================
# If your Tesseract is installed in a different location, change this path.
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# =========================================================
# STREAMLIT PAGE SETTINGS
# =========================================================
st.set_page_config(
    page_title="PDF Text Extractor",
    page_icon="📄",
    layout="wide"
)


# =========================================================
# CUSTOM DESIGN
# =========================================================
st.markdown(
    """
    <style>
    .main-title {
        text-align: center;
        color: #1F4E79;
        font-size: 42px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .sub-title {
        text-align: center;
        font-size: 18px;
        color: #555;
        margin-bottom: 30px;
    }
    .box {
        background-color: #F5F8FF;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #D9E6F2;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="main-title">📄 PDF Text Extractor App</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Extract text from searchable PDFs and scanned image PDFs. Download as TXT or Word file.</div>',
    unsafe_allow_html=True
)


# =========================================================
# TEXT CLEANING FUNCTION
# =========================================================
def clean_text_for_word(text):
    """
    Removes hidden characters that create errors in Word/XML files.
    """
    if text is None:
        return ""

    # Remove NULL bytes
    text = text.replace("\x00", "")

    # Remove illegal XML control characters
    text = re.sub(r"[\x01-\x08\x0B\x0C\x0E-\x1F]", "", text)

    return text


def clean_general_text(text):
    """
    General text cleaning for preview and download.
    """
    if text is None:
        return ""

    text = text.replace("\x00", "")
    text = re.sub(r"[\x01-\x08\x0B\x0C\x0E-\x1F]", "", text)

    # Remove too many empty lines
    text = re.sub(r"\n{4,}", "\n\n\n", text)

    return text.strip()


# =========================================================
# SEARCHABLE PDF TEXT EXTRACTION
# =========================================================
def extract_searchable_pdf_text(pdf_bytes):
    """
    Extracts text from searchable PDFs.
    Works for multiple pages.
    """
    extracted_text = ""

    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = len(pdf_document)

    progress_bar = st.progress(0)
    status_text = st.empty()

    for page_number in range(total_pages):
        page = pdf_document[page_number]
        page_text = page.get_text("text")

        extracted_text += f"\n\n================ Page {page_number + 1} ================\n\n"
        extracted_text += page_text

        progress = int((page_number + 1) / total_pages * 100)
        progress_bar.progress(progress)
        status_text.write(f"Processing page {page_number + 1} of {total_pages}")

    pdf_document.close()

    return clean_general_text(extracted_text)


# =========================================================
# SCANNED PDF OCR EXTRACTION
# =========================================================
def extract_scanned_pdf_text(pdf_bytes, dpi=200, language="eng"):
    """
    Converts each PDF page into image and applies OCR.
    Works for multiple pages.
    """
    extracted_text = ""

    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = len(pdf_document)

    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    progress_bar = st.progress(0)
    status_text = st.empty()

    for page_number in range(total_pages):
        page = pdf_document[page_number]

        # Convert PDF page to image
        pix = page.get_pixmap(matrix=matrix, alpha=False)

        image = Image.frombytes(
            "RGB",
            [pix.width, pix.height],
            pix.samples
        )

        # OCR
        page_text = pytesseract.image_to_string(image, lang=language)

        extracted_text += f"\n\n================ Page {page_number + 1} ================\n\n"
        extracted_text += page_text

        progress = int((page_number + 1) / total_pages * 100)
        progress_bar.progress(progress)
        status_text.write(f"OCR processing page {page_number + 1} of {total_pages}")

    pdf_document.close()

    return clean_general_text(extracted_text)


# =========================================================
# AUTO DETECTION EXTRACTION
# =========================================================
def auto_extract_pdf_text(pdf_bytes, dpi=200, language="eng"):
    """
    First tries direct text extraction.
    If text is too little, OCR is applied page by page.
    This works better for mixed PDFs too.
    """
    extracted_text = ""

    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = len(pdf_document)

    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    progress_bar = st.progress(0)
    status_text = st.empty()

    searchable_pages = 0
    ocr_pages = 0

    for page_number in range(total_pages):
        page = pdf_document[page_number]

        # First try direct text extraction
        page_text = page.get_text("text").strip()

        # If page has enough selectable text, use it
        if len(page_text) > 30:
            searchable_pages += 1
            final_page_text = page_text
            mode_used = "Searchable text"

        # Otherwise use OCR for that page
        else:
            ocr_pages += 1

            pix = page.get_pixmap(matrix=matrix, alpha=False)

            image = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples
            )

            final_page_text = pytesseract.image_to_string(image, lang=language)
            mode_used = "OCR"

        extracted_text += f"\n\n================ Page {page_number + 1} ({mode_used}) ================\n\n"
        extracted_text += final_page_text

        progress = int((page_number + 1) / total_pages * 100)
        progress_bar.progress(progress)
        status_text.write(f"Processing page {page_number + 1} of {total_pages}")

    pdf_document.close()

    message = f"Completed. Searchable pages: {searchable_pages}, OCR pages: {ocr_pages}"

    return clean_general_text(extracted_text), message


# =========================================================
# TXT FILE CREATION
# =========================================================
def create_txt_file(text):
    """
    Creates TXT file from extracted text.
    """
    text = clean_general_text(text)

    txt_buffer = BytesIO()
    txt_buffer.write(text.encode("utf-8", errors="ignore"))
    txt_buffer.seek(0)

    return txt_buffer


# =========================================================
# WORD FILE CREATION
# =========================================================
def create_word_file(text):
    """
    Creates Word file safely.
    Handles long and multiple-page text.
    """
    text = clean_text_for_word(text)

    document = Document()
    document.add_heading("Extracted PDF Text", level=1)

    # Split page-wise
    pages = re.split(r"=+\s*Page\s+", text)

    for index, page_text in enumerate(pages):
        page_text = page_text.strip()

        if not page_text:
            continue

        # Add page heading
        if index == 0 and not page_text.lower().startswith("1"):
            document.add_paragraph(page_text)
        else:
            document.add_heading(f"Page {index}", level=2)

            # Split large text into smaller paragraphs
            paragraphs = page_text.split("\n")

            for para in paragraphs:
                para = clean_text_for_word(para.strip())

                if para:
                    # Word paragraph has practical limits, so chunk long paragraphs
                    chunk_size = 3000

                    for i in range(0, len(para), chunk_size):
                        document.add_paragraph(para[i:i + chunk_size])

    word_buffer = BytesIO()
    document.save(word_buffer)
    word_buffer.seek(0)

    return word_buffer


# =========================================================
# SIDEBAR SETTINGS
# =========================================================
st.sidebar.header("⚙️ Extraction Settings")

extraction_mode = st.sidebar.radio(
    "Select extraction mode",
    [
        "Auto Detect",
        "Searchable PDF Only",
        "Scanned PDF OCR Only"
    ]
)

output_type = st.sidebar.radio(
    "Select output file type",
    [
        "TXT File",
        "Word File"
    ]
)

ocr_dpi = st.sidebar.slider(
    "OCR Image Quality DPI",
    min_value=150,
    max_value=300,
    value=200,
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

st.sidebar.warning(
    "For Urdu OCR, Urdu language data must be installed in Tesseract. "
    "For English PDFs, keep language as eng."
)


# =========================================================
# MAIN FILE UPLOADER
# =========================================================
st.markdown('<div class="box">', unsafe_allow_html=True)

uploaded_pdf = st.file_uploader(
    "Upload your PDF file",
    type=["pdf"]
)

st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# MAIN APP LOGIC
# =========================================================
if uploaded_pdf is not None:
    st.success("PDF uploaded successfully.")

    pdf_bytes = uploaded_pdf.getvalue()

    try:
        pdf_check = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(pdf_check)
        pdf_check.close()

        st.info(f"Total pages detected: {total_pages}")

    except Exception:
        st.error("This file could not be opened as a valid PDF.")
        st.stop()

    if st.button("🚀 Extract Text"):
        try:
            with st.spinner("Extracting text. Please wait..."):

                if extraction_mode == "Searchable PDF Only":
                    extracted_text = extract_searchable_pdf_text(pdf_bytes)
                    extraction_message = "Direct text extraction completed."

                elif extraction_mode == "Scanned PDF OCR Only":
                    extracted_text = extract_scanned_pdf_text(
                        pdf_bytes,
                        dpi=ocr_dpi,
                        language=ocr_language
                    )
                    extraction_message = "OCR extraction completed."

                else:
                    extracted_text, extraction_message = auto_extract_pdf_text(
                        pdf_bytes,
                        dpi=ocr_dpi,
                        language=ocr_language
                    )

                extracted_text = clean_general_text(extracted_text)

            st.success(extraction_message)

            if not extracted_text:
                st.warning(
                    "No text was extracted. The PDF may be handwritten, blurred, damaged, "
                    "or the OCR language may not be installed."
                )

            else:
                st.subheader("📌 Extracted Text Preview")

                st.text_area(
                    "Preview of extracted text",
                    extracted_text[:10000],
                    height=350
                )

                st.write(f"Total extracted characters: {len(extracted_text)}")

                if output_type == "TXT File":
                    txt_file = create_txt_file(extracted_text)

                    st.download_button(
                        label="⬇️ Download TXT File",
                        data=txt_file,
                        file_name="extracted_pdf_text.txt",
                        mime="text/plain"
                    )

                elif output_type == "Word File":
                    word_file = create_word_file(extracted_text)

                    st.download_button(
                        label="⬇️ Download Word File",
                        data=word_file,
                        file_name="extracted_pdf_text.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )

        except pytesseract.TesseractNotFoundError:
            st.error(
                "Tesseract OCR is not installed or the path is incorrect. "
                "Please install Tesseract and check the path in the code."
            )

        except Exception as e:
            st.error("An error occurred while extracting text.")
            st.exception(e)

else:
    st.info("Please upload a PDF file to start extraction.")