import os
import csv
import psycopg2
import requests
from flask import Flask, request

from langchain import OpenAI, LLMChain
from langchain.chat_models import ChatOpenAI
from google.cloud import storage
from langchain.prompts.few_shot import FewShotPromptTemplate
from langchain.prompts.prompt import PromptTemplate
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')
os.environ['OPENAI_API_KEY'] = openai_api_key

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

# Disable SSL certificate verification warning
requests.packages.urllib3.disable_warnings()
# Send HTTP request without certificate verification
response = requests.get('https://example.com', verify=False)

app = Flask(__name__)

@app.route('/process_csv', methods=['POST'])
def process_csv():
    # Get the CSV file content from the request
    file_content = request.data.decode('utf-8')

    # Parse the CSV content
    rows = csv.reader(file_content.splitlines())
    header = next(rows)  # Extract the header row

    # Find the indices of the required columns
    column_indices = [header.index(column) for column in ["Title", "Body", "gpt_status", "gpt_reason"]]

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # Execute the query to retrieve the guidelines_prompt from the database
    query = "SELECT guidelines FROM guidelines_prompt WHERE id = 4;"
    cursor.execute(query)

    # Fetch the result
    result = cursor.fetchone()

    # Extract the guidelines_prompt from the result
    guidelines_prompt = result[0]

    # Iterate over the rows and extract the required columns
    for row in rows:
        columns = [row[index] for index in column_indices]
        title, body, gpt_status, gpt_reason = columns
        # Do something with the extracted columns
        review = f"{title}, {body}"
        # Create a dictionary with the extracted values
        result = {'review': review, 'status': gpt_status, 'reason': gpt_reason}
        # Convert the dictionary to a list
        examples = [result]

        example_prompt = PromptTemplate(input_variables=["review", "status", "reason"],
                                        template="Review: '''{review}'''\nStatus: {status}\nReason: {reason}")

        few_shot_template = FewShotPromptTemplate(
            examples=examples,
            example_prompt=example_prompt,
            prefix=guidelines_prompt,
            suffix="Review: '''{input}'''\nStatus:",
            input_variables=["input"]
        )

        chat_llm = ChatOpenAI(temperature=0)
        llm_chain = LLMChain(llm=chat_llm, prompt=few_shot_template)

        answer = llm_chain.run(review)

        # Split the contents into status and reason
        status, reason = answer.strip().split('\nReason: ', 1) if '\nReason: ' in answer else (answer, '')

        # Insert the extracted values into the 'analysis' table
        insert_query = """
            INSERT INTO analysis (review, status, reason)
            VALUES (%s, %s, %s)
        """
        values = (review, status, reason)

        cursor.execute(insert_query, values)
        conn.commit()
        print(f"Review: {review}\nStatus: {answer.strip()}")

    return "CSV processing completed"

@app.route('/notify_csv_upload', methods=['POST'])
def notify_csv_upload():
    # Add your logic here to handle the trigger event
    print("Trigger event received!")
    return "Notification received"

# if __name__ == '__main__':
#     app.run(ssl_context='adhoc')

if __name__ == '__main__':
    app.run(ssl_context=('certificate_file.crt', 'private_key_file.key'))
    
