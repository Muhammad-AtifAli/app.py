import io
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import streamlit as st


# =========================================================
# WINDOWS PATH SETUP
# =========================================================
def configure_windows_paths() -> None:
    """
    Automatically add common Tesseract and Ghostscript
    installation folders to PATH on Windows.
    """

    if platform.system() != "Windows":
        return

    possible_folders = [
        Path(r"C:\Program Files\Tesseract-OCR"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR"),
    ]

    # Find installed Ghostscript versions automatically.
    ghostscript_root = Path(r"C:\Program Files\gs")

    if ghostscript_root.exists():
        ghostscript_folders = sorted(
            ghostscript_root.glob(r"gs*\bin"),
            reverse=True,
        )

        possible_folders.extend(ghostscript_folders)

    current_path = os.environ.get("PATH", "")
    current_parts = current_path.split(os.pathsep)

    folders_to_add = []

    for folder in possible_folders:
        folder_text = str(folder)

        if folder.exists() and folder_text not in current_parts:
            folders_to_add.append(folder_text)

    if folders_to_add:
        os.environ["PATH"] = os.pathsep.join(
            folders_to_add + [current_path]
        )


# Configure paths before checking dependencies.
configure_windows_paths()


# =========================================================
# STREAMLIT PAGE SETTINGS
# =========================================================
st.set_page_config(
    page_title="Image PDF to Searchable PDF",
    page_icon="📄",
    layout="centered",
)


# =========================================================
# COMMAND HELPERS
# =========================================================
def run_command(
    command: list[str],
    timeout: int = 30,
) -> subprocess.CompletedProcess[str]:
    """
    Run a command without opening an extra CMD window.
    """

    creation_flags = (
        subprocess.CREATE_NO_WINDOW
        if platform.system() == "Windows"
        else 0
    )

    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        creationflags=creation_flags,
    )


def command_works(command: list[str]) -> bool:
    """
    Check whether a command exists and runs successfully.
    """

    try:
        result = run_command(
            command=command,
            timeout=20,
        )

        return result.returncode == 0

    except (
        FileNotFoundError,
        subprocess.TimeoutExpired,
        OSError,
    ):
        return False


def get_ghostscript_command() -> str | None:
    """
    Find the available Ghostscript command.
    """

    possible_commands = [
        "gswin64c",
        "gswin32c",
        "gs",
    ]

    for command in possible_commands:
        if shutil.which(command):
            if command_works([command, "--version"]):
                return command

    return None


def check_dependencies() -> list[str]:
    """
    Check whether Tesseract, Ghostscript, and OCRmyPDF
    are properly installed.
    """

    missing = []

    if not command_works(["tesseract", "--version"]):
        missing.append("Tesseract OCR")

    if get_ghostscript_command() is None:
        missing.append("Ghostscript")

    # Using the current Python executable is more reliable
    # than depending on the ocrmypdf command being in PATH.
    if not command_works(
        [
            sys.executable,
            "-m",
            "ocrmypdf",
            "--version",
        ]
    ):
        missing.append("OCRmyPDF")

    return missing


def get_tesseract_languages() -> set[str]:
    """
    Get all OCR languages currently installed in Tesseract.
    """

    try:
        result = run_command(
            ["tesseract", "--list-langs"],
            timeout=30,
        )

        if result.returncode != 0:
            return set()

        combined_output = (
            result.stdout
            + "\n"
            + result.stderr
        )

        languages = set()

        for line in combined_output.splitlines():
            language = line.strip()

            if not language:
                continue

            if language.lower().startswith(
                "list of available languages"
            ):
                continue

            languages.add(language)

        return languages

    except (
        FileNotFoundError,
        subprocess.TimeoutExpired,
        OSError,
    ):
        return set()


# =========================================================
# FILE HELPERS
# =========================================================
def clean_filename_stem(filename: str) -> str:
    """
    Remove characters that are unsafe in Windows filenames.
    """

    original_name = Path(filename).name
    stem = Path(original_name).stem

    stem = re.sub(
        r'[<>:"/\\|?*\x00-\x1F]',
        "_",
        stem,
    )

    stem = re.sub(
        r"\s+",
        " ",
        stem,
    )

    stem = stem.strip(" ._")

    if not stem:
        stem = "document"

    return stem


def create_unique_output_name(
    original_filename: str,
    used_names: set[str],
) -> str:
    """
    Create a unique output filename.

    Example:
    book.pdf -> book_searchable.pdf
    """

    base_name = (
        f"{clean_filename_stem(original_filename)}"
        f"_searchable"
    )

    output_name = f"{base_name}.pdf"
    number = 2

    while output_name.lower() in used_names:
        output_name = f"{base_name}_{number}.pdf"
        number += 1

    used_names.add(output_name.lower())

    return output_name


def clear_previous_results() -> None:
    """
    Clear old output when the selected files change.
    """

    st.session_state["converted_files"] = []
    st.session_state["failed_files"] = []


# =========================================================
# PDF CONVERSION
# =========================================================
def convert_pdf_to_searchable(
    input_path: Path,
    output_path: Path,
    language: str,
) -> tuple[bool, str]:
    """
    Convert a scanned PDF to a searchable PDF.

    The settings avoid:
    - image optimization
    - deskewing
    - page rotation
    - background removal
    - image cleaning
    - page resizing

    Only an invisible OCR text layer is added.
    """

    command = [
        sys.executable,
        "-m",
        "ocrmypdf",

        # OCR language
        "-l",
        language,

        # Produce a standard PDF instead of PDF/A
        "--output-type",
        "pdf",

        # Disable most image and PDF optimization
        "--optimize",
        "0",

        # Skip pages that already contain text
        "--mode",
        "skip",

        # Use one OCR worker for stability
        "--jobs",
        "1",

        # Allow up to five minutes per difficult page
        "--tesseract-timeout",
        "300",

        # Suppress normal command-line progress messages
        "-q",

        # Input and output files
        str(input_path),
        str(output_path),
    ]

    try:
        result = run_command(
            command=command,
            timeout=3600,
        )

        if (
            result.returncode == 0
            and output_path.exists()
            and output_path.stat().st_size > 0
        ):
            return (
                True,
                "Conversion completed successfully.",
            )

        error_message = (
            result.stderr.strip()
            or result.stdout.strip()
        )

        if not error_message:
            error_message = (
                "OCRmyPDF stopped with exit code "
                f"{result.returncode}."
            )

        return False, error_message

    except subprocess.TimeoutExpired:
        return (
            False,
            "The conversion exceeded the one-hour limit.",
        )

    except FileNotFoundError as error:
        return (
            False,
            f"A required program was not found: {error}",
        )

    except Exception as error:
        return (
            False,
            f"Unexpected conversion error: {error}",
        )


def create_zip_file(
    converted_files: list[dict[str, object]],
) -> bytes:
    """
    Place all converted PDFs inside one ZIP file.
    """

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(
        zip_buffer,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as zip_file:

        for converted_file in converted_files:
            zip_file.writestr(
                str(converted_file["name"]),
                converted_file["data"],
            )

    zip_buffer.seek(0)

    return zip_buffer.getvalue()


# =========================================================
# SESSION STATE
# =========================================================
if "converted_files" not in st.session_state:
    st.session_state["converted_files"] = []

if "failed_files" not in st.session_state:
    st.session_state["failed_files"] = []


# =========================================================
# APP INTERFACE
# =========================================================
st.title("📄 Image PDF to Searchable PDF")

st.write(
    """
    Upload one or multiple scanned PDF files. The app adds an
    invisible OCR text layer so that the PDF text can be searched,
    selected, and copied.
    """
)

st.info(
    """
    The app does not intentionally rotate, resize, deskew, clean,
    compress, or change the visible pages. The internal PDF structure
    will change because searchable text is being added.
    """
)


# =========================================================
# DEPENDENCY CHECK
# =========================================================
missing_dependencies = check_dependencies()

if missing_dependencies:
    st.error(
        "The following required component(s) were not found: "
        + ", ".join(missing_dependencies)
    )

    if "Tesseract OCR" in missing_dependencies:
        st.write(
            "Tesseract is installed on your computer, but Windows "
            "may not have added it to PATH."
        )

        st.code(
            r'set "PATH=C:\Program Files\Tesseract-OCR;%PATH%"',
            language="text",
        )

    if "Ghostscript" in missing_dependencies:
        st.write(
            "Ghostscript could not be detected. Confirm that "
            "`gswin64c --version` works in CMD."
        )

    if "OCRmyPDF" in missing_dependencies:
        st.code(
            "py -m pip install ocrmypdf",
            language="text",
        )

    st.stop()


# =========================================================
# OCR LANGUAGE SETTINGS
# =========================================================
installed_languages = get_tesseract_languages()

language_options = {
    "English": {
        "code": "eng",
        "required": {"eng"},
    },
    "Urdu": {
        "code": "urd",
        "required": {"urd"},
    },
    "English + Urdu": {
        "code": "eng+urd",
        "required": {"eng", "urd"},
    },
}

selected_language_name = st.selectbox(
    "Document language",
    options=list(language_options.keys()),
    index=0,
)

selected_language = language_options[
    selected_language_name
]["code"]

required_languages = language_options[
    selected_language_name
]["required"]

missing_languages = (
    required_languages
    - installed_languages
)

if missing_languages:
    st.error(
        "The selected Tesseract language data is missing: "
        + ", ".join(sorted(missing_languages))
    )

    st.write(
        "Select English, or install the missing language data "
        "inside the Tesseract `tessdata` folder."
    )

    st.stop()


with st.expander("Installed OCR languages"):
    if installed_languages:
        st.write(
            ", ".join(
                sorted(installed_languages)
            )
        )
    else:
        st.warning(
            "The installed language list could not be read."
        )


# =========================================================
# FILE UPLOADER
# =========================================================
uploaded_files = st.file_uploader(
    "Upload scanned PDF files",
    type=["pdf"],
    accept_multiple_files=True,
    on_change=clear_previous_results,
    help=(
        "Select one PDF or hold Ctrl to select several PDFs."
    ),
)


if uploaded_files:
    total_file_size = sum(
        uploaded_file.size
        for uploaded_file in uploaded_files
    )

    st.success(
        f"{len(uploaded_files)} file(s) selected. "
        f"Total size: "
        f"{total_file_size / (1024 * 1024):.2f} MB"
    )

    with st.expander("Selected files"):
        for number, uploaded_file in enumerate(
            uploaded_files,
            start=1,
        ):
            file_size_mb = (
                uploaded_file.size
                / (1024 * 1024)
            )

            st.write(
                f"{number}. **{uploaded_file.name}** "
                f"({file_size_mb:.2f} MB)"
            )


# =========================================================
# CONVERSION BUTTON
# =========================================================
convert_button = st.button(
    "Convert all files",
    type="primary",
    use_container_width=True,
    disabled=not uploaded_files,
)


# =========================================================
# PROCESS FILES
# =========================================================
if convert_button and uploaded_files:
    st.session_state["converted_files"] = []
    st.session_state["failed_files"] = []

    total_files = len(uploaded_files)

    progress_bar = st.progress(0)
    status_area = st.empty()

    used_output_names = set()

    with tempfile.TemporaryDirectory() as temporary_directory:
        temporary_folder = Path(temporary_directory)

        for index, uploaded_file in enumerate(
            uploaded_files,
            start=1,
        ):
            status_area.info(
                f"Processing {index} of {total_files}: "
                f"{uploaded_file.name}"
            )

            output_filename = create_unique_output_name(
                original_filename=uploaded_file.name,
                used_names=used_output_names,
            )

            input_path = (
                temporary_folder
                / f"input_{index}.pdf"
            )

            output_path = (
                temporary_folder
                / f"output_{index}.pdf"
            )

            try:
                uploaded_data = uploaded_file.getvalue()

                # Basic PDF validation.
                if not uploaded_data.startswith(b"%PDF"):
                    raise ValueError(
                        "The uploaded file does not appear "
                        "to be a valid PDF."
                    )

                input_path.write_bytes(uploaded_data)

                success, message = (
                    convert_pdf_to_searchable(
                        input_path=input_path,
                        output_path=output_path,
                        language=selected_language,
                    )
                )

                if success:
                    converted_data = output_path.read_bytes()

                    st.session_state[
                        "converted_files"
                    ].append(
                        {
                            "name": output_filename,
                            "data": converted_data,
                            "original_name": (
                                uploaded_file.name
                            ),
                        }
                    )

                else:
                    st.session_state[
                        "failed_files"
                    ].append(
                        {
                            "name": uploaded_file.name,
                            "error": message,
                        }
                    )

            except Exception as error:
                st.session_state[
                    "failed_files"
                ].append(
                    {
                        "name": uploaded_file.name,
                        "error": str(error),
                    }
                )

            finally:
                input_path.unlink(
                    missing_ok=True
                )

                output_path.unlink(
                    missing_ok=True
                )

            progress_bar.progress(
                index / total_files
            )

    status_area.empty()

    successful_count = len(
        st.session_state["converted_files"]
    )

    failed_count = len(
        st.session_state["failed_files"]
    )

    if successful_count:
        st.success(
            f"{successful_count} file(s) "
            "converted successfully."
        )

    if failed_count:
        st.error(
            f"{failed_count} file(s) "
            "could not be converted."
        )


# =========================================================
# DOWNLOAD RESULTS
# =========================================================
converted_files = st.session_state[
    "converted_files"
]

if converted_files:
    st.divider()
    st.subheader("Download searchable PDFs")

    if len(converted_files) == 1:
        converted_file = converted_files[0]

        st.download_button(
            label="Download searchable PDF",
            data=converted_file["data"],
            file_name=str(
                converted_file["name"]
            ),
            mime="application/pdf",
            use_container_width=True,
        )

    else:
        zip_data = create_zip_file(
            converted_files
        )

        st.download_button(
            label=(
                f"Download all "
                f"{len(converted_files)} "
                "PDFs as ZIP"
            ),
            data=zip_data,
            file_name="searchable_pdfs.zip",
            mime="application/zip",
            use_container_width=True,
        )

        with st.expander(
            "Download files separately"
        ):
            for index, converted_file in enumerate(
                converted_files,
                start=1,
            ):
                st.download_button(
                    label=(
                        f"Download "
                        f"{converted_file['name']}"
                    ),
                    data=converted_file["data"],
                    file_name=str(
                        converted_file["name"]
                    ),
                    mime="application/pdf",
                    key=(
                        f"download_{index}_"
                        f"{converted_file['name']}"
                    ),
                    use_container_width=True,
                )


# =========================================================
# DISPLAY ERRORS
# =========================================================
failed_files = st.session_state[
    "failed_files"
]

if failed_files:
    st.divider()
    st.subheader("Files with errors")

    for failed_file in failed_files:
        with st.expander(
            f"❌ {failed_file['name']}"
        ):
            st.code(
                str(failed_file["error"])
            )