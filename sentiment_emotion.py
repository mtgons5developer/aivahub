import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')

# Set up OpenAI API credentials
openai.api_key = openai_api_key

def analyze_sentiment(review):
    prompt = f"Review: {review}\nSentiment:"
    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=prompt,
        max_tokens=32,
        temperature=0.0,
        n=1,
        stop=None
    )
    sentiment = response.choices[0].text.strip()
    return sentiment

review = "DONT PURCHASE HUGE DISAPPOINTMENT. I’m furious. After days of having it dry, it became all powdery. I am fuming!! This was a gift for my parents and they loved it and now it’s crap!! I want my refund!! This is so disappointing I want to cry."

sentiment = analyze_sentiment(review)
print("Sentiment:", sentiment)

def analyze_sentiment_with_emotion(review):
    prompt = f"Review: {review}\nEmotion:"

    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=prompt,
        max_tokens=32,
        temperature=0.8,
        n=1,
        stop=None
    )

    emotion = response.choices[0].text.strip()
    return emotion


emotion = analyze_sentiment_with_emotion(review)
print("Emotion:", emotion)
