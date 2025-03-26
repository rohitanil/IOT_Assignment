import random
import datetime


def generate_sensor_data():
    """
    Generate random sensor data for a virtual environmental IoT station.

    Returns:
    dict: A dictionary containing sensor readings with the following keys:
    - temperature: Float between -50 and 50 Celsius
    - humidity: Float between 0 and 100 percent
    - co2: Integer between 300 and 2000 ppm
    - timestamp: Current datetime
    """
    sensor_data = {
        'temperature': round(random.uniform(-50, 50), 2),  # Temperature in Celsius
        'humidity': round(random.uniform(0, 100), 2),  # Humidity percentage
        'co2': round(random.uniform(300, 2000), 2),  # CO2 in parts per million
        'timestamp': datetime.datetime.now().isoformat()
    }

    return sensor_data
