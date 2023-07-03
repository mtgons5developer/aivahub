import torch
import pandas as pd
from torch.utils.data import Dataset, DataLoader
from transformers import GPT2LMHeadModel, GPT2Tokenizer

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

from transformers import BartTokenizer, BartForConditionalGeneration

# Function to generate summaries
def generate_summary(text):
# Load the BART model and tokenizer
    model_name = 'facebook/bart-large-cnn'
    tokenizer = BartTokenizer.from_pretrained(model_name)
    model = BartForConditionalGeneration.from_pretrained(model_name)    
    inputs = tokenizer([text], max_length=1024, truncation=True, return_tensors='pt')
    summary_ids = model.generate(inputs['input_ids'], num_beams=4, max_length=150, early_stopping=True)
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

# # Example usage
# text = """Reviewed in the United States on May 21, 2015. Angela says, "High temperature gloves that work! I do some high temperature cooking. After seeing the slow melt of my previous set of oven mitts, I purchased the Ove Glove. It did not work. At temperatures of about 500 degrees or higher, the heat passed through the glove to my hand as if it was not there at all. So I bought these gloves and tried them at 550 degrees. They work at least to that temperature. My only complaint is about the gloves' size. They seem made for a large man's hands. But that won't stop me from using them."""

# summary = generate_summary(text)
# print("Original text:\n", text)
# print("\nSummary:\n", summary)

# Define a custom dataset class to load the data from the CSV file
class CustomDataset(Dataset):
    def __init__(self, csv_file, tokenizer, max_length):
        self.data = pd.read_csv(csv_file)
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        title = str(self.data.iloc[index]['Title'])
        body = str(self.data.iloc[index]['Body'])

        text = title + " " + body
        text = generate_summary(text)
        # print(summary)
        # quit()
        if len(text) > self.max_length:
            text = text[:self.max_length]  # Truncate long sequences
        
        encoded_input = self.tokenizer.encode_plus(
            text,
            padding='max_length',
            truncation=True,
            max_length=self.max_length,
            return_tensors='pt'
        )
        return encoded_input['input_ids'].squeeze()


def train_model(model, dataloader, optimizer, device):
    model.train()
    total_loss = 0
    for batch in dataloader:
        batch = batch.to(device)
        # Ensure the batch tensor has the correct shape
        input_ids = batch[:, :-1]
        labels = batch[:, 1:]
        outputs = model.forward(input_ids=input_ids, labels=labels)
        loss = outputs.loss
        total_loss += loss.item()
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    return total_loss / len(dataloader)

# Load the model and tokenizer
model_name = 'gpt2-large'
model = GPT2LMHeadModel.from_pretrained(model_name).to(device)
tokenizer = GPT2Tokenizer.from_pretrained(model_name)

# Set the padding token
tokenizer.add_special_tokens({'pad_token': '[PAD]'})

# Create the dataset and dataloader
csv_file = 'csv/B00UFJNVTS - Heat Resistant Oven Mitts (2 pack)_ High Temperatu 2023-06-07.csv'
max_length = 2048  # Set the maximum sequence length
dataset = CustomDataset(csv_file, tokenizer, max_length)
dataset = [data for data in dataset if data is not None]

# Calculate and print the maximum sequence length
max_length = max(len(sequence) for sequence in dataset)
print(f"Maximum sequence length: {max_length}")

dataloader = DataLoader(dataset, batch_size=4, shuffle=True)

# Training loop
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-5)
num_epochs = 5

for epoch in range(num_epochs):
    loss = train_model(model, dataloader, optimizer, device)
    print(f"Epoch: {epoch+1} - Loss: {loss}")
