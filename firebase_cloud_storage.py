from google.cloud import pubsub_v1

def hello_gcs(event, context):
    """Triggered by a change to a Cloud Storage bucket.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    file = event
    print(f"Processing file: {file['name']}.")

    # Add your custom logic to handle the event

    # For example, you can publish a message to another Pub/Sub topic
    # publish_message("another-topic", "Event processed successfully.")

def listen_for_events(project_id, subscription_name):
    """Listen for events on the Pub/Sub subscription."""
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subscription_name)

    def callback(message):
        """Process the received Pub/Sub message."""
        # Extract the event payload
        event = message.data.decode('utf-8')
        print(f"Received event: {event}")

        # Process the event

        # Acknowledge the message
        message.ack()

    # Start listening for messages
    subscriber.subscribe(subscription_path, callback=callback)
    print(f"Listening for events on subscription: {subscription_name}...")

    # Keep the listener running
    while True:
        pass

# Set your project ID and subscription name
project_id = "schooapp2022"
subscription_name = "aivahub-topic-sub"

# Start listening for events
listen_for_events(project_id, subscription_name)
