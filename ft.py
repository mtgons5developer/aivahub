import torch
import pandas as pd
from torch.utils.data import Dataset, DataLoader
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from guide import guidelines_prompt

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Function to check if a review complies with the guidelines
def check_compliance(review, guidelines):
    # Access the guidelines_prompt within the function
    guidelines = guidelines_prompt

    # Check compliance for each guideline in the guidelines prompt
    for guideline in guidelines.split("\n\n"):
        guideline_lines = guideline.strip().split("\n")
        guideline_title = guideline_lines[0]
        guideline_keywords = guideline_lines[2:]

        # Check if any of the guideline keywords are present in the review
        if any(keyword in review.lower() for keyword in guideline_keywords):
            compliance_status = False
            violation_details.append(f"Violation: {guideline_title}")
            
    # Implement the logic to check compliance based on the guidelines
    compliance_status = True  # Assume initial compliance status as True
    violation_details = []

    # Check compliance for guideline 1: Seller, Order, or Shipping Feedback
    if any(keyword in review for keyword in ["seller", "order", "shipping"]):
        compliance_status = False
        violation_details.append("Violation: Seller, Order, or Shipping Feedback")

    # Check compliance for guideline 2: Comments about Pricing or Availability
    if any(keyword in review for keyword in ["pricing", "availability"]):
        compliance_status = False
        violation_details.append("Violation: Comments about Pricing or Availability")

    # Check compliance for guideline 3: Content written in unsupported languages
    if any(keyword in review for keyword in ["French", "German", "Italian", "Portuguese"]):
        compliance_status = False
        violation_details.append("Violation: Content written in unsupported languages")

    # Check compliance for guideline 4: Repetitive Text, Spam, or Pictures Created with Symbols
    if any(keyword in review for keyword in ["repetitive", "spam", "symbols"]):
        compliance_status = False
        violation_details.append("Violation: Repetitive Text, Spam, or Pictures Created with Symbols")

    # Check compliance for guideline 5: Private Information
    if any(keyword in review for keyword in ["phone number", "email address", "mailing address"]):
        compliance_status = False
        violation_details.append("Violation: Private Information")

    # Check compliance for guideline 6: Profanity or Harassment
    if any(keyword in review for keyword in ["profanity", "harassment"]):
        compliance_status = False
        violation_details.append("Violation: Profanity or Harassment")

    # Check compliance for guideline 7: Hate Speech
    if any(keyword in review for keyword in ["hate speech", "discrimination"]):
        compliance_status = False
        violation_details.append("Violation: Hate Speech")

    # Check compliance for guideline 8: Sexual Content
    if any(keyword in review for keyword in ["sexual content", "nudity"]):
        compliance_status = False
        violation_details.append("Violation: Sexual Content")

    # Check compliance for guideline 9: External Links
    if "http://" in review or "https://" in review:
        compliance_status = False
        violation_details.append("Violation: External Links")

    # Check compliance for guideline 10: Ads or Promotional Content
    if "promotion" in review or "advertising" in review:
        compliance_status = False
        violation_details.append("Violation: Ads or Promotional Content")

    # Check compliance for guideline 11: Conflicts of Interest
    if any(keyword in review for keyword in ["conflict of interest", "self-promotion"]):
        compliance_status = False
        violation_details.append("Violation: Conflicts of Interest")

    # Check compliance for guideline 12: Solicitations
    if any(keyword in review for keyword in ["solicitation", "compensation"]):
        compliance_status = False
        violation_details.append("Violation: Solicitations")

    # Check compliance for guideline 13: Plagiarism, Infringement, or Impersonation
    if any(keyword in review for keyword in ["plagiarism", "infringement", "impersonation"]):
        compliance_status= False
        violation_details.append("Violation: Plagiarism, Infringement, or Impersonation")

    # Check compliance for guideline 14: Illegal Activities
    if any(keyword in review for keyword in ["illegal activities", "violence", "fraud"]):
        compliance_status = False
        violation_details.append("Violation: Illegal Activities")

    # Return the compliance status and violation details as a dictionary
    return {
        'compliance_status': compliance_status,
        'violation_details': violation_details
    }


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

        combined_text = f"{title} {body}"  # Combine title and body

        # Check compliance for the combined text
        compliance = check_compliance(combined_text, guidelines_prompt)

        encoded_input = self.tokenizer.encode_plus(
            combined_text,
            truncation=True,
            return_tensors='pt'
        )

        input_ids = encoded_input['input_ids'].squeeze()
        attention_mask = encoded_input['attention_mask'].squeeze()
        labels = input_ids.clone()

        # Adjust the max_length based on the input sequence length
        max_length = min(self.max_length, input_ids.size(0))

        # Pad or truncate the input sequences to the adjusted max_length
        input_ids = input_ids[:max_length]
        attention_mask = attention_mask[:max_length]
        labels = labels[:max_length]

        # Pad the sequences if necessary
        padding_length = self.max_length - input_ids.size(0)
        input_ids = torch.nn.functional.pad(input_ids, (0, padding_length), value=self.tokenizer.pad_token_id)
        attention_mask = torch.nn.functional.pad(attention_mask, (0, padding_length), value=0)
        labels = torch.nn.functional.pad(labels, (0, padding_length), value=-100)

        return {
            'input_ids': input_ids,
            'attention_mask': attention_mask,
            'labels': labels,
            'compliance': compliance
        }



def train_model(model, dataloader, optimizer, device):
    model.train()
    total_loss = 0
    for batch in dataloader:
        input_ids = batch['input_ids'][:, :-1].to(device)
        labels = batch['input_ids'][:, 1:].to(device)
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
max_length = max(len(data['input_ids']) for data in dataset)
print(f"Maximum sequence length: {max_length}")

dataloader = DataLoader(dataset, batch_size=4, shuffle=True)

# Training loop
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-5)
num_epochs = 5

for epoch in range(num_epochs):
    loss = train_model(model, dataloader, optimizer, device)
    print(f"Epoch: {epoch+1} - Loss: {loss}")


