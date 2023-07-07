import os
import csv
import sys
import traceback
import time
import json
from openai.error import RateLimitError
import openai
import psycopg2
from psycopg2 import Error
from guide import guidelines_prompt
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from langchain import OpenAI, LLMChain
from langchain.chat_models import ChatOpenAI

from dotenv import load_dotenv

load_dotenv()

openai.openai_api_key = os.getenv('OPENAI_API_KEY')
os.environ['OPENAI_API_KEY'] = openai.openai_api_key

# Database credentials
db_host = os.getenv('HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DATABASE')
db_user = os.getenv('DB_USER')
db_password = os.getenv('PASSWORD')

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

# Create a cursor to execute SQL queries
cursor = conn.cursor()
query = "SELECT * FROM tune_data"

cursor.execute(query)
# Fetch all the rows from the result set
rows = cursor.fetchall()

# Create a variable to store the formatted examples
fine_tune = ""

for row in rows:
    review = row[1]
    status = str(row[2])
    reason = row[3]
    result = str(row[4])

    # Format the example
    data = (
        '"review": "' + review + '",\n' +
        '"status": "' + status + '",\n' +
        '"reason": "' + reason + '",\n' +
        '"result": "' + result + '"\n\n'
    )

    # Append the formatted example to the output
    fine_tune += data

cursor.close()
conn.close()

# Define the PromptTemplate class
class PromptTemplate(BasePromptTemplate):
    def format(self, **kwargs):
        input_variables = self.input_variables
        template = self.template

        return template.format(**kwargs)

    def format_prompt(self, **kwargs):
        formatted_prompt = self.format(**kwargs)
        return formatted_prompt.strip()

# Prompt template with the fine-tuned examples
example_prompt = '''
Review: \'{review}\'
Status: 
Reason: 
Result:'''

prompt_template = PromptTemplate(
    input_variables=["review"],
    template=example_prompt
)

# Add the formatted examples to the prompt
prompt = guidelines_prompt.replace('{fine_tune}', fine_tune)

# Initialize the language model and prompt it with the formatted examples
chat_llm = ChatOpenAI(temperature=0)
llm_chain = LLMChain(llm=chat_llm, prompt=prompt_template)

# Read the CSV file and process each row
try:
    with open("csv/B00UFJNVTS - Heat Resistant Oven Mitts (2 pack)_ High Temperatu 2023-06-07.csv", "r") as file:
        csv_reader = csv.DictReader(file)
        title_column = None
        body_column = None
        ratings_column = None

        # Find the title and body columns
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
            sys.exit(1)

        # Open a file for writing the formatted reviews and reasons
        with open("formatted_reviews.txt", "w") as output_file:
            # Process each row in the CSV file
            for i, row in enumerate(csv_reader, start=1):
                # Extract the title and body from the CSV row
                title = row[title_column]
                body = row[body_column]
                rating = row[ratings_column]

                # Check if the title or body is None
                if title is None or body is None:
                    continue

                # Combine the title and body columns with a comma separator
                review = f"{title}, {body}"

                # Prompt the language model with the review
                answer = llm_chain.run(review)
                print(str(i) + " " + answer + '\n')

except IOError as e:
    print("Error reading the CSV file:", e)

except Exception as e:
    print("An error occurred:", e)
    traceback.print_exc()

# Rest of your code...
