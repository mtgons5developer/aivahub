import os
import sys
import csv
import pandas as pd
import time
import traceback
import json
import torch
import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import torch.nn as nn
from langchain import OpenAI, LLMChain
from langchain.chat_models import ChatOpenAI
from guide import guidelines_prompt

from transformers import GPT2LMHeadModel, GPT2Tokenizer

from dotenv import load_dotenv

load_dotenv()

# Retrieve the PostgreSQL connection details from environment variables
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
connection = connect_to_database()

# Check if the connection was successful
if connection is None:
    print('Unable to connect to the database. Exiting...')
    sys.exit(1)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load the pre-trained GPT   and tokenizer
model_name = 'gpt2'  # or 'gpt2-medium', 'gpt2-large', 'gpt2-xl' for larger models
model = GPT2LMHeadModel.from_pretrained(model_name).to(device)
tokenizer = GPT2Tokenizer.from_pretrained(model_name)


def fine_tune_gpt(json_data, epochs=1, learning_rate=1e-5):
    # Create a list to store the tokenized data
    tokenized_data = []

    # Tokenize the reviews and append them to the tokenized_data list
    for item in data:
        review = item['review']
        tokenized_review = tokenizer.encode(review, add_special_tokens=True)
        tokenized_data.extend(tokenized_review)

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

# Create a cursor to execute SQL queries
# cursor = connection.cursor()

# # Initialize counters
# start_row = 0
# batch_size = 5

# # Create a list to store all the JSON objects
# all_data = []

# # Loop through 22 iterations (220 rows / 10 rows per batch)
# for _ in range(44):
#     # Execute the SQL query to retrieve data from the table with LIMIT and OFFSET
#     query = f"SELECT * FROM tune_data4 LIMIT {batch_size} OFFSET {start_row}"
#     cursor.execute(query)

#     # Fetch the rows from the result set
#     rows = cursor.fetchall()

#     # Create a list to store the JSON objects for the current batch
#     data = []

#     # Format the rows as JSON objects and append them to the data list
#     for row in rows:
#         json_obj = {
#             'review': row[0],
#             'status': row[5],
#             'reason': row[4],
#             'result': row[6]
#         }
#         data.append(json_obj)

#     # Convert the data list to JSON format
#     json_data = json.dumps(data, indent=4, ensure_ascii=False)
#     # print(json_data + "\n")
#     fine_tune_gpt(json_data, epochs=3, learning_rate=1e-5)
#     # Append the current batch of JSON data to the list of all data
#     all_data.extend(data)

#     # Increment the start_row for the next batch
#     start_row += batch_size

# Print all the JSON data after the loop
# for json_obj in all_data:
#     print(json_obj)

# cursor.close()
# connection.close()

chat_llm = ChatOpenAI(temperature=0.8)


def openAI():
    try:
        from langchain.prompts.few_shot import FewShotPromptTemplate
        from langchain.prompts.prompt import PromptTemplate
        
        # Fine-tune the GPT model
        # fine_tune_gpt(json_data, epochs=3, learning_rate=1e-5)
        # quit()

        # Load the fine-tuned model state dictionary
        model_state_dict = torch.load("fine_tuned_model.pt")
        print(model_state_dict)

        # Initialize the GPT-2 model and load the state dictionary
        model = GPT2LMHeadModel.from_pretrained("gpt2")
        model.load_state_dict(model_state_dict)

        # Initialize the tokenizer
        tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        model.config.pad_token_id = model.config.eos_token_id

        # Put the model in evaluation mode
        model.eval()

        # Read the CSV file
        with open("csv/B00UFJNVTS - Heat Resistant Oven Mitts (2 pack)_ High Temperatu 2023-06-07.csv", "r") as file:
            csv_reader = csv.DictReader(file)
            title_column = None
            body_column = None
            ratings_column = None

            # Find the title, body, and ratings columns
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

            # Process each row in the CSV file
            for i, row in enumerate(csv_reader, start=1):

                # Extract the title, body, and rating from the CSV row
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

                    # Encode the review using the tokenizer
                    input_ids = tokenizer.encode(review, return_tensors="pt")
                    attention_mask = torch.ones_like(input_ids)

                    # Generate the output based on the input review
                    output = model.generate(input_ids=input_ids, attention_mask=attention_mask, max_length=100)
                    generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
                    print("Generated text:", generated_text + "\n")
                    quit()

    except IOError as e:
        print("Error reading the CSV file:", e)

    except Exception as e:
        print("An error occurred:", e)
        traceback.print_exc()
        
openAI()




