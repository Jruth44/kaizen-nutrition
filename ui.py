# ui.py
import streamlit as st
import json
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
from models import NutritionCoach
from utils import save_user_data, create_weekly_schedule
import pandas as pd
from typing import Dict
from datetime import datetime

def display_tracker_page(users):
    """Displays the food tracker page."""
    st.header("Food Tracker")

    user_id = "user1"  # Replace with actual user ID later
    if user_id not in users:
        st.warning("No user profile found. Please create one under 'Profile'.")
        return

    # Initialize a 'food_log' key if it doesn't exist
    if "food_log" not in users[user_id]:
        users[user_id]["food_log"] = []

    # Input form for adding a new food entry
    with st.form("food_entry_form"):
        st.subheader("Log a New Food Item")
        food_item = st.text_input("Food Item (e.g., 'Chicken Breast')")
        calories = st.number_input("Calories", min_value=0, value=0)
        protein = st.number_input("Protein (g)", min_value=0, value=0)
        fat = st.number_input("Fat (g)", min_value=0, value=0)
        carbs = st.number_input("Carbohydrates (g)", min_value=0, value=0)
        quantity = st.number_input("Quantity / Serving Size", min_value=1, value=1)

        submitted = st.form_submit_button("Add to Tracker")
        if submitted:
            # Append the entry to the user's food log
            entry = {
                "timestamp": datetime.now().isoformat(),
                "food_item": food_item,
                "calories": calories,
                "protein": protein,
                "fat": fat,
                "carbs": carbs,
                "quantity": quantity,
            }
            users[user_id]["food_log"].append(entry)
            save_user_data(users)
            st.success(f"Added {food_item} to the tracker!")

    # Display the current food log in a table
    if users[user_id]["food_log"]:
        st.subheader("Your Logged Foods")
        df_log = pd.DataFrame(users[user_id]["food_log"])
        AgGrid(df_log, fit_columns_on_grid_load=True)
    else:
        st.info("No foods logged yet.")

    if users[user_id]["food_log"]:
        st.subheader("Analyze a Food Entry")
        selected_entry = st.selectbox(
            "Select an entry to analyze",
            options=[f'{i}: {e["food_item"]}' for i, e in enumerate(users[user_id]["food_log"])]
        )
        if st.button("Analyze Selected Entry"):
            idx = int(selected_entry.split(":")[0])
            entry_text = users[user_id]["food_log"][idx]["food_item"]
            nutrition_coach = NutritionCoach()
            analysis_result = nutrition_coach.analyze_food_entry(users[user_id], entry_text)
            st.json(analysis_result)

def display_coach_page(users):
    """Displays the AI/human coach interaction page."""
    st.header("Ask the Coach")

    user_id = "user1"  # Replace with actual user ID later
    if user_id not in users:
        st.warning("No user profile found. Please create one under 'Profile'.")
        return

    # Initialize a conversation history if not present
    if "coach_chat" not in users[user_id]:
        users[user_id]["coach_chat"] = []

    # Chat display
    for msg in users[user_id]["coach_chat"]:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"**Coach:** {msg['content']}")

    # User input form
    with st.form("coach_form"):
        user_message = st.text_area("Type your question or message to the coach")
        submitted = st.form_submit_button("Send")
        if submitted and user_message.strip():
            # Append user message to conversation
            users[user_id]["coach_chat"].append({"role": "user", "content": user_message})

            # Get AI response
            nutrition_coach = NutritionCoach()
            response = nutrition_coach.get_ai_coach_response(users[user_id], user_message)
            # Append coach response
            users[user_id]["coach_chat"].append({"role": "assistant", "content": response})

            save_user_data(users)
            st.experimental_rerun()  # Refresh to show updated conversation


def display_calendar_page(users):
    """Displays the meal planning calendar."""
    st.header("Calendar")

    user_id = "user1"  # Replace with actual user ID later
    if user_id not in users:
        st.warning("No user profile found. Please create one under 'Profile'.")
        return

    # For demonstration, let's assume the meal plan was stored in `users[user_id]["meals"]`.
    # We'll show the schedule in a tabular format, similar to display_weekly_schedule_table().

    if "meals" not in users[user_id] or not users[user_id]["meals"]:
        st.info("No meal plan found. Generate one under the 'Meal Plan' page.")
        return

    st.subheader("Your Weekly Meal Calendar")
    meal_plan = users[user_id]["meals"]  # This is a dict with Day X => {Breakfast, Lunch, ...}

    # Convert to a format suitable for displaying with AgGrid
    data = []
    for day, meals in meal_plan.items():
        for meal_type, meal_details in meals.items():
            data.append({
                "Day": day,
                "Meal Type": meal_type,
                "Meal Name": meal_details["meal_name"],
                "Instructions": meal_details["instructions"]
            })

    df = pd.DataFrame(data)

    if not df.empty:
        AgGrid(df, fit_columns_on_grid_load=True)
    else:
        st.info("No data to display.")

def display_group_page(users):
    """Displays the group interaction page."""
    # ... (Implementation later)

def display_profile_page(users):
    st.header("User Profile")

    user_id = "user1"  # Replace with actual user ID logic
    if user_id not in users:
        users[user_id] = {
            "profile": {},
            "meals": {},
            "food_log": [],
            "coach_chat": []
        }

    user_profile = users[user_id]["profile"]

    # --- Profile Form ---
    with st.form("profile_form"):
        st.subheader("Personal Information")
        name = st.text_input("Name", value=user_profile.get("name", ""))
        weight = st.number_input("Weight (lbs)", min_value=0.0, value=float(user_profile.get("weight", 0.0)))
        height = st.number_input("Height (inches)", min_value=0, value=user_profile.get("height", 0))
        age = st.number_input("Age", min_value=0, value=user_profile.get("age", 0))
        biological_sex = st.selectbox(
            "Biological Sex", 
            ["Male", "Female"], 
            index=["Male", "Female"].index(user_profile.get("biological_sex")) if user_profile.get("biological_sex") else 0
        )

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
        # You can keep your "goal" if you still want it
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

        # New Rate of Progress
        st.subheader("Rate of Progress")
        # Example radio choices. Adjust text & values as needed
        progress_options = [
            "Lose 1 lb/week (recommended)",
            "Lose 0.5 lb/week",
            "Maintenance",
            "Gain 0.5 lb/week",
            "Gain 1 lb/week (recommended)"
        ]
        default_index = 2  # default "Maintenance"
        if user_profile.get("rate_of_progress") in progress_options:
            default_index = progress_options.index(user_profile["rate_of_progress"])

        rate_of_progress = st.radio("Select your weekly weight change target:", progress_options, index=default_index)

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

        submit_button = st.form_submit_button("Save Profile")

    # --- After Submit ---
    if submit_button:
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
        user_profile["rate_of_progress"] = rate_of_progress

        save_user_data(users)
        st.success("Profile saved successfully!")

        # Now automatically calculate macros (or you can do a separate button):
        nutrition_coach = NutritionCoach()
        users[user_id] = nutrition_coach.calculate_targets(users[user_id])
        save_user_data(users)
        st.success("Macro targets calculated!")

    # --- Display Macro Targets if they exist ---
    if "targets" in users[user_id]:
        st.subheader("Your Current Macro Targets")
        targets = users[user_id]["targets"]
        st.write(f"**Calories:** {targets['calories']}")
        st.write(f"**Protein:** {targets['protein']} g")
        st.write(f"**Fat:** {targets['fat']} g")
        st.write(f"**Carbohydrates:** {targets['carbohydrates']} g")

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

    user_id = "user1"  # Or however you're handling user login
    if user_id not in users or "profile" not in users[user_id] or "targets" not in users[user_id]:
        st.warning("Please complete your profile and calculate targets first.")
        return

    # Let user pick a start date and # days, or a date range
    st.subheader("Meal Plan Parameters")
    start_date = st.date_input("Select start date")
    num_days = st.number_input("Number of days for meal plan", min_value=1, max_value=14, value=3)

    # Example: checkboxes or radio for meal prep
    meal_prep_lunch = st.checkbox("Meal Prep Lunch for all days?", value=False)

    if st.button("Generate Meal Plan"):
        nutrition_coach = NutritionCoach()

        # Store your date + meal prep flags if needed
        users[user_id]["meal_plan_settings"] = {
            "start_date": str(start_date),
            "num_days": num_days,
            "meal_prep_lunch": meal_prep_lunch
        }

        # Possibly pass meal_prep_lunch to your generate function
        users[user_id] = nutrition_coach.generate_meal_plan(users[user_id], num_days, meal_prep=meal_prep_lunch)

        save_user_data(users)
        st.success("Meal plan generated!")

    # Display the meal plan if it exists
    if "meals" in users[user_id]:
        # We pass the entire data structure to a function that renders the interactive table
        display_interactive_meal_table(users[user_id]["meals"], users, user_id)

def display_interactive_meal_table(schedule_data, users, user_id):
    """
    Display an AgGrid table of the meal plan with clickable rows.
    When a row is selected, show detailed info in a separate container.
    """
    st.subheader("Your Meal Plan")

    # Convert to a DataFrame for AgGrid
    data = []
    for day, meals in schedule_data.items():
        for meal_type, meal_details in meals.items():
            data.append({
                "Day": day,
                "Meal Type": meal_type,
                "Meal Name": meal_details.get("meal_name", ""),
                # We'll store the entire meal_details in a hidden column so we can reference later
                "Meal Details": json.dumps(meal_details)  
            })

    df = pd.DataFrame(data)

    # Build AgGrid config
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(
        groupable=True, 
        value=True, 
        enableRowGroup=True, 
        autoHeight=True, 
        wrapText=True
    )
    gb.configure_selection("single")  # single row selection
    gb.configure_grid_options(domLayout="normal")
    gridOptions = gb.build()

    grid_response = AgGrid(
        df,
        gridOptions=gridOptions,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True,
        enable_enterprise_modules=False,
        height=350,
        width="100%",
        reload_data=False,
    )

    # Check if a row is selected
    if grid_response and grid_response["selected_rows"]:
        selected_row = grid_response["selected_rows"][0]  # single selection
        meal_json_str = selected_row.get("Meal Details", "")
        if meal_json_str:
            meal_details = json.loads(meal_json_str)

            # Display the detailed info here
            st.markdown("### Selected Meal Details")
            st.write(f"**Meal Name:** {meal_details.get('meal_name', '')}")
            
            # Ingredients
            ingredients = meal_details.get("ingredients", [])
            if ingredients:
                st.subheader("Ingredients")
                for ing in ingredients:
                    # Expecting ing to look like: {"name": "...", "quantity": "..."}
                    st.write(f"- **{ing['name']}**: {ing['quantity']}")

            # Instructions
            instructions = meal_details.get("instructions", "")
            if instructions:
                st.subheader("Instructions")
                st.write(instructions)

            # Macros
            st.subheader("Macros")
            st.write(f"Calories: {meal_details.get('calories', 0)}")
            st.write(f"Protein: {meal_details.get('protein', 0)} g")
            st.write(f"Fat: {meal_details.get('fat', 0)} g")
            st.write(f"Carbs: {meal_details.get('carbohydrates', 0)} g")