import re
from datetime import datetime, timedelta

import requests
import spacy

SCHEDULING_SERVICE_URL = "http://127.0.0.1:8000"

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("SpaCy model 'en_core_web_sm' not found. Please run:")
    print("python -m spacy download en_core_web_sm")
    exit()


def normalize_date(date_str):
    """Convert natural language date to YYYY-MM-DD format"""
    if not date_str:
        return None

    date_str = date_str.lower().strip()
    current_year = datetime.now().year
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Handle "today"
    if "today" in date_str:
        return today.strftime("%Y-%m-%d")

    # Handle "tomorrow"
    if "tomorrow" in date_str:
        tomorrow = today + timedelta(days=1)
        return tomorrow.strftime("%Y-%m-%d")

    # Handle weekday names
    weekday_map = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    for day_name, target_weekday in weekday_map.items():
        if day_name in date_str:
            current_weekday = today.weekday()
            days_ahead = target_weekday - current_weekday

            # Handle "next friday", "this friday", vs just "friday"
            if "next" in date_str:
                # Always go to next week
                if days_ahead <= 0:
                    days_ahead += 7  # Get to next occurrence
                else:
                    # If the day is later this week, go to next week's occurrence
                    days_ahead += 7
            elif "this" in date_str:
                # Try to stay in current week, but if day has passed, go to next week
                if days_ahead <= 0:
                    days_ahead += 7
            else:
                # Default behavior: go to next occurrence (this week if possible, otherwise next week)
                if days_ahead <= 0:
                    days_ahead += 7

            target_date = today + timedelta(days=days_ahead)
            return target_date.strftime("%Y-%m-%d")

    # Handle "august 4" format
    month_map = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }

    for month_name, month_num in month_map.items():
        if month_name in date_str:
            # Extract day number
            day_match = re.search(r"\b(\d{1,2})\b", date_str)
            if day_match:
                day = int(day_match.group(1))
                try:
                    date_obj = datetime(current_year, month_num, day)
                    return date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    pass

    return None


def normalize_time(time_str):
    """Convert natural language time to HH:MM format"""
    if not time_str:
        return None

    time_str = time_str.lower().strip()

    # Handle AM/PM format with optional minutes
    if "pm" in time_str or "am" in time_str:
        # Try to match "3:30 pm" or "3:30pm" format first
        time_match = re.search(r"\b(\d{1,2}):(\d{2})\s*(am|pm)", time_str)
        if time_match:
            hour = int(time_match.group(1))
            minute = time_match.group(2)
            period = time_match.group(3)

            if period == "pm" and hour != 12:
                hour += 12
            elif period == "am" and hour == 12:
                hour = 0

            return f"{hour:02d}:{minute}"

        # Handle "3 pm" or "3pm" format (no minutes)
        hour_match = re.search(r"\b(\d{1,2})\s*(am|pm)", time_str)
        if hour_match:
            hour = int(hour_match.group(1))
            period = hour_match.group(2)

            if period == "pm" and hour != 12:
                hour += 12
            elif period == "am" and hour == 12:
                hour = 0

            return f"{hour:02d}:00"

    # Handle 24-hour format like "14:00" or "14:30"
    time_match = re.search(r"\b(\d{1,2}):(\d{2})\b", time_str)
    if time_match:
        hour = int(time_match.group(1))
        minute = time_match.group(2)
        if 0 <= hour <= 23:
            return f"{hour:02d}:{minute}"

    return None


def parse_user_input(text):
    """
    Parses user input using spaCy to extract date and time.
    This is a basic example and can be made more robust.
    """
    doc = nlp(text.lower())

    intent = "book_appointment"
    date_entity = None
    time_entity = None

    for ent in doc.ents:
        if ent.label_ == "DATE":
            date_entity = ent.text
        if ent.label_ == "TIME":
            time_entity = ent.text

    # Normalize the extracted entities
    normalized_date = normalize_date(date_entity)
    normalized_time = normalize_time(time_entity)

    return {"intent": intent, "date": normalized_date, "time": normalized_time}


def chat_interface():
    print("Hello! I am your appointment bot. How can I help you today?")
    last_requested_date = None
    alternative_times = []
    option_map = {}

    while True:
        user_input = input("> ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Goodbye!")
            break

        parsed_data = parse_user_input(user_input)

        # Check if this might be a follow-up response (option letter or time)
        if not parsed_data["date"] and not parsed_data["time"]:
            user_input_clean = user_input.strip().lower()

            if len(user_input_clean) == 1 and user_input_clean in option_map:
                selected_time = option_map[user_input_clean]
                parsed_data = {
                    "intent": "book_appointment",
                    "date": last_requested_date,
                    "time": selected_time,
                }
            else:
                # Try to extract just a time from the input
                time_only = normalize_time(user_input)
                if time_only and last_requested_date and time_only in alternative_times:
                    parsed_data = {
                        "intent": "book_appointment",
                        "date": last_requested_date,
                        "time": time_only,
                    }
                else:
                    print(
                        "I couldn't understand the date and time. Please try formats like:"
                    )
                    print("  • 'tomorrow at 3 pm'")
                    print("  • 'friday at 2:30 pm'")
                    print("  • 'next monday at 10 am'")
                    print("  • 'august 15 at 9:00 am'")
                    continue
        elif not parsed_data["date"] or not parsed_data["time"]:
            print("I couldn't understand the date and time. Please try formats like:")
            print("  • 'tomorrow at 3 pm'")
            print("  • 'friday at 2:30 pm'")
            print("  • 'next monday at 10 am'")
            print("  • 'august 15 at 9:00 am'")
            continue

        try:
            response = requests.post(
                f"{SCHEDULING_SERVICE_URL}/check-appointment", json=parsed_data
            )

            if response.status_code != 200:
                print(
                    f"Error: Scheduling service returned status {response.status_code}"
                )
                continue

            try:
                response_data = response.json()
                message = response_data.get("message", "An error occurred.")

                # Handle alternative times specially
                if (
                    response_data.get("status") == "error"
                    and "alternative times" in message
                ):
                    last_requested_date = parsed_data["date"]
                    times_match = re.search(r"alternative times: ([^?]+)", message)
                    if times_match:
                        times_str = times_match.group(1)
                        alternative_times = [
                            time.strip() for time in times_str.split(", ")
                        ]

                        # Create option map and display formatted alternatives
                        option_map = {}
                        letters = ["a", "b", "c", "d", "e", "f"]

                        # Show the base message without alternatives
                        base_message = message.split(
                            "Would you like to book one of these alternative times:"
                        )[0].strip()
                        print(base_message)
                        print("Available alternatives:")

                        for i, time in enumerate(alternative_times):
                            if i < len(letters):
                                letter = letters[i]
                                option_map[letter] = time
                                print(f"  {letter}) {time}")

                        print("Type a letter to select an option.")
                    else:
                        print(message)
                else:
                    # Regular message display
                    print(message)
                    # Clear context on successful booking or other responses
                    last_requested_date = None
                    alternative_times = []
                    option_map = {}

            except ValueError as e:
                print(
                    f"Error: Failed to parse response from scheduling service: {str(e)}"
                )

        except requests.exceptions.ConnectionError:
            print("Error: The scheduling service is not available.")
            print("Please make sure the scheduling service is running.")
        except requests.exceptions.RequestException as e:
            print(f"Error: Request failed: {str(e)}")


if __name__ == "__main__":
    chat_interface()
