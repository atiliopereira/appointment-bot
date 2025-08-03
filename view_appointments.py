#!/usr/bin/env python3
"""
Simple script to view appointments in the database
Displays ID, DATE, and TIME for each appointment
"""
import sqlite3


def view_appointments():
    """View all appointments in a nicely formatted table"""
    conn = sqlite3.connect("data/appointments.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM appointments ORDER BY date, time")
    appointments = cursor.fetchall()

    if not appointments:
        print("No appointments found in the database.")
        return

    print(f"\n{'='*40}")
    print(f"{'APPOINTMENT DATABASE':^40}")
    print(f"{'='*40}")
    print(f"{'ID':<4} {'DATE':<12} {'TIME':<8}")
    print(f"{'-'*40}")

    for apt in appointments:
        id_val, date, time = apt
        print(f"{id_val:<4} {date:<12} {time:<8}")

    print(f"{'-'*40}")
    print(f"Total appointments: {len(appointments)}")

    # Show summary by date
    cursor.execute(
        """
        SELECT date, COUNT(*) as count 
        FROM appointments 
        GROUP BY date 
        ORDER BY date
    """
    )
    date_summary = cursor.fetchall()

    print(f"\nSUMMARY BY DATE:")
    for date, count in date_summary:
        print(f"  {date}: {count} appointment{'s' if count != 1 else ''}")

    conn.close()


if __name__ == "__main__":
    view_appointments()
