import os
from flask import Flask, request, jsonify
from celery import Celery
import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Create Flask app
app = Flask(__name__)

# Configure Celery
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

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

print(db_host)
print(db_port)
print(db_name)
print(db_user)
print(db_password)

# Connect to the Cloud SQL PostgreSQL database
def connect_to_database():
    try:
        conn = psycopg2.connect(
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            database=db_name
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        print('Connected to Cloud SQL PostgreSQL database')
        return conn
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

            # Perform the task asynchronously using Celery
            task = perform_task.delay(field1, field2)
            # You can also use task.get() to retrieve the result if needed

            return 'Data received successfully'
        except Exception as e:
            return str(e), 500
    else:
        return 'Method not allowed', 405

@app.route('/api/my_table', methods=['GET'])
def get_my_table_data():
    try:
        # Connect to the database
        conn = connect_to_database()
        cursor = conn.cursor()

        # Execute the query to fetch data from my_table
        query = "SELECT * FROM my_table"
        cursor.execute(query)
        rows = cursor.fetchall()

        # Convert the data to a list of dictionaries
        results = []
        for row in rows:
            result = {
                'column1': row[0],
                'column2': row[1],
                # Add more columns as needed
            }
            results.append(result)

        # Close the database connection
        cursor.close()
        conn.close()

        # Return the data as JSON response
        return jsonify(results)
    except Exception as e:
        return str(e), 500
        
@app.route('/api/<table_name>', methods=['GET'])
def get_specific_table_data(table_name):
    try:
        # Connect to the database
        conn = connect_to_database()
        cursor = conn.cursor()

        # Get the columns from the request parameters (comma-separated)
        columns = request.args.get('columns')
        if columns:
            columns = columns.split(',')

        # Build the SQL query based on the table name and columns
        query = f"SELECT {', '.join(columns) if columns else '*'} FROM {table_name}"

        # Execute the query to fetch data from the specified table and columns
        cursor.execute(query)
        rows = cursor.fetchall()

        # Convert the data to a list of dictionaries
        results = []
        for row in rows:
            result = {}
            for i, col in enumerate(columns):
                result[col] = row[i]
            results.append(result)

        # Close the database connection
        cursor.close()
        conn.close()

        # Return the data as JSON response
        return jsonify(results)
    except Exception as e:
        return str(e), 500

# Define the route to get the number of columns in a table
@app.route('/api/columns/<table_name>', methods=['GET'])
def get_table_columns(table_name):
    try:
        # Connect to the database
        conn = connect_to_database()
        cursor = conn.cursor()

        # Query to get the number of columns
        query = f"SELECT COUNT(*) FROM information_schema.columns WHERE table_name = '{table_name}'"

        # Execute the query
        cursor.execute(query)
        count = cursor.fetchone()[0]

        # Close the database connection
        cursor.close()
        conn.close()

        # Return the count as JSON response
        return jsonify({'table_name': table_name, 'column_count': count})
    except Exception as e:
        return str(e), 500
    
@app.route('/')
def index():
    return 'Hello, world!'

@celery.task
def perform_task(field1, field2):
    # Do something with the data asynchronously
    # ...
    pass

if __name__ == '__main__':
    conn = connect_to_database()
    app.run(host='0.0.0.0', port=8443)
