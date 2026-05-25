import streamlit as st
from datetime import date


# Page setting
st.set_page_config(
    page_title="Age Calculator",
    page_icon="🎂",
    layout="centered"
)


st.title("🎂 Age Calculator App")
st.write("Enter your date of birth and calculate your exact age.")


# Function to calculate age
def calculate_age(dob):
    today = date.today()

    years = today.year - dob.year
    months = today.month - dob.month
    days = today.day - dob.day

    # If days are negative, borrow days from previous month
    if days < 0:
        months -= 1

        # Find previous month
        previous_month = today.month - 1
        previous_year = today.year

        if previous_month == 0:
            previous_month = 12
            previous_year -= 1

        # Days in previous month
        if previous_month in [1, 3, 5, 7, 8, 10, 12]:
            days += 31
        elif previous_month in [4, 6, 9, 11]:
            days += 30
        else:
            # February leap year check
            if (previous_year % 4 == 0 and previous_year % 100 != 0) or (previous_year % 400 == 0):
                days += 29
            else:
                days += 28

    # If months are negative, borrow one year
    if months < 0:
        years -= 1
        months += 12

    return years, months, days


# Date input
dob = st.date_input(
    "Select your date of birth:",
    min_value=date(1900, 1, 1),
    max_value=date.today()
)


# Button
if st.button("Calculate Age"):
    years, months, days = calculate_age(dob)

    st.success("Your age is:")

    st.subheader(f"{years} Years, {months} Months, and {days} Days")

    # Extra information
    total_days = (date.today() - dob).days
    total_months = years * 12 + months
    total_weeks = total_days // 7

    st.write("### More Details")
    st.write(f"Total months: **{total_months} months**")
    st.write(f"Total weeks: **{total_weeks} weeks**")
    st.write(f"Total days: **{total_days} days**")