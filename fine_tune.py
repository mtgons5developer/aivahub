import os
import csv
import traceback
import time
from openai.error import RateLimitError
import openai

from langchain import OpenAI, LLMChain
from langchain.chat_models import ChatOpenAI

from create_env import create
from dotenv import load_dotenv

load_dotenv()

openai.openai_api_key = os.getenv('OPENAI_API_KEY')
os.environ['OPENAI_API_KEY'] = openai.openai_api_key

chat_llm = ChatOpenAI(temperature=0.8)

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

with open('guidelines.txt', 'r') as file:
    data = file.read()

guidelines_prompt = data

examples = [
    {'review': "The product arrived in good condition, but I had a bad experience with the seller. They didn't respond to my messages and it took longer than expected to receive the product.", 
     'status': 'Violation', 
     'reason': 'Seller, order, or shipping feedback',
     'result': 'yes'},
    {'review': "The product was fine, but the order was mixed up and I received the wrong color. The seller was helpful in resolving the issue, but it was still a hassle.", 
     'status': 'Violation', 
     'reason': 'Seller, order, or shipping feedback',
     'result': 'yes'},
    {'review': "The product was good, but the shipping cost was too high. It made the overall purchase more expensive than I had anticipated.", 
     'status': 'Violation', 
     'reason': 'Seller, order, or shipping feedback',
     'result': 'yes'},
    {'review': "The product is decent, but I found a similar one for a lower price. It's not worth paying extra for this brand.",
     'status': 'Violation',
     'reason': 'Comments about pricing or availability',
     'result': 'yes'},
    {'review': "The product was out of stock for a while and I had to wait for it to become available again. It was frustrating, but I'm glad I finally got it.",
     'status': 'Violation',
     'reason': 'Comments about pricing or availability',
     'result': 'yes'},
    {'review': "It didn't fit as advertised and seems to be for a much smaller baby than the sizing claims.",
     'status': 'Compliant',
     'reason': 'No violation of Amazon guidelines',
     'result': 'no'},
    {'review': "Bu ürünü bir inceleme karşılığında ücretsiz aldım, bu yüzden görüşümü tuzla buz etmek istemeyebilirsiniz. Ürün iyi, ancak tam fiyatını öder miydim emin değilim.",
     'status': 'Violation',
     'reason': 'Content written in unsupported languages',
     'result': 'yes'},
    {'review': "My order didn’t do what I wanted </3 _(ツ)_/ ",
     'status': 'Violation',
     'reason': 'Repetitive text, spam, or pictures created with symbols',
     'result': 'yes'},
    {'review': "The product was fine, but I want more information. Call me at 123-456-7890..",
     'status': 'Violation',
     'reason': 'Private information',
     'result': 'yes'}
]

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
            with open("gpt.txt", "w") as output_file:
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

                        # Create a dictionary with the extracted values
                        result = {'review': review}
                        # examples = [result]

                        example_prompt = PromptTemplate(
                            input_variables=["review"],
                            template='Review: \'{review}\'\nStatus: \nReason: \nResult:'
                        )

                        few_shot_template = FewShotPromptTemplate(
                            examples=examples,
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
                        result = lines[2].replace("Result:", "").strip().lower()

                        # Format the review and reason into a JSON string
                        formatted_review = f'{{"review": "{review}", "reason": "{reason}", "status": "{status}", "result": "{result}"}}'

                        print(formatted_review)
                        output_file.write(formatted_review)
                        # output_file.write(str(i) + " " + answer)
                        output_file.write("\n")



    except IOError as e:
        print("Error reading the CSV file:", e)

    except Exception as e:
        print("An error occurred:", e)
        traceback.print_exc()



# review = sheet()
# create()
openAI()

