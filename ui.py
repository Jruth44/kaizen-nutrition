# ui.py
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
from models import NutritionCoach
from utils import save_user_data, create_weekly_schedule
import pandas as pd
from typing import Dict
from datetime import datetime

def display_tracker_page(users):
    """Displays the food tracker page."""
    # ... (Implementation later)

def display_coach_page(users):
    """Displays the AI/human coach interaction page."""
    # ... (Implementation later)

def display_calendar_page(users):
    """Displays the meal planning calendar."""
    # ... (Implementation later)

def display_group_page(users):
    """Displays the group interaction page."""
    # ... (Implementation later)

def display_profile_page(users):
    st.header("User Profile")

    # Select user (for now, let's assume a single user for simplicity)
    # In a real app, you'd have a login system and user selection
    user_id = "user1"  # Replace with actual user ID later

    if user_id not in users:
        users[user_id] = {
            "profile": {},
            "meals": {}  # Initialize meals data for the new user
        }

    # Get the user's profile data
    user_profile = users[user_id]["profile"]

    # --- Profile Form ---
    with st.form("profile_form"):
        st.subheader("Personal Information")
        name = st.text_input("Name", value=user_profile.get("name", ""))
        weight = st.number_input("Weight (lbs)", min_value=0.0, value=float(user_profile.get("weight", 0.0)))
        height = st.number_input("Height (inches)", min_value=0, value=user_profile.get("height", 0))
        age = st.number_input("Age", min_value=0, value=user_profile.get("age", 0))
        biological_sex = st.selectbox("Biological Sex", ["Male", "Female"], index=["Male", "Female"].index(user_profile.get("biological_sex")) if user_profile.get("biological_sex") else 0)

        st.subheader("Dietary Restrictions")
        dietary_restrictions = st.multiselect(
            "Select all that apply",
            [
                "Vegetarian",
                "Vegan",
                "Gluten-Free",
                "Dairy-Free",
                "Nut Allergies",
                "Soy Allergy",
                "Other",
            ],
            default=user_profile.get("dietary_restrictions", []),
        )
        # Handle "Other" restriction
        if "Other" in dietary_restrictions:
            other_restriction = st.text_input("Specify other restriction")
            if other_restriction:
                dietary_restrictions.append(other_restriction)
                dietary_restrictions.remove("Other")

        st.subheader("Goal and Activity")
        goal = st.selectbox(
            "Goal",
            ["Cutting", "Bulking", "Maintenance", "Reverse Diet"],
            index=["Cutting", "Bulking", "Maintenance", "Reverse Diet"].index(user_profile.get("goal"))
            if user_profile.get("goal")
            else 0,
        )
        activity_level = st.selectbox(
            "Activity Level",
            [
                "Sedentary",
                "Lightly Active",
                "Moderately Active",
                "Very Active",
                "Extremely Active",
            ],
            index=[
                "Sedentary",
                "Lightly Active",
                "Moderately Active",
                "Very Active",
                "Extremely Active",
            ].index(user_profile.get("activity_level"))
            if user_profile.get("activity_level")
            else 0,
        )

        st.subheader("Protein Target")
        protein_target = st.slider(
            "Protein per lb of lean body mass",
            min_value=0.6,
            max_value=1.4,
            value=float(user_profile.get("protein_target", 0.8)),
            step=0.1,
        )
        
        st.subheader("Lean Body Mass")
        lean_body_mass = st.number_input(
            "Lean Body Mass (lbs) (Leave 0 if unknown)",
            min_value=0.0,
            value=float(user_profile.get("lean_body_mass", 0.0)),
            step=0.1,
        )

        # Save Profile Button
        submit_button = st.form_submit_button("Save Profile")

    if submit_button:
        # Update the user's profile
        user_profile["name"] = name
        user_profile["weight"] = weight
        user_profile["height"] = height
        user_profile["age"] = age
        user_profile["biological_sex"] = biological_sex
        user_profile["dietary_restrictions"] = dietary_restrictions
        user_profile["goal"] = goal
        user_profile["activity_level"] = activity_level
        user_profile["protein_target"] = protein_target
        user_profile["lean_body_mass"] = lean_body_mass

        # Save the updated data (using the function from utils.py)
        save_user_data(users)
        st.success("Profile saved successfully!")

def display_weekly_schedule_table(schedule_data, users, selected_user=None):
    """Displays the weekly schedule using Ag-Grid."""
    if selected_user:
        data = []
        for day, meals in schedule_data.items():
            for meal_type, meal_details in meals.items():
                data.append(
                    {
                        "Day": day,
                        "Meal Type": meal_type,
                        "Meal Name": meal_details["meal_name"],
                        "Details": meal_details["instructions"],
                    }
                )
        df = pd.DataFrame(data)
    else:
        data = []
        for day, entries in schedule_data.items():
            for entry in entries:
                data.append({"Day": day, "Appointment": entry})
        df = pd.DataFrame(data)

    if not df.empty:
        if "Day" not in df.columns:
            df["Day"] = ""

        days_order = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        # Check if 'Day' column exists and create it if it doesn't
        if "Day" not in df.columns:
            df["Day"] = ""  # or some default value, or another logic to fill it

        # Check if 'Day' column has the expected categories before setting the category type
        if set(df["Day"].unique()).issubset(set(days_order)):
            df["Day"] = pd.Categorical(df["Day"], categories=days_order, ordered=True)
            df = df.sort_values("Day")
        else:
            print("Warning: 'Day' column contains unexpected values. Skipping sorting.")

        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(
            groupable=True, value=True, enableRowGroup=True, autoHeight=True, wrapText=True
        )
        gb.configure_grid_options(domLayout="normal")

        if selected_user:
            gb.configure_selection("multiple", use_checkbox=False)
            gb.configure_column(
                "Day",
                editable=False,
                cellEditor="agSelectCellEditor",
                cellEditorParams={"values": days_order},
            )
            gb.configure_column("Meal Type", editable=True)
            gb.configure_column("Meal Name", editable=True)
            gb.configure_column("Details", editable=True)

        gridOptions = gb.build()

        grid_response = AgGrid(
            df,
            gridOptions=gridOptions,
            data_return_mode=DataReturnMode.AS_INPUT,
            update_mode=GridUpdateMode.MODEL_CHANGED
            if selected_user
            else GridUpdateMode.VALUE_CHANGED,
            fit_columns_on_grid_load=True,
            allow_unsafe_jscode=True,
            enable_enterprise_modules=False,
            height=350,
            width="100%",
            reload_data=False,
        )

def display_meal_plan_page(users):
    st.header("Meal Plan")

    user_id = "user1"  # Replace with actual user ID later
    if user_id not in users or "profile" not in users[user_id] or "targets" not in users[user_id]:
        st.warning("Please complete your profile and calculate targets first.")
        return

    num_days = st.number_input("Number of days for meal plan", min_value=1, max_value=7, value=3)

    if st.button("Generate Meal Plan"):
        nutrition_coach = NutritionCoach()
        users[user_id] = nutrition_coach.generate_meal_plan(users[user_id], num_days)
        save_user_data(users)
        st.success("Meal plan generated!")

    # Display the meal plan if it exists
    if "meals" in users[user_id]:
        display_weekly_schedule_table(users[user_id]["meals"], users, user_id)


