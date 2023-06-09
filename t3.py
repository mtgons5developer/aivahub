import os
import asyncio
from flask import Flask, request
import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Create Flask app
app = Flask(__name__)

# Define the Cloud SQL PostgreSQL connection details
from dotenv import load_dotenv

load_dotenv()

# Retrieve the PostgreSQL connection details from environment variables
db_host = os.getenv('HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DATABASE')
db_user = os.getenv('DB_USER')
db_password = os.getenv('PASSWORD')
db_connection_name = 'review-tool-388312:us-central1-b:blackwidow'

# Connect to the Cloud SQL PostgreSQL database
async def connect_to_database():
    try:
        conn = await asyncio.get_event_loop().run_in_executor(
            None, psycopg2.connect, user=db_user, password=db_password,
            host=db_host, port=db_port, database=db_name
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        print('Connected to Cloud SQL PostgreSQL database')
        return conn
    except Error as e:
        print('Error connecting to Cloud SQL PostgreSQL database:', e)

# Define the route for the HTTPS POST request
@app.route('/post-data', methods=['GET', 'POST'])  # Allow both GET and POST methods
async def post_data():
    if request.method == 'POST':
        try:
            # Get the data from the request
            data = await request.get_json()

            # Extract the required fields from the data
            field1 = data.get('field1')
            field2 = data.get('field2')

            # Do something with the data asynchronously
            await asyncio.sleep(1)  # Simulating an asynchronous task

            return 'Data received successfully'
        except Exception as e:
            return str(e), 500
    else:
        return 'Method not allowed', 405

@app.route('/')
def index():
    return 'Hello, world!'

async def main():
    await connect_to_database()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    app.run(host='0.0.0.0', port=8443)
