import streamlit as st
import pandas as pd
from PIL import Image
from pathlib import Path
from skimage.metrics import structural_similarity as ssim
from skimage.transform import resize
import numpy as np
import uuid
import os
from datetime import datetime

# Website search library
try:
    from ddgs import DDGS
except Exception:
    DDGS = None


# -----------------------------
# Folder Setup
# -----------------------------
BASE_DIR = Path(__file__).parent
DESIGN_DIR = BASE_DIR / "designs"
DATA_DIR = BASE_DIR / "data"
EXCEL_FILE = DATA_DIR / "dress_designs.xlsx"

DESIGN_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)


# -----------------------------
# Page Setting
# -----------------------------
st.set_page_config(
    page_title="Dress Design Finder App",
    page_icon="👗",
    layout="wide"
)


# -----------------------------
# Required Columns
# -----------------------------
REQUIRED_COLUMNS = [
    "Design_ID",
    "Title",
    "Gender",
    "Category",
    "Style",
    "Fabric",
    "Season",
    "Color",
    "Price",
    "Keywords",
    "Description",
    "Image_Path",
    "Date_Added"
]


# -----------------------------
# Database Functions
# -----------------------------
def create_database():
    if not EXCEL_FILE.exists():
        df = pd.DataFrame(columns=REQUIRED_COLUMNS)
        df.to_excel(EXCEL_FILE, index=False)


def load_data():
    create_database()
    df = pd.read_excel(EXCEL_FILE)

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df = df[REQUIRED_COLUMNS]
    return df


def save_data(df):
    df.to_excel(EXCEL_FILE, index=False)


# -----------------------------
# Image Functions
# -----------------------------
def save_uploaded_image(uploaded_file):
    extension = uploaded_file.name.split(".")[-1]
    unique_name = f"{uuid.uuid4()}.{extension}"
    image_path = DESIGN_DIR / unique_name

    with open(image_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return str(image_path)


def image_to_array(image_path, size=(250, 250)):
    img = Image.open(image_path).convert("L")
    img = np.array(img)
    img = resize(img, size, anti_aliasing=True)
    return img


def calculate_similarity(reference_image, design_image_path):
    try:
        ref_img = reference_image.convert("L")
        ref_img = np.array(ref_img)
        ref_img = resize(ref_img, (250, 250), anti_aliasing=True)

        design_img = image_to_array(design_image_path)

        score = ssim(ref_img, design_img, data_range=1.0)
        return round(score * 100, 2)
    except Exception:
        return 0


def download_image_button(image_path, button_text):
    if os.path.exists(str(image_path)):
        with open(image_path, "rb") as file:
            st.download_button(
                label=button_text,
                data=file,
                file_name=os.path.basename(image_path),
                mime="image/jpeg"
            )


# -----------------------------
# Local Search Function
# -----------------------------
def search_designs(df, query, gender, category, style, fabric, color):
    result = df.copy()

    if gender != "All":
        result = result[result["Gender"].astype(str) == gender]

    if category != "All":
        result = result[result["Category"].astype(str) == category]

    if style != "All":
        result = result[result["Style"].astype(str) == style]

    if fabric != "All":
        result = result[result["Fabric"].astype(str) == fabric]

    if color.strip() != "":
        result = result[
            result["Color"].astype(str).str.lower().str.contains(color.lower(), na=False)
        ]

    if query.strip() != "":
        query = query.lower()

        result = result[
            result["Title"].astype(str).str.lower().str.contains(query, na=False) |
            result["Gender"].astype(str).str.lower().str.contains(query, na=False) |
            result["Category"].astype(str).str.lower().str.contains(query, na=False) |
            result["Style"].astype(str).str.lower().str.contains(query, na=False) |
            result["Fabric"].astype(str).str.lower().str.contains(query, na=False) |
            result["Season"].astype(str).str.lower().str.contains(query, na=False) |
            result["Color"].astype(str).str.lower().str.contains(query, na=False) |
            result["Keywords"].astype(str).str.lower().str.contains(query, na=False) |
            result["Description"].astype(str).str.lower().str.contains(query, na=False)
        ]

    return result


# -----------------------------
# Website Search Function
# -----------------------------
def search_websites(search_query, max_results=10):
    if DDGS is None:
        return []

    results = []

    try:
        with DDGS() as ddgs:
            for item in ddgs.text(
                search_query,
                region="wt-wt",
                safesearch="moderate",
                max_results=max_results
            ):
                results.append({
                    "title": item.get("title", "No title"),
                    "link": item.get("href", ""),
                    "body": item.get("body", "")
                })
    except Exception as e:
        st.error(f"Website search error: {e}")

    return results


def search_website_images(search_query, max_results=12):
    if DDGS is None:
        return []

    images = []

    try:
        with DDGS() as ddgs:
            for item in ddgs.images(
                search_query,
                region="wt-wt",
                safesearch="moderate",
                max_results=max_results
            ):
                images.append({
                    "title": item.get("title", "Dress Design"),
                    "image": item.get("image", ""),
                    "url": item.get("url", "")
                })
    except Exception as e:
        st.error(f"Website image search error: {e}")

    return images


# -----------------------------
# Display Local Design
# -----------------------------
def display_design(row, show_similarity=False):
    with st.container():
        col1, col2 = st.columns([1, 2])

        with col1:
            if os.path.exists(str(row["Image_Path"])):
                st.image(row["Image_Path"], use_container_width=True)
            else:
                st.warning("Image not found.")

        with col2:
            st.subheader(str(row["Title"]))

            if show_similarity:
                st.success(f"Similarity Score: {row['Similarity']}%")

            st.write(f"**Gender:** {row['Gender']}")
            st.write(f"**Category:** {row['Category']}")
            st.write(f"**Style:** {row['Style']}")
            st.write(f"**Fabric:** {row['Fabric']}")
            st.write(f"**Season:** {row['Season']}")
            st.write(f"**Color:** {row['Color']}")
            st.write(f"**Price:** Rs. {row['Price']}")
            st.write(f"**Keywords:** {row['Keywords']}")
            st.write(f"**Description:** {row['Description']}")

            download_image_button(row["Image_Path"], "⬇️ Download This Design")

        st.divider()


# -----------------------------
# Load Database
# -----------------------------
df = load_data()


# -----------------------------
# App Title
# -----------------------------
st.title("👗 Dress Design Finder and Recommendation App")
st.write("For tailors, boutiques, fashion designers, customers, and online dress design searching.")


# -----------------------------
# Sidebar
# -----------------------------
menu = st.sidebar.radio(
    "Choose Option",
    [
        "🏠 Home",
        "➕ Add New Design",
        "🔎 Search Saved Designs",
        "📸 Search by Image",
        "🌐 Search Designs from Websites",
        "📊 View Database",
        "🗑️ Delete Design"
    ]
)


# -----------------------------
# Home Page
# -----------------------------
if menu == "🏠 Home":
    st.header("Welcome to Dress Design App")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Saved Designs", len(df))

    with col2:
        st.metric("Male Designs", len(df[df["Gender"] == "Male"]))

    with col3:
        st.metric("Female Designs", len(df[df["Gender"] == "Female"]))

    st.info("""
    This app has three main search systems:

    1. Search saved designs from your own database.
    2. Upload a picture and find similar saved designs.
    3. Search latest dress designs from websites.
    """)


# -----------------------------
# Add New Design
# -----------------------------
elif menu == "➕ Add New Design":
    st.header("➕ Add New Dress Design")

    with st.form("add_design_form"):
        title = st.text_input("Design Title", placeholder="Example: Black Embroidered Kurta")

        gender = st.selectbox("Gender", ["Male", "Female"])

        category = st.selectbox(
            "Category",
            [
                "Shalwar Kameez",
                "Kurta Pajama",
                "Waistcoat Suit",
                "Pathani Suit",
                "Prince Coat",
                "Sherwani",
                "Casual Kurta",
                "Formal Kurta",
                "Lawn Suit",
                "Embroidered Suit",
                "Anarkali",
                "Gharara",
                "Sharara",
                "Palazzo Suit",
                "Farshi Salwar",
                "Bridal Dress",
                "Party Wear",
                "Other"
            ]
        )

        style = st.selectbox(
            "Style",
            [
                "Simple",
                "Modern",
                "Traditional",
                "Formal",
                "Casual",
                "Wedding",
                "Party Wear",
                "Luxury",
                "Trendy",
                "Other"
            ]
        )

        fabric = st.selectbox(
            "Fabric",
            [
                "Cotton",
                "Lawn",
                "Wash & Wear",
                "Khaddar",
                "Silk",
                "Chiffon",
                "Organza",
                "Velvet",
                "Linen",
                "Boski",
                "Karandi",
                "Other"
            ]
        )

        season = st.selectbox(
            "Season",
            ["Summer", "Winter", "Spring", "Autumn", "All Season"]
        )

        color = st.text_input("Color", placeholder="Example: Black, White, Red, Green")

        price = st.number_input("Price", min_value=0, step=100)

        keywords = st.text_input(
            "Search Keywords",
            placeholder="Example: black kurta male formal wedding embroidered"
        )

        description = st.text_area(
            "Description",
            placeholder="Write neck design, sleeves, embroidery, trouser style, dupatta style, etc."
        )

        uploaded_image = st.file_uploader(
            "Upload Dress Image",
            type=["jpg", "jpeg", "png"]
        )

        save_button = st.form_submit_button("✅ Save Design")

    if save_button:
        if title.strip() == "":
            st.error("Please write design title.")
        elif uploaded_image is None:
            st.error("Please upload design image.")
        else:
            image_path = save_uploaded_image(uploaded_image)

            new_data = {
                "Design_ID": str(uuid.uuid4())[:8],
                "Title": title,
                "Gender": gender,
                "Category": category,
                "Style": style,
                "Fabric": fabric,
                "Season": season,
                "Color": color,
                "Price": price,
                "Keywords": keywords,
                "Description": description,
                "Image_Path": image_path,
                "Date_Added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
            save_data(df)

            st.success("Design saved successfully!")
            st.image(image_path, width=300)


# -----------------------------
# Search Saved Designs
# -----------------------------
elif menu == "🔎 Search Saved Designs":
    st.header("🔎 Search Designs from Your Saved Database")

    if df.empty:
        st.warning("No designs found. First add some designs.")
    else:
        with st.form("search_form"):
            query = st.text_input(
                "Write Search Word",
                placeholder="Example: black kurta, female bridal, lawn suit, sherwani"
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                gender = st.selectbox("Gender", ["All", "Male", "Female"])

            with col2:
                category = st.selectbox(
                    "Category",
                    ["All"] + sorted(df["Category"].dropna().astype(str).unique().tolist())
                )

            with col3:
                style = st.selectbox(
                    "Style",
                    ["All"] + sorted(df["Style"].dropna().astype(str).unique().tolist())
                )

            col4, col5 = st.columns(2)

            with col4:
                fabric = st.selectbox(
                    "Fabric",
                    ["All"] + sorted(df["Fabric"].dropna().astype(str).unique().tolist())
                )

            with col5:
                color = st.text_input("Color", placeholder="Example: black, red, white")

            search_button = st.form_submit_button("🔍 Search Now")

        if search_button:
            result = search_designs(df, query, gender, category, style, fabric, color)

            st.success(f"{len(result)} design(s) found.")

            if result.empty:
                st.warning("No matching design found.")
            else:
                for index, row in result.iterrows():
                    display_design(row)

        if st.button("🔄 Show All Saved Designs"):
            st.success(f"Showing all {len(df)} designs.")
            for index, row in df.iterrows():
                display_design(row)


# -----------------------------
# Search by Image
# -----------------------------
elif menu == "📸 Search by Image":
    st.header("📸 Search Similar Saved Dress by Uploading Image")

    if df.empty:
        st.warning("No designs found. First add some designs.")
    else:
        with st.form("image_search_form"):
            reference_file = st.file_uploader(
                "Upload Reference Dress Picture",
                type=["jpg", "jpeg", "png"]
            )

            gender_choice = st.selectbox(
                "Search In",
                ["All", "Male", "Female"]
            )

            top_n = st.slider("How many similar designs?", 1, 10, 5)

            image_search_button = st.form_submit_button("📸 Find Similar Designs")

        if image_search_button:
            if reference_file is None:
                st.error("Please upload a reference image first.")
            else:
                reference_image = Image.open(reference_file).convert("RGB")

                st.subheader("Your Uploaded Reference Image")
                st.image(reference_image, width=300)

                result_df = df.copy()

                if gender_choice != "All":
                    result_df = result_df[result_df["Gender"] == gender_choice]

                similarity_scores = []

                for index, row in result_df.iterrows():
                    image_path = row["Image_Path"]

                    if os.path.exists(str(image_path)):
                        score = calculate_similarity(reference_image, image_path)
                    else:
                        score = 0

                    similarity_scores.append(score)

                result_df = result_df.copy()
                result_df["Similarity"] = similarity_scores
                result_df = result_df.sort_values(by="Similarity", ascending=False).head(top_n)

                st.success(f"{len(result_df)} similar design(s) found.")

                for index, row in result_df.iterrows():
                    display_design(row, show_similarity=True)


# -----------------------------
# Website Search
# -----------------------------
elif menu == "🌐 Search Designs from Websites":
    st.header("🌐 Search Latest Dress Designs from Websites")

    st.write("""
    Use this option to search latest dress designs from online websites.
    Example searches:
    - latest male shalwar kameez design 2026
    - latest female bridal dress design
    - Pakistani lawn suit design
    - latest kurta design for men
    - latest party wear dress for women
    """)

    if DDGS is None:
        st.error("The ddgs library is not installed. Please run: pip install ddgs")
    else:
        with st.form("website_search_form"):
            web_query = st.text_input(
                "Search Online Dress Designs",
                placeholder="Example: latest Pakistani female bridal dress design"
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                gender_web = st.selectbox(
                    "Gender",
                    ["Any", "Male", "Female"]
                )

            with col2:
                design_type = st.selectbox(
                    "Design Type",
                    [
                        "Any",
                        "Shalwar Kameez",
                        "Kurta",
                        "Sherwani",
                        "Waistcoat",
                        "Lawn Suit",
                        "Bridal Dress",
                        "Party Wear",
                        "Gharara",
                        "Sharara",
                        "Anarkali",
                        "Farshi Salwar"
                    ]
                )

            with col3:
                result_count = st.slider(
                    "Number of Results",
                    5,
                    20,
                    10
                )

            search_mode = st.radio(
                "Search Mode",
                ["Website Links", "Image Designs"]
            )

            web_search_button = st.form_submit_button("🌐 Search from Websites")

        if web_search_button:
            if web_query.strip() == "":
                st.error("Please write something to search.")
            else:
                final_query = web_query

                if gender_web != "Any":
                    final_query += f" {gender_web}"

                if design_type != "Any":
                    final_query += f" {design_type}"

                final_query += " dress design fashion tailor boutique"

                st.info(f"Searching for: {final_query}")

                if search_mode == "Website Links":
                    web_results = search_websites(final_query, result_count)

                    if len(web_results) == 0:
                        st.warning("No website results found. Try different search words.")
                    else:
                        st.success(f"{len(web_results)} website result(s) found.")

                        for i, item in enumerate(web_results, start=1):
                            st.subheader(f"{i}. {item['title']}")
                            st.write(item["body"])

                            if item["link"]:
                                st.link_button("Open Website", item["link"])

                            st.divider()

                elif search_mode == "Image Designs":
                    image_results = search_website_images(final_query, result_count)

                    if len(image_results) == 0:
                        st.warning("No image results found. Try different search words.")
                    else:
                        st.success(f"{len(image_results)} image design result(s) found.")

                        cols = st.columns(3)

                        for i, item in enumerate(image_results):
                            with cols[i % 3]:
                                if item["image"]:
                                    st.image(item["image"], use_container_width=True)

                                st.caption(item["title"])

                                if item["url"]:
                                    st.link_button("Open Source Website", item["url"])

                                st.divider()

        st.warning("""
        Note: Designs found from websites may be copyrighted.
        For business use, take permission or use them only as inspiration.
        """)


# -----------------------------
# View Database
# -----------------------------
elif menu == "📊 View Database":
    st.header("📊 Dress Design Database")

    if df.empty:
        st.warning("No data available.")
    else:
        st.dataframe(df, use_container_width=True)

        csv_data = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="⬇️ Download Database CSV",
            data=csv_data,
            file_name="dress_design_database.csv",
            mime="text/csv"
        )


# -----------------------------
# Delete Design
# -----------------------------
elif menu == "🗑️ Delete Design":
    st.header("🗑️ Delete Design")

    if df.empty:
        st.warning("No designs available.")
    else:
        design_list = df["Design_ID"].astype(str) + " - " + df["Title"].astype(str)

        selected_design = st.selectbox("Select Design", design_list)

        selected_id = selected_design.split(" - ")[0]

        selected_row = df[df["Design_ID"] == selected_id]

        if not selected_row.empty:
            row = selected_row.iloc[0]

            display_design(row)

            if st.button("❌ Delete Selected Design"):
                image_path = row["Image_Path"]

                if os.path.exists(str(image_path)):
                    os.remove(image_path)

                df = df[df["Design_ID"] != selected_id]
                save_data(df)

                st.success("Design deleted successfully. Please refresh the page.")