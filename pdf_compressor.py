import streamlit as st
import tempfile
import os
import zipfile
import subprocess
from pathlib import Path


st.set_page_config(
    page_title="PDF Compressor App",
    page_icon="📄",
    layout="wide"
)


def format_size(size_bytes):
    """Convert bytes into KB or MB."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def get_ghostscript_command():
    """
    Detect Ghostscript command.
    Windows usually uses gswin64c or gswin32c.
    Linux/Mac usually use gs.
    """
    possible_commands = ["gswin64c", "gswin32c", "gs"]

    for cmd in possible_commands:
        try:
            subprocess.run(
                [cmd, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            return cmd
        except Exception:
            continue

    return None


def compress_pdf(input_path, output_path, compression_level):
    """
    Compress PDF using Ghostscript.
    """

    gs_command = get_ghostscript_command()

    if gs_command is None:
        raise RuntimeError(
            "Ghostscript is not installed or not found. Please install Ghostscript first."
        )

    compression_settings = {
        "Very High Compression - Low Quality": "/screen",
        "High Compression - Medium Quality": "/ebook",
        "Medium Compression - Good Quality": "/printer",
        "Low Compression - Best Quality": "/prepress"
    }

    pdf_setting = compression_settings[compression_level]

    command = [
        gs_command,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS={pdf_setting}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_path}",
        input_path
    ]

    subprocess.run(command, check=True)


def make_safe_filename(filename):
    """Clean filename for saving."""
    name = Path(filename).stem
    return "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip()


st.title("📄 PDF Compressor App")
st.write("Upload multiple PDF files, compress them, and download them individually or as a ZIP file.")

st.sidebar.header("Compression Settings")

compression_level = st.sidebar.selectbox(
    "Choose Compression Level",
    [
        "Very High Compression - Low Quality",
        "High Compression - Medium Quality",
        "Medium Compression - Good Quality",
        "Low Compression - Best Quality"
    ]
)

st.sidebar.info(
    """
    **Very High Compression** reduces size more but may reduce quality.

    **Low Compression** keeps better quality but size reduction may be small.
    """
)

uploaded_files = st.file_uploader(
    "Upload PDF files",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"{len(uploaded_files)} PDF file(s) uploaded successfully.")

    if st.button("Compress PDFs"):
        compressed_files = []

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)

            progress_bar = st.progress(0)
            status_text = st.empty()

            for index, uploaded_file in enumerate(uploaded_files):
                try:
                    original_filename = uploaded_file.name
                    safe_name = make_safe_filename(original_filename)

                    input_path = temp_dir / original_filename
                    output_path = temp_dir / f"{safe_name}_compressed.pdf"

                    with open(input_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    status_text.write(f"Compressing: {original_filename}")

                    original_size = os.path.getsize(input_path)

                    compress_pdf(
                        str(input_path),
                        str(output_path),
                        compression_level
                    )

                    compressed_size = os.path.getsize(output_path)

                    with open(output_path, "rb") as f:
                        compressed_data = f.read()

                    compressed_files.append(
                        {
                            "filename": f"{safe_name}_compressed.pdf",
                            "data": compressed_data,
                            "original_size": original_size,
                            "compressed_size": compressed_size
                        }
                    )

                    progress_bar.progress((index + 1) / len(uploaded_files))

                except Exception as e:
                    st.error(f"Error compressing {uploaded_file.name}: {e}")

            if compressed_files:
                st.success("PDF compression completed.")

                st.subheader("Compression Results")

                for file in compressed_files:
                    original_size = file["original_size"]
                    compressed_size = file["compressed_size"]

                    if original_size > 0:
                        reduction = ((original_size - compressed_size) / original_size) * 100
                    else:
                        reduction = 0

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.write(file["filename"])

                    with col2:
                        st.write(f"Original: {format_size(original_size)}")

                    with col3:
                        st.write(f"Compressed: {format_size(compressed_size)}")

                    with col4:
                        st.write(f"Reduction: {reduction:.2f}%")

                    st.download_button(
                        label=f"Download {file['filename']}",
                        data=file["data"],
                        file_name=file["filename"],
                        mime="application/pdf"
                    )

                    st.divider()

                zip_path = temp_dir / "compressed_pdfs.zip"

                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for file in compressed_files:
                        zip_file.writestr(file["filename"], file["data"])

                with open(zip_path, "rb") as zip_file:
                    zip_data = zip_file.read()

                st.download_button(
                    label="Download All PDFs as ZIP",
                    data=zip_data,
                    file_name="compressed_pdfs.zip",
                    mime="application/zip"
                )

else:
    st.warning("Please upload one or more PDF files.")