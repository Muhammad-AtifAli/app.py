import streamlit as st
import time
import random
import html
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Typing Tutor App",
    page_icon="⌨️",
    layout="wide"
)

# -----------------------------
# CSS Styling
# -----------------------------
st.markdown("""
<style>
.main {
    background-color: #f5f7fb;
}

.big-title {
    font-size: 42px;
    font-weight: 800;
    text-align: center;
    color: #1f2937;
    margin-bottom: 5px;
}

.sub-title {
    text-align: center;
    color: #6b7280;
    font-size: 18px;
    margin-bottom: 30px;
}

.card {
    background: white;
    padding: 25px;
    border-radius: 18px;
    box-shadow: 0px 4px 18px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}

.exercise-box {
    background: #111827;
    color: #f9fafb;
    padding: 22px;
    border-radius: 15px;
    font-size: 22px;
    line-height: 1.8;
    letter-spacing: 1px;
}

.result-box {
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    color: white;
    padding: 22px;
    border-radius: 18px;
    text-align: center;
    font-size: 22px;
    font-weight: 700;
}

.small-note {
    color: #6b7280;
    font-size: 15px;
}

.correct {
    color: #16a34a;
    font-weight: bold;
}

.wrong {
    color: #dc2626;
    font-weight: bold;
    text-decoration: underline;
}

.pending {
    color: #9ca3af;
}
</style>
""", unsafe_allow_html=True)


# -----------------------------
# Exercises
# -----------------------------
EXERCISES = {
    "Low": [
        "cat dog sun moon book pen table chair.",
        "I can type fast and clean.",
        "The boy has a red ball.",
        "This is a simple typing lesson.",
        "Practice daily to improve typing speed.",
        "A good student learns every day.",
        "My school has many classrooms.",
        "Typing is useful for office work.",
        "Read the sentence and type it carefully.",
        "Small steps make big progress."
    ],
    "Medium": [
        "Typing practice improves focus, speed, and accuracy when it is done regularly.",
        "A computer user should learn keyboard skills to complete office tasks quickly.",
        "Students can improve their assignments by typing neatly and checking their mistakes.",
        "The teacher prepared a useful lesson for the students in the computer lab.",
        "Accuracy is more important than speed in the beginning of typing practice.",
        "When you type with confidence, your work becomes faster and more professional.",
        "A good typing habit saves time in school, office, and online business work.",
        "The quick brown fox jumps over the lazy dog near the old wooden bridge.",
        "Digital skills are very important for students, teachers, and business owners.",
        "Regular practice helps the fingers remember the position of keys on the keyboard."
    ],
    "High": [
        "Professional typing requires accuracy, rhythm, concentration, and continuous practice without looking at the keyboard.",
        "In modern offices, fast typing skills help workers prepare reports, emails, invoices, and official documents efficiently.",
        "A successful learner does not only type quickly but also understands punctuation, capitalization, spacing, and correction.",
        "Technology has changed education, business, communication, and administration in almost every field of daily life.",
        "The development of keyboard confidence allows users to complete digital tasks with less stress and more productivity.",
        "Advanced typing exercises should include paragraphs, numbers, symbols, punctuation marks, and mixed vocabulary patterns.",
        "Students who practice typing regularly can prepare assignments, research papers, and presentations more effectively.",
        "Typing speed is measured through words per minute, but true expertise also depends on accuracy and consistency.",
        "A disciplined learner reviews mistakes carefully because every error shows where more practice is required.",
        "Efficient digital communication depends on clear writing, correct typing, and the ability to revise text quickly."
    ]
}

BUBBLE_WORDS = {
    "Low": [
        "cat", "dog", "sun", "pen", "book", "red", "blue", "ball", "fan", "cup",
        "tree", "fish", "milk", "home", "school", "desk", "bag", "car", "bus", "hat"
    ],
    "Medium": [
        "typing", "student", "teacher", "keyboard", "practice", "accuracy", "lesson",
        "computer", "window", "office", "report", "invoice", "message", "result",
        "learning", "subject", "english", "science", "digital", "system"
    ],
    "High": [
        "professional", "administration", "communication", "development", "punctuation",
        "concentration", "productivity", "technology", "efficiency", "improvement",
        "evaluation", "presentation", "assignment", "discipline", "consistency",
        "performance", "correction", "vocabulary", "confidence", "management"
    ]
}


# -----------------------------
# Session State
# -----------------------------
if "paragraph_start_time" not in st.session_state:
    st.session_state.paragraph_start_time = None

if "selected_exercise" not in st.session_state:
    st.session_state.selected_exercise = ""

if "completed_results" not in st.session_state:
    st.session_state.completed_results = []


# -----------------------------
# Helper Functions
# -----------------------------
def calculate_accuracy(original, typed):
    if not typed:
        return 0

    correct = 0
    total = max(len(original), len(typed))

    for i in range(min(len(original), len(typed))):
        if original[i] == typed[i]:
            correct += 1

    accuracy = (correct / total) * 100
    return round(accuracy, 2)


def calculate_wpm(typed_text, elapsed_seconds):
    if elapsed_seconds <= 0:
        return 0

    words = len(typed_text.split())
    minutes = elapsed_seconds / 60
    return round(words / minutes, 2)


def count_mistakes(original, typed):
    mistakes = 0
    total = max(len(original), len(typed))

    for i in range(total):
        if i >= len(original) or i >= len(typed):
            mistakes += 1
        elif original[i] != typed[i]:
            mistakes += 1

    return mistakes


def highlighted_text(original, typed):
    result = ""

    for i, char in enumerate(original):
        safe_char = html.escape(char)

        if i < len(typed):
            if typed[i] == char:
                result += f"<span class='correct'>{safe_char}</span>"
            else:
                result += f"<span class='wrong'>{safe_char}</span>"
        else:
            result += f"<span class='pending'>{safe_char}</span>"

    return result


def get_random_exercise(level):
    return random.choice(EXERCISES[level])


# -----------------------------
# Header
# -----------------------------
st.markdown("<div class='big-title'>⌨️ Advanced Typing Tutor App</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='sub-title'>Practice typing through paragraphs and falling bubbles. Improve speed, accuracy, and confidence.</div>",
    unsafe_allow_html=True
)

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("⚙️ App Settings")

mode = st.sidebar.radio(
    "Select Practice Mode",
    ["Paragraph Practice", "Falling Bubbles Game", "Typing Lessons"]
)

difficulty = st.sidebar.selectbox(
    "Select Difficulty Level",
    ["Low", "Medium", "High"]
)

st.sidebar.markdown("---")
st.sidebar.info(
    "Low level is for beginners. Medium level is for normal practice. High level is for advanced users."
)


# -----------------------------
# Paragraph Practice
# -----------------------------
if mode == "Paragraph Practice":
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📘 Paragraph Typing Practice")

        exercise_method = st.radio(
            "Choose Exercise Type",
            ["Random Exercise", "Select Exercise Manually", "Write My Own Paragraph"],
            horizontal=True
        )

        if exercise_method == "Random Exercise":
            if st.button("🎲 Generate Random Exercise"):
                st.session_state.selected_exercise = get_random_exercise(difficulty)
                st.session_state.paragraph_start_time = None

            if st.session_state.selected_exercise == "":
                st.session_state.selected_exercise = get_random_exercise(difficulty)

        elif exercise_method == "Select Exercise Manually":
            selected_index = st.selectbox(
                "Select an Exercise",
                list(range(1, len(EXERCISES[difficulty]) + 1))
            )
            st.session_state.selected_exercise = EXERCISES[difficulty][selected_index - 1]

        else:
            custom_text = st.text_area(
                "Write or paste your own paragraph here",
                height=150,
                placeholder="Write your custom typing paragraph here..."
            )

            if custom_text.strip():
                st.session_state.selected_exercise = custom_text.strip()
            else:
                st.session_state.selected_exercise = "Please write your own paragraph first."

        original_text = st.session_state.selected_exercise

        st.markdown("### Text to Type")
        st.markdown(
            f"<div class='exercise-box'>{html.escape(original_text)}</div>",
            unsafe_allow_html=True
        )

        st.markdown("### Type Here")

        if st.session_state.paragraph_start_time is None:
            if st.button("▶️ Start Typing Test"):
                st.session_state.paragraph_start_time = time.time()
                st.rerun()

        if st.session_state.paragraph_start_time is not None:
            typed_text = st.text_area(
                "Start typing the above text:",
                height=180,
                placeholder="Type here..."
            )

            live_accuracy = calculate_accuracy(original_text, typed_text)
            live_mistakes = count_mistakes(original_text, typed_text)
            elapsed = time.time() - st.session_state.paragraph_start_time
            live_wpm = calculate_wpm(typed_text, elapsed)

            st.markdown("### Live Checking")
            st.markdown(
                f"<div class='exercise-box'>{highlighted_text(original_text, typed_text)}</div>",
                unsafe_allow_html=True
            )

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("⏱️ Time", f"{round(elapsed, 1)} sec")
            c2.metric("🚀 WPM", live_wpm)
            c3.metric("🎯 Accuracy", f"{live_accuracy}%")
            c4.metric("❌ Mistakes", live_mistakes)

            if st.button("✅ Finish Test"):
                final_time = time.time() - st.session_state.paragraph_start_time
                final_wpm = calculate_wpm(typed_text, final_time)
                final_accuracy = calculate_accuracy(original_text, typed_text)
                final_mistakes = count_mistakes(original_text, typed_text)

                st.session_state.completed_results.append({
                    "Mode": "Paragraph",
                    "Difficulty": difficulty,
                    "WPM": final_wpm,
                    "Accuracy": final_accuracy,
                    "Mistakes": final_mistakes,
                    "Time": round(final_time, 2)
                })

                st.markdown(
                    f"""
                    <div class='result-box'>
                    Result: {final_wpm} WPM | {final_accuracy}% Accuracy | {final_mistakes} Mistakes | {round(final_time, 2)} Seconds
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.session_state.paragraph_start_time = None

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📊 Your Recent Results")

        if st.session_state.completed_results:
            for i, result in enumerate(reversed(st.session_state.completed_results[-5:]), start=1):
                st.write(f"**Result {i}**")
                st.write(f"Mode: {result['Mode']}")
                st.write(f"Difficulty: {result['Difficulty']}")
                st.write(f"WPM: {result['WPM']}")
                st.write(f"Accuracy: {result['Accuracy']}%")
                st.write(f"Mistakes: {result['Mistakes']}")
                st.write("---")
        else:
            st.write("No result yet. Complete a test first.")

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("💡 Typing Tips")
        st.write("1. First focus on accuracy.")
        st.write("2. Do not look at the keyboard again and again.")
        st.write("3. Practice daily for 15 to 20 minutes.")
        st.write("4. Keep your fingers on the home row keys.")
        st.write("5. Increase speed slowly.")
        st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# Falling Bubbles Game
# -----------------------------
elif mode == "Falling Bubbles Game":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("🫧 Falling Bubbles Typing Game")

    st.write(
        "Type the falling word correctly and press Enter. "
        "If the bubble reaches the bottom, you lose one life."
    )

    if difficulty == "Low":
        speed = 2.2
        spawn_time = 1800
        game_time = 60
    elif difficulty == "Medium":
        speed = 3.0
        spawn_time = 1400
        game_time = 75
    else:
        speed = 4.0
        spawn_time = 1050
        game_time = 90

    words_js = BUBBLE_WORDS[difficulty]

    bubble_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f3f4f6;
        }}

        #gameWrapper {{
            width: 100%;
            height: 620px;
            background: linear-gradient(180deg, #dbeafe, #eff6ff);
            border-radius: 20px;
            position: relative;
            overflow: hidden;
            border: 3px solid #2563eb;
        }}

        #topBar {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 65px;
            background: #111827;
            color: white;
            display: flex;
            align-items: center;
            justify-content: space-around;
            font-size: 18px;
            font-weight: bold;
            z-index: 10;
        }}

        #typingInput {{
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            width: 55%;
            padding: 15px;
            border-radius: 30px;
            border: 3px solid #2563eb;
            font-size: 22px;
            text-align: center;
            outline: none;
            z-index: 10;
        }}

        .bubble {{
            position: absolute;
            min-width: 70px;
            height: 70px;
            padding: 5px 12px;
            border-radius: 50px;
            background: radial-gradient(circle at 30% 30%, #ffffff, #60a5fa, #2563eb);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 17px;
            box-shadow: 0px 8px 20px rgba(37,99,235,0.35);
            user-select: none;
        }}

        #startScreen, #gameOverScreen {{
            position: absolute;
            width: 100%;
            height: 100%;
            background: rgba(17, 24, 39, 0.92);
            color: white;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 20;
            text-align: center;
        }}

        button {{
            background: #22c55e;
            border: none;
            color: white;
            padding: 16px 35px;
            border-radius: 30px;
            font-size: 20px;
            font-weight: bold;
            cursor: pointer;
            margin-top: 20px;
        }}

        button:hover {{
            background: #16a34a;
        }}

        .finalScore {{
            font-size: 26px;
            margin-top: 15px;
            color: #facc15;
        }}
    </style>
    </head>

    <body>
        <div id="gameWrapper">
            <div id="topBar">
                <div>Level: {difficulty}</div>
                <div>Score: <span id="score">0</span></div>
                <div>Lives: <span id="lives">5</span></div>
                <div>Time: <span id="timeLeft">{game_time}</span>s</div>
                <div>Correct: <span id="correct">0</span></div>
                <div>Wrong: <span id="wrong">0</span></div>
            </div>

            <div id="startScreen">
                <h1>🫧 Falling Bubbles Game</h1>
                <p>Type the word inside the bubble and press Enter.</p>
                <p>Difficulty: <b>{difficulty}</b></p>
                <button onclick="startGame()">Start Game</button>
            </div>

            <div id="gameOverScreen" style="display:none;">
                <h1>Game Over</h1>
                <div class="finalScore" id="finalScore"></div>
                <button onclick="restartGame()">Play Again</button>
            </div>

            <input id="typingInput" placeholder="Type bubble word here and press Enter" autocomplete="off" />
        </div>

    <script>
        const words = {words_js};
        const gameWrapper = document.getElementById("gameWrapper");
        const input = document.getElementById("typingInput");

        let bubbles = [];
        let score = 0;
        let lives = 5;
        let correct = 0;
        let wrong = 0;
        let timeLeft = {game_time};
        let gameRunning = false;
        let spawnInterval;
        let timerInterval;
        let animationFrame;

        const speed = {speed};
        const spawnTime = {spawn_time};

        function updateStats() {{
            document.getElementById("score").innerText = score;
            document.getElementById("lives").innerText = lives;
            document.getElementById("correct").innerText = correct;
            document.getElementById("wrong").innerText = wrong;
            document.getElementById("timeLeft").innerText = timeLeft;
        }}

        function randomWord() {{
            return words[Math.floor(Math.random() * words.length)];
        }}

        function createBubble() {{
            if (!gameRunning) return;

            const bubble = document.createElement("div");
            bubble.className = "bubble";
            bubble.innerText = randomWord();

            const maxX = gameWrapper.clientWidth - 120;
            const x = Math.floor(Math.random() * maxX);

            bubble.style.left = x + "px";
            bubble.style.top = "75px";

            gameWrapper.appendChild(bubble);

            bubbles.push({{
                element: bubble,
                word: bubble.innerText,
                y: 75
            }});
        }}

        function moveBubbles() {{
            if (!gameRunning) return;

            for (let i = bubbles.length - 1; i >= 0; i--) {{
                bubbles[i].y += speed;
                bubbles[i].element.style.top = bubbles[i].y + "px";

                if (bubbles[i].y > gameWrapper.clientHeight - 100) {{
                    bubbles[i].element.remove();
                    bubbles.splice(i, 1);
                    lives -= 1;
                    wrong += 1;
                    updateStats();

                    if (lives <= 0) {{
                        endGame();
                        return;
                    }}
                }}
            }}

            animationFrame = requestAnimationFrame(moveBubbles);
        }}

        input.addEventListener("keydown", function(event) {{
            if (event.key === "Enter") {{
                const typed = input.value.trim().toLowerCase();
                input.value = "";

                if (!typed || !gameRunning) return;

                let found = false;

                for (let i = 0; i < bubbles.length; i++) {{
                    if (bubbles[i].word.toLowerCase() === typed) {{
                        bubbles[i].element.remove();
                        bubbles.splice(i, 1);
                        score += 10;
                        correct += 1;
                        found = true;
                        break;
                    }}
                }}

                if (!found) {{
                    score -= 2;
                    wrong += 1;
                    if (score < 0) score = 0;
                }}

                updateStats();
            }}
        }});

        function startGame() {{
            document.getElementById("startScreen").style.display = "none";
            document.getElementById("gameOverScreen").style.display = "none";

            score = 0;
            lives = 5;
            correct = 0;
            wrong = 0;
            timeLeft = {game_time};
            gameRunning = true;

            bubbles.forEach(b => b.element.remove());
            bubbles = [];

            updateStats();
            input.focus();

            spawnInterval = setInterval(createBubble, spawnTime);
            timerInterval = setInterval(function() {{
                timeLeft -= 1;
                updateStats();

                if (timeLeft <= 0) {{
                    endGame();
                }}
            }}, 1000);

            moveBubbles();
        }}

        function endGame() {{
            gameRunning = false;
            clearInterval(spawnInterval);
            clearInterval(timerInterval);
            cancelAnimationFrame(animationFrame);

            bubbles.forEach(b => b.element.remove());
            bubbles = [];

            document.getElementById("finalScore").innerHTML =
                "Score: " + score +
                "<br>Correct Words: " + correct +
                "<br>Wrong/Missed Words: " + wrong;

            document.getElementById("gameOverScreen").style.display = "flex";
        }}

        function restartGame() {{
            startGame();
        }}

        updateStats();
    </script>
    </body>
    </html>
    """

    components.html(bubble_html, height=660)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("🫧 Bubble Game Rules")
    st.write("1. Read the falling word inside the bubble.")
    st.write("2. Type the same word in the input box.")
    st.write("3. Press Enter.")
    st.write("4. Correct word gives you 10 points.")
    st.write("5. Wrong word reduces your score.")
    st.write("6. If a bubble reaches the bottom, you lose one life.")
    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# Typing Lessons
# -----------------------------
else:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📚 Typing Lessons for Beginners to Advanced Users")

    lesson_level = st.selectbox(
        "Choose Lesson Category",
        [
            "Home Row Keys",
            "Top Row Keys",
            "Bottom Row Keys",
            "Capital Letters",
            "Numbers Practice",
            "Punctuation Practice",
            "Speed Building",
            "Accuracy Building"
        ]
    )

    lessons = {
        "Home Row Keys": [
            "asdf jkl;",
            "aaa sss ddd fff jjj kkk lll ;;;",
            "as as df df jk jk l; l;",
            "sad lad fall ask flask"
        ],
        "Top Row Keys": [
            "qwer uiop",
            "qqq www eee rrr uuu iii ooo ppp",
            "we were quite quick",
            "power writer requires quiet practice"
        ],
        "Bottom Row Keys": [
            "zxcv bnm",
            "zzz xxx ccc vvv bbb nnn mmm",
            "mix box van zoom camp",
            "maximum vocabulary comes from practice"
        ],
        "Capital Letters": [
            "My Name Is Atif.",
            "Pakistan Is A Beautiful Country.",
            "Typing Practice Builds Confidence.",
            "Students Should Practice Daily."
        ],
        "Numbers Practice": [
            "12345 67890",
            "111 222 333 444 555",
            "My marks are 85 out of 100.",
            "The school has 14 classes and 520 students."
        ],
        "Punctuation Practice": [
            "Hello, how are you?",
            "Typing is useful: practice it daily.",
            "Accuracy, speed, and focus are important.",
            "Can you type this sentence correctly?"
        ],
        "Speed Building": [
            "the and you that was for are with his they",
            "practice practice practice makes typing better",
            "fast fingers need correct movement",
            "speed comes after accuracy"
        ],
        "Accuracy Building": [
            "Do not hurry. Type carefully.",
            "Correct typing is better than fast typing.",
            "Every mistake teaches you something.",
            "Slow practice creates strong typing habits."
        ]
    }

    st.markdown("### Practice Lines")
    for i, line in enumerate(lessons[lesson_level], start=1):
        st.markdown(
            f"<div class='exercise-box'>{i}. {html.escape(line)}</div>",
            unsafe_allow_html=True
        )
        st.write("")

    st.markdown("### Practice Area")
    lesson_input = st.text_area(
        "Type the lesson lines here:",
        height=180,
        placeholder="Type your lesson practice here..."
    )

    if lesson_input:
        st.success("Good! Keep practicing. Try to type without looking at the keyboard.")

    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# Footer
# -----------------------------
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#6b7280;'>Developed as a Streamlit Typing Tutor Project</p>",
    unsafe_allow_html=True
)