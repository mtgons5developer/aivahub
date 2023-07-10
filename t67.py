import re
import unicodedata
import urllib.request
import urllib.error
import os
import csv
import json
import ssl
import sys
import time
import requests
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from celery import Celery
import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from openai.error import RateLimitError
from google.cloud import storage
from guide import guidelines_prompt
from transformers import GPT2Tokenizer

from langchain import LLMChain
from langchain.chat_models import ChatOpenAI

# Define the Cloud SQL PostgreSQL connection details
from dotenv import load_dotenv

load_dotenv()

# Retrieve the PostgreSQL connection details from environment variables
certfile1 = os.getenv('CERTFILE')
keyfile1 = os.getenv('KEYFILE')
db_host = os.getenv('HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DATABASE')
db_user = os.getenv('DB_USER')
db_password = os.getenv('PASSWORD')
bucket_name = os.getenv('BUCKET')
openai_api_key = os.getenv('OPENAI_API_KEY')
os.environ['OPENAI_API_KEY'] = openai_api_key

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
    retry_count = 0
    max_retries = 10
    retry_delay = 5  # seconds

    while retry_count < max_retries:
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
            retry_count += 1
            print(f'Retrying connection ({retry_count}/{max_retries})...')
            time.sleep(retry_delay)

# Connect to the database
conn = connect_to_database()

# Check if the connection was successful
if conn is None:
    print('Unable to connect to the database. Exiting...')
    sys.exit(1)


def load_fine_tune(cursor):
    
    global guidelines_prompt

    # query = "SELECT * FROM tune_data4"
    query = "SELECT * FROM tune_data4 LIMIT 12"

    cursor.execute(query)
    # Fetch all the rows from the result set
    rows = cursor.fetchall()

    # Create a variable to store the formatted examples
    fine_tune = ""

    for row in rows:
        review = row[0]
        # status = str(row[2])
        status2 = str(row[5])
        # reason = row[1]
        reason2 = row[4]
        # result = str(row[3])
        result2 = str(row[6])

        # Format the example
        data = (
            '"review": "' + str(review) + '",\n' +
            # '"status": "' + status + '",\n' +
            '"status": "' + status2 + '",\n' +
            # '"reason": "' + str(reason) + '",\n' +
            '"reason": "' + str(reason2) + '",\n' +
            # '"result": "' + result + '",\n' +
            '"result": "' + result2 + '"\n\n'
        )
        # print(data)
        # Append the formatted example to the output
        fine_tune += data

    # Replace {fine_tune} with the actual value
    guidelines_prompt = guidelines_prompt.format(fine_tune=fine_tune)

    return guidelines_prompt

# Calculates the number of tokens used in the given guidelines_prompt:
# tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
# tokenized_prompt = tokenizer.encode(guidelines_prompt, add_special_tokens=False)
# num_tokens = len(tokenized_prompt)
# print("Number of tokens used:", num_tokens)

@app.route('/')
def index():

    return 'Hello, SSL!'

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
        uuid = insert_file_details(new_filename)

        if uuid is not None:
            # Create a JSON response with the inserted ID
            response = {
                'status': 'processing',
                'id': uuid,
            }

            cursor = conn.cursor()
            cursor.execute(
                "UPDATE csv_upload SET status = %s WHERE id = %s",
                ("processing", uuid)
            )
            return jsonify(response), 200

        else:
            return jsonify({'error': 'Failed to insert file details'}), 500

    # Return the error message in JSON format
    return jsonify({'error': 'No file provided'}), 400
    # return None

@app.route('/process/<string:ff_id>', methods=['GET'])
def process_csv(ff_id):

#     # Retrieve the file details from the request
    new_filename = get_filename(ff_id)

    if new_filename is not None:
        # Call 1 to process the uploaded file
        process_csv_and_openAI(bucket_name, new_filename, ff_id)
        data = get_gpt_data(ff_id)
        print(data)
        if data == None:
            data = "CSV contains 4-5 ratings only, no data has been processed."
            
        response_data = {
            'status': 'complete',
            'gpt_data': data
        }

        return jsonify(response_data), 200
        # return jsonify({'File/GPT uploaded successfully:': data}), 200
    else:
        return jsonify({'error': 'Invalid file ID'}), 400
    
# Define a function to insert a row with file details into the database
def insert_file_details(filename):
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO csv_upload (filename, status) VALUES (%s, %s) RETURNING id",
            (filename, "processing")
        )
        
        row_id = cursor.fetchone()[0]
        conn.commit()
        print('File details inserted successfully')

        return row_id

    except Error as e:
        print('Error inserting file details:', e)
        return jsonify({'error': 'Error inserting file details'}), e


# Define a function to retrieve file details from the database by ID
def get_file_details(ff_idd):
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status FROM csv_upload WHERE id = %s",
            (ff_idd,)
        )
        
        # Fetch the result as a tuple
        result = cursor.fetchone()

        # Extract the value from the tuple
        result = result[0]

        return result
            
    except Error as e:
        print('Error retrieving file details:', e)
        return jsonify({'error': 'Error inserting file details'}), e

def get_gpt_data(fff_id):
    try:

        cursor = conn.cursor()
        cursor.execute(
            f'SELECT * FROM "{fff_id}"'
        )
        rows = cursor.fetchall()

        if rows:
            result = []
            for row in rows:
                data = {
                    # 'id': row[0],
                    'status': row[2],
                    'reason': row[3],
                    'result': row[4].lower(),
                    # Add more columns as needed
                }
                result.append(data)

            return result

    except Error as e:
        print('Error retrieving data from the table:', e)
        return jsonify({'error': 'Error retrieving data from the table'}), e


@app.route('/status/<string:file_id>', methods=['GET'])
def get_status(file_id):
    if file_id is None or file_id == '':
        return jsonify({'error': 'File not found or no UUID on payload.'}), 404

    try:
        # Retrieve file details from the database
        file_details = get_file_details(file_id)
        print(file_details)
        # Remove special characters and convert to lowercase
        # formatted_status = file_details.lower()

        if file_details == "completed":
            data = get_gpt_data(file_id)
            print(data)
            if data == None:
                data = "CSV contains 4-5 ratings only, no data has been processed."

            response_data = {
                'status': 'complete',
                'gpt_data': data
            }
            return jsonify(response_data), 200
        else:
            processing = {"status": "processing"}
            return jsonify(processing), 200

    except requests.HTTPError as error:
        if error.response.status_code == 404:
            print('404 Not Found Error: The requested URL was not found on the server.')
            abort(404)
        else:
            print('An HTTP error occurred:', error)
            # return jsonify(error), 403
            return jsonify({'error': 'An HTTP error occurred'}), error
        

def detect_column_count(file_path):
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        first_row = next(reader)
        return len(first_row)

def get_filename(ff_id):
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT filename FROM csv_upload WHERE id = %s",
            (ff_id,)
        )
        # Fetch the result as a tuple
        result = cursor.fetchone()

        # Extract the value from the tuple
        result = result[0]
            
        return result
            
    except Error as e:
        print('Error retrieving file details:', e)
        return jsonify({'error': 'Error retrieving file details'}), e

def has_unicode_characters(text):
    for char in text:
        if ord(char) > 127:
            return True
    return False

def remove_unicode(sentence):
    # Remove Unicode characters and replace them with a space
    clean_sentence = re.sub(r'[^\x00-\x7F]', ' ', sentence)
    
    # Replace any multiple spaces with a single space
    clean_sentence = re.sub(r' +', ' ', clean_sentence)
    
    return clean_sentence

def correct_spanish_text(text):
    try:
        # Normalize the text using NFKD normalization form
        normalized_text = unicodedata.normalize('NFKD', text)
        
        # Replace incorrect characters with their correct counterparts
        corrected_text = normalized_text.encode('latin-1', 'ignore').decode('utf-8')
        
        return corrected_text
    except UnicodeDecodeError:
        # Handle decoding error
        print("Decoding error occurred. Unable to correct the text.")
        return text
            
def process_csv_and_openAI(bucket_name, new_filename, uuid):
    try:
        no_count = 0
        yes_count = 0
        maybe_count = 0
        not_applicable = 0
        total = 0

        from langchain.prompts.few_shot import FewShotPromptTemplate
        from langchain.prompts.prompt import PromptTemplate

        # Download the file from the GCS bucket
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(new_filename)

        # Create a temporary file path to download the file
        temp_file_path = f"/tmp/{new_filename}"

        # Download the file to the temporary file path
        blob.download_to_filename(temp_file_path)

        # Create the PostgreSQL table if it doesn't exist
        # create_table_query = f'CREATE TABLE IF NOT EXISTS "{row_id}" (id SERIAL PRIMARY KEY,status TEXT,reason TEXT);'                  
        # create_table_query = f'CREATE TABLE IF NOT EXISTS "{uuid}" (id SERIAL PRIMARY KEY, "tbody" VARCHAR, "status" VARCHAR, "reason" VARCHAR, "result" VARCHAR);'
        create_table_query = f'CREATE TABLE IF NOT EXISTS "{uuid}" (id SERIAL PRIMARY KEY, "tbody" VARCHAR, "status" VARCHAR, "reason" VARCHAR, "result" VARCHAR, timestamp_column TIMESTAMP DEFAULT CURRENT_TIMESTAMP);'

        # print(bucket_name, new_filename, uuid)
        cursor = conn.cursor()
        cursor.execute(create_table_query)
        conn.commit()

        # Create a cursor to execute SQL queries
        cursor = conn.cursor()
        # Call the function to create the fine_tune variable
        guidelines_prompt = load_fine_tune(cursor)

        # Insert data from the CSV file into the PostgreSQL table
        with open(temp_file_path, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)

            # Find the title and body columns
            title_column = None
            body_column = None
            ratings_column = None
            
            for column in csv_reader.fieldnames:
                if column.lower() == "title":
                    title_column = column
                elif column.lower() == "body":
                    body_column = column
                elif column.lower() == "rating":
                    ratings_column = column

            # Check if the title, body, and ratings columns are found
            if title_column is None or body_column is None or ratings_column is None:
                print("Title, body, and/or ratings columns not found in the CSV file.")
                return jsonify({'error': 'Title, body and/or rating columns not found in the CSV file.'}), uuid
            
            insert_query = f'INSERT INTO "{uuid}" ("tbody", "status", "reason", "result") VALUES (%s, %s, %s, %s)'

            # Process each row in the CSV file
            # for row in csv_reader:
            for i, row in enumerate(csv_reader, start=1):
                # Extract the title and body from the CSV row
                title = row[title_column]
                body = row[body_column]
                rating = row[ratings_column]

                # Check if the title or body is None
                if title is None or body is None:
                    continue

                # Check if the rating value is 4 or 5
                elif rating in ['4', '5']:
                    status = "N/A"
                    reason = "N/A"
                    result = "N/A"
                    # Combine the title and body columns with a comma separator
                    review = f"{title}, {body}"

                    cursor.execute(insert_query, (review, status, reason, result))
                    conn.commit()                
                elif rating in ['1', '2', '3']:
                    total += 1
                    # Combine the title and body columns with a comma separator
                    review = f"{body}"
                    unicode = has_unicode_characters(review)
                    review = correct_spanish_text(review)

                    if unicode == True:                    
                        review = remove_unicode(review)

                    result = {'review': review}
                    data_examples = [result]
                
                    example_prompt = PromptTemplate(
                        input_variables=["review"],
                        template='Review: \'{review}\'\nStatus: \nReason: \nResult:'
                    )

                    few_shot_template = FewShotPromptTemplate(
                        examples=data_examples,
                        example_prompt=example_prompt,
                        prefix=guidelines_prompt,
                        suffix='Review: \'{input}\'\nStatus: \nReason: \nResult:',
                        input_variables=["input"]
                    )

                    chat_llm = ChatOpenAI(temperature=0.5)
                    llm_chain = LLMChain(llm=chat_llm, prompt=few_shot_template)

                    answer = llm_chain.run(review)
                    # print(str(i) + " " + answer + '\n')

                    # Extract reason
                    reason_start = answer.find("Reason:") + len("Reason:")
                    reason_end = answer.find("Result:")
                    reason = answer[reason_start:reason_end].strip()

                    # Extract status
                    status_start = answer.find("Status:") + len("Status:")
                    status_end = answer.find("\nReason:")
                    status = answer[status_start:status_end].strip()

                    # Extract result
                    result_start = answer.find("Result:") + len("Result:")
                    result = answer[result_start:].strip()

                    print(i)
                    print("Review:", review)
                    print("Reason:", reason)
                    print("Status:", status)
                    print("Result:", result + '\n')

                    if result.lower() == 'no':
                        no_count += 1
                    elif result.lower() == 'yes':
                        yes_count += 1
                    elif 'maybe' in result.lower():
                        maybe_count += 1
                        result = 'maybe'
                    else:
                        not_applicable += 1
                        result = 'N/A'

                    cursor.execute(insert_query, (review, status, reason, result.lower()))
                    conn.commit()

            # Print the counts
            print("'Total' count:", total)
            print("'No' count:", no_count)
            print("'Yes' count:", yes_count)
            print("'Maybe' count:", maybe_count)
            print("'Not Applicable' count:", not_applicable)

        # Clean up the temporary file
        os.remove(temp_file_path)
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE csv_upload SET status = %s WHERE id = %s",
            ("completed", uuid)
        )        
        conn.commit()
        # return None
        return jsonify({'status': 'completed'}), 200

    except psycopg2.Error as e:
        print("Error connecting to PostgreSQL:", e)
        return jsonify({'error': 'Error connecting to PostgreSQL'}), 500


if __name__ == '__main__':
    # Create an SSL context
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile=certfile1, keyfile=keyfile1)
    # Run the app with SSL enabled
    app.run(ssl_context=ssl_context, host='0.0.0.0', port=8443, threaded=True)
    # app.run(host='0.0.0.0', port=8443, threaded=True)