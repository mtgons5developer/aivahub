import os
import csv
import psycopg2
import traceback
import time
from openai.error import RateLimitError

from langchain import OpenAI, LLMChain
from langchain.chat_models import ChatOpenAI

from create_env import create
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')
os.environ['OPENAI_API_KEY'] = openai_api_key

# Retrieve the PostgreSQL connection details from environment variables
db_host = 'localhost'
db_port = 5432
db_name = 'postgres'
db_user = 'datax'
db_password = 'root1234'

chat_llm = ChatOpenAI()

def completion_with_retry(prompt):
    retry_delay = 1.0
    max_retries = 3
    retries = 0

    while True:
        try:
            return chat_llm.completion(prompt)
        except RateLimitError as e:
            if retries >= max_retries:
                raise e
            else:
                retries += 1
                print(f"Rate limit exceeded. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)


guidelines_prompt = '''
...
'''

# Connect to the PostgreSQL database
conn = psycopg2.connect(
    host=db_host,
    port=db_port,
    database=db_name,
    user=db_user,
    password=db_password
)

def openAI():
    try:
        from langchain.prompts.few_shot import FewShotPromptTemplate
        from langchain.prompts.prompt import PromptTemplate

        # Read the CSV file
        with open("csv-gpt.csv", "r") as file:
            csv_reader = csv.DictReader(file)
            title_column = None
            body_column = None

            # Find the title and body columns
            for column in csv_reader.fieldnames:
                if column.lower() == "title":
                    title_column = column
                elif column.lower() == "body":
                    body_column = column

            # Check if the title and body columns are found
            if title_column is None or body_column is None:
                print("Title and/or body columns not found in the CSV file.")
                return

            # Process each row in the CSV file
            for row in csv_reader:
                # Extract the title and body from the CSV row
                title = row[title_column]
                body = row[body_column]

                # Combine the title and body columns with a comma separator
                review = f"{title}, {body}"

                # Create a dictionary with the extracted values
                result = {'review': review}
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
                answer = completion_with_retry(answer)

                print(f"Review: {review}\nStatus: {answer.strip()}")

    except IOError as e:
        print("Error reading the CSV file:", e)

    except Exception as e:
        print("An error occurred:", e)
        traceback.print_exc()


openAI()
