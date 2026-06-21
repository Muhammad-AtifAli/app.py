import asyncio
import random
import tempfile
from pathlib import Path

import edge_tts
import streamlit as st
from streamlit_mic_recorder import speech_to_text


# =========================================================
# STREAMLIT PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="SpeakFree Live Tutor",
    page_icon="🎙️",
    layout="centered",
)


# =========================================================
# APP SETTINGS
# =========================================================

MALE_VOICE = "en-US-GuyNeural"

VOICE_RATE = "-5%"

VOICE_VOLUME = "+0%"

VOICE_PITCH = "-5Hz"


TOPICS = {
    "General Conversation": [
        "Hello. How are you today?",
        "What have you been doing today?",
        "Tell me something interesting about your day.",
        "What do you usually do in your free time?",
        "What would you like to talk about?",
    ],

    "Daily Routine": [
        "What time do you usually wake up?",
        "What do you do after waking up?",
        "What do you normally eat for breakfast?",
        "How do you travel to work or school?",
        "What do you usually do in the evening?",
    ],

    "School and Teaching": [
        "What subject do you teach?",
        "What do you enjoy most about teaching?",
        "How do you make your lessons interesting?",
        "What difficulties do your students face?",
        "Describe your classroom.",
    ],

    "Shopping": [
        "What do you usually buy from the market?",
        "How often do you go shopping?",
        "Do you prefer shopping online or in a shop?",
        "How do you ask a shopkeeper for a discount?",
        "Describe something you recently purchased.",
    ],

    "Travel": [
        "Which city would you like to visit?",
        "How do you normally travel?",
        "Describe your favourite journey.",
        "What should a traveller carry?",
        "Would you prefer travelling alone or with family?",
    ],

    "Job Interview": [
        "Please introduce yourself.",
        "What are your main strengths?",
        "Why should we hire you?",
        "What experience do you have?",
        "Where do you see yourself in five years?",
    ],
}


FOLLOW_UP_QUESTIONS = {
    "General Conversation": [
        "That sounds interesting. Can you tell me more?",
        "Why do you feel that way?",
        "What happened after that?",
        "How was that experience for you?",
    ],

    "Daily Routine": [
        "What do you do after that?",
        "How much time does that normally take?",
        "Do you follow the same routine every day?",
        "Which part of your routine do you enjoy most?",
    ],

    "School and Teaching": [
        "How do your students respond?",
        "Can you give me an example?",
        "What teaching method do you use?",
        "How could that lesson be improved?",
    ],

    "Shopping": [
        "How much did it cost?",
        "Why did you choose that item?",
        "Was the shopkeeper helpful?",
        "Would you buy it again?",
    ],

    "Travel": [
        "Why would you like to visit that place?",
        "Who would you travel with?",
        "How long would you stay there?",
        "What would you like to do there?",
    ],

    "Job Interview": [
        "Can you give me an example?",
        "How would that help this organisation?",
        "What did you learn from that experience?",
        "How do you handle difficult situations?",
    ],
}


CORRECTIONS = {
    "i am agree": "I agree.",
    "he go": "He goes.",
    "she go": "She goes.",
    "he don't": "He doesn't.",
    "she don't": "She doesn't.",
    "i did not went": "I did not go.",
    "i am having": "I have.",
    "myself atif": "My name is Atif.",
    "i am belong to": "I belong to.",
    "more better": "better",
    "return back": "return",
    "discuss about": "discuss",
    "i has": "I have.",
    "they is": "They are.",
    "we was": "We were.",
    "people is": "People are.",
}


# =========================================================
# SESSION STATE
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


if "current_question" not in st.session_state:
    st.session_state.current_question = (
        "Hello. How are you today?"
    )


if "last_spoken_text" not in st.session_state:
    st.session_state.last_spoken_text = ""


if "points" not in st.session_state:
    st.session_state.points = 0


if "conversation_started" not in st.session_state:
    st.session_state.conversation_started = False


if "question_number" not in st.session_state:
    st.session_state.question_number = 0


# =========================================================
# MALE TEXT-TO-SPEECH
# =========================================================

async def create_male_voice(text, output_file):
    communicate = edge_tts.Communicate(
        text=text,
        voice=MALE_VOICE,
        rate=VOICE_RATE,
        volume=VOICE_VOLUME,
        pitch=VOICE_PITCH,
    )

    await communicate.save(output_file)


def generate_male_audio(text):
    temporary_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".mp3",
    )

    temporary_path = temporary_file.name

    temporary_file.close()

    try:
        asyncio.run(
            create_male_voice(
                text,
                temporary_path,
            )
        )

        audio_bytes = Path(
            temporary_path
        ).read_bytes()

        return audio_bytes

    except Exception:
        return None

    finally:
        Path(
            temporary_path
        ).unlink(
            missing_ok=True
        )


def play_male_voice(text):
    audio_bytes = generate_male_audio(
        text
    )

    if audio_bytes:
        st.audio(
            audio_bytes,
            format="audio/mp3",
            autoplay=True,
        )

    else:
        st.warning(
            "The male voice could not be loaded. "
            "Please check your internet connection."
        )


# =========================================================
# CONVERSATION FUNCTIONS
# =========================================================

def find_grammar_correction(user_text):
    lower_text = user_text.lower()

    for mistake, correction in CORRECTIONS.items():
        if mistake in lower_text:
            return correction

    return None


def generate_tutor_reply(
    user_text,
    selected_topic,
    selected_level,
):
    clean_text = user_text.strip()

    word_count = len(
        clean_text.split()
    )

    correction = find_grammar_correction(
        clean_text
    )

    if correction:
        return (
            f"Good attempt. A more natural sentence is: "
            f"{correction} Please repeat the corrected sentence."
        )

    if word_count == 1:
        return (
            "Please try to answer with a complete sentence. "
            "Add a subject, a verb and one detail."
        )

    if word_count < 4:
        return (
            "Your answer is understandable. "
            "Please add one more detail. "
            + random.choice(
                FOLLOW_UP_QUESTIONS[
                    selected_topic
                ]
            )
        )

    if selected_level == "Beginner":
        opening = random.choice(
            [
                "Good answer.",
                "Well done.",
                "That is clear.",
                "I understand you.",
            ]
        )

    elif selected_level == "Intermediate":
        opening = random.choice(
            [
                "That is a good explanation.",
                "Your answer is clear and meaningful.",
                "You expressed that idea well.",
                "That was a natural response.",
            ]
        )

    else:
        opening = random.choice(
            [
                "That was a thoughtful response.",
                "You expressed your idea confidently.",
                "Your explanation was clear and well developed.",
                "That was a coherent and natural answer.",
            ]
        )

    follow_up = random.choice(
        FOLLOW_UP_QUESTIONS[
            selected_topic
        ]
    )

    return f"{opening} {follow_up}"


def add_message(
    role,
    content,
):
    st.session_state.messages.append(
        {
            "role": role,
            "content": content,
        }
    )


def start_new_conversation(
    selected_topic,
):
    first_question = random.choice(
        TOPICS[
            selected_topic
        ]
    )

    st.session_state.messages = []

    st.session_state.current_question = (
        first_question
    )

    st.session_state.question_number = 1

    st.session_state.conversation_started = True

    add_message(
        "assistant",
        first_question,
    )


def reset_conversation():
    st.session_state.messages = []

    st.session_state.current_question = (
        "Hello. How are you today?"
    )

    st.session_state.last_spoken_text = ""

    st.session_state.points = 0

    st.session_state.question_number = 0

    st.session_state.conversation_started = False


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.title("Settings")

    learner_name = st.text_input(
        "Your name",
        value="Atif",
    )

    selected_level = st.selectbox(
        "English level",
        [
            "Beginner",
            "Intermediate",
            "Advanced",
        ],
    )

    selected_topic = st.selectbox(
        "Conversation topic",
        list(
            TOPICS.keys()
        ),
    )

    st.divider()

    st.metric(
        "Practice points",
        st.session_state.points,
    )

    st.metric(
        "Questions",
        st.session_state.question_number,
    )

    if st.button(
        "Start new conversation",
        type="primary",
        use_container_width=True,
    ):
        start_new_conversation(
            selected_topic
        )

        st.rerun()

    if st.button(
        "Reset conversation",
        use_container_width=True,
    ):
        reset_conversation()

        st.rerun()


# =========================================================
# MAIN APP
# =========================================================

st.title("🎙️ SpeakFree Live English Tutor")

st.write(
    f"Welcome, **{learner_name}**. "
    "Speak naturally and your male English tutor "
    "will answer you immediately."
)

st.info(
    "Press the microphone button, speak in English, "
    "and press it again when you finish."
)


if not st.session_state.conversation_started:
    st.subheader(
        "Ready to begin?"
    )

    st.write(
        "Choose your level and conversation topic "
        "from the sidebar."
    )

    if st.button(
        "Begin live conversation",
        type="primary",
        use_container_width=True,
    ):
        start_new_conversation(
            selected_topic
        )

        st.rerun()


else:
    st.subheader(
        f"Topic: {selected_topic}"
    )

    st.caption(
        f"Level: {selected_level}"
    )

    st.divider()


    # =====================================================
    # DISPLAY CONVERSATION
    # =====================================================

    for message in st.session_state.messages:

        with st.chat_message(
            message["role"]
        ):
            st.write(
                message["content"]
            )


    # =====================================================
    # PLAY CURRENT TUTOR QUESTION
    # =====================================================

    if (
        st.session_state.current_question
        != st.session_state.last_spoken_text
    ):
        play_male_voice(
            st.session_state.current_question
        )

        st.session_state.last_spoken_text = (
            st.session_state.current_question
        )


    # =====================================================
    # LIVE SPEECH INPUT
    # =====================================================

    st.subheader(
        "Your turn"
    )

    spoken_text = speech_to_text(
        language="en",
        start_prompt="🎙️ Start speaking",
        stop_prompt="⏹️ Stop speaking",
        just_once=True,
        use_container_width=True,
        key="live_speech",
    )


    if spoken_text:
        add_message(
            "user",
            spoken_text,
        )

        tutor_reply = generate_tutor_reply(
            user_text=spoken_text,
            selected_topic=selected_topic,
            selected_level=selected_level,
        )

        add_message(
            "assistant",
            tutor_reply,
        )

        st.session_state.current_question = (
            tutor_reply
        )

        st.session_state.last_spoken_text = ""

        st.session_state.points += 5

        st.session_state.question_number += 1

        st.rerun()


    # =====================================================
    # OPTIONAL TEXT INPUT
    # =====================================================

    typed_text = st.chat_input(
        "You may also type your answer here"
    )


    if typed_text:
        add_message(
            "user",
            typed_text,
        )

        tutor_reply = generate_tutor_reply(
            user_text=typed_text,
            selected_topic=selected_topic,
            selected_level=selected_level,
        )

        add_message(
            "assistant",
            tutor_reply,
        )

        st.session_state.current_question = (
            tutor_reply
        )

        st.session_state.last_spoken_text = ""

        st.session_state.points += 5

        st.session_state.question_number += 1

        st.rerun()


    # =====================================================
    # CONVERSATION CONTROLS
    # =====================================================

    st.divider()

    first_column, second_column = st.columns(
        2
    )


    with first_column:
        if st.button(
            "Repeat tutor voice",
            use_container_width=True,
        ):
            play_male_voice(
                st.session_state.current_question
            )


    with second_column:
        if st.button(
            "Change question",
            use_container_width=True,
        ):
            new_question = random.choice(
                TOPICS[
                    selected_topic
                ]
            )

            add_message(
                "assistant",
                new_question,
            )

            st.session_state.current_question = (
                new_question
            )

            st.session_state.last_spoken_text = ""

            st.session_state.question_number += 1

            st.rerun()


st.divider()

st.caption(
    "This app uses a male English voice only. "
    "Speech recognition and voice generation require "
    "an active internet connection."
)