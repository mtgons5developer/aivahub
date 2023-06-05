import re

def find_violated_guidelines(review):
    violated_guidelines = []

    guideline_patterns = {
        1: r"\b(sellers?|customer service|ordering issues|returns|shipping packaging|product condition|damage|shipping cost|shipping speed)\b",
        2: r"\b(price|pricing|availability|local store)\b",
        3: r"\b(unsupported languages|French)\b",
        4: r"\b(repetitive text|spam|punctuation|symbols|ASCII art)\b",
        5: r"\b(phone number|email address|mailing address|license plate|DSN|order number)\b",
        6: r"\b(profanity|obscenities|name-calling|harassment|threats|attacks|libel|defamation|inflammatory|multiple accounts)\b",
        7: r"\b(race|ethnicity|nationality|gender|gender identity|sexual orientation|religion|age|disability)\b",
        8: r"\b(sexual content|profanity|obscene language|nudity|sexually explicit)\b",
        9: r"\b(external links|phishing|malware sites|URLs|referrer tags|affiliate codes)\b",
        10: r"\b(ads|promotional content|company|website|author|special offer)\b",
        11: r"\b(conflicts of interest|friends|relatives|employers|business associates|competitors)\b",
        12: r"\b(solicitations|influence|compensation|manipulate|Verified Purchase badge|financial connection)\b",
        13: r"\b(plagiarism|infringement|impersonation|intellectual property|copyrights|trademarks)\b",
        14: r"\b(illegal activities|violence|illegal drug use|underage drinking|child abuse|animal abuse|fraud|terrorism|dangerous misuse)\b"
    }

    for guideline_num, pattern in guideline_patterns.items():
        if re.search(pattern, review, re.IGNORECASE):
            violated_guidelines.append(guideline_num)

    return violated_guidelines


# Example usage
review = """Developed mold, I thought i did everything right. The model came out right but it started to develop mold. 
I’m not sure why this happened, but yes it did. Ok, so i did my second model two weeks later, and yes AGAIN, the mold started to appear... DO NOT BUY THIS PRODUCT!!!"""

violated_guidelines = find_violated_guidelines(review)

if violated_guidelines:
    print("The review violates the following guidelines:")
    for guideline_num in violated_guidelines:
        print(f"- Guideline {guideline_num}")
else:
    print("The review does not violate any guidelines.")
