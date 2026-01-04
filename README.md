# DHT11 Temperature and Humidity Monitoring System

A Django web application for monitoring DHT11 sensor data with real-time visualization, alerts, and data export functionality.

## Features

- **Real-time Monitoring**: Display current temperature and humidity readings
- **Data Visualization**: Interactive charts for temperature and humidity over time
- **Alert System**: Automatic alerts when temperature exceeds 23°C
- **Data Storage**: SQLite database for storing sensor readings
- **Data Export**: CSV download functionality
- **Responsive Design**: Bootstrap 5 UI that works on all devices

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Run migrations:
   ```bash
   python manage.py migrate
   ```
6. Start the development server:
   ```bash
   python manage.py runserver
   ```

## API Endpoints

- `POST /api/post/` - Receive sensor data (JSON format: `{"temp": 23.5, "hum": 65.2}`)
- `GET /api/` - Retrieve all sensor data
- `GET /latest/` - Get latest sensor reading
- `GET /api/chart_data/jour/` - Get chart data for last 24 hours
- `GET /api/chart_data/semaine/` - Get chart data for last week
- `GET /api/chart_data/mois/` - Get chart data for last month

## Project Structure

- `ProjetIoT/` - Main Django project
- `DHT/` - DHT11 monitoring app
  - `models.py` - Database models
  - `views.py` - View functions
  - `api.py` - API endpoints
  - `urls.py` - URL routing
  - `templates/` - HTML templates
- `static/` - CSS, JavaScript, and other static files
- `templates/` - Base HTML templates

## Alert System

The system automatically sends alerts when temperature exceeds 23°C:
- Email notifications (configured in settings.py)
- Incident tracking in the database

## Data Export

Download all sensor data in CSV format at `/download_csv/`