import boto3
from boto3.dynamodb.conditions import Key
import time
import json
from pprint import pprint

# Initialize DynamoDB
session = boto3.Session(
    aws_access_key_id='ACCESS_KEY',
    aws_secret_access_key='SECRET_KEY',
    aws_session_token='TOKEN',
    region_name='us-west-2'
)

dynamodb = session.resource('dynamodb')
table_name = 'SensorData'
table = dynamodb.Table(table_name)


# Function to get the latest data
def get_latest_data():
    try:
        response = table.scan(
            Limit=1,
            Select='ALL_ATTRIBUTES'
        )

        if 'Items' in response and response['Items']:
            latest_item = sorted(response['Items'], key=lambda x: x['timestamp'], reverse=True)[0]
            latest_item['data'] = json.loads(latest_item['data'])
            return latest_item
        else:
            print("No data found in DynamoDB.")
            return None
    except Exception as e:
        print(f"Error fetching latest data: {e}")
        return None


# Function to get data from the last 5 hours
def get_last_5_hours_data():
    try:
        current_timestamp = int(time.time())
        five_hours_ago = current_timestamp - (5 * 60 * 60)

        response = table.scan(
            FilterExpression=Key('timestamp').gt(five_hours_ago)
        )

        if 'Items' in response and response['Items']:
            for item in response['Items']:
                item['data'] = json.loads(item['data'])
            return response['Items']
        else:
            print("No data found in the last 5 hours.")
            return []
    except Exception as e:
        print(f"Error fetching last 5 hours of data: {e}")
        return []


def pretty_print_data(data, title="Data"):
    if data:
        print(f"\n🔍 {title}:")
        pprint(data, sort_dicts=False)
    else:
        print(f"\n❌ No {title.lower()} available.")


# Usage
if __name__ == '__main__':
    # Get latest data
    latest_data = get_latest_data()
    pretty_print_data(latest_data, title="Latest Data")

    # Get data from last 5 hours
    last_5_hours_data = get_last_5_hours_data()
    pretty_print_data(last_5_hours_data, title="Last 5 Hours Data")
