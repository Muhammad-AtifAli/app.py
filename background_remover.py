import streamlit as st
from PIL import Image
from io import BytesIO
import zipfile
import os


# ---------------- PAGE SETTINGS ----------------
st.set_page_config(
    page_title="Batch Image Background Remover",
    page_icon="🖼️",
    layout="wide"
)

st.title("🖼️ Batch Image Background Remover")
st.write("Upload multiple images, remove backgrounds, preview results, and download all images in one ZIP file.")


# ---------------- SESSION STATE ----------------
if "processed_images" not in st.session_state:
    st.session_state.processed_images = []


# ---------------- FUNCTIONS ----------------
@st.cache_resource
def load_rembg_model():
    from rembg import new_session
    return new_session("u2net")


def remove_background(image, session):
    from rembg import remove

    image = image.convert("RGBA")
    result = remove(image, session=session)
    return result


def add_solid_background(image, color):
    image = image.convert("RGBA")
    background = Image.new("RGBA", image.size, color)
    background.paste(image, mask=image.split()[3])
    return background.convert("RGB")


def image_to_png_bytes(image):
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


def create_zip_file(processed_images):
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_name, image_bytes in processed_images:
            zip_file.writestr(file_name, image_bytes)

    zip_buffer.seek(0)
    return zip_buffer.getvalue()


# ---------------- SIDEBAR SETTINGS ----------------
st.sidebar.header("⚙️ Settings")

background_choice = st.sidebar.radio(
    "Choose output background",
    [
        "Transparent Background",
        "White Background",
        "Custom Color Background"
    ]
)

custom_color = "#ffffff"

if background_choice == "Custom Color Background":
    custom_color = st.sidebar.color_picker("Choose background color", "#ffffff")

st.sidebar.info("Supported formats: PNG, JPG, JPEG, WEBP, BMP, TIFF")


# ---------------- UPLOAD MULTIPLE FILES ----------------
uploaded_files = st.file_uploader(
    "Upload multiple images",
    type=["png", "jpg", "jpeg", "webp", "bmp", "tiff"],
    accept_multiple_files=True
)


# ---------------- CLEAR BUTTON ----------------
if st.button("Clear Previous Results"):
    st.session_state.processed_images = []
    st.success("Previous results cleared.")


# ---------------- PROCESS IMAGES ----------------
if uploaded_files:
    st.success(f"{len(uploaded_files)} image(s) uploaded successfully.")

    if st.button("Remove Background From All Images"):
        st.session_state.processed_images = []

        with st.spinner("Loading AI background remover model. Please wait..."):
            session = load_rembg_model()

        progress_bar = st.progress(0)
        status_text = st.empty()

        for index, uploaded_file in enumerate(uploaded_files):
            try:
                status_text.write(
                    f"Processing {index + 1} of {len(uploaded_files)}: {uploaded_file.name}"
                )

                original_image = Image.open(uploaded_file)

                result_image = remove_background(original_image, session)

                if background_choice == "White Background":
                    result_image = add_solid_background(result_image, "white")

                elif background_choice == "Custom Color Background":
                    result_image = add_solid_background(result_image, custom_color)

                base_name = os.path.splitext(uploaded_file.name)[0]
                output_name = f"{base_name}_background_removed.png"

                image_bytes = image_to_png_bytes(result_image)

                st.session_state.processed_images.append(
                    (output_name, image_bytes)
                )

                progress_bar.progress((index + 1) / len(uploaded_files))

            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}")
                st.write(e)

        status_text.success("All images processed successfully.")


# ---------------- SHOW RESULTS ----------------
if st.session_state.processed_images:
    st.subheader("✅ Processed Images")

    for file_name, image_bytes in st.session_state.processed_images:
        with st.expander(file_name):
            st.image(image_bytes, use_container_width=True)

            st.download_button(
                label=f"⬇️ Download {file_name}",
                data=image_bytes,
                file_name=file_name,
                mime="image/png",
                key=f"single_{file_name}"
            )

    zip_bytes = create_zip_file(st.session_state.processed_images)

    st.download_button(
        label="⬇️ Download All Images as ZIP",
        data=zip_bytes,
        file_name="background_removed_images.zip",
        mime="application/zip",
        key="download_all_zip"
    )

else:
    st.info("Upload images and click the button to remove backgrounds.")