import os
import sqlite3
import tempfile
from unittest.mock import patch

import pytest

from data.database import _check_availability, find_alternative_times, init_db


class TestDatabaseOperations:
    """Test database operations for appointment management"""

    def setup_method(self):
        """Set up a temporary database for each test"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db_name = self.temp_db.name
        self.temp_db.close()

        # Patch the DATABASE_NAME constant
        self.database_patcher = patch("data.database.DATABASE_NAME", self.temp_db_name)
        self.database_patcher.start()

        # Initialize the test database
        init_db()

    def teardown_method(self):
        """Clean up after each test"""
        self.database_patcher.stop()
        if os.path.exists(self.temp_db_name):
            os.unlink(self.temp_db_name)

    def test_empty_database_availability(self):
        """Test availability checking on empty database"""
        # All times should be available in empty database
        assert _check_availability("2025-08-08", "15:00") is True
        assert _check_availability("2025-08-08", "10:00") is True
        assert _check_availability("2025-12-25", "09:00") is True

    def test_book_and_check_availability(self):
        """Test booking an appointment and checking availability"""
        # Book an appointment
        conn = sqlite3.connect(self.temp_db_name)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO appointments (date, time) VALUES (?, ?)",
            ("2025-08-08", "15:00"),
        )
        conn.commit()
        conn.close()

        # Check that the time is no longer available
        assert _check_availability("2025-08-08", "15:00") is False

        # Check that other times are still available
        assert _check_availability("2025-08-08", "14:00") is True
        assert _check_availability("2025-08-08", "16:00") is True
        assert _check_availability("2025-08-09", "15:00") is True

    def test_multiple_bookings_same_time_different_dates(self):
        """Test that same time on different dates can be booked"""
        conn = sqlite3.connect(self.temp_db_name)
        cursor = conn.cursor()

        # Book same time on different dates
        cursor.execute(
            "INSERT INTO appointments (date, time) VALUES (?, ?)",
            ("2025-08-08", "15:00"),
        )
        cursor.execute(
            "INSERT INTO appointments (date, time) VALUES (?, ?)",
            ("2025-08-09", "15:00"),
        )
        conn.commit()
        conn.close()

        # Both should be unavailable
        assert _check_availability("2025-08-08", "15:00") is False
        assert _check_availability("2025-08-09", "15:00") is False

        # Same time on different date should be available
        assert _check_availability("2025-08-10", "15:00") is True

    def test_find_alternative_times_empty_database(self):
        """Test finding alternatives when database is empty"""
        alternatives = find_alternative_times("2025-08-08", "15:00", max_alternatives=2)

        # Should find 2 alternatives - algorithm checks before times first (14:00, 13:00)
        assert len(alternatives) == 2
        assert "14:00" in alternatives  # 1 hour before
        assert (
            "13:00" in alternatives
        )  # 2 hours before (since 16:00 comes after 14:00 in loop)
        assert alternatives == sorted(alternatives)  # Should be sorted

    def test_find_alternative_times_with_conflicts(self):
        """Test finding alternatives when some times are already booked"""
        # Book some appointments
        conn = sqlite3.connect(self.temp_db_name)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO appointments (date, time) VALUES (?, ?)",
            ("2025-08-08", "14:00"),  # Book 14:00
        )
        cursor.execute(
            "INSERT INTO appointments (date, time) VALUES (?, ?)",
            ("2025-08-08", "16:00"),  # Book 16:00
        )
        conn.commit()
        conn.close()

        alternatives = find_alternative_times("2025-08-08", "15:00", max_alternatives=2)

        # Should find alternatives that avoid the booked times
        assert len(alternatives) <= 2
        assert "14:00" not in alternatives  # Should be excluded (booked)
        assert "16:00" not in alternatives  # Should be excluded (booked)

        # Should find other available times
        for alt_time in alternatives:
            assert _check_availability("2025-08-08", alt_time) is True

    def test_find_alternative_times_max_limit(self):
        """Test that find_alternative_times respects max_alternatives limit"""
        alternatives_2 = find_alternative_times(
            "2025-08-08", "15:00", max_alternatives=2
        )
        alternatives_4 = find_alternative_times(
            "2025-08-08", "15:00", max_alternatives=4
        )

        assert len(alternatives_2) <= 2
        assert len(alternatives_4) <= 4
        assert len(alternatives_4) >= len(alternatives_2)

    def test_find_alternative_times_sorted_output(self):
        """Test that alternative times are returned in sorted order"""
        alternatives = find_alternative_times("2025-08-08", "12:00", max_alternatives=4)

        # Convert to comparable format for sorting test
        time_values = [int(time.replace(":", "")) for time in alternatives]
        assert time_values == sorted(time_values), f"Times not sorted: {alternatives}"

    def test_database_table_structure(self):
        """Test that database table has correct structure"""
        conn = sqlite3.connect(self.temp_db_name)
        cursor = conn.cursor()

        # Get table info
        cursor.execute("PRAGMA table_info(appointments)")
        columns = cursor.fetchall()
        conn.close()

        # Check that all required columns exist
        column_names = [col[1] for col in columns]
        assert "id" in column_names
        assert "date" in column_names
        assert "time" in column_names

        # Check that id is primary key
        id_column = next(col for col in columns if col[1] == "id")
        assert id_column[5] == 1  # pk column should be 1 for primary key

    def test_database_constraints(self):
        """Test database constraints and data integrity"""
        conn = sqlite3.connect(self.temp_db_name)
        cursor = conn.cursor()

        # Test that all required fields must be provided
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO appointments (date) VALUES (?)",
                ("2025-08-08",),  # Missing time
            )
            conn.commit()

        conn.close()

    def test_alternative_times_boundary_conditions(self):
        """Test alternative time generation at day boundaries"""
        # Test early morning time
        alternatives = find_alternative_times("2025-08-08", "01:00", max_alternatives=2)
        # Should not suggest negative hours
        for alt_time in alternatives:
            hour = int(alt_time.split(":")[0])
            assert 0 <= hour <= 23

        # Test late evening time
        alternatives = find_alternative_times("2025-08-08", "23:00", max_alternatives=2)
        # Should not suggest hours > 23
        for alt_time in alternatives:
            hour = int(alt_time.split(":")[0])
            assert 0 <= hour <= 23


class TestDatabaseInitialization:
    """Test database initialization"""

    def test_init_db_creates_table(self):
        """Test that init_db creates the appointments table"""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_db_name = temp_db.name
        temp_db.close()

        try:
            with patch("data.database.DATABASE_NAME", temp_db_name):
                init_db()

            # Check that table was created
            conn = sqlite3.connect(temp_db_name)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='appointments'"
            )
            result = cursor.fetchone()
            conn.close()

            assert result is not None
            assert result[0] == "appointments"

        finally:
            if os.path.exists(temp_db_name):
                os.unlink(temp_db_name)

    def test_init_db_idempotent(self):
        """Test that init_db can be called multiple times safely"""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_db_name = temp_db.name
        temp_db.close()

        try:
            with patch("data.database.DATABASE_NAME", temp_db_name):
                # Call init_db multiple times
                init_db()
                init_db()
                init_db()

            # Should still work without errors
            conn = sqlite3.connect(temp_db_name)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='appointments'"
            )
            result = cursor.fetchone()
            conn.close()

            assert result is not None

        finally:
            if os.path.exists(temp_db_name):
                os.unlink(temp_db_name)
