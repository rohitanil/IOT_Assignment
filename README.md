# IOT_Assignment

### Cloud-Based IoT System Using AWS IoT and DynamoDB
This project simulates a cloud-based IoT system that collects data from virtual sensors (temperature, humidity, CO2) and publishes the data using the MQTT protocol. The data is stored in DynamoDB, and a query module is used to fetch and display the latest data and data from the last 5 hours.

### 📝 Project Overview
Key Components:
Sensor Data Publisher (sensor.py): Simulates virtual sensors generating data.
1. Publishes data to an MQTT topic using AWS IoT.
2. Stores published data in DynamoDB (SensorData table).

Data Query Module (query.py): Retrieves and displays:
1. The latest sensor data.
2. Data collected over the last 5 hours.

Automation Script (start.sh): Checks and installs required dependencies.
1. Downloads AWS Root CA certificate if not available.
2. Runs the sensor and query modules.

### ⚡ Prerequisites
Ensure the following are installed:

- Python 3.x
- AWS CLI configured with access credentials
- boto3 and awscrt Python packages
- AWS IoT Device SDK for Python v2

### Python Dependencies
`pip install boto3 awscrt
`
### 🚀 Setup and Usage
1. Clone the Repository
```
git clone git@github.com:rohitanil/IOT_Assignment.git
cd IOT_Assignment
```
2. Run the Setup Script
The start.sh script automates the setup and launches the application.
```
chmod +x start.sh
./start.sh
```
3. Run Sensor Simulation Manually (Optional)
To run the sensor publisher separately:
```
python3 sensor.py --endpoint <your-endpoint> --ca_file ./root-CA.crt --cert <path-to-cert> --key <path-to-key> --client_id basicPubSub --topic sdk/test/python --count 5
```
5. Run Query to Fetch Data
To manually fetch data:
`python3 query.py`

### 🔧 Configuration
AWS IoT Credentials
Update the following in start.sh and sensor.py with the correct paths to your certificates:
```
--endpoint <your-endpoint>.amazonaws.com
--cert <path-to-cert>
--key <path-to-key>
--ca_file ./root-CA.crt
```
DynamoDB Table Name
The table name is set to SensorData by default. To change this: Update table_name in sensor.py and query.py.



