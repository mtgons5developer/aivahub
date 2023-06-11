import os
import uuid
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
            return jsonify({'message': 'File uploaded successfully', 'id': row_id})
        else:
            return jsonify({'error': 'Failed to insert file details'}), 500

    # Return the error message in JSON format
    return jsonify({'error': 'No file provided'}), 400

# Define a function to insert a row with file details into the database
def insert_file_details(filename, uuid):
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO files (filename, uuid) VALUES (%s, %s)",
            (filename, uuid)
        )
        conn.commit()
        print('File details inserted successfully')
    except Error as e:
        print('Error inserting file details:', e)

# Define a function to retrieve file details from the database by UUID
def get_file_details(uuid):
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM files WHERE uuid = %s",
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

# Define a function to insert a row with file details into the database
def get_file_details(file_uuid):
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, status FROM csv_upload WHERE id = %s",
            (str(file_uuid),)  # Convert the UUID to a string
        )
        row = cursor.fetchone()
        if row:
            file_id, status = row
            return {'id': str(file_id), 'status': status}
        else:
            return {'error': 'File not found'}
    except Error as e:
        return {'error': f'Error retrieving file details: {e}'}

            
@app.route('/status/<uuid:file_id>', methods=['GET'])
def get_status(file_id):
    # Retrieve file details from the database
    file_details = get_file_details(file_id)

    if 'error' in file_details:
        return jsonify(file_details), 404
    else:
        return jsonify(file_details)




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8443)
