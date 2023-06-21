import urllib.request
import urllib.error
import os
import csv
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
                    'result': row[4],
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
        create_table_query = f'CREATE TABLE IF NOT EXISTS "{uuid}" (id SERIAL PRIMARY KEY, "tbody" VARCHAR, "status" VARCHAR, "reason" VARCHAR, "result" VARCHAR);'

        # print(bucket_name, new_filename, uuid)
        cursor = conn.cursor()
        cursor.execute(create_table_query)
        conn.commit()
        data_to_insert = []

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
                    continue
                
                else:
                    # Combine the title and body columns with a comma separator
                    review = f"{title}, {body}"

                    # Create a dictionary with the extracted values
                    result = {'review': review}
                    examples = [result]

                    example_prompt = PromptTemplate(input_variables=["review"],
                                        template="Review: '''{review}'''\nStatus: \nReason: \nResult:")

                    few_shot_template = FewShotPromptTemplate(
                        examples=examples,
                        example_prompt=example_prompt,
                        prefix=guidelines_prompt,
                        suffix="Review: '''{input}",
                        input_variables=["input"]
                    )
                    
                    llm_chain = LLMChain(llm=chat_llm, prompt=few_shot_template)

                    answer = llm_chain.run(review)
                    answer = answer.replace("'''", "")
                    # print(f"Review: {review} \n{text_without_quotes}")

                    status_start = answer.find("Status:")
                    status_end = answer.find("\nReason:")
                    status = answer[status_start + len("Status:"):status_end].strip()
                    reason_start = answer.find("Reason:")
                    reason_end = answer.find("\nResult:")
                    reason = answer[reason_start + len("Reason:"):reason_end].strip()
                    result_start = answer.find("Result:")
                    result = answer[result_start + len("Result:"):].strip()

                    print(f"Review: {review}\nStatus: {status}\nReason: {reason}\nResult: {result}")                
                    # print(f"Row {i} - Review: {review}\nStatus: {status}\nReason: {reason}\nResult: {result}")
                    # if i == 17: quit()
                    
                    cursor.execute(insert_query, (review, status, reason, result))
                    conn.commit()

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

    # finally:
    #     # Close the connection
    #     if conn is not None:
    #         conn.close()

guidelines_prompt = '''
''Does the following review comply with all 14 of Amazon's guidelines? If not, which guideline(s) does it potentially violate?

    1- Seller, Order, or Shipping Feedback:
    Reviews and Questions and Answers should focus on the product itself rather than individual experiences related to sellers, ordering, or shipping.
    - Avoid discussing the following topics in reviews and questions and answers:
    - Seller performance and customer service.
    - Ordering issues, returns, and refunds.
    - Shipping packaging.
    - Product condition and damage caused during shipping.
    - Shipping cost and delivery speed.
    Why? The purpose of community content is to provide information about the product. While we value feedback on sellers and packaging, we encourage you to share such feedback through appropriate channels other than reviews or questions and answers.

    2- Comments about Pricing or Availability:
    It is acceptable to comment on pricing if it directly relates to the product's value. For example, "This blender is excellent for only $29."
    - Comments regarding pricing based on individual experiences are not permitted. For example, "I found this product $5 cheaper at my local store."
    - Such comments are irrelevant to all customers and therefore not allowed.
    - Certain comments about availability are allowed, such as expressing a desire for a product to be available in a different format, like paperback for a book.
    - However, comments specific to availability at a particular store are not permitted.
    The community's purpose is to share product-specific feedback that will be relevant to all customers.

    3- Content written in unsupported languages:
    Supported languages for content are English and Spanish.
    To ensure the usefulness of content, it should only be written in English or Spanish, depending on the supported language(s) of the Amazon site where it will appear.
    For example, reviews written in French, German, Italian, Portuguese, Dutch, Russian, Chinese, Japanese, Korean, Arabic, Hindi, Turkish, Polish, Swedish, or any other unsupported language are not allowed on Amazon.com, as it only supports English and Spanish.
    Please make sure to write your content in the appropriate supported language for the specific Amazon site to which it is intended.

    4- Repetitive Text, Spam, or Pictures Created with Symbols:
    Contributions with distracting content and spam are not allowed.
    This includes:
    - Repetitive text that serves no meaningful purpose.
    - Nonsense, gibberish, or content that lacks coherence.
    - Content consisting solely of punctuation marks and symbols.
    - ASCII art, which refers to pictures created using symbols and letters.
    Why? The purpose of contributions is to provide helpful and relevant information to the community. Repetitive text, spam, and content that lacks substance or meaningful value detract from the overall usefulness and readability of the platform.

    5- Private Information:
    Do not post content that invades others' privacy or shares your own personal information.
    This includes, but is not limited to:
    - Phone numbers
    - Email addresses
    - Mailing addresses
    - License plate numbers
    - Data source names (DSN)
    - Order numbers
    Why? Respecting privacy is crucial to maintain a safe and secure environment. Sharing personal information can lead to unintended consequences or potential misuse. Please refrain from posting any content that compromises privacy, both yours and others'.

    6- Profanity or Harassment:
    While questioning others' beliefs and expertise is acceptable, it's important to maintain a respectful tone.
    The following actions are not allowed:
    - Using profanity, obscenities, or engaging in name-calling.
    - Engaging in harassment or making threats.
    - Launching personal attacks on individuals with whom you disagree.
    - Posting content that constitutes libel, defamation, or is deliberately inflammatory.
    - Drowning out others' opinions by posting from multiple accounts or coordinating with others.
    Why? Promoting a respectful and inclusive environment fosters constructive discussions. Avoiding profanity, harassment, and personal attacks ensures that conversations remain civil and beneficial for everyone involved.

    7- Hate Speech:
    Expressing hatred towards individuals based on their characteristics is strictly prohibited.
    This includes but is not limited to:
    - Race
    - Ethnicity
    - Nationality
    - Gender
    - Gender identity
    - Sexual orientation
    - Religion
    - Age
    - Disability
    Additionally, promoting organizations that propagate hate speech based on these characteristics is also not allowed.
    Why? Creating a safe and inclusive environment is paramount. By disallowing hate speech and the promotion of such organizations, we ensure that our platform remains respectful, tolerant, and free from discrimination.

    8- Sexual Content:
    Discussions regarding sex and sensuality products available on Amazon are permissible.
    Likewise, products containing sexual content such as books and movies can be discussed.
    However, the following restrictions apply:
    - Profanity and obscene language are not allowed.
    - Content containing nudity or sexually explicit images or descriptions is prohibited.
    Why? Allowing discussions about sex-related products while maintaining a respectful atmosphere is essential. By prohibiting profanity, explicit images, and descriptions, we ensure that the community remains appropriate and comfortable for all users.

    9- External Links:
    - Links to other products on Amazon are permitted, but linking to external sites is not allowed.
    - Avoid posting links to phishing or malware-infected websites.
    - Refrain from sharing URLs that include referrer tags or affiliate codes.
    Why? Allowing links to other products on Amazon enables users to access additional information. However, prohibiting external links ensures the safety and security of our community by preventing potential malicious content or unauthorized tracking through referrer tags and affiliate codes.

    10- Ads or Promotional Content:
    - Do not post content that primarily serves the purpose of promoting a company, website, author, or special offer.
    - Contributions should focus on providing genuine and helpful information rather than promotional material.
    Why? The primary objective of the community is to facilitate informative discussions and share knowledge. By discouraging ads or promotional content, we ensure that the platform remains focused on valuable contributions rather than overt advertising.

    11- Conflicts of Interest:
    Creating, editing, or posting content about your own products or services is strictly prohibited.
    The same restriction applies to content related to products or services offered by:
    - Friends
    - Relatives
    - Employers
    - Business associates
    - Competitors
    Why? Upholding a fair and unbiased environment is crucial. By avoiding conflicts of interest, we maintain the integrity and authenticity of the community's content, ensuring that discussions are driven by genuine experiences and unbiased perspectives.

    12- Solicitations:
    When requesting others to post content about your products, ensure that the request remains neutral. Influencing them to leave a positive rating or review is not allowed.
    Offering, requesting, or accepting compensation for creating, editing, or posting content is strictly prohibited. Compensation includes free and discounted products, refunds, reimbursements, and any attempts to manipulate the Amazon Verified Purchase badge through special pricing or reimbursements for reviewers.
    If you have a financial or close personal connection to a brand, seller, author, or artist:
    - Posting content other than reviews and questions and answers is acceptable, but it is essential to clearly disclose your connection.
    - Brands or businesses cannot engage in activities that divert Amazon customers to non-Amazon websites, applications, services, or channels. This includes ads, special offers, and "calls to action" designed to conduct marketing or sales transactions. Additional labeling is not necessary if you post content about your own products or services through a brand, seller, author, or artist account.
    - Authors and publishers can still provide readers with free or discounted copies of their books as long as they do not require a review in exchange or attempt to influence the review.
    Why? Maintaining transparency, fairness, and unbiased opinions is fundamental to the integrity of the community. By discouraging solicitations and ensuring clear disclosure of connections, we foster an environment that promotes authentic engagement and trust among users.

    13- Plagiarism, Infringement, or Impersonation:
    Only post content on Amazon that you own or have proper permission to use. This includes text, images, and videos.
    The following actions are strictly prohibited:
    - Posting content that infringes on others' intellectual property rights, including copyrights, trademarks, patents, and trade secrets.
    - Engaging in interactions with community members that infringe on others' intellectual property or proprietary rights.
    - Impersonating individuals or organizations.
    Why? Respecting intellectual property rights and preventing impersonation is crucial to maintain a fair and trustworthy community. By discouraging plagiarism, infringement, and impersonation, we ensure that original content is shared, intellectual property is respected, and individuals are not misrepresented.

    14- Illegal Activities:
    Posting content that promotes or encourages illegal activities is strictly prohibited. This includes:
    - Violence
    - Illegal drug use
    - Underage drinking
    - Child or animal abuse
    - Fraudulent activities
    Content that advocates or threatens physical or financial harm to yourself or others, including terrorism, is not allowed. Jokes or sarcastic comments about causing harm are also prohibited.
    Offering fraudulent goods, services, promotions, or participating in schemes such as "make money fast" or pyramid schemes is not allowed.
    Encouraging the dangerous misuse of a product is strictly prohibited.
    Why? Upholding legal and ethical standards is of utmost importance. By prohibiting content that promotes illegal activities, harm, or fraud, we maintain a safe and trustworthy community where users can engage responsibly and contribute to meaningful discussions.

    ```
    Only state Compliant or Violation for Status:
    If Compliant set Result: 'NO', don't add anything. If in Violation set Result: 'YES', don't add anything. The "Result" is assigned as "Maybe" to convey uncertainty or ambiguity.'''
'''
'''''''''

if __name__ == '__main__':
    # Create an SSL context
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile=certfile1, keyfile=keyfile1)
    # Run the app with SSL enabled
    app.run(ssl_context=ssl_context, host='0.0.0.0', port=8443, threaded=True)

