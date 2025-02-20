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

chat_llm = ChatOpenAI(temperature=0.8)

# Create a cursor to execute SQL queries
cursor = conn.cursor()
query = "SELECT * FROM tune_data2"
cursor.execute(query)
# Fetch all the rows from the result set
rows = cursor.fetchall()
# Create a list to store the JSON objects
data = []
for row in rows:
    review = row[0]
    status = row[1]
    reason = row[2]
    result = row[3]
    examples = {
        'review': row[6],
        'reason': row[0],
        'reason': row[4],
        'status': row[1],
        'status': row[5],
        'result': row[2],
        'result': row[5]  
    }
    data.append(examples)

cursor.close()
conn.close()

def openAI():
    try:
        from langchain.prompts.few_shot import FewShotPromptTemplate
        from langchain.prompts.prompt import PromptTemplate

        # Read the CSV file
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
                return

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

                    # Check if the rating value is 4 or 5
                    elif rating in ['4', '5']:
                        continue

                    else:
                        # Combine the title and body columns with a comma separator
                        review = f"{title}, {body}"

                        example_prompt = PromptTemplate(
                            input_variables=["review"],
                            template='Review: \'{review}\'\nStatus: \nReason: \nResult:'
                        )

                        few_shot_template = FewShotPromptTemplate(
                            examples=data,
                            example_prompt=example_prompt,
                            prefix=guidelines_prompt,
                            suffix='Review: \'{input}\'\nStatus: \nReason: \nResult:',
                            input_variables=["input"]
                        )

                        llm_chain = LLMChain(llm=chat_llm, prompt=few_shot_template)

                        answer = llm_chain.run(review)
                        print(str(i) + " " + answer + '\n')

                        lines = answer.split("\n")
                        status = lines[0].replace("Status:", "").strip()
                        reason = lines[1].replace("Reason:", "").strip()
                        result = lines[2].replace("Result:", "").strip().lower() if lines[2] else None

                        if result is None:
                            if status == "Compliant":
                                result = "no"
                                print("ERROR")
                            elif status == "Violation":
                                result = "yes"
                                print("ERROR")

                        # formatted_review = f'{{"review": "{review}", "reason": "{reason}", "status": "{status}", "result": "{result}"}}'
                        # print(formatted_review + "\n")

    except IOError as e:
        print("Error reading the CSV file:", e)

    except Exception as e:
        print("An error occurred:", e)
        traceback.print_exc()

openAI()

