
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()

# Retrieve the PostgreSQL connection details from environment variables
db_host = os.getenv('HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DATABASE')
db_user = os.getenv('DB_USER')
db_password = os.getenv('PASSWORD')

# Connect to the PostgreSQL database
conn = psycopg2.connect(
    host=db_host,
    port=db_port,
    database=db_name,
    user=db_user,
    password=db_password
)

# Set the isolation level to autocommit
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

# Create a new cursor
cur = conn.cursor()

# Define a function to handle the trigger event
def notify_csv_upload_trigger():
    # Add your logic here to handle the trigger event
    print("Trigger event received!")

# Enable listening for notifications
cur.execute("LISTEN csv_upload_channel")

# Loop to listen for notifications
while True:
    conn.poll()
    while conn.notifies:
        notify = conn.notifies.pop(0)
        print("Received notification on channel:", notify.channel)
        # Perform actions based on the received notification
        if notify.channel == 'csv_upload_channel':
            notify_csv_upload_trigger()

    # Add any other processing or wait mechanism as needed
