# models.py
import os
import json
import anthropic
import streamlit as st
from typing import Dict, List

class NutritionCoach:
    def __init__(self):
        # Get API key from environment variable (required)
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")

        if not anthropic_api_key:
            raise ValueError("The ANTHROPIC_API_KEY environment variable is not set!")

        self.client = anthropic.Anthropic(api_key=anthropic_api_key)

    def calculate_targets(self, user_data: Dict) -> Dict:
        """Calculates calorie and macro targets based on user data."""
        user_profile = user_data["profile"]

        # --- 1. Calculate BMR (Basal Metabolic Rate) ---
        weight_kg = user_profile["weight"] * 0.453592  # Convert lbs to kg
        height_cm = user_profile["height"] * 2.54  # Convert inches to cm
        age = user_profile["age"]

        if user_profile["biological_sex"] == "Male":
            bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
        else:  # Female
            bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

        # --- 2. Calculate TDEE (Total Daily Energy Expenditure) ---
        activity_multipliers = {
            "Sedentary": 1.2,
            "Lightly Active": 1.375,
            "Moderately Active": 1.55,
            "Very Active": 1.725,
            "Extremely Active": 1.9,
        }
        activity_multiplier = activity_multipliers[user_profile["activity_level"]]
        tdee = bmr * activity_multiplier

        # --- 3. Adjust Calories for Goal ---
        goal = user_profile["goal"]
        if goal == "Cutting":
            calorie_target = tdee * 0.8  # Example: 20% deficit
        elif goal == "Bulking":
            calorie_target = tdee * 1.1  # Example: 10% surplus
        elif goal == "Maintenance":
            calorie_target = tdee
        elif goal == "Reverse Diet":
            calorie_target = tdee + 100  # Example: Start with +100 calories

        # --- 4. Calculate Macronutrients ---
        # Protein
        if user_profile["lean_body_mass"] == 0:
            protein_target = user_profile["protein_target"] * user_profile["weight"]
        else:
            protein_target = user_profile["protein_target"] * user_profile["lean_body_mass"]

        # Fat (minimum 20% of calories)
        fat_target = max(0.2 * calorie_target, calorie_target - (protein_target * 4) - (tdee * 0.5)) / 9
        # Example: Ensure fat doesn't go below 20% and carbs don't go above 50% for most
        # If you want more control in the future, consider adding a slider for fat like you did protein

        # Carbohydrates (remainder)
        carb_target = (calorie_target - (protein_target * 4) - (fat_target * 9)) / 4

        # --- 5. Store Targets ---
        targets = {
            "calories": round(calorie_target),
            "protein": round(protein_target),
            "fat": round(fat_target),
            "carbohydrates": round(carb_target),
        }
        user_data["targets"] = targets  # Add a "targets" key to the user data

        return user_data

    def generate_meal_plan(self, user_data: Dict, num_days: int) -> Dict:
        """Generate meal recommendations based on user data."""
        user_profile = user_data["profile"]
        targets = user_data["targets"]

        # --- 1. Define Meal Structure ---
        # For simplicity, let's assume 3 meals per day (breakfast, lunch, dinner)
        # You can make this more flexible later (e.g., add snacks, allow user to customize)
        meals_per_day = 3

        # --- 2. Iterate through Days and Meals ---
        meal_plan = {}
        for day in range(1, num_days + 1):
            meal_plan[f"Day {day}"] = {}
            for meal_num in range(1, meals_per_day + 1):
                if meal_num == 1:
                    meal_type = "Breakfast"
                elif meal_num == 2:
                    meal_type = "Lunch"
                else:
                    meal_type = "Dinner"

                # --- 3. Calculate Meal Targets ---
                # Divide daily targets roughly equally among meals (you can adjust this later)
                meal_calories = targets["calories"] / meals_per_day
                meal_protein = targets["protein"] / meals_per_day
                meal_fat = targets["fat"] / meals_per_day
                meal_carbs = targets["carbohydrates"] / meals_per_day

                # --- 4. Create Prompt for Anthropic API ---
                prompt = f"""
Create a {meal_type} that fits the following criteria:

- Calories: {round(meal_calories)}
- Protein: {round(meal_protein)}g
- Fat: {round(meal_fat)}g
- Carbohydrates: {round(meal_carbs)}g
- Dietary Restrictions: {', '.join(user_profile["dietary_restrictions"])}

Provide the meal suggestion in the following JSON format:

{{
    "meal_name": "...",
    "ingredients": [...],
    "instructions": "...",
    "calories": ...,
    "protein": ...,
    "fat": ...,
    "carbohydrates": ...
}}
"""

                # --- 5. Call Anthropic API ---
                try:
                    message = self.client.messages.create(
                        model="claude-3-sonnet-20240229",  # Or another suitable model
                        max_tokens=1000,
                        temperature=0.7, #increase temperature here for creativity.
                        system="You are an expert nutritionist, generating meal plans that adhere to specific dietary requirements and macronutrient targets. Provide well-balanced and varied meal suggestions in JSON format.",
                        messages=[
                            {"role": "user", "content": prompt}
                        ]
                    )

                    # --- 6. Parse API Response ---
                    if isinstance(message.content, list):
                        content = message.content[0].text
                    else:
                        content = message.content

                    meal_data = json.loads(content)
                    meal_plan[f"Day {day}"][meal_type] = meal_data

                except Exception as e:
                    st.error(f"An error occurred while generating meal suggestions: {e}")
                    return None  # Or handle the error in a more appropriate way

        # --- 7. Store Meal Plan ---
        user_data["meals"] = meal_plan  # Add the generated meal plan to user_data

        return user_data

    def analyze_food_entry(self, user_data: Dict, food_entry: str) -> Dict:
        """Analyzes a user's food entry using the Anthropic API."""
        # ... (Implementation later)

    def get_ai_coach_response(self, user_data: Dict, user_message: str) -> str:
        """Gets a response from the AI coach based on user data and a message."""
        # ... (Implementation later)