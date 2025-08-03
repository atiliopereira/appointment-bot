# Appointment Bot

A simple appointment booking system built with FastAPI and spaCy for natural language processing.

## Project Structure

```
appointment-bot/
├── app/
│   ├── __init__.py     # Package initialization
│   └── app.py          # Main API service for appointment booking
├── data/
│   ├── __init__.py     # Package initialization
│   └── database.py     # Database service for availability checking
├── ui/
│   ├── __init__.py     # Package initialization
│   └── main.py         # Command-line chat interface
├── tests/
│   ├── __init__.py     # Package initialization
│   ├── test_date_time_parsing.py    # Tests for date/time parsing logic
│   ├── test_api_integration.py      # Tests for API integration
│   └── test_database_operations.py  # Tests for database operations
├── view_appointments.py    # Script to view database records
├── requirements.txt    # Python dependencies
├── pytest.ini         # Pytest configuration
├── .gitignore         # Git ignore rules
├── LICENSE            # GPL v3 License
└── README.md          # This file
```

## Features

- Natural language processing for appointment requests using spaCy
- SQLite database for storing appointments
- FastAPI-based microservices architecture
- Interactive command-line interface
- Automatic alternative time suggestions
- Support for multiple date formats (weekdays, relative dates, specific dates)
- Lettered options for selecting alternative times
- Comprehensive test suite with pytest

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd appointment-bot
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Download the spaCy English model:

```bash
python -m spacy download en_core_web_sm
```

## Usage

### Start the Services

1. **Start the database service** (Terminal 1):

```bash
cd data
uvicorn database:app --host 127.0.0.1 --port 8001
```

2. **Start the main API service** (Terminal 2):

```bash
cd app
uvicorn app:app --host 127.0.0.1 --port 8000
```

3. **Run the chat interface** (Terminal 3):

```bash
cd ui
python main.py
```

### Using the Chat Interface

The bot accepts natural language input for booking appointments:

**Supported date formats:**

- Relative dates: `tomorrow`, `today`
- Weekdays: `friday`, `next monday`, `this wednesday`
- Specific dates: `august 15`, `december 25`

**Supported time formats:**

- 12-hour format: `3 pm`, `10:30 am`, `12:00 pm`
- 24-hour format: `15:00`, `14:30`

**Example interactions:**

```
> I'd like to book an appointment for tomorrow at 2pm
> Book me for friday at 10:30 am
> Can I get an appointment next monday at 3:00 pm?
> Book me for august 15 at 14:00
```

**Alternative time selection:**
When your requested time is unavailable, you'll see options like:

```
2025-08-08 at 15:00 is not available.
Available alternatives:
  a) 13:00
  b) 14:00
Type a letter to select an option.
> a
```

Type `exit`, `quit`, or `bye` to exit the chat interface.

## API Endpoints

### Main API Service (Port 8000)

- `POST /check-appointment` - Check and book appointments

### Database Service (Port 8001)

- `POST /check-availability` - Check if a time slot is available
- `POST /book-appointment` - Book an appointment

## Testing

The project includes comprehensive tests using pytest. To run the tests:

1. **Install test dependencies** (if not already installed):

```bash
pip install pytest pytest-mock freezegun
```

2. **Run all tests**:

```bash
pytest
```

3. **Run specific test files**:

```bash
pytest tests/test_date_time_parsing.py        # Date/time parsing tests
pytest tests/test_api_integration.py          # API integration tests
pytest tests/test_database_operations.py      # Database operation tests
```

4. **Run tests with verbose output**:

```bash
pytest -v
```

## Dependencies

### Runtime Dependencies

- **FastAPI**: Web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI applications
- **Requests**: HTTP library for making API calls
- **Pydantic**: Data validation using Python type hints
- **spaCy**: Natural language processing library

### Test Dependencies

- **pytest**: Testing framework
- **pytest-mock**: Mock objects for testing
- **freezegun**: Time manipulation for testing date/time logic

## Database

The system uses SQLite with a simple `appointments` table:

- `id`: Primary key
- `date`: Appointment date (TEXT)  
- `time`: Appointment time (TEXT)

### Viewing Database Records

You can view your appointment records using several methods:

#### Method 1: Python Script (Recommended)
```bash
python view_appointments.py
```
This shows a formatted table with appointment counts and summaries.

#### Method 2: SQLite Command Line
```bash
# Simple view
sqlite3 data/appointments.db "SELECT * FROM appointments;"

# Formatted view with headers
sqlite3 data/appointments.db -header -column "SELECT * FROM appointments ORDER BY date, time;"

# Count appointments by date
sqlite3 data/appointments.db -header -column "SELECT date, COUNT(*) as count FROM appointments GROUP BY date ORDER BY date;"
```

#### Method 3: Interactive SQLite Session
```bash
sqlite3 data/appointments.db
```
Then use SQL commands like:
- `.headers on` - Show column headers
- `.mode column` - Format as columns  
- `SELECT * FROM appointments;` - View all records
- `SELECT * FROM appointments WHERE date = '2025-08-04';` - Filter by date
- `.quit` - Exit

## License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details.

