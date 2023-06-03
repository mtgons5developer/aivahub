import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')

# Set up OpenAI API credentials
openai.api_key = openai_api_key

# Customer review
review = "DONT PURCHASE HUGE DISAPPOINTMENT. I’m furious. After days of having it dry, it became all powdery. I am fuming!! This was a gift for my parents and they loved it and now it’s crap!! I want my refund!! This is so disappointing I want to cry."

# Define the prompt for analysis
prompt = """
Given the following customer review:
"{}"

create analysis for this review by a customer.
"""

# Generate analysis using OpenAI's Davinci model
response = openai.Completion.create(
    engine="davinci",
    prompt=prompt.format(review),
    max_tokens=100,
    n=1,
    stop=None,
    temperature=0.7,
    top_p=1.0,
)

# Extract the generated analysis from the OpenAI response
analysis = response.choices[0].text.strip()

# Print the analysis
print(analysis)
