import streamlit as st
import streamlit.components.v1 as components
import random
import string
from datetime import datetime

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Online Meeting App",
    page_icon="🎥",
    layout="wide"
)

# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>
.main-title {
    text-align: center;
    font-size: 40px;
    font-weight: bold;
    color: #1f77b4;
}
.sub-title {
    text-align: center;
    font-size: 18px;
    color: #555;
}
.meeting-box {
    background-color: #f4f8fb;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #d9e6f2;
}
</style>
""", unsafe_allow_html=True)

# ---------------- FUNCTIONS ----------------
def generate_meeting_id(length=10):
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))


# ---------------- SESSION STATE ----------------
if "meeting_id" not in st.session_state:
    st.session_state.meeting_id = ""

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []


# ---------------- HEADER ----------------
st.markdown("<div class='main-title'>🎥 Online Meeting App</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='sub-title'>Create or join an online meeting with audio, video, chat, and screen sharing.</div>",
    unsafe_allow_html=True
)

st.write("---")

# ---------------- SIDEBAR ----------------
st.sidebar.title("Meeting Controls")

user_name = st.sidebar.text_input("Your Name", placeholder="Enter your name")

meeting_option = st.sidebar.radio(
    "Choose Option",
    ["Create New Meeting", "Join Existing Meeting"]
)

if meeting_option == "Create New Meeting":
    if st.sidebar.button("Generate Meeting ID"):
        st.session_state.meeting_id = generate_meeting_id()

else:
    entered_id = st.sidebar.text_input("Enter Meeting ID")
    if st.sidebar.button("Join Meeting"):
        if entered_id.strip():
            st.session_state.meeting_id = entered_id.strip()
        else:
            st.sidebar.warning("Please enter a Meeting ID.")

# ---------------- MAIN AREA ----------------
left_col, right_col = st.columns([3, 1])

with left_col:
    st.subheader("Meeting Room")

    if st.session_state.meeting_id == "":
        st.info("Create a new meeting or enter a meeting ID to join.")
    else:
        meeting_id = st.session_state.meeting_id

        st.markdown("<div class='meeting-box'>", unsafe_allow_html=True)
        st.success(f"Meeting ID: {meeting_id}")

        meeting_link = f"https://meet.jit.si/{meeting_id}"
        st.info("Share this Meeting ID or meeting link with other people.")

        st.code(meeting_link)

        display_name = user_name if user_name.strip() else "Guest"

        jitsi_html = f"""
        <html>
        <head>
            <script src='https://meet.jit.si/external_api.js'></script>
        </head>
        <body style="margin:0; padding:0;">
            <div id="jitsi-container" style="height:700px; width:100%;"></div>

            <script>
                const domain = "meet.jit.si";
                const options = {{
                    roomName: "{meeting_id}",
                    width: "100%",
                    height: 700,
                    parentNode: document.querySelector('#jitsi-container'),
                    userInfo: {{
                        displayName: "{display_name}"
                    }},
                    configOverwrite: {{
                        startWithAudioMuted: false,
                        startWithVideoMuted: false
                    }},
                    interfaceConfigOverwrite: {{
                        SHOW_JITSI_WATERMARK: false,
                        SHOW_WATERMARK_FOR_GUESTS: false
                    }}
                }};

                const api = new JitsiMeetExternalAPI(domain, options);
            </script>
        </body>
        </html>
        """

        components.html(jitsi_html, height=720)

        st.markdown("</div>", unsafe_allow_html=True)

with right_col:
    st.subheader("App Chat")

    st.caption("This is a simple Streamlit-side chat. Jitsi also has its own built-in meeting chat.")

    if st.session_state.meeting_id == "":
        st.info("Join or create a meeting first.")
    else:
        message = st.text_area("Write message", height=100)

        if st.button("Send Message"):
            if user_name.strip() == "":
                st.warning("Please enter your name first.")
            elif message.strip() == "":
                st.warning("Please write a message.")
            else:
                st.session_state.chat_messages.append({
                    "name": user_name,
                    "message": message,
                    "time": datetime.now().strftime("%I:%M %p")
                })
                st.rerun()

        st.write("---")

        if len(st.session_state.chat_messages) == 0:
            st.info("No messages yet.")
        else:
            for chat in reversed(st.session_state.chat_messages):
                st.markdown(
                    f"""
                    **{chat['name']}**  
                    {chat['message']}  
                    <small>{chat['time']}</small>
                    """,
                    unsafe_allow_html=True
                )
                st.write("---")