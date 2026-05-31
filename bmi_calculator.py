import streamlit as st

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="BMI Health Calculator",
    page_icon="⚖️",
    layout="centered"
)

# ---------------- CSS DESIGN ----------------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f0f9ff, #ecfeff, #f8fafc);
    }

    .main-heading {
        text-align: center;
        font-size: 46px;
        font-weight: 900;
        color: #0f766e;
        margin-top: 10px;
        margin-bottom: 5px;
    }

    .sub-heading {
        text-align: center;
        font-size: 18px;
        color: #475569;
        margin-bottom: 30px;
    }

    .input-card {
        background-color: #ffffff;
        padding: 30px;
        border-radius: 22px;
        box-shadow: 0px 10px 30px rgba(15, 118, 110, 0.15);
        border: 1px solid #ccfbf1;
        margin-bottom: 25px;
    }

    .section-title {
        font-size: 25px;
        font-weight: 800;
        color: #115e59;
        margin-bottom: 15px;
    }

    .result-card {
        background: linear-gradient(135deg, #ecfdf5, #d1fae5);
        padding: 25px;
        border-radius: 20px;
        border-left: 8px solid #10b981;
        margin-top: 25px;
        box-shadow: 0px 6px 18px rgba(0,0,0,0.08);
    }

    .underweight-card {
        background: linear-gradient(135deg, #fff7ed, #ffedd5);
        padding: 25px;
        border-radius: 20px;
        border-left: 8px solid #f97316;
        margin-top: 25px;
        box-shadow: 0px 6px 18px rgba(0,0,0,0.08);
    }

    .overweight-card {
        background: linear-gradient(135deg, #eff6ff, #dbeafe);
        padding: 25px;
        border-radius: 20px;
        border-left: 8px solid #2563eb;
        margin-top: 25px;
        box-shadow: 0px 6px 18px rgba(0,0,0,0.08);
    }

    .obese-card {
        background: linear-gradient(135deg, #fef2f2, #fee2e2);
        padding: 25px;
        border-radius: 20px;
        border-left: 8px solid #dc2626;
        margin-top: 25px;
        box-shadow: 0px 6px 18px rgba(0,0,0,0.08);
    }

    .stButton>button {
        background: linear-gradient(135deg, #14b8a6, #0f766e);
        color: white;
        font-size: 20px;
        font-weight: 800;
        border: none;
        border-radius: 15px;
        padding: 14px;
        width: 100%;
    }

    .stButton>button:hover {
        background: linear-gradient(135deg, #0d9488, #115e59);
        color: white;
    }

    .footer-note {
        text-align: center;
        color: #64748b;
        font-size: 15px;
        margin-top: 25px;
    }
</style>
""", unsafe_allow_html=True)


# ---------------- FUNCTIONS ----------------
def calculate_bmi(weight_kg, height_m):
    bmi = weight_kg / (height_m ** 2)
    return bmi


def get_bmi_category(bmi):
    if bmi < 18.5:
        return (
            "Underweight",
            "underweight-card",
            "Your weight is below the normal range."
        )
    elif 18.5 <= bmi < 25:
        return (
            "Normal Weight",
            "result-card",
            "Excellent! Your BMI is within the healthy range."
        )
    elif 25 <= bmi < 30:
        return (
            "Overweight",
            "overweight-card",
            "Your weight is above the normal range."
        )
    else:
        return (
            "Obese",
            "obese-card",
            "Your BMI is in the obesity range. Please consider health guidance."
        )


def show_result(bmi, height_m):
    category, card_class, message = get_bmi_category(bmi)

    healthy_min = 18.5 * (height_m ** 2)
    healthy_max = 24.9 * (height_m ** 2)

    st.markdown(f"""
    <div class="{card_class}">
        <h2>📊 BMI Result</h2>
        <h1>{bmi:.2f}</h1>
        <h3>Category: {category}</h3>
        <p>{message}</p>
        <p><b>Healthy Weight Range:</b> {healthy_min:.1f} kg to {healthy_max:.1f} kg</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### BMI Category Guide")

    st.table({
        "BMI Range": [
            "Below 18.5",
            "18.5 - 24.9",
            "25.0 - 29.9",
            "30.0 and above"
        ],
        "Category": [
            "Underweight",
            "Normal Weight",
            "Overweight",
            "Obese"
        ]
    })


# ---------------- MAIN HEADING ----------------
st.markdown(
    '<div class="main-heading">BMI Health Calculator</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-heading">Calculate your BMI using height in feet/inches and weight in kilograms</div>',
    unsafe_allow_html=True
)

# ---------------- INPUT CARD ----------------
st.markdown('<div class="input-card">', unsafe_allow_html=True)

st.markdown(
    '<div class="section-title">Enter Your Information</div>',
    unsafe_allow_html=True
)

# ---------------- USER INPUTS ----------------
age = st.number_input(
    "Age",
    min_value=2,
    max_value=120,
    value=25,
    step=1
)

gender = st.radio(
    "Gender",
    ["Male", "Female"],
    horizontal=True
)

st.markdown("### Height")

col1, col2 = st.columns(2)

with col1:
    height_feet = st.number_input(
        "Feet",
        min_value=1,
        max_value=8,
        value=5,
        step=1
    )

with col2:
    height_inches = st.number_input(
        "Inches",
        min_value=0,
        max_value=11,
        value=7,
        step=1
    )

weight_kg = st.number_input(
    "Weight in KG",
    min_value=1.0,
    max_value=300.0,
    value=65.0,
    step=1.0
)

calculate = st.button("Calculate BMI")

# ---------------- CALCULATION ----------------
if calculate:
    total_inches = (height_feet * 12) + height_inches
    height_m = total_inches * 0.0254

    if height_m <= 0:
        st.error("Please enter a valid height.")
    elif weight_kg <= 0:
        st.error("Please enter a valid weight.")
    else:
        bmi = calculate_bmi(weight_kg, height_m)
        show_result(bmi, height_m)

st.markdown('</div>', unsafe_allow_html=True)

# ---------------- EXTRA HEALTH TIPS ----------------
st.markdown("## Health Suggestions")

st.info(
    "BMI is a general health indicator. It does not directly measure body fat, muscle mass, or medical condition."
)

with st.expander("Click here to read useful health tips"):
    st.write("""
    1. Eat a balanced diet including fruits, vegetables, protein, and whole grains.
    2. Drink enough water daily.
    3. Do regular walking or light exercise.
    4. Avoid excessive sugar, oily food, and soft drinks.
    5. Sleep properly and follow a healthy daily routine.
    6. Consult a doctor or nutritionist for proper medical advice.
    """)

st.markdown(
    '<div class="footer-note">Developed with Python and Streamlit</div>',
    unsafe_allow_html=True
)