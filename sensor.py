import uuid
import boto3
from awscrt import mqtt, http
from awsiot import mqtt_connection_builder
import sys
import threading
import time
import json
from utils.command_line_utils import CommandLineUtils
from utils.data_generator import generate_sensor_data
from botocore.exceptions import ClientError

cmdData = CommandLineUtils.parse_sample_input_pubsub()
received_count = 0
received_all_event = threading.Event()

# Create a session and DynamoDB resource
session = boto3.Session(
    aws_access_key_id='accesskey',
    aws_secret_access_key='secretkey',
    aws_session_token='token',
    region_name='us-west-2'
)

dynamodb = session.resource('dynamodb')
table_name = 'SensorData'


# Create DynamoDB table if it doesn't exist
def create_dynamodb_table():
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        table.wait_until_exists()
        print(f"Table {table_name} created successfully!")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"Table {table_name} already exists.")
        else:
            print(f"Error creating table: {e}")
            raise


# Function to store message in DynamoDB
def store_in_dynamodb(message_data):
    table = dynamodb.Table(table_name)
    try:
        # Generate a unique ID for each record
        record_id = str(uuid.uuid4())

        # Create a comprehensive record
        record = {
            'id': record_id,
            'timestamp': int(time.time()),
            'data': json.dumps(message_data)  # Store JSON as string
        }

        # Store the message in DynamoDB
        table.put_item(Item=record)
        print(f"Stored message in DynamoDB: {record}")
    except Exception as e:
        print(f"Error storing message in DynamoDB: {e}")


# Callback when connection is accidentally lost.
def on_connection_interrupted(connection, error, **kwargs):
    print(f"Connection interrupted. error: {error}")


# Callback when an interrupted connection is re-established.
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print(f"Connection resumed. return_code: {return_code} session_present: {session_present}")
    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        print("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()
        resubscribe_future.add_done_callback(on_resubscribe_complete)


def on_resubscribe_complete(resubscribe_future):
    resubscribe_results = resubscribe_future.result()
    print(f"Resubscribe results: {resubscribe_results}")
    for topic, qos in resubscribe_results['topics']:
        if qos is None:
            sys.exit(f"Server rejected resubscribe to topic: {topic}")


# Callback when the subscribed topic receives a message
def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    print(f"Received message from topic '{topic}': {payload}")
    try:
        message_data = json.loads(payload)
        # Store in DynamoDB
        store_in_dynamodb(message_data)
    except json.JSONDecodeError:
        print("Error decoding JSON payload")
    except Exception as e:
        print(f"Error: {e}")

    global received_count
    received_count += 1
    if received_count == cmdData.input_count:
        received_all_event.set()


# Callback when the connection successfully connects
def on_connection_success(connection, callback_data):
    assert isinstance(callback_data, mqtt.OnConnectionSuccessData)
    print(f"Connection Successful with return code: {callback_data.return_code}, session present: {callback_data.session_present}")


# Callback when a connection attempt fails
def on_connection_failure(connection, callback_data):
    assert isinstance(callback_data, mqtt.OnConnectionFailureData)
    print(f"Connection failed with error code: {callback_data.error}")


# Callback when a connection has been disconnected or shutdown successfully
def on_connection_closed(connection, callback_data):
    print("Connection closed")


if __name__ == '__main__':
    # Create the DynamoDB table if not already present
    create_dynamodb_table()

    # Create the proxy options if the data is present in cmdData
    proxy_options = None
    if cmdData.input_proxy_host is not None and cmdData.input_proxy_port != 0:
        proxy_options = http.HttpProxyOptions(
            host_name=cmdData.input_proxy_host,
            port=cmdData.input_proxy_port
        )

    # Create a MQTT connection from the command line data
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=cmdData.input_endpoint,
        port=cmdData.input_port,
        cert_filepath=cmdData.input_cert,
        pri_key_filepath=cmdData.input_key,
        ca_filepath=cmdData.input_ca,
        on_connection_interrupted=on_connection_interrupted,
        on_connection_resumed=on_connection_resumed,
        client_id=cmdData.input_clientId,
        clean_session=False,
        keep_alive_secs=120,
        http_proxy_options=proxy_options,
        on_connection_success=on_connection_success,
        on_connection_failure=on_connection_failure,
        on_connection_closed=on_connection_closed
    )

    if not cmdData.input_is_ci:
        print(f"Connecting to {cmdData.input_endpoint} with client ID '{cmdData.input_clientId}'...")
    else:
        print("Connecting to endpoint with client ID")
    connect_future = mqtt_connection.connect()

    # Future.result() waits until a result is available
    connect_future.result()
    print("Connected!")

    message_count = cmdData.input_count
    message_topic = cmdData.input_topic
    message_string = generate_sensor_data()

    # Subscribe
    print(f"Subscribing to topic '{message_topic}'...")
    subscribe_future, packet_id = mqtt_connection.subscribe(
        topic=message_topic,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message_received
    )

    subscribe_result = subscribe_future.result()
    print(f"Subscribed with {str(subscribe_result['qos'])}")

    # Publish message to server desired number of times.
    if message_string:
        if message_count == 0:
            print("Sending messages until program killed")
        else:
            print(f"Sending {message_count} message(s)")

        publish_count = 1
        while (publish_count <= message_count) or (message_count == 0):
            message_string = generate_sensor_data()
            message = f"{message_string} [{publish_count}]"
            print(f"Publishing message to topic '{message_topic}': {message}")
            message_json = json.dumps(message_string)
            mqtt_connection.publish(
                topic=message_topic,
                payload=message_json,
                qos=mqtt.QoS.AT_LEAST_ONCE
            )
            time.sleep(1)
            publish_count += 1

    # Wait for all messages to be received.
    if message_count != 0 and not received_all_event.is_set():
        print("Waiting for all messages to be received...")

    received_all_event.wait()
    print(f"{received_count} message(s) received.")

    # Disconnect
    print("Disconnecting...")
    disconnect_future = mqtt_connection.disconnect()
    disconnect_future.result()
    print("Disconnected!")
