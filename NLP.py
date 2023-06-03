import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')

# Set up OpenAI API credentials
openai.api_key = openai_api_key

def apply_nlp_techniques(review):
    prompt = f"Apply natural language processing techniques: {review}\nProcessed text:"

    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=prompt,
        max_tokens=64,
        temperature=0.8,
        n=1,
        stop=None
    )

    processed_text = response.choices[0].text.strip()
    return processed_text

# review = "DONT PURCHASE HUGE DISAPPOINTMENT. I’m furious. After days of having it dry, it became all powdery. I am fuming!! This was a gift for my parents and they loved it and now it’s crap!! I want my refund!! This is so disappointing I want to cry."
# review = "Came out very nice we all loved it. 2 days pass n black spots here n there. Now wat looks like peace fuzz all over. Sad to have to throw away... would not buy again and ill tell ppl i recommended to try, not to spend there money"
review = "Product was used for my best friends dying mother.. we followed the directions and both times (because we bought two) we added water and stirred and one minute into stirring mixture from powder it turned into a solid both batches.. I’m very disappointed as we were unable to cast their hands.. I’d like amazon to send me two new ones please before her mom passes."

processed_text = apply_nlp_techniques(review)
print("Processed Text:", processed_text)
