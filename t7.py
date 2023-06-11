import os
import uuid
import time
from flask import Flask, request, jsonify
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

# Rest of your code...

@app.route('/upload-to-gcs', methods=['POST'])
def upload_to_gcs():
    file = request.files.get('file')
    access_token = request.headers.get('access_token')

    if not access_token:
        return jsonify({'error': 'Missing access token'}), 400

    if file:
        # Check if the file is a CSV file
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'File type mismatch, CSV files only.'}), 400

        # Reset the file stream position to the beginning
        file.seek(0)

        # Check if the file is empty
        if file.seek(0, os.SEEK_END) == 0:
            return jsonify({'error': 'Empty file provided'}), 400

        # Generate a unique ID for the upload process
        upload_id = str(uuid.uuid4())

        # Update the status to "processing"
        update_upload_status(upload_id, 'processing', access_token)

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
        try:
            blob.upload_from_file(file)
            # Update the status to "complete"
            update_upload_status(upload_id, 'complete', access_token, new_filename)
            return jsonify({'status': 'complete', 'file': new_filename})
        except Exception as e:
            # Update the status to "failed"
            update_upload_status(upload_id, 'failed', access_token)
            return jsonify({'status': 'Upload failed'})

    # Return the error message in JSON format
    return jsonify({'error': 'No file provided'}), 400


def update_upload_status(upload_id, status, access_token, file=None):
    # Update the upload status in the database
    conn = connect_to_database()
    if conn is not None:
        try:
            cursor = conn.cursor()
            if file:
                cursor.execute(
                    "UPDATE uploads SET status = %s, file = %s WHERE upload_id = %s AND access_token = %s",
                    (status, file, upload_id, access_token)
                )
            else:
                cursor.execute(
                    "UPDATE uploads SET status = %s WHERE upload_id = %s AND access_token = %s",
                    (status, upload_id, access_token)
                )
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Upload status updated: ID={upload_id}, Status={status}")
        except Error as e:
            print('Error updating upload status:', e)

# Rest of your code...

@app.route('/status/<access_token>', methods=['GET'])
def get_upload_status(access_token):
    # Fetch the upload status from the database
    conn = connect_to_database()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT status, file FROM uploads WHERE access_token = %s",
                (access_token,)
            )
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            if result is not None:
                status, file = result
                if status == 'complete':
                    return jsonify({'status': status, 'file': file})
                else:
                    return jsonify({'status': status})
            else:
                return jsonify({'status': 'Invalid access token'})
        except Error as e:
            print('Error fetching upload status:', e)

    return jsonify({'status': 'Error fetching upload status'})

# Rest of your code...

if __name__ == '__main__':
    conn = connect_to_database()
    app.run(host='0.0.0.0', port=8443)
