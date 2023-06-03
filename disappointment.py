import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')

# Set up OpenAI API credentials
openai.api_key = openai_api_key

def generate_disappointment_phrases(review):
    prompt = f"Expand the list of disappointment phrases: {review}\nDisappointment phrases:"

    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=prompt,
        max_tokens=64,
        temperature=0,
        n=1,
        stop=None
    )

    disappointment_phrases = [choice.text.strip() for choice in response.choices]
    return disappointment_phrases

review = "DONT PURCHASE HUGE DISAPPOINTMENT. I’m furious. After days of having it dry, it became all powdery. I am fuming!! This was a gift for my parents and they loved it and now it’s crap!! I want my refund!! This is so disappointing I want to cry."

phrases = generate_disappointment_phrases(review)
print("Disappointment Phrases:")
for phrase in phrases:
    print(phrase)
