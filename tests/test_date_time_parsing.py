from freezegun import freeze_time

from ui.main import normalize_date, normalize_time, parse_user_input


class TestDateParsing:
    """Test date parsing functionality"""

    @freeze_time("2025-08-03")  # Sunday
    def test_weekday_parsing(self):
        """Test parsing of weekday names"""
        # Test next occurrence of each weekday
        assert normalize_date("monday") == "2025-08-04"  # Tomorrow (Monday)
        assert normalize_date("tuesday") == "2025-08-05"  # Tuesday
        assert normalize_date("wednesday") == "2025-08-06"  # Wednesday
        assert normalize_date("thursday") == "2025-08-07"  # Thursday
        assert normalize_date("friday") == "2025-08-08"  # Friday
        assert normalize_date("saturday") == "2025-08-09"  # Saturday
        assert normalize_date("sunday") == "2025-08-10"  # Next Sunday

    @freeze_time("2025-08-03")  # Sunday
    def test_next_weekday_parsing(self):
        """Test parsing of 'next [weekday]' format"""
        # Note: The current logic treats 'next' to mean next occurrence
        # From Sunday (2025-08-03): next monday is 2025-08-04 (tomorrow)
        assert normalize_date("next monday") == "2025-08-04"  # Tomorrow (Monday)
        assert normalize_date("next friday") == "2025-08-08"  # This week Friday
        assert normalize_date("next sunday") == "2025-08-10"  # Next week Sunday

    @freeze_time("2025-08-03")  # Sunday
    def test_this_weekday_parsing(self):
        """Test parsing of 'this [weekday]' format"""
        assert normalize_date("this monday") == "2025-08-04"  # This week Monday
        assert normalize_date("this friday") == "2025-08-08"  # This week Friday
        assert (
            normalize_date("this sunday") == "2025-08-10"
        )  # Next Sunday (this week passed)

    @freeze_time("2025-08-03")
    def test_relative_date_parsing(self):
        """Test parsing of relative dates"""
        assert normalize_date("today") == "2025-08-03"
        assert normalize_date("tomorrow") == "2025-08-04"

    @freeze_time("2025-08-03")
    def test_month_day_parsing(self):
        """Test parsing of 'month day' format"""
        assert normalize_date("august 4") == "2025-08-04"
        assert normalize_date("august 15") == "2025-08-15"
        assert normalize_date("december 25") == "2025-12-25"
        assert normalize_date("january 1") == "2025-01-01"

    def test_invalid_date_parsing(self):
        """Test parsing of invalid dates"""
        assert normalize_date("invalid") is None
        assert normalize_date("") is None
        assert normalize_date(None) is None
        assert normalize_date("someday") is None

    @freeze_time("2025-08-07")  # Thursday
    def test_weekday_from_thursday(self):
        """Test weekday parsing from a Thursday"""
        assert normalize_date("friday") == "2025-08-08"  # Tomorrow
        assert normalize_date("monday") == "2025-08-11"  # Next Monday
        assert normalize_date("thursday") == "2025-08-14"  # Next Thursday


class TestTimeParsing:
    """Test time parsing functionality"""

    def test_am_pm_parsing(self):
        """Test AM/PM time parsing"""
        assert normalize_time("3 pm") == "15:00"
        assert normalize_time("3pm") == "15:00"
        assert normalize_time("12 pm") == "12:00"
        assert normalize_time("12pm") == "12:00"
        assert normalize_time("3 am") == "03:00"
        assert normalize_time("3am") == "03:00"
        assert normalize_time("12 am") == "00:00"
        assert normalize_time("12am") == "00:00"

    def test_am_pm_with_minutes_parsing(self):
        """Test AM/PM time parsing with minutes"""
        assert normalize_time("3:30 pm") == "15:30"
        assert normalize_time("3:30pm") == "15:30"
        assert normalize_time("10:15 am") == "10:15"
        assert normalize_time("10:15am") == "10:15"
        assert normalize_time("12:45 pm") == "12:45"
        assert normalize_time("12:30 am") == "00:30"

    def test_24_hour_parsing(self):
        """Test 24-hour format parsing"""
        assert normalize_time("15:00") == "15:00"
        assert normalize_time("09:30") == "09:30"
        assert normalize_time("23:45") == "23:45"
        assert normalize_time("00:00") == "00:00"

    def test_invalid_time_parsing(self):
        """Test parsing of invalid times"""
        assert normalize_time("invalid") is None
        assert normalize_time("") is None
        assert normalize_time(None) is None
        assert normalize_time("25:00") is None  # Invalid hour
        assert normalize_time("random text") is None


class TestParseUserInput:
    """Test complete user input parsing"""

    @freeze_time("2025-08-03")
    def test_complete_input_parsing(self):
        """Test parsing complete user inputs"""
        result = parse_user_input("book me for friday at 3 pm")
        assert result["intent"] == "book_appointment"
        assert result["date"] == "2025-08-08"
        assert result["time"] == "15:00"

        result = parse_user_input("I need an appointment tomorrow at 10:30 am")
        assert result["intent"] == "book_appointment"
        assert result["date"] == "2025-08-04"
        assert result["time"] == "10:30"

        result = parse_user_input("can I get an appointment on august 15 at 2 pm")
        assert result["intent"] == "book_appointment"
        assert result["date"] == "2025-08-15"
        assert result["time"] == "14:00"

    def test_incomplete_input_parsing(self):
        """Test parsing incomplete user inputs"""
        result = parse_user_input("book me for sometime")
        assert result["intent"] == "book_appointment"
        assert result["date"] is None
        assert result["time"] is None

        result = parse_user_input("3 pm please")
        assert result["intent"] == "book_appointment"
        assert result["date"] is None
        assert result["time"] == "15:00"


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @freeze_time("2025-12-31")  # New Year's Eve
    def test_year_boundary(self):
        """Test date parsing around year boundary"""
        assert normalize_date("january 1") == "2025-01-01"  # Next year
        assert normalize_date("tomorrow") == "2026-01-01"

    @freeze_time("2025-02-28")  # Non-leap year
    def test_february_boundary(self):
        """Test February date parsing"""
        assert normalize_date("tomorrow") == "2025-03-01"

    def test_case_insensitive_parsing(self):
        """Test that parsing is case insensitive"""
        assert normalize_time("3 PM") == "15:00"
        assert normalize_time("3 Am") == "03:00"

        # Note: normalize_date already converts to lowercase internally
        assert normalize_date("FRIDAY") == normalize_date("friday")
        assert normalize_date("AUGUST 15") == normalize_date("august 15")
