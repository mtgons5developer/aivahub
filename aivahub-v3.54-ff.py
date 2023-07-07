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
from transformers import GPT2Tokenizer

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

chat_llm = ChatOpenAI(temperature=0)

# Create a cursor to execute SQL queries
cursor = conn.cursor()
# query = "SELECT * FROM tune_data2"
query = "SELECT * FROM tune_data2 LIMIT 11"

cursor.execute(query)
# Fetch all the rows from the result set
rows = cursor.fetchall()

# Create a variable to store the formatted examples
fine_tune = ""

for row in rows:
    review = row[6]
    status = str(row[1])
    status2 = str(row[4])
    reason = row[0]
    reason2 = row[3]
    result = str(row[2])
    result2 = str(row[5])

    # Format the example
    data = (
        '"review": "' + review + '",\n' +
        '"status": "' + status + '",\n' +
        '"status": "' + status2 + '",\n' +
        '"reason": "' + reason + '",\n' +
        '"reason": "' + reason2 + '",\n' +
        '"result": "' + result + '",\n' +
        '"result": "' + result2 + '"\n\n'
    )

    # Append the formatted example to the output
    fine_tune += data

# print(fine_tune)
# quit()

cursor.close()
conn.close()

# Replace {fine_tune} with the actual value
guidelines_prompt = guidelines_prompt.format(fine_tune=fine_tune)

# Calculates the number of tokens used in the given guidelines_prompt:
tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
tokenized_prompt = tokenizer.encode(guidelines_prompt, add_special_tokens=False)
num_tokens = len(tokenized_prompt)

print("Number of tokens used:", num_tokens)
# quit()

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

                    elif rating in ['1', '2', '3']:

                        # Combine the title and body columns with a comma separator
                        review = f"{title}, {body}"
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

                        llm_chain = LLMChain(llm=chat_llm, prompt=few_shot_template)

                        answer = llm_chain.run(review)
                        print(str(i+1) + " " + answer + '\n')
                        # quit()

                        # Run the code again if the status is empty
                        if not status:
                            answer = llm_chain.run(review)
                            print(str(i) + " " + answer + '\n')
                        # else:
                            # print(str(i) + " Status already exists: " + status)
                            # status = "SKIP"

                        # lines = answer.split("\n")
                        # status = lines[0].replace("Status:", "").strip()
                        # reason = lines[1].replace("Reason:", "").strip()
                        # result = lines[2].replace("Result:", "").strip().lower() if lines[2] else None

                        # if result is None:
                        #     if status == "Compliant":
                        #         result = "no"
                        #         print("ERROR")
                        #     elif status == "Violation":
                        #         result = "yes"
                        #         print("ERROR")
                
    except IOError as e:
        print("Error reading the CSV file:", e)

    except Exception as e:
        print("An error occurred:", e)
        traceback.print_exc()

openAI()
