import streamlit as st
from PIL import Image
import io
import os
import zipfile

# --------------------------------------------------
# Page settings
# --------------------------------------------------
st.set_page_config(
    page_title="Batch Image Resizer and Compressor",
    page_icon="🖼️",
    layout="wide"
)

st.title("🖼️ Batch Image Resizer and Compressor")
st.write("Upload multiple images, resize/compress them in one click, and download all images as a ZIP file.")

# --------------------------------------------------
# Supported formats
# --------------------------------------------------
SUPPORTED_TYPES = ["jpg", "jpeg", "png", "webp", "bmp", "tiff"]

# --------------------------------------------------
# Upload multiple images
# --------------------------------------------------
uploaded_files = st.file_uploader(
    "Upload Multiple Images",
    type=SUPPORTED_TYPES,
    accept_multiple_files=True
)

# --------------------------------------------------
# Sidebar settings
# --------------------------------------------------
st.sidebar.header("Resize and Compression Settings")

preset_options = {
    "Custom Size": None,
    "Thumbnail - 150 x 150": (150, 150),
    "Small - 300 x 300": (300, 300),
    "Medium - 600 x 600": (600, 600),
    "Large - 1024 x 1024": (1024, 1024),
    "HD - 1280 x 720": (1280, 720),
    "Full HD - 1920 x 1080": (1920, 1080),
    "Instagram Post - 1080 x 1080": (1080, 1080),
    "Facebook Cover - 1640 x 924": (1640, 924),
    "YouTube Thumbnail - 1280 x 720": (1280, 720),
    "Passport Size - 413 x 531": (413, 531)
}

preset_choice = st.sidebar.selectbox(
    "Choose Image Dimensions",
    list(preset_options.keys())
)

custom_width = st.sidebar.number_input(
    "Custom Width",
    min_value=1,
    max_value=10000,
    value=600
)

custom_height = st.sidebar.number_input(
    "Custom Height",
    min_value=1,
    max_value=10000,
    value=600
)

keep_aspect_ratio = st.sidebar.checkbox(
    "Keep Aspect Ratio",
    value=True
)

output_format = st.sidebar.selectbox(
    "Download Format",
    ["JPEG", "PNG", "WEBP", "BMP"]
)

compression_mode = st.sidebar.radio(
    "Compression Mode",
    [
        "Resize only",
        "Compress by quality",
        "Compress to target KB"
    ]
)

quality = st.sidebar.slider(
    "Image Quality",
    min_value=5,
    max_value=100,
    value=85
)

target_kb = st.sidebar.number_input(
    "Target Size Per Image in KB",
    min_value=1,
    max_value=5000,
    value=50,
    step=1
)

allow_auto_resize = st.sidebar.checkbox(
    "Automatically reduce dimensions if needed",
    value=True
)

preview_limit = st.sidebar.slider(
    "Preview Images",
    min_value=1,
    max_value=20,
    value=5
)

# --------------------------------------------------
# Resize function
# --------------------------------------------------
def resize_image(image, width, height, keep_ratio=True):
    original_width, original_height = image.size

    if keep_ratio:
        ratio = min(width / original_width, height / original_height)
        new_width = max(1, int(original_width * ratio))
        new_height = max(1, int(original_height * ratio))
        resized_img = image.resize((new_width, new_height), Image.LANCZOS)
    else:
        resized_img = image.resize((width, height), Image.LANCZOS)

    return resized_img


# --------------------------------------------------
# Save image to bytes
# --------------------------------------------------
def save_image_to_bytes(image, output_format, quality=85):
    img_bytes = io.BytesIO()

    if output_format == "JPEG":
        image = image.convert("RGB")
        image.save(
            img_bytes,
            format="JPEG",
            quality=quality,
            optimize=True
        )

    elif output_format == "WEBP":
        image = image.convert("RGB")
        image.save(
            img_bytes,
            format="WEBP",
            quality=quality,
            optimize=True
        )

    elif output_format == "PNG":
        image.save(
            img_bytes,
            format="PNG",
            optimize=True
        )

    elif output_format == "BMP":
        image = image.convert("RGB")
        image.save(
            img_bytes,
            format="BMP"
        )

    img_bytes.seek(0)
    return img_bytes


# --------------------------------------------------
# Compress image to target KB
# --------------------------------------------------
def compress_to_target_size(image, output_format, target_kb, allow_auto_resize=True):
    target_bytes = target_kb * 1024
    working_image = image.copy()

    # JPEG or WEBP is better for very small file sizes
    if output_format in ["PNG", "BMP"]:
        output_format = "JPEG"

    min_quality = 5
    max_quality = 95

    best_bytes = None
    best_quality = None
    best_image = working_image.copy()

    for resize_attempt in range(25):
        low = min_quality
        high = max_quality

        while low <= high:
            mid_quality = (low + high) // 2

            img_bytes = save_image_to_bytes(
                working_image,
                output_format,
                quality=mid_quality
            )

            current_size = len(img_bytes.getvalue())

            if current_size <= target_bytes:
                best_bytes = img_bytes
                best_quality = mid_quality
                best_image = working_image.copy()
                low = mid_quality + 1
            else:
                high = mid_quality - 1

        if best_bytes is not None:
            return best_image, best_bytes, best_quality, output_format

        if not allow_auto_resize:
            img_bytes = save_image_to_bytes(
                working_image,
                output_format,
                quality=min_quality
            )
            return working_image, img_bytes, min_quality, output_format

        width, height = working_image.size
        new_width = int(width * 0.85)
        new_height = int(height * 0.85)

        if new_width < 20 or new_height < 20:
            img_bytes = save_image_to_bytes(
                working_image,
                output_format,
                quality=min_quality
            )
            return working_image, img_bytes, min_quality, output_format

        working_image = working_image.resize(
            (new_width, new_height),
            Image.LANCZOS
        )

    img_bytes = save_image_to_bytes(
        working_image,
        output_format,
        quality=min_quality
    )

    return working_image, img_bytes, min_quality, output_format


# --------------------------------------------------
# Process single image
# --------------------------------------------------
def process_single_image(uploaded_file):
    image = Image.open(uploaded_file)

    if preset_options[preset_choice] is not None:
        selected_width, selected_height = preset_options[preset_choice]
    else:
        selected_width, selected_height = custom_width, custom_height

    resized_image = resize_image(
        image,
        selected_width,
        selected_height,
        keep_aspect_ratio
    )

    final_quality = quality
    final_format = output_format

    if compression_mode == "Resize only":
        output_bytes = save_image_to_bytes(
            resized_image,
            output_format,
            quality=quality
        )
        final_image = resized_image

    elif compression_mode == "Compress by quality":
        output_bytes = save_image_to_bytes(
            resized_image,
            output_format,
            quality=quality
        )
        final_image = resized_image

    else:
        final_image, output_bytes, final_quality, final_format = compress_to_target_size(
            resized_image,
            output_format,
            target_kb,
            allow_auto_resize
        )

    return {
        "original_name": uploaded_file.name,
        "original_size_kb": uploaded_file.size / 1024,
        "original_dimensions": image.size,
        "final_image": final_image,
        "final_bytes": output_bytes,
        "final_size_kb": len(output_bytes.getvalue()) / 1024,
        "final_dimensions": final_image.size,
        "final_quality": final_quality,
        "final_format": final_format
    }


# --------------------------------------------------
# Main app
# --------------------------------------------------
if uploaded_files:
    st.success(f"{len(uploaded_files)} image(s) uploaded successfully.")

    st.subheader("Uploaded Images")
    st.write("You can now resize/compress all images in a single click.")

    process_button = st.button("🚀 Resize and Compress All Images")

    if process_button:
        processed_results = []
        zip_buffer = io.BytesIO()

        progress_bar = st.progress(0)
        status_text = st.empty()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for index, uploaded_file in enumerate(uploaded_files):
                try:
                    result = process_single_image(uploaded_file)
                    processed_results.append(result)

                    original_name_without_ext = os.path.splitext(result["original_name"])[0]
                    extension = result["final_format"].lower()

                    output_file_name = f"{original_name_without_ext}_resized.{extension}"

                    zip_file.writestr(
                        output_file_name,
                        result["final_bytes"].getvalue()
                    )

                    progress = (index + 1) / len(uploaded_files)
                    progress_bar.progress(progress)
                    status_text.write(
                        f"Processing {index + 1} of {len(uploaded_files)} images..."
                    )

                except Exception as e:
                    st.error(f"Error processing {uploaded_file.name}: {e}")

        zip_buffer.seek(0)

        st.success("All images processed successfully!")

        # --------------------------------------------------
        # Summary table
        # --------------------------------------------------
        st.subheader("Processing Summary")

        summary_data = []

        for result in processed_results:
            summary_data.append({
                "File Name": result["original_name"],
                "Original Size KB": round(result["original_size_kb"], 2),
                "Final Size KB": round(result["final_size_kb"], 2),
                "Original Dimensions": f"{result['original_dimensions'][0]} x {result['original_dimensions'][1]}",
                "Final Dimensions": f"{result['final_dimensions'][0]} x {result['final_dimensions'][1]}",
                "Final Format": result["final_format"],
                "Final Quality": result["final_quality"]
            })

        st.dataframe(summary_data, use_container_width=True)

        # --------------------------------------------------
        # Download ZIP
        # --------------------------------------------------
        st.download_button(
            label="⬇️ Download All Resized Images as ZIP",
            data=zip_buffer,
            file_name="resized_images.zip",
            mime="application/zip"
        )

        # --------------------------------------------------
        # Preview processed images
        # --------------------------------------------------
        st.subheader("Preview Processed Images")

        for result in processed_results[:preview_limit]:
            col1, col2 = st.columns([1, 2])

            with col1:
                st.image(
                    result["final_image"],
                    caption=result["original_name"],
                    use_container_width=True
                )

            with col2:
                st.write(f"**Original Size:** {result['original_size_kb']:.2f} KB")
                st.write(f"**Final Size:** {result['final_size_kb']:.2f} KB")
                st.write(
                    f"**Original Dimensions:** "
                    f"{result['original_dimensions'][0]} x {result['original_dimensions'][1]}"
                )
                st.write(
                    f"**Final Dimensions:** "
                    f"{result['final_dimensions'][0]} x {result['final_dimensions'][1]}"
                )
                st.write(f"**Final Format:** {result['final_format']}")

else:
    st.info("Please upload multiple images to start.")