import streamlit as st
import fitz  # PyMuPDF
import re
import io
import requests
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# -----------------------------
# Page Settings
# -----------------------------
st.set_page_config(
    page_title="Research Paper Summarizer & Chat",
    layout="wide"
)

st.title("📚 Research Paper Summarizer, Chat & Relationship Finder")
st.write(
    "Upload one or multiple research papers. Summarize sections, ask questions, "
    "and find relationships among papers."
)


# -----------------------------
# Helper Functions
# -----------------------------
def extract_text_from_pdf(uploaded_file):
    """Extract text from searchable PDF."""
    text = ""
    try:
        file_bytes = uploaded_file.read()
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")

        for page in pdf_document:
            page_text = page.get_text()
            text += page_text + "\n"

        return clean_text(text)

    except Exception as e:
        return f"Error extracting PDF text: {e}"


def extract_text_from_txt(uploaded_file):
    """Extract text from TXT file."""
    try:
        return clean_text(uploaded_file.read().decode("utf-8", errors="ignore"))
    except Exception as e:
        return f"Error extracting TXT text: {e}"


def clean_text(text):
    """Clean unnecessary spaces and line breaks."""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'Page\s+\d+', '', text, flags=re.IGNORECASE)
    return text.strip()


def split_into_sentences(text):
    """Simple sentence splitter."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
    return sentences


def extract_section(text, section_name):
    """
    Extract section using common research paper headings.
    This is flexible but not perfect because every paper has different heading styles.
    """

    section_patterns = {
        "Abstract": [
            r"\babstract\b"
        ],
        "Introduction": [
            r"\bintroduction\b"
        ],
        "Literature Review": [
            r"\bliterature review\b",
            r"\breview of literature\b",
            r"\brelated work\b",
            r"\bprevious studies\b"
        ],
        "Methodology": [
            r"\bmethodology\b",
            r"\bmethods\b",
            r"\bmaterials and methods\b",
            r"\bresearch method\b",
            r"\bresearch methodology\b"
        ],
        "Results": [
            r"\bresults\b",
            r"\bfindings\b"
        ],
        "Discussion": [
            r"\bdiscussion\b"
        ],
        "Conclusion": [
            r"\bconclusion\b",
            r"\bconclusions\b",
            r"\bsummary and conclusion\b"
        ],
        "References": [
            r"\breferences\b",
            r"\bbibliography\b",
            r"\bworks cited\b"
        ]
    }

    all_headings = []
    for sec, patterns in section_patterns.items():
        for pattern in patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                all_headings.append((match.start(), sec))

    if not all_headings:
        return ""

    all_headings = sorted(all_headings, key=lambda x: x[0])

    selected_positions = [
        index for index, item in enumerate(all_headings)
        if item[1] == section_name
    ]

    if not selected_positions:
        return ""

    selected_index = selected_positions[0]
    start_pos = all_headings[selected_index][0]

    if selected_index + 1 < len(all_headings):
        end_pos = all_headings[selected_index + 1][0]
    else:
        end_pos = len(text)

    section_text = text[start_pos:end_pos]

    return section_text.strip()


def extractive_summary(text, summary_sentences=5):
    """
    Summarize text using TF-IDF sentence scoring.
    No paid API is required.
    """
    sentences = split_into_sentences(text)

    if not sentences:
        return "No enough text found for summarization."

    if len(sentences) <= summary_sentences:
        return " ".join(sentences)

    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(sentences)

        sentence_scores = tfidf_matrix.sum(axis=1).A1
        ranked_indices = sentence_scores.argsort()[::-1]

        selected_indices = sorted(ranked_indices[:summary_sentences])
        summary = " ".join([sentences[i] for i in selected_indices])

        return summary

    except Exception as e:
        return f"Summarization error: {e}"


def chunk_text(text, chunk_size=900, overlap=150):
    """Split long text into chunks for question answering."""
    words = text.split()
    chunks = []

    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def retrieve_relevant_chunks(question, papers_data, top_k=5):
    """Find most relevant text chunks for user question."""
    chunks = []
    metadata = []

    for paper_name, text in papers_data.items():
        paper_chunks = chunk_text(text)
        for chunk in paper_chunks:
            chunks.append(chunk)
            metadata.append(paper_name)

    if not chunks:
        return []

    documents = chunks + [question]

    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform(documents)

    question_vector = vectors[-1]
    chunk_vectors = vectors[:-1]

    similarities = cosine_similarity(question_vector, chunk_vectors).flatten()
    top_indices = similarities.argsort()[::-1][:top_k]

    results = []
    for idx in top_indices:
        results.append({
            "paper": metadata[idx],
            "chunk": chunks[idx],
            "score": similarities[idx]
        })

    return results


def ask_ollama(question, context, model_name="llama3"):
    """
    Optional: Generate AI-style answer using Ollama.
    Ollama must be installed separately on your computer.
    """
    prompt = f"""
You are a research assistant. Answer the question only using the provided research paper context.

Question:
{question}

Context:
{context}

Answer clearly with academic style:
"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        if response.status_code == 200:
            return response.json().get("response", "No response from Ollama.")
        else:
            return "Ollama is not responding properly. Make sure Ollama is installed and running."

    except Exception:
        return "Ollama is not running. The app will show relevant paper chunks instead."


def calculate_paper_similarity(papers_data):
    """Calculate similarity among uploaded papers."""
    names = list(papers_data.keys())
    texts = list(papers_data.values())

    if len(texts) < 2:
        return None, None

    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(texts)

    similarity_matrix = cosine_similarity(tfidf_matrix)

    similarity_df = pd.DataFrame(
        similarity_matrix,
        index=names,
        columns=names
    )

    relationships = []

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            relationships.append({
                "Paper 1": names[i],
                "Paper 2": names[j],
                "Similarity Score": round(similarity_matrix[i][j], 3),
                "Relationship Level": relationship_level(similarity_matrix[i][j])
            })

    relationship_df = pd.DataFrame(relationships)

    return similarity_df, relationship_df


def relationship_level(score):
    """Convert similarity score into simple explanation."""
    if score >= 0.70:
        return "Very Strong Relationship"
    elif score >= 0.50:
        return "Strong Relationship"
    elif score >= 0.30:
        return "Moderate Relationship"
    elif score >= 0.15:
        return "Weak Relationship"
    else:
        return "Very Weak Relationship"


def draw_relationship_graph(relationship_df):
    """Draw graph of paper relationships."""
    if relationship_df is None or relationship_df.empty:
        st.info("No relationship graph available.")
        return

    G = nx.Graph()

    for _, row in relationship_df.iterrows():
        if row["Similarity Score"] >= 0.15:
            G.add_edge(
                row["Paper 1"],
                row["Paper 2"],
                weight=row["Similarity Score"]
            )

    if len(G.nodes) == 0:
        st.warning("Similarity is too low to create a meaningful graph.")
        return

    plt.figure(figsize=(10, 6))
    pos = nx.spring_layout(G, seed=42)

    weights = [G[u][v]["weight"] * 5 for u, v in G.edges()]

    nx.draw(
        G,
        pos,
        with_labels=True,
        node_size=2500,
        font_size=8,
        width=weights
    )

    edge_labels = nx.get_edge_attributes(G, "weight")
    edge_labels = {k: round(v, 2) for k, v in edge_labels.items()}

    nx.draw_networkx_edge_labels(
        G,
        pos,
        edge_labels=edge_labels,
        font_size=8
    )

    st.pyplot(plt)


# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("⚙️ Settings")

summary_length = st.sidebar.slider(
    "Summary Length",
    min_value=3,
    max_value=15,
    value=6,
    help="Number of important sentences in summary"
)

top_k_chunks = st.sidebar.slider(
    "Relevant Chunks for Chat",
    min_value=3,
    max_value=10,
    value=5
)

use_ollama = st.sidebar.checkbox(
    "Use Ollama for AI-style answers",
    value=False
)

ollama_model = st.sidebar.text_input(
    "Ollama Model Name",
    value="llama3"
)


# -----------------------------
# File Upload
# -----------------------------
uploaded_files = st.file_uploader(
    "Upload Research Papers",
    type=["pdf", "txt"],
    accept_multiple_files=True
)

papers_data = {}

if uploaded_files:
    with st.spinner("Extracting text from uploaded papers..."):
        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name

            if file_name.lower().endswith(".pdf"):
                text = extract_text_from_pdf(uploaded_file)
            elif file_name.lower().endswith(".txt"):
                text = extract_text_from_txt(uploaded_file)
            else:
                text = ""

            if text and not text.lower().startswith("error"):
                papers_data[file_name] = text

    st.success(f"{len(papers_data)} paper(s) processed successfully.")


# -----------------------------
# Main Tabs
# -----------------------------
if papers_data:

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📄 Paper Overview",
        "📝 Section Summarizer",
        "💬 Chat with Papers",
        "🔗 Paper Relationships",
        "⬇️ Download Results"
    ])

    # -------------------------
    # Tab 1: Paper Overview
    # -------------------------
    with tab1:
        st.header("📄 Uploaded Paper Overview")

        overview_data = []

        for paper_name, text in papers_data.items():
            word_count = len(text.split())
            char_count = len(text)

            overview_data.append({
                "Paper Name": paper_name,
                "Words": word_count,
                "Characters": char_count
            })

        st.dataframe(pd.DataFrame(overview_data), use_container_width=True)

        selected_paper_overview = st.selectbox(
            "Select paper to preview text",
            list(papers_data.keys())
        )

        st.text_area(
            "Extracted Text Preview",
            papers_data[selected_paper_overview][:5000],
            height=300
        )

    # -------------------------
    # Tab 2: Section Summarizer
    # -------------------------
    with tab2:
        st.header("📝 Summarize Different Sections of Research Paper")

        selected_paper = st.selectbox(
            "Select Paper",
            list(papers_data.keys()),
            key="summary_paper"
        )

        section_name = st.selectbox(
            "Select Section",
            [
                "Abstract",
                "Introduction",
                "Literature Review",
                "Methodology",
                "Results",
                "Discussion",
                "Conclusion",
                "References"
            ]
        )

        if st.button("Generate Section Summary"):
            full_text = papers_data[selected_paper]
            section_text = extract_section(full_text, section_name)

            if section_text:
                summary = extractive_summary(section_text, summary_length)

                st.subheader(f"Summary of {section_name}")
                st.write(summary)

                with st.expander("View Extracted Section Text"):
                    st.write(section_text[:10000])

            else:
                st.warning(
                    f"{section_name} section was not clearly found. "
                    "Try selecting another section or use full paper summary."
                )

        if st.button("Generate Full Paper Summary"):
            full_text = papers_data[selected_paper]
            summary = extractive_summary(full_text, summary_length + 4)

            st.subheader("Full Paper Summary")
            st.write(summary)

    # -------------------------
    # Tab 3: Chat with Papers
    # -------------------------
    with tab3:
        st.header("💬 Talk with Your Research Papers")

        question = st.text_input(
            "Ask a question from uploaded papers",
            placeholder="Example: What is the research gap in these papers?"
        )

        if st.button("Ask Question"):
            if question.strip():
                relevant_chunks = retrieve_relevant_chunks(
                    question,
                    papers_data,
                    top_k=top_k_chunks
                )

                if relevant_chunks:
                    combined_context = "\n\n".join(
                        [
                            f"Paper: {item['paper']}\n{item['chunk']}"
                            for item in relevant_chunks
                        ]
                    )

                    if use_ollama:
                        answer = ask_ollama(
                            question,
                            combined_context,
                            model_name=ollama_model
                        )

                        st.subheader("AI Answer")
                        st.write(answer)

                    else:
                        st.subheader("Relevant Answer Material from Papers")
                        st.info(
                            "This mode does not generate a full AI answer. "
                            "It shows the most relevant chunks from your papers."
                        )

                    st.subheader("Most Relevant Paper Chunks")

                    for i, item in enumerate(relevant_chunks, start=1):
                        with st.expander(
                            f"{i}. {item['paper']} | Relevance: {round(item['score'], 3)}"
                        ):
                            st.write(item["chunk"])

                else:
                    st.warning("No relevant information found.")

            else:
                st.warning("Please write a question first.")

    # -------------------------
    # Tab 4: Paper Relationships
    # -------------------------
    with tab4:
        st.header("🔗 Relationship Among Research Papers")

        if len(papers_data) < 2:
            st.warning("Upload at least two papers to find relationships.")
        else:
            similarity_df, relationship_df = calculate_paper_similarity(papers_data)

            st.subheader("Similarity Matrix")
            st.dataframe(similarity_df, use_container_width=True)

            st.subheader("Relationship Table")
            st.dataframe(relationship_df, use_container_width=True)

            st.subheader("Relationship Graph")
            draw_relationship_graph(relationship_df)

            st.info(
                "Higher similarity means the papers share more common vocabulary, "
                "themes, concepts, or research focus."
            )

    # -------------------------
    # Tab 5: Download Results
    # -------------------------
    with tab5:
        st.header("⬇️ Download Summaries and Relationship Results")

        all_summaries = []

        for paper_name, text in papers_data.items():
            full_summary = extractive_summary(text, summary_length + 4)

            all_summaries.append({
                "Paper Name": paper_name,
                "Full Summary": full_summary
            })

        summary_df = pd.DataFrame(all_summaries)

        st.subheader("All Paper Summaries")
        st.dataframe(summary_df, use_container_width=True)

        summary_csv = summary_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download Summaries as CSV",
            data=summary_csv,
            file_name="research_paper_summaries.csv",
            mime="text/csv"
        )

        if len(papers_data) >= 2:
            similarity_df, relationship_df = calculate_paper_similarity(papers_data)

            relationship_csv = relationship_df.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="Download Paper Relationships as CSV",
                data=relationship_csv,
                file_name="paper_relationships.csv",
                mime="text/csv"
            )

else:
    st.info("Please upload one or multiple PDF/TXT research papers to start.")