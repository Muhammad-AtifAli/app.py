import ast
import calendar
import math
from datetime import date, timedelta

import streamlit as st


# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="Daily Calculator",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CUSTOM DESIGN
# =========================================================

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }

        [data-testid="stMetric"] {
            background-color: rgba(128, 128, 128, 0.08);
            border: 1px solid rgba(128, 128, 128, 0.20);
            padding: 15px;
            border-radius: 12px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def format_number(value, decimal_places=2):
    """Format a number and remove unnecessary zeros."""

    formatted = f"{value:,.{decimal_places}f}"
    return formatted.rstrip("0").rstrip(".")


def format_money(value):
    """Format an amount as Pakistani rupees."""

    return f"Rs. {value:,.2f}"


def calculate_age(birth_date, calculation_date):
    """Calculate age in years, months and days."""

    years = calculation_date.year - birth_date.year
    months = calculation_date.month - birth_date.month
    days = calculation_date.day - birth_date.day

    if days < 0:
        months -= 1

        previous_month = calculation_date.month - 1

        if previous_month == 0:
            previous_month = 12
            previous_year = calculation_date.year - 1
        else:
            previous_year = calculation_date.year

        days += calendar.monthrange(
            previous_year,
            previous_month,
        )[1]

    if months < 0:
        years -= 1
        months += 12

    return years, months, days


# =========================================================
# SAFE SCIENTIFIC CALCULATOR
# =========================================================

ALLOWED_FUNCTIONS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log10,
    "ln": math.log,
    "abs": abs,
    "round": round,
    "floor": math.floor,
    "ceil": math.ceil,
    "factorial": math.factorial,
    "radians": math.radians,
    "degrees": math.degrees,
}

ALLOWED_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
}


def safe_calculate(expression):
    """Safely evaluate mathematical expressions."""

    expression = expression.replace("^", "**").strip()

    tree = ast.parse(expression, mode="eval")

    def evaluate(node):

        if isinstance(node, ast.Expression):
            return evaluate(node.body)

        if isinstance(node, ast.Constant):

            if isinstance(node.value, (int, float)):
                return node.value

            raise ValueError("Only numbers are allowed.")

        if isinstance(node, ast.Name):

            if node.id in ALLOWED_CONSTANTS:
                return ALLOWED_CONSTANTS[node.id]

            raise ValueError(f"Unknown value: {node.id}")

        if isinstance(node, ast.BinOp):

            left = evaluate(node.left)
            right = evaluate(node.right)

            if isinstance(node.op, ast.Add):
                return left + right

            if isinstance(node.op, ast.Sub):
                return left - right

            if isinstance(node.op, ast.Mult):
                return left * right

            if isinstance(node.op, ast.Div):

                if right == 0:
                    raise ZeroDivisionError("Cannot divide by zero.")

                return left / right

            if isinstance(node.op, ast.FloorDiv):

                if right == 0:
                    raise ZeroDivisionError("Cannot divide by zero.")

                return left // right

            if isinstance(node.op, ast.Mod):

                if right == 0:
                    raise ZeroDivisionError(
                        "Cannot calculate remainder using zero."
                    )

                return left % right

            if isinstance(node.op, ast.Pow):
                return left ** right

        if isinstance(node, ast.UnaryOp):

            value = evaluate(node.operand)

            if isinstance(node.op, ast.UAdd):
                return value

            if isinstance(node.op, ast.USub):
                return -value

        if isinstance(node, ast.Call):

            if not isinstance(node.func, ast.Name):
                raise ValueError("Invalid function.")

            function_name = node.func.id

            if function_name not in ALLOWED_FUNCTIONS:
                raise ValueError(
                    f"Function '{function_name}' is not supported."
                )

            arguments = [
                evaluate(argument)
                for argument in node.args
            ]

            return ALLOWED_FUNCTIONS[function_name](*arguments)

        raise ValueError("Invalid mathematical expression.")

    return evaluate(tree)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("🧮 Daily Calculator")

page = st.sidebar.radio(
    "Select Calculator",
    [
        "Home",
        "Basic Calculator",
        "Percentage Calculator",
        "Discount Calculator",
        "Profit and Loss",
        "Loan EMI Calculator",
        "Bill and Tip Calculator",
        "BMI Calculator",
        "Age Calculator",
        "Date Difference",
        "Unit Converter",
        "Fuel Calculator",
        "GPA Calculator",
        "Currency Converter",
    ],
)


# =========================================================
# HOME PAGE
# =========================================================

if page == "Home":

    st.title("🧮 Daily Calculator")

    st.write(
        """
        This application contains calculators for:

        - Basic and scientific calculations
        - Percentages
        - Discounts
        - Profit and loss
        - Loan instalments
        - Bills, tax and tips
        - BMI
        - Age and date difference
        - Unit conversion
        - Fuel calculations
        - GPA
        - Currency conversion
        """
    )


# =========================================================
# BASIC CALCULATOR
# =========================================================

elif page == "Basic Calculator":

    st.title("Basic and Scientific Calculator")

    expression = st.text_input(
        "Enter calculation",
        value="25 + 15 * 2",
        placeholder="Example: sqrt(144) + 5^2",
    )

    decimal_places = st.number_input(
        "Decimal places",
        min_value=0,
        max_value=10,
        value=4,
        step=1,
    )

    if st.button(
        "Calculate",
        type="primary",
        use_container_width=True,
    ):

        try:

            result = safe_calculate(expression)

            st.success(
                f"Answer: "
                f"{format_number(result, decimal_places)}"
            )

        except Exception as error:

            st.error(str(error))

    st.info(
        """
        Examples:

        `25 + 10`

        `100 / 4`

        `sqrt(144)`

        `5^2`

        `sin(radians(30))`

        `log(100)`
        """
    )

    st.divider()

    st.subheader("Quick Calculator")

    column1, column2 = st.columns(2)

    first_number = column1.number_input(
        "First number",
        value=0.0,
    )

    second_number = column2.number_input(
        "Second number",
        value=0.0,
    )

    operation = st.selectbox(
        "Select operation",
        [
            "Addition",
            "Subtraction",
            "Multiplication",
            "Division",
            "Power",
            "Remainder",
            "Average",
        ],
    )

    if st.button("Calculate Result"):

        try:

            if operation == "Addition":
                result = first_number + second_number

            elif operation == "Subtraction":
                result = first_number - second_number

            elif operation == "Multiplication":
                result = first_number * second_number

            elif operation == "Division":

                if second_number == 0:
                    raise ZeroDivisionError(
                        "Cannot divide by zero."
                    )

                result = first_number / second_number

            elif operation == "Power":
                result = first_number ** second_number

            elif operation == "Remainder":

                if second_number == 0:
                    raise ZeroDivisionError(
                        "Cannot calculate remainder using zero."
                    )

                result = first_number % second_number

            else:
                result = (
                    first_number + second_number
                ) / 2

            st.metric(
                "Result",
                format_number(result, 6),
            )

        except Exception as error:

            st.error(str(error))


# =========================================================
# PERCENTAGE CALCULATOR
# =========================================================

elif page == "Percentage Calculator":

    st.title("Percentage Calculator")

    tab1, tab2, tab3 = st.tabs(
        [
            "Percentage of Number",
            "Find Percentage",
            "Percentage Change",
        ]
    )

    with tab1:

        percentage = st.number_input(
            "Percentage",
            value=10.0,
            key="percentage",
        )

        number = st.number_input(
            "Number",
            value=1000.0,
            key="percentage_number",
        )

        result = number * percentage / 100

        st.success(
            f"{percentage}% of {number} = "
            f"{result:,.2f}"
        )

    with tab2:

        part = st.number_input(
            "Part value",
            value=20.0,
            key="part",
        )

        total = st.number_input(
            "Total value",
            value=100.0,
            key="total",
        )

        if total != 0:

            result = part / total * 100

            st.success(
                f"Percentage = {result:,.2f}%"
            )

        else:

            st.error(
                "Total value cannot be zero."
            )

    with tab3:

        old_value = st.number_input(
            "Old value",
            value=100.0,
            key="old_value",
        )

        new_value = st.number_input(
            "New value",
            value=120.0,
            key="new_value",
        )

        if old_value != 0:

            change = (
                new_value - old_value
            ) / abs(old_value) * 100

            if change >= 0:

                st.success(
                    f"Percentage increase: "
                    f"{change:,.2f}%"
                )

            else:

                st.error(
                    f"Percentage decrease: "
                    f"{abs(change):,.2f}%"
                )

        else:

            st.error(
                "Old value cannot be zero."
            )


# =========================================================
# DISCOUNT CALCULATOR
# =========================================================

elif page == "Discount Calculator":

    st.title("Discount Calculator")

    column1, column2 = st.columns(2)

    original_price = column1.number_input(
        "Original price",
        min_value=0.0,
        value=5000.0,
    )

    discount_percentage = column2.number_input(
        "Discount percentage",
        min_value=0.0,
        max_value=100.0,
        value=10.0,
    )

    discount_amount = (
        original_price
        * discount_percentage
        / 100
    )

    final_price = (
        original_price
        - discount_amount
    )

    column1, column2 = st.columns(2)

    column1.metric(
        "Discount Amount",
        format_money(discount_amount),
    )

    column2.metric(
        "Final Price",
        format_money(final_price),
    )


# =========================================================
# PROFIT AND LOSS
# =========================================================

elif page == "Profit and Loss":

    st.title("Profit and Loss Calculator")

    column1, column2 = st.columns(2)

    cost_price = column1.number_input(
        "Cost price",
        min_value=0.0,
        value=1000.0,
    )

    selling_price = column2.number_input(
        "Selling price",
        min_value=0.0,
        value=1200.0,
    )

    difference = (
        selling_price - cost_price
    )

    if cost_price > 0:

        percentage = (
            abs(difference)
            / cost_price
            * 100
        )

        if difference > 0:

            st.success(
                f"Profit: {format_money(difference)}"
            )

            st.metric(
                "Profit Percentage",
                f"{percentage:,.2f}%",
            )

        elif difference < 0:

            st.error(
                f"Loss: {format_money(abs(difference))}"
            )

            st.metric(
                "Loss Percentage",
                f"{percentage:,.2f}%",
            )

        else:

            st.info(
                "No profit and no loss."
            )

    else:

        st.error(
            "Cost price must be greater than zero."
        )


# =========================================================
# LOAN EMI CALCULATOR
# =========================================================

elif page == "Loan EMI Calculator":

    st.title("Loan EMI Calculator")

    column1, column2, column3 = st.columns(3)

    loan_amount = column1.number_input(
        "Loan amount",
        min_value=0.0,
        value=500000.0,
    )

    annual_rate = column2.number_input(
        "Annual loan rate (%)",
        min_value=0.0,
        value=15.0,
    )

    loan_years = column3.number_input(
        "Loan period in years",
        min_value=1,
        value=5,
    )

    months = loan_years * 12
    monthly_rate = annual_rate / 12 / 100

    if monthly_rate == 0:

        monthly_payment = (
            loan_amount / months
        )

    else:

        monthly_payment = (
            loan_amount
            * monthly_rate
            * (1 + monthly_rate) ** months
        ) / (
            (1 + monthly_rate) ** months - 1
        )

    total_payment = (
        monthly_payment * months
    )

    additional_cost = (
        total_payment - loan_amount
    )

    column1, column2, column3 = st.columns(3)

    column1.metric(
        "Monthly EMI",
        format_money(monthly_payment),
    )

    column2.metric(
        "Additional Loan Cost",
        format_money(additional_cost),
    )

    column3.metric(
        "Total Repayment",
        format_money(total_payment),
    )


# =========================================================
# BILL AND TIP CALCULATOR
# =========================================================

elif page == "Bill and Tip Calculator":

    st.title("Bill, Tax and Tip Calculator")

    column1, column2, column3 = st.columns(3)

    bill_amount = column1.number_input(
        "Bill amount",
        min_value=0.0,
        value=3000.0,
    )

    tax_percentage = column2.number_input(
        "Tax percentage",
        min_value=0.0,
        value=16.0,
    )

    tip_percentage = column3.number_input(
        "Tip percentage",
        min_value=0.0,
        value=5.0,
    )

    people = st.number_input(
        "Number of people",
        min_value=1,
        value=2,
    )

    tax_amount = (
        bill_amount
        * tax_percentage
        / 100
    )

    tip_amount = (
        bill_amount
        * tip_percentage
        / 100
    )

    total_bill = (
        bill_amount
        + tax_amount
        + tip_amount
    )

    per_person = (
        total_bill / people
    )

    column1, column2, column3, column4 = st.columns(4)

    column1.metric(
        "Tax",
        format_money(tax_amount),
    )

    column2.metric(
        "Tip",
        format_money(tip_amount),
    )

    column3.metric(
        "Total Bill",
        format_money(total_bill),
    )

    column4.metric(
        "Per Person",
        format_money(per_person),
    )


# =========================================================
# BMI CALCULATOR
# =========================================================

elif page == "BMI Calculator":

    st.title("BMI Calculator")

    column1, column2 = st.columns(2)

    weight = column1.number_input(
        "Weight in kilograms",
        min_value=1.0,
        value=70.0,
    )

    height_cm = column2.number_input(
        "Height in centimetres",
        min_value=50.0,
        value=170.0,
    )

    height_m = height_cm / 100

    bmi = weight / (height_m ** 2)

    if bmi < 18.5:
        category = "Underweight"

    elif bmi < 25:
        category = "Healthy Range"

    elif bmi < 30:
        category = "Overweight"

    else:
        category = "Obesity Range"

    column1, column2 = st.columns(2)

    column1.metric(
        "BMI",
        f"{bmi:,.2f}",
    )

    column2.metric(
        "Category",
        category,
    )

    st.warning(
        "BMI is only a general screening measurement."
    )


# =========================================================
# AGE CALCULATOR
# =========================================================

elif page == "Age Calculator":

    st.title("Age Calculator")

    column1, column2 = st.columns(2)

    birth_date = column1.date_input(
        "Date of birth",
        value=date(1990, 1, 1),
        max_value=date.today(),
    )

    calculation_date = column2.date_input(
        "Calculate age on",
        value=date.today(),
    )

    if calculation_date >= birth_date:

        years, months, days = calculate_age(
            birth_date,
            calculation_date,
        )

        total_days = (
            calculation_date - birth_date
        ).days

        st.success(
            f"Age: {years} years, "
            f"{months} months and {days} days"
        )

        st.metric(
            "Total Days",
            f"{total_days:,}",
        )

    else:

        st.error(
            "Calculation date cannot be before the date of birth."
        )


# =========================================================
# DATE DIFFERENCE
# =========================================================

elif page == "Date Difference":

    st.title("Date Difference Calculator")

    column1, column2 = st.columns(2)

    start_date = column1.date_input(
        "Start date",
        value=date.today(),
    )

    end_date = column2.date_input(
        "End date",
        value=date.today() + timedelta(days=30),
    )

    difference = end_date - start_date

    total_days = difference.days

    column1, column2, column3 = st.columns(3)

    column1.metric(
        "Days",
        total_days,
    )

    column2.metric(
        "Weeks",
        f"{abs(total_days) / 7:,.2f}",
    )

    column3.metric(
        "Approximate Months",
        f"{abs(total_days) / 30.4375:,.2f}",
    )


# =========================================================
# UNIT CONVERTER
# =========================================================

elif page == "Unit Converter":

    st.title("Unit Converter")

    category = st.selectbox(
        "Select category",
        [
            "Length",
            "Weight",
            "Temperature",
            "Area",
        ],
    )

    value = st.number_input(
        "Enter value",
        value=1.0,
    )

    if category == "Length":

        units = {
            "Millimetre": 0.001,
            "Centimetre": 0.01,
            "Metre": 1,
            "Kilometre": 1000,
            "Inch": 0.0254,
            "Foot": 0.3048,
            "Yard": 0.9144,
            "Mile": 1609.344,
        }

    elif category == "Weight":

        units = {
            "Milligram": 0.000001,
            "Gram": 0.001,
            "Kilogram": 1,
            "Tonne": 1000,
            "Ounce": 0.0283495,
            "Pound": 0.453592,
        }

    elif category == "Area":

        units = {
            "Square Metre": 1,
            "Square Kilometre": 1000000,
            "Square Foot": 0.092903,
            "Square Yard": 0.836127,
            "Acre": 4046.856,
            "Hectare": 10000,
        }

    else:

        units = None

    if category == "Temperature":

        temperature_units = [
            "Celsius",
            "Fahrenheit",
            "Kelvin",
        ]

        column1, column2 = st.columns(2)

        from_unit = column1.selectbox(
            "Convert from",
            temperature_units,
        )

        to_unit = column2.selectbox(
            "Convert to",
            temperature_units,
            index=1,
        )

        if from_unit == "Celsius":
            celsius = value

        elif from_unit == "Fahrenheit":
            celsius = (value - 32) * 5 / 9

        else:
            celsius = value - 273.15

        if to_unit == "Celsius":
            result = celsius

        elif to_unit == "Fahrenheit":
            result = celsius * 9 / 5 + 32

        else:
            result = celsius + 273.15

    else:

        column1, column2 = st.columns(2)

        from_unit = column1.selectbox(
            "Convert from",
            list(units.keys()),
        )

        to_unit = column2.selectbox(
            "Convert to",
            list(units.keys()),
            index=1,
        )

        result = (
            value * units[from_unit]
        ) / units[to_unit]

    st.success(
        f"{format_number(value, 6)} {from_unit} = "
        f"{format_number(result, 6)} {to_unit}"
    )


# =========================================================
# FUEL CALCULATOR
# =========================================================

elif page == "Fuel Calculator":

    st.title("Fuel Calculator")

    tab1, tab2 = st.tabs(
        [
            "Fuel Average",
            "Trip Cost",
        ]
    )

    with tab1:

        distance = st.number_input(
            "Distance travelled in kilometres",
            min_value=0.0,
            value=300.0,
        )

        fuel_used = st.number_input(
            "Fuel used in litres",
            min_value=0.01,
            value=25.0,
        )

        average = distance / fuel_used

        st.metric(
            "Fuel Average",
            f"{average:,.2f} km/litre",
        )

    with tab2:

        distance = st.number_input(
            "Trip distance in kilometres",
            min_value=0.0,
            value=500.0,
            key="trip_distance",
        )

        vehicle_average = st.number_input(
            "Vehicle average in km/litre",
            min_value=0.01,
            value=12.0,
        )

        fuel_price = st.number_input(
            "Fuel price per litre",
            min_value=0.0,
            value=260.0,
        )

        people = st.number_input(
            "People sharing the cost",
            min_value=1,
            value=1,
        )

        fuel_required = (
            distance / vehicle_average
        )

        total_cost = (
            fuel_required * fuel_price
        )

        cost_per_person = (
            total_cost / people
        )

        column1, column2, column3 = st.columns(3)

        column1.metric(
            "Fuel Required",
            f"{fuel_required:,.2f} litres",
        )

        column2.metric(
            "Trip Cost",
            format_money(total_cost),
        )

        column3.metric(
            "Cost Per Person",
            format_money(cost_per_person),
        )


# =========================================================
# GPA CALCULATOR
# =========================================================

elif page == "GPA Calculator":

    st.title("GPA Calculator")

    number_of_subjects = st.number_input(
        "Number of subjects",
        min_value=1,
        max_value=20,
        value=5,
    )

    total_credit_hours = 0
    total_quality_points = 0
    subject_information = []

    for subject_number in range(
        int(number_of_subjects)
    ):

        st.subheader(
            f"Subject {subject_number + 1}"
        )

        column1, column2, column3 = st.columns(
            [2, 1, 1]
        )

        subject_name = column1.text_input(
            "Subject name",
            value=f"Subject {subject_number + 1}",
            key=f"subject_{subject_number}",
        )

        credit_hours = column2.number_input(
            "Credit hours",
            min_value=0.0,
            value=3.0,
            key=f"credit_{subject_number}",
        )

        grade_point = column3.number_input(
            "Grade point",
            min_value=0.0,
            max_value=5.0,
            value=3.0,
            key=f"grade_{subject_number}",
        )

        quality_points = (
            credit_hours * grade_point
        )

        total_credit_hours += credit_hours
        total_quality_points += quality_points

        subject_information.append(
            {
                "Subject": subject_name,
                "Credit Hours": credit_hours,
                "Grade Point": grade_point,
                "Quality Points": quality_points,
            }
        )

    if total_credit_hours > 0:

        gpa = (
            total_quality_points
            / total_credit_hours
        )

    else:

        gpa = 0

    st.metric(
        "Calculated GPA",
        f"{gpa:,.3f}",
    )

    st.dataframe(
        subject_information,
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# CURRENCY CONVERTER
# =========================================================

elif page == "Currency Converter":

    st.title("Currency Converter")

    column1, column2 = st.columns(2)

    source_currency = column1.text_input(
        "Source currency",
        value="USD",
    ).upper()

    target_currency = column2.text_input(
        "Target currency",
        value="PKR",
    ).upper()

    column1, column2 = st.columns(2)

    amount = column1.number_input(
        f"Amount in {source_currency}",
        min_value=0.0,
        value=100.0,
    )

    exchange_rate = column2.number_input(
        f"1 {source_currency} equals how many {target_currency}?",
        min_value=0.0,
        value=280.0,
    )

    converted_amount = (
        amount * exchange_rate
    )

    st.success(
        f"{amount:,.2f} {source_currency} = "
        f"{converted_amount:,.2f} {target_currency}"
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Daily Calculator developed with Python and Streamlit"
)