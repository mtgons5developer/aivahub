from textblob import TextBlob

review = "DONT PURCHASE HUGE DISAPPOINTMENT. I’m furious. After days of having it dry, it became all powdery. I am fuming!! This was a gift for my parents and they loved it and now it’s crap!! I want my refund!! This is so disappointing I want to cry."

# Perform sentiment analysis
sentiment = TextBlob(review).sentiment.polarity
sentiment_label = "Positive" if sentiment > 0 else "Negative" if sentiment < 0 else "Neutral"

# Define the list of disappointment phrases
disappointment_phrases = ["huge disappointment", "furious", "powdery", "crap", "disappointing", "so disappointing"]

# Find the specific disappointment phrases in the review
found_phrases = [phrase for phrase in disappointment_phrases if phrase in review.lower()]

# Save the key information to a text file
output_file = "review_analysis.txt"
with open(output_file, "w") as file:
    file.write("Review Analysis\n")
    file.write("================\n\n")
    file.write("Review:\n{}\n\n".format(review))
    file.write("Sentiment: {}\n\n".format(sentiment_label))
    
    if found_phrases:
        file.write("Disappointment Phrases:\n")
        for phrase in found_phrases:
            file.write("- {}\n".format(phrase))
    else:
        file.write("No disappointment phrases found.\n")

print("Key information extracted from the review and saved to", output_file)
