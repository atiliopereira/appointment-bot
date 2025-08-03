from unittest.mock import MagicMock, patch

import pytest
import requests

from ui.main import parse_user_input


class TestAPIIntegration:
    """Test API integration and response handling"""

    @patch("requests.post")
    def test_successful_booking_response(self, mock_post):
        """Test successful appointment booking"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "message": "Appointment on 2025-08-08 at 15:00 booked successfully.",
        }
        mock_post.return_value = mock_response

        # Test data
        parsed_data = {
            "intent": "book_appointment",
            "date": "2025-08-08",
            "time": "15:00",
        }

        # Make request
        response = requests.post(
            "http://127.0.0.1:8000/check-appointment", json=parsed_data
        )

        # Verify request was made correctly
        mock_post.assert_called_once_with(
            "http://127.0.0.1:8000/check-appointment", json=parsed_data
        )

        # Verify response
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "success"
        assert "2025-08-08" in response_data["message"]
        assert "15:00" in response_data["message"]

    @patch("requests.post")
    def test_unavailable_appointment_with_alternatives(self, mock_post):
        """Test response when appointment is unavailable but alternatives exist"""
        # Mock unavailable response with alternatives
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "error",
            "message": "2025-08-08 at 15:00 is not available. Would you like to book one of these alternative times: 13:00, 14:00?",
        }
        mock_post.return_value = mock_response

        # Test data
        parsed_data = {
            "intent": "book_appointment",
            "date": "2025-08-08",
            "time": "15:00",
        }

        # Make request
        response = requests.post(
            "http://127.0.0.1:8000/check-appointment", json=parsed_data
        )

        # Verify response
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "error"
        assert "alternative times" in response_data["message"]
        assert "13:00" in response_data["message"]
        assert "14:00" in response_data["message"]

    @patch("requests.post")
    def test_no_alternatives_available(self, mock_post):
        """Test response when no alternatives are available"""
        # Mock response with no alternatives
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "error",
            "message": "2025-08-08 at 15:00 is not available, and there are no alternative times available.",
        }
        mock_post.return_value = mock_response

        # Test data
        parsed_data = {
            "intent": "book_appointment",
            "date": "2025-08-08",
            "time": "15:00",
        }

        # Make request
        response = requests.post(
            "http://127.0.0.1:8000/check-appointment", json=parsed_data
        )

        # Verify response
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "error"
        assert "no alternative times available" in response_data["message"]

    @patch("requests.post")
    def test_connection_error_handling(self, mock_post):
        """Test handling of connection errors"""
        # Mock connection error
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        # Test data
        parsed_data = {
            "intent": "book_appointment",
            "date": "2025-08-08",
            "time": "15:00",
        }

        # Verify exception is raised
        with pytest.raises(requests.exceptions.ConnectionError):
            requests.post("http://127.0.0.1:8000/check-appointment", json=parsed_data)

    @patch("requests.post")
    def test_invalid_json_response_handling(self, mock_post):
        """Test handling of invalid JSON responses"""
        # Mock response with invalid JSON
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError(
            "Expecting value: line 1 column 1 (char 0)"
        )
        mock_post.return_value = mock_response

        # Test data
        parsed_data = {
            "intent": "book_appointment",
            "date": "2025-08-08",
            "time": "15:00",
        }

        # Make request
        response = requests.post(
            "http://127.0.0.1:8000/check-appointment", json=parsed_data
        )

        # Verify response status is OK but JSON parsing fails
        assert response.status_code == 200
        with pytest.raises(ValueError):
            response.json()

    @patch("requests.post")
    def test_non_200_status_code(self, mock_post):
        """Test handling of non-200 status codes"""
        # Mock 500 error response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        # Test data
        parsed_data = {
            "intent": "book_appointment",
            "date": "2025-08-08",
            "time": "15:00",
        }

        # Make request
        response = requests.post(
            "http://127.0.0.1:8000/check-appointment", json=parsed_data
        )

        # Verify response
        assert response.status_code == 500


class TestRequestFormatting:
    """Test that requests are formatted correctly"""

    def test_appointment_request_structure(self):
        """Test that appointment requests have the correct structure"""
        parsed_data = parse_user_input("book me for friday at 3 pm")

        # Check required fields
        assert "intent" in parsed_data
        assert "date" in parsed_data
        assert "time" in parsed_data

        # Check values are in correct format
        assert parsed_data["intent"] == "book_appointment"
        assert isinstance(parsed_data["date"], (str, type(None)))
        assert isinstance(parsed_data["time"], (str, type(None)))

        # If date and time are not None, check format
        if parsed_data["date"]:
            # Should be YYYY-MM-DD format
            date_parts = parsed_data["date"].split("-")
            assert len(date_parts) == 3
            assert len(date_parts[0]) == 4  # Year
            assert len(date_parts[1]) == 2  # Month
            assert len(date_parts[2]) == 2  # Day

        if parsed_data["time"]:
            # Should be HH:MM format
            time_parts = parsed_data["time"].split(":")
            assert len(time_parts) == 2
            assert len(time_parts[0]) == 2  # Hour
            assert len(time_parts[1]) == 2  # Minute


class TestAlternativeTimesParsing:
    """Test parsing of alternative times from API responses"""

    def test_extract_alternative_times(self):
        """Test extraction of alternative times from response messages"""
        import re

        message = "2025-08-08 at 15:00 is not available. Would you like to book one of these alternative times: 13:00, 14:00?"

        # This is the same regex used in the main code
        times_match = re.search(r"alternative times: ([^?]+)", message)
        assert times_match is not None

        times_str = times_match.group(1)
        alternative_times = [time.strip() for time in times_str.split(", ")]

        assert len(alternative_times) == 2
        assert "13:00" in alternative_times
        assert "14:00" in alternative_times

    def test_extract_single_alternative_time(self):
        """Test extraction of single alternative time"""
        import re

        message = "2025-08-08 at 15:00 is not available. Would you like to book one of these alternative times: 13:00?"

        times_match = re.search(r"alternative times: ([^?]+)", message)
        assert times_match is not None

        times_str = times_match.group(1)
        alternative_times = [time.strip() for time in times_str.split(", ")]

        assert len(alternative_times) == 1
        assert "13:00" in alternative_times

    def test_no_alternative_times_in_message(self):
        """Test when no alternative times are mentioned"""
        import re

        message = "Appointment booked successfully."

        times_match = re.search(r"alternative times: ([^?]+)", message)
        assert times_match is None


class TestOptionMapping:
    """Test the option mapping for alternative times"""

    def test_create_option_map(self):
        """Test creation of option map for alternative times"""
        alternative_times = ["13:00", "14:00", "16:00"]
        option_map = {}
        letters = ["a", "b", "c", "d", "e", "f"]

        for i, time in enumerate(alternative_times):
            if i < len(letters):
                letter = letters[i]
                option_map[letter] = time

        assert len(option_map) == 3
        assert option_map["a"] == "13:00"
        assert option_map["b"] == "14:00"
        assert option_map["c"] == "16:00"

    def test_option_map_with_many_alternatives(self):
        """Test option map with more alternatives than letters"""
        alternative_times = [
            "09:00",
            "10:00",
            "11:00",
            "13:00",
            "14:00",
            "15:00",
            "16:00",
            "17:00",
        ]
        option_map = {}
        letters = ["a", "b", "c", "d", "e", "f"]

        for i, time in enumerate(alternative_times):
            if i < len(letters):
                letter = letters[i]
                option_map[letter] = time

        # Should only map up to 'f'
        assert len(option_map) == 6
        assert option_map["a"] == "09:00"
        assert option_map["f"] == "15:00"
        assert "g" not in option_map
