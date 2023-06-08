import os
import csv
import psycopg2
import traceback

from langchain import OpenAI, LLMChain
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv
from google.cloud import storage
from langchain.prompts.few_shot import FewShotPromptTemplate
from langchain.prompts.prompt import PromptTemplate
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

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


def listener():
    # Set the isolation level to autocommit
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    # Create a new cursor
    cur = conn.cursor()

    # Define a function to handle the trigger event
    def notify_csv_upload_trigger():
        # Add your logic here to handle the trigger event
        print("Trigger event received!")

    # Enable listening for notifications
    cur.execute("LISTEN csv_upload_channel")

    # Loop to listen for notifications
    while True:
        conn.poll()
        while conn.notifies:
            notify = conn.notifies.pop(0)
            print("Received notification on channel:", notify.channel)
            # Perform actions based on the received notification
            if notify.channel == 'csv_upload_channel':
                notify_csv_upload_trigger()

        # Add any other processing or wait mechanism as needed

def process_csv():

    # Provide the name of your bucket and the file you want to read
    bucket_name = "schooapp2022.appspot.com"
    file_name = "csv-gpt.csv"

    # Read the file from Google Cloud Storage
    file_content = read_file_from_gcs(bucket_name, file_name)

    # Parse the CSV content
    rows = csv.reader(file_content.splitlines())
    header = next(rows)  # Extract the header row
    # print("CSV Header:", header)  # Print the header for debugging

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
        # print(f"Review: {review}\nStatus: {answer.strip()}")

        # Split the contents into status and reason
        status, reason = answer.strip().split('\nReason: ', 1) if '\nReason: ' in answer else (answer, '')

        # Insert the extracted values into the 'analysis' table
        insert_query = """
            INSERT INTO analysis (review, status, reason)
            VALUES (%s, %s, %s)
        """
        values = (review, status, reason)  # Assuming you have the 'review' value

        cursor.execute(insert_query, values)
        conn.commit()
        print(f"Review: {review}\nStatus: {answer.strip()}")

def read_file_from_gcs(bucket_name, file_name):
    # Instantiate the client
    client = storage.Client()

    # Retrieve the bucket and file
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    # Download the file's content as a string
    content = blob.download_as_text()

    return content

try:
    listener()
    process_csv()

except psycopg2.Error as e:
    print("Error connecting to PostgreSQL:", e)
    traceback.print_exc()

finally:
    # Close the connection
    if conn is not None:
        conn.close()
