import os
import csv
import ssl
import sys
import time
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from celery import Celery
import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from openai.error import RateLimitError
from google.cloud import storage

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

chat_llm = ChatOpenAI(temperature=0.8)

def completion_with_retry(prompt):
    retry_delay = 1.0
    max_retries = 3
    retries = 0

    while True:
        try:
            return chat_llm.chat(prompt).get('choices')[0]['message']['content']
        except RateLimitError as e:
            if retries >= max_retries:
                raise e
            else:
                retries += 1
                print(f"Rate limit exceeded. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)


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
        response_data = {
            'status': 'complete',
            'data': data
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
                    'id': row[0],
                    'status': row[1],
                    'reason': row[2],
                    # Add more columns as needed
                }
                result.append(data)

            return result

    except Error as e:
        print('Error retrieving data from the table:', e)


@app.route('/status/<string:file_id>', methods=['GET'])
def get_status(file_id):

    if file_id is None:
        return jsonify({'error': 'File not found or no UUID on payload.'}), 404
    elif file_id == '':
        return jsonify({'error': 'File not found or no UUID on payload.'}), 404

    try:

        # Retrieve file details from the database
        file_details = get_file_details(file_id)

        # Remove special characters and convert to lowercase
        formatted_status = file_details.lower()

        if formatted_status == "completed":
            data = get_gpt_data(file_id)
            response_data = {
                'status': 'complete',
                'gpt_data': data
            }
            return jsonify(response_data), 200
        else:
            # return jsonify({'error': 'File not found'}), 404
            processing = {"status": "processing"}
            return jsonify(processing), 200

    except requests.HTTPError as error:
        if error.response.status_code == 404:
            print('404 Not Found Error: The requested URL was not found on the server.')
            return jsonify(processing), 404
        else:
            print('An HTTP error occurred:', error)
            return jsonify(error), 403
        

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
        
def process_csv_and_openAI(bucket_name, new_filename, uuid):
    try:
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
        create_table_query = f'CREATE TABLE IF NOT EXISTS "{uuid}" (id SERIAL PRIMARY KEY, "status" VARCHAR, "reason" VARCHAR);'

        # print(bucket_name, new_filename, uuid)
        cursor = conn.cursor()
        cursor.execute(create_table_query)
        conn.commit()

        # Insert data from the CSV file into the PostgreSQL table
        with open(temp_file_path, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)

            # Find the title and body columns
            title_column = None
            body_column = None
            for column in csv_reader.fieldnames:
                if column.lower() == "title":
                    title_column = column
                elif column.lower() == "body":
                    body_column = column

            # Check if the title and body columns are found
            if title_column is None or body_column is None:
                print("Title and/or body columns not found in the CSV file.")
                return uuid

            insert_query = f'INSERT INTO "{uuid}" ("status", "reason") VALUES (%s, %s)'

            for row in csv_reader:
                # Extract the title and body from the CSV row
                title = row[title_column]
                body = row[body_column]

                # Combine the title and body columns with a comma separator
                review = f"{title}, {body}"

                # Create a dictionary with the extracted values
                result = {'review': review}
                # Convert the dictionary to a list
                examples = [result]

                example_prompt = PromptTemplate(input_variables=["review"],
                                        template="Review: '''{review}'''\nStatus: \nReason: ")

                few_shot_template = FewShotPromptTemplate(
                    examples=examples,
                    example_prompt=example_prompt,
                    prefix=guidelines_prompt,
                    suffix="Review: '''{input}",
                    input_variables=["input"]
                )

                llm_chain = LLMChain(llm=chat_llm, prompt=few_shot_template)

                answer = llm_chain.run(review)
                status_end = answer.find("\nReason: ")
                status = answer[:status_end].strip()
                reason = answer[status_end:].strip()
                # print(f"Review: {review}\nStatus: {status}\nReason: {reason}")

                cursor.execute(insert_query, (status, reason))
                conn.commit()

        # Clean up the temporary file
        os.remove(temp_file_path)
        cursor = conn.cursor()
        # cursor.execute(
        #     "UPDATE csv_upload SET status = %s",
        #     ("completed",)
        # )
        cursor.execute(
            "UPDATE csv_upload SET status = %s WHERE id = %s",
            ("completed", uuid)
        )        
        conn.commit()
        return None

    except psycopg2.Error as e:
        print("Error connecting to PostgreSQL:", e)

    # finally:
    #     # Close the connection
    #     if conn is not None:
    #         conn.close()

guidelines_prompt = '''
''Run each guideline and analyze why it was violated. Always provide a reason:

    1- Seller, order, or shipping feedback:
    We don't allow reviews or questions and answers that focus on:
    - Sellers and the customer service they provide
    - Ordering issues and returns
    - Shipping packaging
    - Product condition and damage
    - Shipping cost and speed
    Why not? Community content is meant to help customers learn about the product itself, not someone's individual experience ordering it. That said, we definitely want to hear your feedback about sellers and packaging, just not in reviews or questions and answers.

    2- Comments about pricing or availability:
    It's OK to comment on price if it's related to the product's value. For example, "For only $29, this blender is really great."
    Pricing comments related to someone's individual experience aren't allowed. For example, "Found this here for $5 less than at my local store."
    These comments aren't allowed because they aren't relevant for all customers.
    Some comments about availability are OK. For example, "I wish this book was also available in paperback."
    However, we don't allow comments about availability at a specific store. Again, the purpose of the community is to share product-specific feedback that will be relevant to all other customers.

    3- Content written in unsupported languages:
    Supported languages are English and Spanish.
    To ensure that content is useful, we only allow it to be written in the supported language(s) of the Amazon site where it will appear. For example, we don't allow reviews written in French on Amazon.com. It only supports English and Spanish. Some Amazon sites support multiple languages, but content written in a mix of languages isn't allowed.

    4- Repetitive text, spam, or pictures created with symbols:
    We don't allow contributions with distracting content and spam. This includes:
    - Repetitive text
    - Nonsense and gibberish
    - Content that's just punctuation and symbols
    - ASCII art (pictures created using symbols and letters)

    5- Private information:
    Don't post content that invades others' privacy or shares your own personal information, including:
    - Phone number
    - Email address
    - Mailing address
    - License plate
    - Data source name (DSN)
    - Order number

    6- Profanity or harassment:
    It's OK to question others' beliefs and expertise, but be respectful. We don't allow:
    - Profanity, obscenities, or name-calling
    - Harassment or threats
    - Attacks on people you disagree with
    - Libel, defamation, or inflammatory content
    - Drowning out others' opinions. Don't post from multiple accounts or coordinate with others.

    7- Hate speech:
    It's not allowed to express hatred for people based on characteristics like:
    - Race
    - Ethnicity
    - Nationality
    - Gender
    - Gender identity
    - Sexual orientation
    - Religion
    - Age
    - Disability
    It's also not allowed to promote organizations that use such hate speech.

    8- Sexual content:
    It's OK to discuss sex and sensuality products sold on Amazon. The same goes for products with sexual content (books, movies). That said, we still don't allow profanity or obscene language. We also don't allow content with nudity or sexually explicit images or descriptions.

    9- External links
    We allow links to other products on Amazon, but not to external sites. Don't post links to phishing or other malware sites. We don't allow URLs with referrer tags or affiliate codes.

    10- Ads or promotional content:
    Don't post content if its main purpose is to promote a company, website, author, or special offer.

    11- Conflicts of interest:
    It's not allowed to create, edit, or post content about your own products or services. The same goes for services offered by:
    - Friends
    - Relatives
    - Employers
    - Business associates
    - Competitors

    12- Solicitations:
    If you ask others to post content about your products, keep it neutral. For example, don't try to influence them into leaving a positive rating or review.
    Don't offer, request, or accept compensation for creating, editing, or posting content. Compensations include free and discounted products, refunds, and reimbursements. Don't try to manipulate the Amazon Verified Purchase badge by offering reviewers special pricing or reimbursements.
    Have a financial or close personal connection to a brand, seller, author, or artist?:
    - It’s OK to post content other than reviews and questions and answers, but you need to clearly disclose your connection. However, brands or businesses can’t participate in the community in ways that divert Amazon customers to non-Amazon websites, applications, services, or channels. This includes ads, special offers, and “calls to action” used to conduct marketing or sales transactions. If you post content about your own products or services through a brand, seller, author, or artist account, additional labeling isn’t necessary.
    - Authors and publishers can continue to give readers free or discounted copies of their books if they don't require a review in exchange or try to influence the review.

    13- Plagiarism, infringement, or impersonation:
    Only post your own content or content you have permission to use on Amazon. This includes text, images, and videos. You're not allowed to:
    - Post content that infringes on others' intellectual property (including copyrights, trademarks, patents, trade secrets) or other proprietary rights
    - Interact with community members in ways that infringe on others' intellectual property or proprietary rights
    - Impersonate someone or an organization

    14- Illegal activities:
    Don't post content that encourages illegal activity like:
    - Violence
    - Illegal drug use
    - Underage drinking
    - Child or animal abuse
    - Fraud
    We don't allow content that advocates or threatens physical or financial harm to yourself or others. This includes terrorism. Jokes or sarcastic comments about causing harm aren't allowed.
    It's also not allowed to offer fraudulent goods, services, promotions, or schemes (make money fast, pyramid).
    It's not allowed to encourage the dangerous misuse of a product.

    ```
    Does the following review violate any of the 14 Amazon's rules guidelines above? If you are not sure, just say I don't know, don't try to make up an answer.'''
'''
'''''''''

if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=8443, threaded=True)
    # Create an SSL context
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile=certfile1, keyfile=keyfile1)
    # ssl_context.load_cert_chain(certfile='/home/almedae/github/aivahub/server-signed-cert.pem', keyfile='/home/almedae/github/aivahub/server-key.pem')
    # Run the app with SSL enabled
    app.run(ssl_context=ssl_context, host='0.0.0.0', port=8443, threaded=True)



