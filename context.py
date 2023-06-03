from transformers import GPT2LMHeadModel, GPT2Tokenizer

# Load the pre-trained GPT-2 model and tokenizer
model_name = "gpt2"
model = GPT2LMHeadModel.from_pretrained(model_name)
tokenizer = GPT2Tokenizer.from_pretrained(model_name)

# Review text
# review = "The product arrived on time, but the customer service was terrible. I had an issue with the product, and when I contacted the support team, they were unresponsive and unwilling to help."
review = "Came out very nice we all loved it. 2 days pass n black spots here n there. Now wat looks like peace fuzz all over. Sad to have to throw away... would not buy again and ill tell ppl i recommended to try, not to spend there money"

# Define the context based on the review and relevant aspects
context = f"Review: {review}\nContext: product, delivery, customer service"

# Tokenize the context
input_ids = tokenizer.encode(context, return_tensors="pt")

# Generate response from the model
output = model.generate(input_ids=input_ids, max_length=100, num_return_sequences=1)

# Decode and print the response
response = tokenizer.decode(output[0], skip_special_tokens=True)
print("Response:")
print(response)
