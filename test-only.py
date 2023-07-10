import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

# Load the fine-tuned model and tokenizer
model_state_dict = torch.load("fine_tuned_model.pt")
model = GPT2LMHeadModel.from_pretrained("GPT3", state_dict=model_state_dict)
tokenizer = GPT2Tokenizer.from_pretrained("GPT3")
model.config.pad_token_id = model.config.eos_token_id

# Load the generation configuration file
generation_config = "generation_config.json"  # Replace with the path to your generation configuration file

# Generate output text using the generation configuration
input_text = "Hello, how are you?"
input_ids = tokenizer.encode(input_text, return_tensors="pt")

# Experiment with different temperature values
decoding_methods = ["greedy", "nucleus", "beam"]
temperature_values = [0.2, 0.5, 1.0]
for decoding_method in decoding_methods:
    for temperature in temperature_values:
        # Generate output text with different decoding techniques
        if decoding_method == "greedy":
            output = model.generate(input_ids, max_length=100, num_return_sequences=1, temperature=temperature)
        elif decoding_method == "nucleus":
            output = model.generate(input_ids, max_length=100, num_return_sequences=1, temperature=temperature, top_p=0.9)
        elif decoding_method == "beam":
            output = model.generate(input_ids, max_length=100, num_return_sequences=1, temperature=temperature, num_beams=5)

        # Decode and print the generated text
        for i, generated_sequence in enumerate(output):
            generated_text = tokenizer.decode(generated_sequence, skip_special_tokens=True)
            print(f"Generated Text {i+1} ({decoding_method.capitalize()}, Temperature={temperature}):", generated_text)