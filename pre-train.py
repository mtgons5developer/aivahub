import os
import csv
import traceback
import time
import torch
from openai.error import RateLimitError
import openai
from guide import guidelines_prompt

from langchain import OpenAI, LLMChain
from langchain.chat_models import ChatOpenAI

from dotenv import load_dotenv

load_dotenv()

openai.openai_api_key = os.getenv('OPENAI_API_KEY')
os.environ['OPENAI_API_KEY'] = openai.openai_api_key

chat_llm = ChatOpenAI(temperature=0.8)

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

                        # Create a dictionary with the extracted values
                        result = {'review': review}
                        examples = pretrained #dldl
                        print(examples)

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

                        # Load the LLMChain model
                        model_path = "llm_chain_model.pt"
                        if os.path.isfile(model_path):
                            llm_chain = torch.load(model_path)
                            print("loaded")
                        else:
                            llm_chain = LLMChain(llm=chat_llm, prompt=few_shot_template)
                            # Save the LLMChain model for future use
                            torch.save(llm_chain, model_path)
                            print("saved")

                        answer = llm_chain.run(review)
                        # print(str(i) + " " + answer + '\n')

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
