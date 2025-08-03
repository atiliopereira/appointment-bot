import requests
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class AppointmentRequest(BaseModel):
    intent: str
    date: str
    time: str


DATA_SERVICE_URL = "http://127.0.0.1:8001"


@app.post("/check-appointment")
async def check_appointment(request: AppointmentRequest):
    date_requested = request.date
    time_requested = request.time

    if request.intent == "book_appointment":
        try:
            response = requests.post(
                f"{DATA_SERVICE_URL}/check-availability",
                json={"date": date_requested, "time": time_requested},
            )

            if response.status_code != 200:
                return {
                    "status": "error",
                    "message": f"Availability service returned status {response.status_code}",
                }

            try:
                response_data = response.json()
            except ValueError as e:
                return {
                    "status": "error",
                    "message": f"Failed to parse availability response: {str(e)}",
                }

            is_available = response_data.get("available", False)

            if is_available:
                book_response = requests.post(
                    f"{DATA_SERVICE_URL}/book-appointment",
                    json={"date": date_requested, "time": time_requested},
                )
                if book_response.status_code == 200:
                    try:
                        book_data = book_response.json()
                        if book_data.get("success", False):
                            return {
                                "status": "success",
                                "message": f"Appointment on {date_requested} at {time_requested} booked successfully.",
                            }
                        else:
                            return {
                                "status": "error",
                                "message": book_data.get(
                                    "message", "Failed to book appointment."
                                ),
                            }
                    except ValueError:
                        return {
                            "status": "error",
                            "message": "Failed to parse booking response.",
                        }
                else:
                    return {
                        "status": "error",
                        "message": f"Booking service returned status {book_response.status_code}",
                    }
            else:
                alternative_times = response_data.get("alternative_time", [])

                if alternative_times:
                    alternatives_str = ", ".join(alternative_times)
                    message = (
                        f"{date_requested} at {time_requested} is not available. "
                        f"Would you like to book one of these alternative times: {alternatives_str}?"
                    )
                else:
                    message = (
                        f"{date_requested} at {time_requested} is not available, "
                        "and there are no alternative times available."
                    )

                return {
                    "status": "error",
                    "message": message,
                }
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"Failed to check availability: {str(e)}",
            }

    return {
        "status": "error",
        "message": "I'm sorry, I don't know how to handle that request intent.",
    }
