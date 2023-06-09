import os
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
db_connection_name = 'review-tool-388312:us-central1:blackwidow'

# Connect to the Cloud SQL PostgreSQL database
try:
    conn = psycopg2.connect(
        user=db_user,
        password=db_password,
        host='/cloudsql/{}:{}'.format(db_connection_name, db_port),
        database=db_name
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    print('Connected to Cloud SQL PostgreSQL database')
except Error as e:
    print('Error connecting to Cloud SQL PostgreSQL database:', e)

# Define the route for the HTTPS POST request
@app.route('/post-data', methods=['GET', 'POST'])  # Allow both GET and POST methods
def post_data():
    if request.method == 'POST':
        try:
            # Get the data from the request
            data = request.get_json()

            # Extract the required fields from the data
            field1 = data.get('field1')
            field2 = data.get('field2')

            # Do something with the data
            # ...

            return 'Data received successfully'
        except Exception as e:
            return str(e), 500
    else:
        return 'Method not allowed', 405

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8443)
