# utils.py
import json
from datetime import datetime
import pandas as pd
from typing import Dict

def create_weekly_schedule():
    """Create a weekly schedule template."""
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    return {day: [] for day in days}

def load_user_data():
    """Loads user data from a JSON file or initializes an empty dictionary."""
    try:
        with open("users.json", "r") as f:
            users = json.load(f)
    except FileNotFoundError:
        users = {}
    return users

def save_user_data(users):
    """Saves user data to a JSON file."""
    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)