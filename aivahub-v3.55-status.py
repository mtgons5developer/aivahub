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

def load_fine_tune(cursor):
    
    global guidelines_prompt

    # query = "SELECT * FROM tune_data4"
    query = "SELECT * FROM tune_data4 LIMIT 10"

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

# Function to check if a review exists in the table
def review_exists(cursor, review):
    query = "SELECT COUNT(*) FROM tune_data4 WHERE 'review' = %s"
    cursor.execute(query, (review,))
    count = cursor.fetchone()[0]
    return count > 0

def openAI():
    try:
        no_count = 0
        yes_count = 0
        maybe_count = 0
        not_applicable = 0
        total = 0

        # Create a cursor to execute SQL queries
        cursor = conn.cursor()
        # Call the function to create the fine_tune variable
        guidelines_prompt = load_fine_tune(cursor)

        from langchain.prompts.few_shot import FewShotPromptTemplate
        from langchain.prompts.prompt import PromptTemplate

        # Read the CSV file
        with open("csv/B00UFJNVTS - Heat Resistant Oven Mitts (2 pack)_ High Temperatu 2023-06-07.csv", "r") as file:
        # with open("csv/20230630 - B0050FRY5Y - Reviews SMCS - PATRICK REVIEW.csv", "r") as file:    
            
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

                    elif rating in ['1', '2', '3']:# and i == 85:
                        total += 1
                        # Combine the title and body columns with a comma separator
                        review = f"{title}, {body}"
                        result = {'review': review}
                        data_examples = [result]
                        # print(review)

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
                        else:
                            not_applicable += 1

                # Print the counts
                print("'Total' count:", total)
                print("'No' count:", no_count)
                print("'Yes' count:", yes_count)
                print("'Maybe' count:", maybe_count)
                print("'Not Applicable' count:", not_applicable)
                # #264 total 4 high 12 moderate 19 low and 229 NA

    except IOError as e:
        print("Error reading the CSV file:", e)

    except Exception as e:
        print("An error occurred:", e)
        traceback.print_exc()

openAI()
