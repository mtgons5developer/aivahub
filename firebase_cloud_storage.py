# import json
# from google.cloud import pubsub_v1

# project_id = 'schooapp2022'
# subscription_name = 'aivahub-topic-sub'

# # Create a Pub/Sub subscriber client
# subscriber = pubsub_v1.SubscriberClient()

# # Set the subscription path
# subscription_path = f'projects/{project_id}/subscriptions/{subscription_name}'
# # print(subscription_path)

# def parse(msg):

#     received_message = msg

#     # Extract the JSON part of the received message
#     json_str = received_message.split("Received message: b'")[1][:-3]

#     # Parse the JSON string
#     parsed_message = json.loads(json_str)

#     # Access specific fields from the parsed message
#     bucket_name = parsed_message["bucket"]
#     object_name = parsed_message["name"]
#     content_type = parsed_message["contentType"]
#     size = parsed_message["size"]
#     created_time = parsed_message["timeCreated"]
#     updated_time = parsed_message["updated"]

#     # Print the extracted information
#     print("Bucket Name:", bucket_name)
#     print("Object Name:", object_name)
#     print("Content Type:", content_type)
#     print("Size:", size)
#     print("Created Time:", created_time)
#     print("Updated Time:", updated_time)

# def callback(message):
#     # Process the received message
#     print(f'Received message: {message.data}')

#     # Acknowledge the message to remove it from the subscription
#     message.ack()

# # Create a subscriber for the subscription
# future = subscriber.subscribe(subscription_path, callback)

# # Keep the main thread alive
# try:
#     future.result()
# except KeyboardInterrupt:
#     future.cancel()

#==============================================================================================================================

from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1

project_id = "schooapp2022"
subscription_id = "aivahub-topic-sub"
# Number of seconds the subscriber should listen for messages
timeout = 60

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, subscription_id)

def callback(message: pubsub_v1.subscriber.message.Message) -> None:
    print(f"Received {message.data!r}.")
    if message.attributes:
        print("Attributes:")
        for key in message.attributes:
            value = message.attributes.get(key)
            print(f"{key}: {value}")
    message.ack()

streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
print(f"Listening for messages on {subscription_path}..\n")

# Wrap subscriber in a 'with' block to automatically call close() when done.
with subscriber:
    try:
        # When `timeout` is not set, result() will block indefinitely,
        # unless an exception is encountered first.
        streaming_pull_future.result(timeout=timeout)
    except TimeoutError:
        streaming_pull_future.cancel()  # Trigger the shutdown.
        streaming_pull_future.result()  # Block until the shutdown is complete.

#==============================================================================================================================

# from concurrent.futures import TimeoutError
# from google.cloud import pubsub_v1

# # TODO(developer)
# project_id = 'schooapp2022'
# subscription_name = 'aivahub-topic-sub'
# # Number of seconds the subscriber should listen for messages
# timeout = 5.0

# subscriber = pubsub_v1.SubscriberClient()
# # The `subscription_path` method creates a fully qualified identifier
# # in the form `projects/{project_id}/subscriptions/{subscription_id}`
# subscription_path = subscriber.subscription_path(project_id, subscription_name)

# def callback(message: pubsub_v1.subscriber.message.Message) -> None:
#     print(f"Received {message}.")
#     message.ack()

# streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
# print(f"Listening for messages on {subscription_path}..\n")

# # Wrap subscriber in a 'with' block to automatically call close() when done.
# with subscriber:
#     try:
#         # When `timeout` is not set, result() will block indefinitely,
#         # unless an exception is encountered first.
#         streaming_pull_future.result(timeout=timeout)
#     except TimeoutError:
#         streaming_pull_future.cancel()  # Trigger the shutdown.
#         streaming_pull_future.result()  # Block until the shutdown is complete.

