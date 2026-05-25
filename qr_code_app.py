import streamlit as st
import qrcode
from io import BytesIO
from PIL import Image

st.set_page_config(
    page_title="Advanced QR Code Generator",
    page_icon="🔳",
    layout="centered"
)

st.title("🔳 Advanced QR Code Generator")
st.write("Generate colorful QR codes with custom size and download option.")

# Text or URL input
qr_text = st.text_area(
    "Enter text or URL:",
    placeholder="Example: https://www.google.com"
)

st.divider()

# QR settings
st.subheader("QR Code Settings")

box_size = st.slider(
    "QR Code Box Size",
    min_value=5,
    max_value=30,
    value=10
)

border_size = st.slider(
    "Border Size",
    min_value=1,
    max_value=10,
    value=4
)

# Two dimensional final size
st.subheader("Final Image Size")

image_width = st.number_input(
    "Image Width in Pixels",
    min_value=100,
    max_value=2000,
    value=500,
    step=50
)

image_height = st.number_input(
    "Image Height in Pixels",
    min_value=100,
    max_value=2000,
    value=500,
    step=50
)

st.divider()

# Color scheme options
st.subheader("Color Scheme")

color_scheme = st.selectbox(
    "Choose Color Scheme",
    [
        "Black on White",
        "Blue on White",
        "Red on White",
        "Green on White",
        "White on Black",
        "Custom Colors"
    ]
)

if color_scheme == "Black on White":
    fill_color = "black"
    back_color = "white"

elif color_scheme == "Blue on White":
    fill_color = "blue"
    back_color = "white"

elif color_scheme == "Red on White":
    fill_color = "red"
    back_color = "white"

elif color_scheme == "Green on White":
    fill_color = "green"
    back_color = "white"

elif color_scheme == "White on Black":
    fill_color = "white"
    back_color = "black"

else:
    fill_color = st.color_picker("Choose QR Code Color", "#000000")
    back_color = st.color_picker("Choose Background Color", "#FFFFFF")

st.divider()

# Generate QR Code
if st.button("Generate QR Code"):
    if qr_text.strip() == "":
        st.warning("Please enter text or URL first.")

    else:
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=box_size,
            border=border_size
        )

        qr.add_data(qr_text)
        qr.make(fit=True)

        img = qr.make_image(
            fill_color=fill_color,
            back_color=back_color
        ).convert("RGB")

        # Resize image according to width and height
        img = img.resize((int(image_width), int(image_height)))

        # Save image in memory
        img_buffer = BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        st.success("QR Code generated successfully!")

        st.subheader("Your QR Code")
        st.image(img, caption="Generated QR Code")

        st.download_button(
            label="Download QR Code",
            data=img_buffer,
            file_name="advanced_qr_code.png",
            mime="image/png"
        )