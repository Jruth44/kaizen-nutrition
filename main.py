# main.py
import streamlit as st
from ui import (
    display_tracker_page,
    display_coach_page,
    display_calendar_page,
    display_group_page,
    display_profile_page,
    display_meal_plan_page
)
from utils import load_user_data, save_user_data
from models import NutritionCoach


def main():
    st.title("Nutrition Coach App")

    # Load user data (replace with actual loading logic)
    users = load_user_data()

    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Select Page",
        ["Tracker", "Coach", "Calendar", "Profile", "Meal Plan"],  # Add "Meal Plan" here
    )

    # Display the selected page
    if page == "Tracker":
        display_tracker_page(users)
    elif page == "Coach":
        display_coach_page(users)
    elif page == "Calendar":
        display_calendar_page(users)
    elif page == "Group":
        display_group_page(users)
    elif page == "Profile":
        display_profile_page(users)
    elif page == "Meal Plan":
        display_meal_plan_page(users)

if __name__ == "__main__":
    main()