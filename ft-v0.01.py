import os
import csv
import traceback
import json
import torch
import torch.nn as nn
from langchain import OpenAI, LLMChain
from langchain.chat_models import ChatOpenAI

from transformers import GPT2LMHeadModel, GPT2Tokenizer

from dotenv import load_dotenv

load_dotenv()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load the pre-trained GPT model and tokenizer
model_name = 'gpt2'  # or 'gpt2-medium', 'gpt2-large', 'gpt2-xl' for larger models
model = GPT2LMHeadModel.from_pretrained(model_name).to(device)
tokenizer = GPT2Tokenizer.from_pretrained(model_name)

with open('guidelines.txt', 'r') as file:
    data = file.read()

guidelines_prompt = data

file_path = "gpt.json"  # Replace with the actual file path

# Read the data from the JSON file
with open(file_path, 'r') as file:
    content = file.read()
    data = json.loads(content)

examples = data

chat_llm = ChatOpenAI(temperature=0.8)

def fine_tune_gpt(file_path, epochs=1, learning_rate=1e-5):
    # Read the dataset file
    with open(file_path, 'r') as file:
        data = file.read()

    # Tokenize the dataset
    tokenized_data = tokenizer.encode(data, add_special_tokens=True)

    # Convert the tokenized data to PyTorch tensors
    inputs = torch.tensor(tokenized_data[:-1]).unsqueeze(0).to(device)
    labels = torch.tensor(tokenized_data[1:]).unsqueeze(0).to(device)

    # Create the optimizer and loss function
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    criterion = nn.CrossEntropyLoss()

    # Fine-tuning loop
    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        outputs = model(inputs, labels=labels)
        loss = criterion(outputs.logits.view(-1, outputs.logits.size(-1)), labels.view(-1))
        loss.backward()
        optimizer.step()

        print(f"Epoch {epoch + 1}/{epochs} - Loss: {loss.item()}")

    # Save the fine-tuned model
    save_dir = os.path.dirname(os.path.realpath(__file__))
    save_path = os.path.join(save_dir, 'fine_tuned_model.pt')
    torch.save(model.state_dict(), save_path)
    print(f"Fine-tuned model saved to: {save_path}")

def openAI():
    try:
        # Fine-tune the GPT model
        # fine_tune_gpt('gpt.txt', epochs=3, learning_rate=1e-5)

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
            with open("gpt.txt", "a") as output_file:
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
                        examples = [result]

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

openAI()
