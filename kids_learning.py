import streamlit as st
import random
import time

# ---------------- PAGE SETTINGS ----------------
st.set_page_config(
    page_title="Kids Learning Adventure",
    page_icon="🧠",
    layout="wide"
)

# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>
    .main-title {
        text-align: center;
        font-size: 42px;
        color: #ff6f61;
        font-weight: bold;
    }
    .subtitle {
        text-align: center;
        font-size: 20px;
        color: #555;
    }
    .activity-card {
        background-color: #fff7e6;
        padding: 20px;
        border-radius: 18px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 15px;
        border-radius: 10px;
        font-size: 18px;
    }
    .wrong-box {
        background-color: #f8d7da;
        color: #721c24;
        padding: 15px;
        border-radius: 10px;
        font-size: 18px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if "score" not in st.session_state:
    st.session_state.score = 0

if "attempts" not in st.session_state:
    st.session_state.attempts = 0

if "math_question" not in st.session_state:
    st.session_state.math_question = None

if "memory_sequence" not in st.session_state:
    st.session_state.memory_sequence = []

if "pattern_question" not in st.session_state:
    st.session_state.pattern_question = None


# ---------------- HELPER FUNCTIONS ----------------
def add_score(points=1):
    st.session_state.score += points
    st.session_state.attempts += 1


def add_attempt():
    st.session_state.attempts += 1


def show_score():
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("⭐ Score", st.session_state.score)

    with col2:
        st.metric("📝 Attempts", st.session_state.attempts)

    with col3:
        if st.session_state.attempts > 0:
            accuracy = round((st.session_state.score / st.session_state.attempts) * 100, 1)
        else:
            accuracy = 0
        st.metric("🎯 Accuracy", f"{accuracy}%")


def feedback(correct):
    if correct:
        st.markdown('<div class="success-box">✅ Great job! You answered correctly.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="wrong-box">❌ Not correct. Try again and learn from it.</div>', unsafe_allow_html=True)


# ---------------- TITLE ----------------
st.markdown('<div class="main-title">🧠 Kids Learning Adventure</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Fun activities for daily life learning, thinking, and problem solving</div>', unsafe_allow_html=True)

st.write("")
show_score()
st.write("---")

# ---------------- SIDEBAR ----------------
st.sidebar.title("🎮 Activity Menu")

activity = st.sidebar.radio(
    "Choose an activity:",
    [
        "🏠 Home",
        "➕ Math Practice",
        "🛒 Shopping Problem",
        "🚦 Daily Life Decisions",
        "🔤 Word Builder",
        "🧠 Memory Game",
        "🔢 Pattern Puzzle",
        "📦 Sorting Activity",
        "🏆 Progress Report"
    ]
)

if st.sidebar.button("🔄 Reset Score"):
    st.session_state.score = 0
    st.session_state.attempts = 0
    st.session_state.math_question = None
    st.session_state.memory_sequence = []
    st.session_state.pattern_question = None
    st.success("Score has been reset.")


# ---------------- HOME ----------------
if activity == "🏠 Home":
    st.subheader("Welcome to Kids Learning Adventure 👋")

    st.markdown("""
    This app helps children learn useful daily-life skills in a fun way.

    Children can practice:

    - Basic mathematics
    - Shopping and money problems
    - Good daily-life decisions
    - Word making
    - Memory skills
    - Pattern recognition
    - Sorting and classification

    These activities improve:

    - Thinking skills
    - Problem-solving skills
    - Confidence
    - Quick decision-making
    - Learning through play
    """)

    st.info("Choose any activity from the left sidebar to begin.")


# ---------------- MATH PRACTICE ----------------
elif activity == "➕ Math Practice":
    st.subheader("➕ Math Practice")

    level = st.selectbox("Choose level:", ["Easy", "Medium", "Hard"])

    if st.button("Generate New Math Question"):
        if level == "Easy":
            a = random.randint(1, 10)
            b = random.randint(1, 10)
            op = random.choice(["+", "-"])
        elif level == "Medium":
            a = random.randint(10, 50)
            b = random.randint(1, 20)
            op = random.choice(["+", "-", "×"])
        else:
            a = random.randint(20, 100)
            b = random.randint(2, 20)
            op = random.choice(["+", "-", "×"])

        if op == "+":
            answer = a + b
        elif op == "-":
            answer = a - b
        else:
            answer = a * b

        st.session_state.math_question = {
            "a": a,
            "b": b,
            "op": op,
            "answer": answer
        }

    if st.session_state.math_question:
        q = st.session_state.math_question
        st.markdown(f"### Solve this: {q['a']} {q['op']} {q['b']} = ?")

        user_answer = st.number_input("Write your answer:", step=1)

        if st.button("Check Math Answer"):
            if user_answer == q["answer"]:
                add_score()
                feedback(True)
            else:
                add_attempt()
                feedback(False)
                st.info(f"The correct answer is: {q['answer']}")


# ---------------- SHOPPING PROBLEM ----------------
elif activity == "🛒 Shopping Problem":
    st.subheader("🛒 Shopping Problem Solving")

    items = {
        "Apple": 30,
        "Banana": 20,
        "Milk": 150,
        "Bread": 100,
        "Pencil": 15,
        "Notebook": 80,
        "Juice": 120
    }

    item1, item2 = random.sample(list(items.keys()), 2)
    qty1 = random.randint(1, 4)
    qty2 = random.randint(1, 4)

    total = items[item1] * qty1 + items[item2] * qty2

    st.markdown(f"""
    ### Problem:
    You buy:

    **{qty1} {item1}(s)** at Rs. **{items[item1]}** each  
    **{qty2} {item2}(s)** at Rs. **{items[item2]}** each  

    What is the total bill?
    """)

    answer = st.number_input("Enter total amount in Rs:", step=1)

    if st.button("Check Shopping Answer"):
        if answer == total:
            add_score()
            feedback(True)
        else:
            add_attempt()
            feedback(False)
            st.info(f"The correct total is Rs. {total}")


# ---------------- DAILY LIFE DECISIONS ----------------
elif activity == "🚦 Daily Life Decisions":
    st.subheader("🚦 Daily Life Decision Quiz")

    questions = [
        {
            "q": "You see a red traffic light. What should you do?",
            "options": ["Run fast", "Stop", "Cross quickly", "Ignore it"],
            "answer": "Stop"
        },
        {
            "q": "You find money on the classroom floor. What should you do?",
            "options": ["Keep it", "Give it to teacher", "Hide it", "Buy candy"],
            "answer": "Give it to teacher"
        },
        {
            "q": "Your friend falls down while playing. What should you do?",
            "options": ["Laugh", "Help your friend", "Run away", "Ignore"],
            "answer": "Help your friend"
        },
        {
            "q": "Before eating food, what should you do?",
            "options": ["Wash hands", "Sleep", "Run outside", "Watch TV"],
            "answer": "Wash hands"
        },
        {
            "q": "You do not understand homework. What should you do?",
            "options": ["Leave it", "Ask teacher or parents", "Throw book", "Cry only"],
            "answer": "Ask teacher or parents"
        }
    ]

    q = random.choice(questions)

    st.markdown(f"### {q['q']}")
    selected = st.radio("Choose the best answer:", q["options"])

    if st.button("Check Decision"):
        if selected == q["answer"]:
            add_score()
            feedback(True)
        else:
            add_attempt()
            feedback(False)
            st.info(f"The best answer is: {q['answer']}")


# ---------------- WORD BUILDER ----------------
elif activity == "🔤 Word Builder":
    st.subheader("🔤 Word Builder")

    word_data = [
        {
            "letters": ["C", "A", "T"],
            "word": "CAT",
            "hint": "A small animal that says meow."
        },
        {
            "letters": ["D", "O", "G"],
            "word": "DOG",
            "hint": "A pet animal that barks."
        },
        {
            "letters": ["B", "O", "O", "K"],
            "word": "BOOK",
            "hint": "You read it."
        },
        {
            "letters": ["M", "I", "L", "K"],
            "word": "MILK",
            "hint": "A white drink."
        },
        {
            "letters": ["S", "U", "N"],
            "word": "SUN",
            "hint": "It gives us light."
        }
    ]

    item = random.choice(word_data)
    shuffled = item["letters"][:]
    random.shuffle(shuffled)

    st.markdown(f"### Arrange these letters to make a word:")
    st.markdown(f"## {'  '.join(shuffled)}")
    st.info(f"Hint: {item['hint']}")

    user_word = st.text_input("Write the correct word:").upper().strip()

    if st.button("Check Word"):
        if user_word == item["word"]:
            add_score()
            feedback(True)
        else:
            add_attempt()
            feedback(False)
            st.info(f"The correct word is: {item['word']}")


# ---------------- MEMORY GAME ----------------
elif activity == "🧠 Memory Game":
    st.subheader("🧠 Memory Sequence Game")

    st.write("Look at the numbers carefully, then write them in the same order.")

    if st.button("Create Memory Sequence"):
        length = random.randint(3, 6)
        st.session_state.memory_sequence = [random.randint(1, 9) for _ in range(length)]

    if st.session_state.memory_sequence:
        st.markdown("### Remember this sequence:")
        st.markdown(f"## {' - '.join(map(str, st.session_state.memory_sequence))}")

        st.warning("Now write the same numbers below with spaces. Example: 1 4 7")

        user_seq = st.text_input("Enter sequence:")

        if st.button("Check Memory"):
            try:
                user_list = [int(x) for x in user_seq.split()]
                if user_list == st.session_state.memory_sequence:
                    add_score()
                    feedback(True)
                else:
                    add_attempt()
                    feedback(False)
                    st.info(
                        "Correct sequence was: "
                        + " ".join(map(str, st.session_state.memory_sequence))
                    )
            except:
                st.error("Please write numbers only, separated by spaces.")


# ---------------- PATTERN PUZZLE ----------------
elif activity == "🔢 Pattern Puzzle":
    st.subheader("🔢 Pattern Puzzle")

    if st.button("Generate Pattern"):
        start = random.randint(1, 10)
        step = random.randint(2, 5)
        pattern = [start + step * i for i in range(5)]
        missing_index = random.randint(1, 3)
        answer = pattern[missing_index]
        display_pattern = pattern[:]
        display_pattern[missing_index] = "?"

        st.session_state.pattern_question = {
            "pattern": display_pattern,
            "answer": answer
        }

    if st.session_state.pattern_question:
        q = st.session_state.pattern_question

        st.markdown("### Find the missing number:")
        st.markdown(f"## {' , '.join(map(str, q['pattern']))}")

        ans = st.number_input("Missing number is:", step=1)

        if st.button("Check Pattern Answer"):
            if ans == q["answer"]:
                add_score()
                feedback(True)
            else:
                add_attempt()
                feedback(False)
                st.info(f"The missing number was: {q['answer']}")


# ---------------- SORTING ACTIVITY ----------------
elif activity == "📦 Sorting Activity":
    st.subheader("📦 Sorting Activity")

    sorting_questions = [
        {
            "item": "Apple",
            "options": ["Fruit", "Animal", "Vehicle", "Furniture"],
            "answer": "Fruit"
        },
        {
            "item": "Chair",
            "options": ["Fruit", "Animal", "Vehicle", "Furniture"],
            "answer": "Furniture"
        },
        {
            "item": "Car",
            "options": ["Fruit", "Animal", "Vehicle", "Furniture"],
            "answer": "Vehicle"
        },
        {
            "item": "Lion",
            "options": ["Fruit", "Animal", "Vehicle", "Furniture"],
            "answer": "Animal"
        },
        {
            "item": "Mango",
            "options": ["Fruit", "Animal", "Vehicle", "Furniture"],
            "answer": "Fruit"
        }
    ]

    q = random.choice(sorting_questions)

    st.markdown(f"### Which category does **{q['item']}** belong to?")

    selected = st.radio("Choose category:", q["options"])

    if st.button("Check Sorting Answer"):
        if selected == q["answer"]:
            add_score()
            feedback(True)
        else:
            add_attempt()
            feedback(False)
            st.info(f"The correct category is: {q['answer']}")


# ---------------- PROGRESS REPORT ----------------
elif activity == "🏆 Progress Report":
    st.subheader("🏆 Progress Report")

    st.write("Here is the child's learning progress:")

    show_score()

    if st.session_state.attempts == 0:
        st.info("No activity attempted yet.")
    else:
        accuracy = round((st.session_state.score / st.session_state.attempts) * 100, 1)

        if accuracy >= 80:
            st.success("Excellent performance! The child is learning very well.")
        elif accuracy >= 50:
            st.warning("Good effort. More practice will improve the result.")
        else:
            st.error("The child needs more practice and guidance.")

    st.write("---")
    st.subheader("Teacher / Parent Suggestions")

    st.markdown("""
    To improve learning:

    1. Let the child practice 15 to 20 minutes daily.
    2. Start with easy activities.
    3. Encourage the child after every attempt.
    4. Use real-life examples like shopping, traffic rules, and classroom habits.
    5. Repeat memory and pattern games to improve thinking skills.
    """)

# ---------------- FOOTER ----------------
st.write("---")
st.caption("Made with Python and Streamlit for kids' learning and problem-solving.")