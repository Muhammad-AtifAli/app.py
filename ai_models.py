import streamlit as st
import pandas as pd
from huggingface_hub import list_models
from io import BytesIO

# -----------------------------
# Page Setting
# -----------------------------
st.set_page_config(
    page_title="AI Models Directory",
    page_icon="🤖",
    layout="wide"
)

# -----------------------------
# App Title
# -----------------------------
st.title("🤖 AI Models Directory")
st.write("Search and explore hundreds of AI models with clickable links.")

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.header("🔍 Search Options")

search_text = st.sidebar.text_input(
    "Search model name",
    placeholder="Example: gpt, llama, bert, whisper"
)

task_options = [
    "All",
    "text-generation",
    "text-classification",
    "question-answering",
    "translation",
    "summarization",
    "sentence-similarity",
    "fill-mask",
    "image-classification",
    "object-detection",
    "text-to-image",
    "image-to-text",
    "automatic-speech-recognition",
    "text-to-speech",
    "audio-classification"
]

selected_task = st.sidebar.selectbox(
    "Select AI task/category",
    task_options
)

sort_option = st.sidebar.selectbox(
    "Sort models by",
    ["downloads", "likes", "last_modified", "created_at", "trending_score"]
)

model_limit = st.sidebar.slider(
    "Number of models to show",
    min_value=50,
    max_value=500,
    value=100,
    step=50
)

# -----------------------------
# Famous AI Models
# -----------------------------
st.subheader("🌟 Famous AI Model Platforms")

famous_models = [
    {
        "Model / Platform": "OpenAI GPT Models",
        "Company": "OpenAI",
        "Type": "Text / Chat / Vision",
        "Link": "https://platform.openai.com/docs/models"
    },
    {
        "Model / Platform": "Google Gemini",
        "Company": "Google",
        "Type": "Multimodal AI",
        "Link": "https://ai.google.dev/gemini-api/docs/models"
    },
    {
        "Model / Platform": "Claude",
        "Company": "Anthropic",
        "Type": "Chat / Reasoning",
        "Link": "https://docs.anthropic.com/en/docs/about-claude/models"
    },
    {
        "Model / Platform": "Meta Llama",
        "Company": "Meta",
        "Type": "Open-source LLM",
        "Link": "https://www.llama.com/"
    },
    {
        "Model / Platform": "Mistral AI",
        "Company": "Mistral",
        "Type": "LLM",
        "Link": "https://docs.mistral.ai/getting-started/models/"
    },
    {
        "Model / Platform": "Hugging Face Models",
        "Company": "Hugging Face",
        "Type": "Model Hub",
        "Link": "https://huggingface.co/models"
    }
]

famous_df = pd.DataFrame(famous_models)

st.data_editor(
    famous_df,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Link": st.column_config.LinkColumn("Official Link")
    },
    disabled=True
)

# -----------------------------
# Fetch Models Function
# -----------------------------
@st.cache_data(ttl=300)
def fetch_models(search_query, task_filter, sort_by, limit):
    if search_query.strip() == "":
        search_query = None

    if task_filter == "All":
        task_filter = None

    try:
        models = list_models(
            search=search_query,
            filter=task_filter,
            sort=sort_by,
            limit=limit,
            full=True
        )
    except TypeError:
        models = list_models(
            search=search_query,
            filter=task_filter,
            limit=limit,
            full=True
        )

    data = []

    for model in models:
        model_id = getattr(model, "modelId", "")
        task = getattr(model, "pipeline_tag", "")
        downloads = getattr(model, "downloads", 0)
        likes = getattr(model, "likes", 0)
        tags = getattr(model, "tags", [])
        last_modified = getattr(model, "lastModified", "")

        data.append({
            "Model Name": model_id,
            "Task": task if task else "Not specified",
            "Downloads": downloads if downloads else 0,
            "Likes": likes if likes else 0,
            "Last Modified": str(last_modified).split(" ")[0] if last_modified else "",
            "Tags": ", ".join(tags[:5]) if tags else "",
            "Model Link": f"https://huggingface.co/{model_id}"
        })

    return pd.DataFrame(data)

# -----------------------------
# Load Button
# -----------------------------
st.write("---")

if st.button("🚀 Load AI Models", use_container_width=True):
    with st.spinner("Please wait. AI models are loading..."):
        try:
            df = fetch_models(
                search_text,
                selected_task,
                sort_option,
                model_limit
            )

            if df.empty:
                st.warning("No model found. Try another search word or select All category.")
            else:
                st.success(f"{len(df)} AI models loaded successfully!")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Total Models", len(df))

                with col2:
                    st.metric("Total Downloads", f"{int(df['Downloads'].sum()):,}")

                with col3:
                    st.metric("Total Likes", f"{int(df['Likes'].sum()):,}")

                st.subheader("📋 AI Models List")

                st.data_editor(
                    df,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "Model Link": st.column_config.LinkColumn("Open Model")
                    },
                    disabled=True
                )

                st.subheader("📊 Top Models by Downloads")

                chart_df = df.sort_values("Downloads", ascending=False).head(20)
                st.bar_chart(chart_df.set_index("Model Name")["Downloads"])

                # CSV download
                csv = df.to_csv(index=False).encode("utf-8")

                st.download_button(
                    label="⬇️ Download as CSV",
                    data=csv,
                    file_name="ai_models.csv",
                    mime="text/csv",
                    use_container_width=True
                )

                # Excel download
                excel_buffer = BytesIO()

                with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="AI Models")

                st.download_button(
                    label="⬇️ Download as Excel",
                    data=excel_buffer.getvalue(),
                    file_name="ai_models.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

        except Exception as e:
            st.error("Something went wrong.")
            st.code(str(e))

else:
    st.info("Click the **Load AI Models** button to fetch AI models.")

# -----------------------------
# Help Section
# -----------------------------
with st.expander("📘 How to Use"):
    st.write("""
    1. Write a model name such as gpt, llama, bert, whisper, or qwen.
    2. Select task/category.
    3. Select number of models.
    4. Click Load AI Models.
    5. Click model links to open them.
    6. Download the list as CSV or Excel.
    """)