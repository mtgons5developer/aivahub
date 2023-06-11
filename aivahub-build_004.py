import os
import psycopg2
import traceback

from langchain import OpenAI, LLMChain
from langchain.chat_models import ChatOpenAI

from create_env import create
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')
os.environ['OPENAI_API_KEY'] = openai_api_key

# Retrieve the PostgreSQL connection details from environment variables
db_host = os.getenv('HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DATABASE')
db_user = os.getenv('USER')
db_password = os.getenv('PASSWORD')

# Connect to the PostgreSQL database
conn = psycopg2.connect(
    host=db_host,
    port=db_port,
    database=db_name,
    user=db_user,
    password=db_password
)

def openAI():
    # Build_002 Anaylze Title and Body only
    try:
        from langchain.prompts.few_shot import FewShotPromptTemplate
        from langchain.prompts.prompt import PromptTemplate
        
        # Create a cursor object to execute SQL queries
        cur = conn.cursor()
        
        # Fetch the first row from the table
        sheet_id = '1hH4TZP1g9ZoYTYUo8TZARlSeXqKqLGvSAh5CNShvxVs'
        table_name = sheet_id.replace('-', '_')  # Generate a valid table name from the sheet ID
        
        cur.execute(f'SELECT title, body, gpt_status, gpt_reason FROM "{table_name}" LIMIT 1')
        row = cur.fetchone()

        if row:
            # Combine the title and body columns with a comma separator
            review = f"{row[0]}, {row[1]}"
            status = row[2]
            reason = row[3]

            # Create a dictionary with the extracted values
            result = {'review': review, 'status': status, 'reason': reason}
            # Convert the dictionary to a list
            examples = [result]

            example_prompt = PromptTemplate(input_variables=["review", "status", "reason"],
                                            template="Review: '''{review}'''\nStatus: {status}\nReason: {reason}")

            # Execute the query to retrieve the guidelines_prompt from the database
            query = "SELECT guidelines FROM guidelines_prompt WHERE id = 1;"
            cur.execute(query)

            # Fetch the result
            result = cur.fetchone()

            # Extract the guidelines_prompt from the result
            guidelines_prompt = result[0]

            few_shot_template = FewShotPromptTemplate(
                examples=examples,
                example_prompt=example_prompt,
                prefix=guidelines_prompt,
                suffix="Review: '''{input}'''\nStatus:",
                input_variables=["input"]
            )

        # if row:
        #     # Combine the title and body columns with a comma separator
        #     review = f"{row[0]}, {row[1]}"

        #     # Create a dictionary with the extracted values
        #     result = {'review': review}
        #     examples = [result]

        #     example_prompt = PromptTemplate(input_variables=["review"],
        #                                     template="Review: '''{review}")

        #     # Execute the query to retrieve the guidelines_prompt from the database
        #     query = "SELECT guidelines FROM guidelines_prompt WHERE id = 4;"
        #     cur.execute(query)

        #     # Fetch the result
        #     result = cur.fetchone()

        #     # Extract the guidelines_prompt from the result
        #     guidelines_prompt = result[0]

        #     few_shot_template = FewShotPromptTemplate(
        #         examples=examples,
        #         example_prompt=example_prompt,
        #         prefix=guidelines_prompt,
        #         suffix="Review: '''{input}",
        #         input_variables=["input"]
        #     )

            chat_llm = ChatOpenAI(temperature=0.8)
            llm_chain = LLMChain(llm=chat_llm, prompt=few_shot_template)

            answer = llm_chain.run(review)

            print(f"Review: {review}\nStatus: {answer.strip()}")
    
        else:
            print("No rows found in the table.")
        
        # Close the cursor
        cur.close()

    except psycopg2.Error as e:
        print("Error connecting to PostgreSQL:", e)
        traceback.print_exc()

    finally:
        # Close the connection
        if conn is not None:
            conn.close()

# review = sheet()
# create()
openAI()
