import torch
from torch.utils.data import Dataset, DataLoader
from transformers import GPT2LMHeadModel, GPT2Tokenizer, AdamW
import json

# Define the dataset class
class ReviewDataset(Dataset):
    def __init__(self, file_path, tokenizer):
        self.data = []
        self.tokenizer = tokenizer

        with open(file_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                entry = json.loads(line.strip())  # Convert the JSON string to a Python dictionary
                review = entry['review']
                self.data.append(review)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        review = self.data[idx]
        tokens = self.tokenizer.encode(review, add_special_tokens=True)
        return torch.tensor(tokens)

# Set the path to the dataset file
dataset_file = 'gpt.txt'

# Load the GPT tokenizer
tokenizer = GPT2Tokenizer.from_pretrained('gpt2')

# Create the dataset
dataset = ReviewDataset(dataset_file, tokenizer)

# Create the data loader
batch_size = 4
data_loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

# Load the pre-trained GPT model
model = GPT2LMHeadModel.from_pretrained('gpt2')

# Fine-tuning settings
learning_rate = 1e-5
num_epochs = 3

# Prepare the model for fine-tuning
model.train()
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)

# Define the optimizer
optimizer = AdamW(model.parameters(), lr=learning_rate)

# Fine-tuning loop
for epoch in range(num_epochs):
    total_loss = 0

    for batch in data_loader:
        inputs = batch[:, :-1].to(device)
        labels = batch[:, 1:].to(device)

        # Forward pass
        outputs = model(inputs, labels=labels)
        loss = outputs.loss

        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    average_loss = total_loss / len(data_loader)
    print(f"Epoch {epoch + 1}/{num_epochs} - Loss: {average_loss}")

# Save the fine-tuned model
model.save_pretrained('fine_tuned_model')
tokenizer.save_pretrained('fine_tuned_model')
