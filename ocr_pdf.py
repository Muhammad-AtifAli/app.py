import hashlib
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import streamlit as st


# ---------------------------------------------------------
# STREAMLIT PAGE SETTINGS
# ---------------------------------------------------------

st.set_page_config(
    page_title="Searchable PDF Converter",
    page_icon="📄",
    layout="centered",
)


# ---------------------------------------------------------
# ADD COMMON WINDOWS PROGRAM FOLDERS TO PATH
# ---------------------------------------------------------

def add_windows_programs_to_path():
    if os.name != "nt":
        return

    possible_folders = [
        Path(r"C:\Program Files\Tesseract-OCR"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR"),
    ]

    ghostscript_base_folders = [
        Path(r"C:\Program Files\gs"),
        Path(r"C:\Program Files (x86)\gs"),
    ]

    for base_folder in ghostscript_base_folders:
        if base_folder.exists():
            for version_folder in base_folder.glob("gs*"):
                possible_folders.append(version_folder / "bin")

    current_path = os.environ.get("PATH", "")
    current_path_items = current_path.split(os.pathsep)

    for folder in possible_folders:
        folder_text = str(folder)

        if folder.exists() and folder_text not in current_path_items:
            current_path = folder_text + os.pathsep + current_path

    os.environ["PATH"] = current_path


# ---------------------------------------------------------
# RUN A COMMAND SAFELY
# ---------------------------------------------------------

def run_command(command, timeout=None):
    creation_flags = 0

    if os.name == "nt":
        creation_flags = subprocess.CREATE_NO_WINDOW

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            creationflags=creation_flags,
        )

        return result.returncode, result.stdout.strip()

    except FileNotFoundError:
        return 127, "The required program was not found."

    except subprocess.TimeoutExpired:
        return 124, "The command took too long and was stopped."

    except Exception as error:
        return 1, str(error)


# ---------------------------------------------------------
# FIND GHOSTSCRIPT
# ---------------------------------------------------------

def find_ghostscript():
    if os.name == "nt":
        command_names = [
            "gswin64c",
            "gswin32c",
        ]
    else:
        command_names = ["gs"]

    for command_name in command_names:
        command_path = shutil.which(command_name)

        if command_path:
            return command_path

    return None


# ---------------------------------------------------------
# GET INSTALLED TESSERACT LANGUAGES
# ---------------------------------------------------------

def get_tesseract_languages():
    if shutil.which("tesseract") is None:
        return []

    return_code, output = run_command(
        ["tesseract", "--list-langs"],
        timeout=30,
    )

    if return_code != 0:
        return []

    installed_languages = []

    for line in output.splitlines():
        language = line.strip()

        if not language:
            continue

        if language.lower().startswith("list of available"):
            continue

        installed_languages.append(language)

    return installed_languages


# ---------------------------------------------------------
# CHECK REQUIRED PROGRAMS
# ---------------------------------------------------------

def check_dependencies(selected_language):
    problems = []

    if importlib.util.find_spec("ocrmypdf") is None:
        problems.append(
            "OCRmyPDF is not installed. Run: "
            "python -m pip install ocrmypdf"
        )

    if shutil.which("tesseract") is None:
        problems.append(
            "Tesseract OCR was not found. Install Tesseract or add "
            "its installation folder to Windows PATH."
        )

    else:
        installed_languages = get_tesseract_languages()
        required_languages = selected_language.split("+")

        missing_languages = []

        for language in required_languages:
            if language not in installed_languages:
                missing_languages.append(language)

        if missing_languages:
            problems.append(
                "Missing Tesseract language data: "
                + ", ".join(missing_languages)
                + "."
            )

    if find_ghostscript() is None:
        problems.append(
            "Ghostscript was not found. Install Ghostscript or add "
            "its bin folder to Windows PATH."
        )

    return problems


# ---------------------------------------------------------
# CREATE THE OCR COMMAND
# ---------------------------------------------------------

def build_ocr_command(
    input_path,
    output_path,
    language,
    deskew,
    rotate_pages,
    processing_mode,
    jobs,
):
    command = [
        sys.executable,
        "-m",
        "ocrmypdf",
        "--language",
        language,
        "--output-type",
        "pdf",
        "--optimize",
        "0",
        "--jobs",
        str(jobs),
    ]

    if processing_mode == "Skip pages that already contain text":
        command.append("--skip-text")

    else:
        command.append("--force-ocr")

    if deskew:
        command.append("--deskew")

    if rotate_pages:
        command.append("--rotate-pages")

    command.append(str(input_path))
    command.append(str(output_path))

    return command


# ---------------------------------------------------------
# CONVERT PDF
# ---------------------------------------------------------

def convert_pdf(
    pdf_bytes,
    original_filename,
    language,
    deskew,
    rotate_pages,
    processing_mode,
    jobs,
):
    original_stem = Path(original_filename).stem
    output_filename = original_stem + "_searchable.pdf"

    with tempfile.TemporaryDirectory() as temporary_folder:
        temporary_path = Path(temporary_folder)

        input_path = temporary_path / "input.pdf"
        output_path = temporary_path / "searchable_output.pdf"

        input_path.write_bytes(pdf_bytes)

        command = build_ocr_command(
            input_path=input_path,
            output_path=output_path,
            language=language,
            deskew=deskew,
            rotate_pages=rotate_pages,
            processing_mode=processing_mode,
            jobs=jobs,
        )

        return_code, processing_log = run_command(command)

        if return_code != 0:
            return None, output_filename, processing_log

        if not output_path.exists():
            return (
                None,
                output_filename,
                "OCRmyPDF finished but did not create an output PDF.",
            )

        output_bytes = output_path.read_bytes()

        return output_bytes, output_filename, processing_log


# ---------------------------------------------------------
# RESET PREVIOUS RESULT
# ---------------------------------------------------------

def reset_result():
    st.session_state.result_bytes = None
    st.session_state.result_filename = None
    st.session_state.processing_log = ""


# ---------------------------------------------------------
# INITIAL SETUP
# ---------------------------------------------------------

add_windows_programs_to_path()

if "result_bytes" not in st.session_state:
    st.session_state.result_bytes = None

if "result_filename" not in st.session_state:
    st.session_state.result_filename = None

if "processing_log" not in st.session_state:
    st.session_state.processing_log = ""

if "uploaded_file_hash" not in st.session_state:
    st.session_state.uploaded_file_hash = None


# ---------------------------------------------------------
# APPLICATION INTERFACE
# ---------------------------------------------------------

st.title("📄 Searchable PDF Converter")

st.write(
    "Upload a scanned or image-based PDF. The application will "
    "add an OCR text layer so that the text can be searched, "
    "selected, and copied."
)

st.info(
    "For the closest visual match to the original PDF, leave "
    "automatic rotation and page straightening disabled."
)


# ---------------------------------------------------------
# OCR SETTINGS
# ---------------------------------------------------------

with st.expander("OCR settings", expanded=True):
    language_label = st.selectbox(
        "Document language",
        [
            "English",
            "Urdu",
            "English and Urdu",
        ],
    )

    language_codes = {
        "English": "eng",
        "Urdu": "urd",
        "English and Urdu": "eng+urd",
    }

    selected_language = language_codes[language_label]

    processing_mode = st.radio(
        "How should pages with existing text be handled?",
        [
            "Skip pages that already contain text",
            "OCR every page again",
        ],
        index=0,
        help=(
            "Use the first option for normal scanned PDFs. "
            "Use OCR every page again only when an existing "
            "text layer is incorrect."
        ),
    )

    deskew = st.checkbox(
        "Straighten tilted pages",
        value=False,
        help=(
            "This may improve OCR on crooked scans, but it may "
            "slightly change the visible page."
        ),
    )

    rotate_pages = st.checkbox(
        "Automatically rotate sideways pages",
        value=False,
        help=(
            "Enable this when some pages are upside down or sideways."
        ),
    )

    jobs = st.slider(
        "Processor jobs",
        min_value=1,
        max_value=4,
        value=1,
        help=(
            "Use 1 on an older computer or when processing "
            "a large PDF."
        ),
    )


# ---------------------------------------------------------
# FILE UPLOADER
# ---------------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload a non-searchable PDF",
    type=["pdf"],
    accept_multiple_files=False,
)


# ---------------------------------------------------------
# PROCESS UPLOADED PDF
# ---------------------------------------------------------

if uploaded_file is not None:
    uploaded_bytes = uploaded_file.getvalue()

    current_file_hash = hashlib.sha256(
        uploaded_bytes
    ).hexdigest()

    if current_file_hash != st.session_state.uploaded_file_hash:
        st.session_state.uploaded_file_hash = current_file_hash
        reset_result()

    if not uploaded_bytes.startswith(b"%PDF"):
        st.error(
            "The selected file does not appear to be a valid PDF."
        )

    else:
        file_size_mb = len(uploaded_bytes) / (1024 * 1024)

        st.write(
            "Selected file: **"
            + uploaded_file.name
            + "**"
        )

        st.write(
            "File size: **"
            + f"{file_size_mb:.2f}"
            + " MB**"
        )

        convert_button = st.button(
            "Convert to searchable PDF",
            type="primary",
            use_container_width=True,
        )

        if convert_button:
            dependency_problems = check_dependencies(
                selected_language
            )

            if dependency_problems:
                reset_result()

                st.error(
                    "The required OCR programs are not ready."
                )

                for problem in dependency_problems:
                    st.write("• " + problem)

            else:
                with st.spinner(
                    "Applying OCR and creating the searchable PDF..."
                ):
                    (
                        result_bytes,
                        result_filename,
                        processing_log,
                    ) = convert_pdf(
                        pdf_bytes=uploaded_bytes,
                        original_filename=uploaded_file.name,
                        language=selected_language,
                        deskew=deskew,
                        rotate_pages=rotate_pages,
                        processing_mode=processing_mode,
                        jobs=jobs,
                    )

                st.session_state.processing_log = processing_log

                if result_bytes is None:
                    st.session_state.result_bytes = None
                    st.session_state.result_filename = None

                    st.error(
                        "The PDF could not be converted."
                    )

                else:
                    st.session_state.result_bytes = result_bytes
                    st.session_state.result_filename = (
                        result_filename
                    )

                    st.success(
                        "Conversion completed. The output PDF "
                        "now contains a searchable text layer."
                    )


# ---------------------------------------------------------
# DOWNLOAD OUTPUT PDF
# ---------------------------------------------------------

if st.session_state.result_bytes is not None:
    output_size_mb = (
        len(st.session_state.result_bytes)
        / (1024 * 1024)
    )

    st.write(
        "Output size: **"
        + f"{output_size_mb:.2f}"
        + " MB**"
    )

    st.download_button(
        label="Download searchable PDF",
        data=st.session_state.result_bytes,
        file_name=st.session_state.result_filename,
        mime="application/pdf",
        use_container_width=True,
    )


# ---------------------------------------------------------
# SHOW PROCESSING LOG
# ---------------------------------------------------------

if st.session_state.processing_log:
    with st.expander("Processing details"):
        st.code(st.session_state.processing_log)


# ---------------------------------------------------------
# INSTALLATION INSTRUCTIONS
# ---------------------------------------------------------

with st.expander("Installation and running instructions"):
    st.subheader("1. Install Python packages")

    st.code(
        "python -m pip install --upgrade pip\n"
        "python -m pip install streamlit ocrmypdf",
        language="bash",
    )

    st.subheader("2. Check required programs")

    st.code(
        "tesseract --version\n"
        "gswin64c --version\n"
        "python -m ocrmypdf --version",
        language="bash",
    )

    st.subheader("3. Run the application")

    st.code(
        'python -m streamlit run '
        '"C:\\Users\\STUDENT 79\\ocr_pdf.py"',
        language="bash",
    )

    st.subheader("Urdu language requirement")

    st.write(
        "For Urdu OCR, the file urd.traineddata must be "
        "available inside the Tesseract tessdata folder."
    )