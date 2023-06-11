import os
import csv
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from celery import Celery
import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from google.cloud import storage

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

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure Celery
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

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

# Connect to the database
conn = connect_to_database()

@app.route('/upload-to-gcs', methods=['POST'])
def upload_to_gcs():
    file = request.files.get('file')

    if file:
        # Check if the file is a CSV file
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'File type mismatch, CSV files only.'}), 400

        # Reset the file stream position to the beginning
        file.seek(0)

        # Check if the file is empty
        if file.seek(0, os.SEEK_END) == 0:
            return jsonify({'error': 'Empty file provided'}), 400

        # Upload the file to your GCS bucket
        bucket_name = "schooapp2022.appspot.com"
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)
        original_filename = file.filename
        file_name, file_extension = os.path.splitext(original_filename)

        # Check if the file already exists in the bucket
        counter = 1
        new_filename = f"{file_name}{file_extension}"
        while bucket.blob(new_filename).exists():
            new_filename = f"{file_name}-{counter}{file_extension}"
            counter += 1

        # Reset the file stream position to the beginning again
        file.seek(0)

        blob = bucket.blob(new_filename)
        blob.upload_from_file(file)

        # Insert file details into the database and get the row ID
        row_id = insert_file_details(new_filename)

        if row_id is not None:
            # Call read_csv_file to process the uploaded file
            table_name = read_csv_file(bucket_name, new_filename, row_id)
            return jsonify({'message': 'File uploaded successfully', 'id': row_id, 'table_name': table_name})
        else:
            return jsonify({'error': 'Failed to insert file details'}), 500

    # Return the error message in JSON format
    return jsonify({'error': 'No file provided'}), 400

# Define a function to insert a row with file details into the database
def insert_file_details(filename):
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO csv_upload (filename, status) VALUES (%s, %s) RETURNING id",
            (filename, "Processing")
        )
        row_id = cursor.fetchone()[0]
        conn.commit()
        print('File details inserted successfully')
        return row_id
    except Error as e:
        print('Error inserting file details:', e)

# Define a function to retrieve file details from the database by ID
def get_file_details(uuid):
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM csv_upload WHERE uuid = %s",
            (uuid,)
        )
        row = cursor.fetchone()
        if row:
            file_id, filename, uuid = row
            return {
                'id': file_id,
                'filename': filename,
                'uuid': uuid
            }
        else:
            return None
    except Error as e:
        print('Error retrieving file details:', e)

@app.route('/status/<int:file_id>', methods=['GET'])
def get_status(file_id):
    # Retrieve file details from the database
    file_details = get_file_details(file_id)

    if file_details is not None:
        return jsonify(file_details)
    else:
        return jsonify({'error': 'File not found'}), 404

def detect_column_count(file_path):
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        first_row = next(reader)
        return len(first_row)

# Function to read a CSV file from a GCS bucket and create a PostgreSQL table
def read_csv_file(bucket_name, new_filename, row_id):
    # Download the file from the GCS bucket
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(new_filename)

    # Create a temporary file path to download the file
    temp_file_path = f"/tmp/{new_filename}"

    # Download the file to the temporary file path
    blob.download_to_filename(temp_file_path)

    # Detect the number of columns in the CSV file
    column_count = detect_column_count(temp_file_path)

    # Create the PostgreSQL table if it doesn't exist
    create_table_query = f'CREATE TABLE IF NOT EXISTS "{row_id}" ('

    with open(temp_file_path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        header_row = next(csv_reader)  # Get the header row

        for i, column_name in enumerate(header_row):
            create_table_query += f'"{column_name}" VARCHAR, '

    create_table_query = create_table_query.rstrip(', ') + ');'

    cursor = conn.cursor()
    cursor.execute(create_table_query)
    conn.commit()

    # Insert data from the CSV file into the PostgreSQL table
    with open(temp_file_path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)  # Skip the header row

        insert_query = f'INSERT INTO "{row_id}" VALUES ({", ".join(["%s"] * column_count)})'

        for row in csv_reader:
            cursor.execute(insert_query, row)
            conn.commit()

    # Clean up the temporary file
    os.remove(temp_file_path)

    return row_id


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8443)
