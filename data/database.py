import sqlite3
from datetime import datetime, timedelta

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class AvailabilityCheck(BaseModel):
    date: str
    time: str


class BookingRequest(BaseModel):
    date: str
    time: str


DATABASE_NAME = "appointments.db"


def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY,
        date TEXT NOT NULL,
        time TEXT NOT NULL
        )
    """
    )
    conn.commit()
    conn.close()


init_db()


def _check_availability(date: str, time: str) -> bool:
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM appointments WHERE date = ? AND time = ?", (date, time)
    )
    count = cursor.fetchone()[0]
    conn.close()
    return count == 0


def find_alternative_times(
    date: str, requested_time: str, max_alternatives: int = 2
) -> list[str]:
    """
    Finds a specified number of alternative available time slots.
    The alternatives are an hour before and an hour after the requested time.
    This is a simplified example; a real-world system would use more complex logic.
    """

    alternatives = []
    requested_dt = datetime.strptime(f"{date} {requested_time}", "%Y-%m-%d %H:%M")

    # Check for times an hour before and an hour after
    for i in range(1, max_alternatives + 1):
        after_time = (requested_dt + timedelta(hours=i)).strftime("%H:%M")
        if _check_availability(date, after_time):
            alternatives.append(after_time)

        before_time = (requested_dt - timedelta(hours=i)).strftime("%H:%M")
        if before_time not in alternatives and _check_availability(date, before_time):
            alternatives.append(before_time)

    alternatives.sort()
    return alternatives[:max_alternatives]


@app.post("/check-availability")
async def check_availability(check: AvailabilityCheck):
    is_available = _check_availability(check.date, check.time)

    if is_available:
        return {"available": True}
    else:
        alternatives = find_alternative_times(check.date, check.time)
        return {"available": False, "alternative_time": alternatives}


@app.post("/book-appointment")
async def book_appointment(booking: BookingRequest):
    if not _check_availability(booking.date, booking.time):
        return {"success": False, "message": "Time slot not available"}

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO appointments (date, time) VALUES (?, ?)",
        (booking.date, booking.time),
    )
    conn.commit()
    conn.close()
    return {"success": True, "message": "Appointment booked successfully"}
