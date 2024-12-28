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
        user_profile = user_data.get("profile", {})

        # 1. Basic BMR/TDEE logic
        weight_kg = user_profile.get("weight", 0) * 0.453592
        height_cm = user_profile.get("height", 0) * 2.54
        age = user_profile.get("age", 0)
        sex = user_profile.get("biological_sex", "Male")

        if sex == "Male":
            bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
        else:  # Female
            bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

        activity_multipliers = {
            "Sedentary": 1.2,
            "Lightly Active": 1.375,
            "Moderately Active": 1.55,
            "Very Active": 1.725,
            "Extremely Active": 1.9,
        }
        activity_level = user_profile.get("activity_level", "Sedentary")
        tdee = bmr * activity_multipliers.get(activity_level, 1.2)

        # 2. Rate of Progress => Calorie adjustment
        # 1 lb of body weight ≈ 3500 calories. So 1 lb/week ~ -500 cals/day, 0.5 lb/week ~ -250 cals/day, etc.
        progress_map = {
            "Lose 1 lb/week (recommended)": -500,
            "Lose 0.5 lb/week": -250,
            "Maintenance": 0,
            "Gain 0.5 lb/week": 250,
            "Gain 1 lb/week (recommended)": 500
        }
        rate_of_progress = user_profile.get("rate_of_progress", "Maintenance")
        daily_calorie_delta = progress_map.get(rate_of_progress, 0)

        # Final calorie target
        calorie_target = tdee + daily_calorie_delta

        # 3. If you still want to factor "goal" (Cutting, Bulking, etc.), you can integrate or override
        #    For example, if user_profile["goal"] == "Cutting", you might do additional logic. 
        #    Or ignore "goal" entirely if you're always using rate_of_progress.

        # 4. Calculate macros
        # Protein
        if user_profile.get("lean_body_mass", 0) == 0:
            # If no LBM given, use total weight for the protein calculation
            protein_target = user_profile.get("protein_target", 0.8) * user_profile.get("weight", 0)
        else:
            protein_target = user_profile.get("protein_target", 0.8) * user_profile.get("lean_body_mass", 0)

        # Fat: ensure at least 20% of total cals, etc.
        # (Below is the same logic you had, but you might want to tweak the "max" logic if you prefer a simpler approach)
        # Example: we'll just do a minimum of 20% cals from fat:
        fat_min = 0.2 * calorie_target / 9
        # We also subtract macros for protein from total cals:
        # Then see how we handle the remainder. 
        # If you'd like to set a max for carbs, you can do so similarly.

        # We'll keep your original logic for demonstration, but watch out for negative values if the math doesn't align:
        fat_target = max(fat_min, calorie_target - (protein_target * 4) - (tdee * 0.5)) / 9

        # Carbs: leftover
        carb_target = (calorie_target - (protein_target * 4) - (fat_target * 9)) / 4

        # 5. Round and store
        targets = {
            "calories": max(round(calorie_target), 0),
            "protein": max(round(protein_target), 0),
            "fat": max(round(fat_target), 0),
            "carbohydrates": max(round(carb_target), 0),
        }

        user_data["targets"] = targets
        return user_data

    def generate_meal_plan(self, user_data: Dict, num_days: int, meal_prep: bool = False) -> Dict:
        """
        Generate meal recommendations based on user data.
        If meal_prep is True, then lunch is the same each day, etc.
        """
        user_profile = user_data["profile"]
        targets = user_data["targets"]

        meals_per_day = 3
        meal_plan = {}

        # Optionally, pre-generate a single lunch if meal prep is True
        prepped_lunch = None
        if meal_prep:
            # Generate one lunch meal here to reuse
            meal_calories = targets["calories"] / meals_per_day
            meal_protein = targets["protein"] / meals_per_day
            meal_fat = targets["fat"] / meals_per_day
            meal_carbs = targets["carbohydrates"] / meals_per_day

            prompt = f"""
    Create a LUNCH that fits the following criteria:

    - Calories: {round(meal_calories)}
    - Protein: {round(meal_protein)}g
    - Fat: {round(meal_fat)}g
    - Carbohydrates: {round(meal_carbs)}g
    - Dietary Restrictions: {', '.join(user_profile["dietary_restrictions"])}

    Provide JSON:
    {{
        "meal_name": "...",
        "ingredients": [
            {{"name": "chicken breast", "quantity": "8 oz"}},
            ...
        ],
        "instructions": "...",
        "calories": ...,
        "protein": ...,
        "fat": ...,
        "carbohydrates": ...
    }}
    """
            prepped_lunch = self._call_anthropic_api(prompt, user_profile)

        for day in range(1, num_days + 1):
            day_key = f"Day {day}"
            meal_plan[day_key] = {}

            for meal_num in range(1, meals_per_day + 1):
                if meal_num == 1:
                    meal_type = "Breakfast"
                elif meal_num == 2:
                    meal_type = "Lunch"
                else:
                    meal_type = "Dinner"

                meal_calories = targets["calories"] / meals_per_day
                meal_protein = targets["protein"] / meals_per_day
                meal_fat = targets["fat"] / meals_per_day
                meal_carbs = targets["carbohydrates"] / meals_per_day

                if meal_type == "Lunch" and meal_prep and prepped_lunch:
                    # Reuse the prepped lunch
                    meal_plan[day_key][meal_type] = prepped_lunch
                else:
                    # Generate a fresh meal
                    prompt = f"""
    Create a {meal_type} that fits the following criteria:

    - Calories: {round(meal_calories)}
    - Protein: {round(meal_protein)}g
    - Fat: {round(meal_fat)}g
    - Carbohydrates: {round(meal_carbs)}g
    - Dietary Restrictions: {', '.join(user_profile["dietary_restrictions"])}

    Provide JSON:
    {{
        "meal_name": "...",
        "ingredients": [
            {{"name": "food item", "quantity": "amount"}},
            ...
        ],
        "instructions": "...",
        "calories": ...,
        "protein": ...,
        "fat": ...,
        "carbohydrates": ...
    }}
    """
                    generated_meal = self._call_anthropic_api(prompt, user_profile)
                    meal_plan[day_key][meal_type] = generated_meal

        user_data["meals"] = meal_plan
        return user_data

    def _call_anthropic_api(self, prompt: str, user_profile: Dict) -> Dict:
        """
        Helper function to call the Anthropic API and parse JSON output.
        """
        try:
            message = self.client.messages.create(
                model="claude-2.0",
                max_tokens=1000,
                temperature=0.7,
                system="You are an expert nutritionist ...",
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract text
            if isinstance(message.content, list):
                content = message.content[0].text
            else:
                content = message.content

            # Attempt JSON parse
            meal_data = json.loads(content)
            return meal_data

        except Exception as e:
            st.error(f"Error generating meal: {e}")
            # Return a fallback meal
            return {
                "meal_name": "Error Meal",
                "ingredients": [],
                "instructions": "Error",
                "calories": 0,
                "protein": 0,
                "fat": 0,
                "carbohydrates": 0,
            }


    def analyze_food_entry(self, user_data: Dict, food_entry: str) -> Dict:
            """
            Analyzes a user's food entry using the Anthropic API.
            For example, you might ask the AI to estimate macros, highlight any issues,
            or provide suggestions for healthier alternatives.
            """

            system_prompt = (
                "You are a highly skilled nutritionist. The user will provide a description "
                "of a food item or meal they consumed. Analyze the meal with respect to "
                "its nutritional content, healthiness, and alignment with the user's goals."
            )

            user_profile = user_data.get("profile", {})
            user_goal = user_profile.get("goal", "Maintenance")

            prompt = f"""
    Analyze the following meal/food entry in the context of a user whose goal is '{user_goal}'.
    User's food entry: "{food_entry}"

    Respond in JSON with:
    - "analysis": A brief analysis of whether this is healthy or not and how it fits the user's goal
    - "recommendations": Suggestions on how to modify or improve the meal
            """

            try:
                message = self.client.messages.create(
                    model="claude-2.0",  # Or whichever Anthropic model you have
                    max_tokens=500,
                    temperature=0.7,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                if isinstance(message.content, list):
                    content = message.content[0].text
                else:
                    content = message.content

                return json.loads(content)

            except Exception as e:
                st.error(f"An error occurred while analyzing the food entry: {e}")
                return {
                    "analysis": "Error occurred.",
                    "recommendations": []
                }

    def get_ai_coach_response(self, user_data: Dict, user_message: str) -> str:
        """
        Gets a response from the AI coach based on user data and a message.
        We pass some user info and goals to contextualize the response.
        """

        system_prompt = (
            "You are a helpful AI nutrition coach. You have access to the user's profile data: "
            f"{json.dumps(user_data.get('profile', {}), indent=2)} "
            "Be informative, motivational, and accurate in your responses."
        )

        try:
            message = self.client.messages.create(
                model="claude-2.0",
                max_tokens=500,
                temperature=0.7,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            )

            if isinstance(message.content, list):
                content = message.content[0].text
            else:
                content = message.content

            return content

        except Exception as e:
            st.error(f"An error occurred while getting AI coach response: {e}")
            return "Sorry, I encountered an error while processing your request."