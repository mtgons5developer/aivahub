import os
import csv
import psycopg2
import traceback
import time
from openai.error import RateLimitError


from langchain import OpenAI, LLMChain
from langchain.chat_models import ChatOpenAI

from create_env import create
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')
os.environ['OPENAI_API_KEY'] = openai_api_key

# Retrieve the PostgreSQL connection details from environment variables
db_host = 'localhost'
db_port = 5432
db_name = 'postgres'
db_user = 'datax'
db_password = 'root1234'

chat_llm = ChatOpenAI(temperature=0.8)

def completion_with_retry(prompt):
    retry_delay = 1.0
    max_retries = 3
    retries = 0

    while True:
        try:
            return chat_llm.completion(prompt)
        except RateLimitError as e:
            if retries >= max_retries:
                raise e
            else:
                retries += 1
                print(f"Rate limit exceeded. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)


guidelines_prompt = '''
''Run each guideline and analyze why it was violated. Always provide a reason:

    1- Seller, order, or shipping feedback:
    We don't allow reviews or questions and answers that focus on:
    - Sellers and the customer service they provide
    - Ordering issues and returns
    - Shipping packaging
    - Product condition and damage
    - Shipping cost and speed
    Why not? Community content is meant to help customers learn about the product itself, not someone's individual experience ordering it. That said, we definitely want to hear your feedback about sellers and packaging, just not in reviews or questions and answers.

    2- Comments about pricing or availability:
    It's OK to comment on price if it's related to the product's value. For example, "For only $29, this blender is really great."
    Pricing comments related to someone's individual experience aren't allowed. For example, "Found this here for $5 less than at my local store."
    These comments aren't allowed because they aren't relevant for all customers.
    Some comments about availability are OK. For example, "I wish this book was also available in paperback."
    However, we don't allow comments about availability at a specific store. Again, the purpose of the community is to share product-specific feedback that will be relevant to all other customers.

    3- Content written in unsupported languages:
    Supported languages are English and Spanish.
    To ensure that content is useful, we only allow it to be written in the supported language(s) of the Amazon site where it will appear. For example, we don't allow reviews written in French on Amazon.com. It only supports English and Spanish. Some Amazon sites support multiple languages, but content written in a mix of languages isn't allowed.

    4- Repetitive text, spam, or pictures created with symbols:
    We don't allow contributions with distracting content and spam. This includes:
    - Repetitive text
    - Nonsense and gibberish
    - Content that's just punctuation and symbols
    - ASCII art (pictures created using symbols and letters)

    5- Private information:
    Don't post content that invades others' privacy or shares your own personal information, including:
    - Phone number
    - Email address
    - Mailing address
    - License plate
    - Data source name (DSN)
    - Order number

    6- Profanity or harassment:
    It's OK to question others' beliefs and expertise, but be respectful. We don't allow:
    - Profanity, obscenities, or name-calling
    - Harassment or threats
    - Attacks on people you disagree with
    - Libel, defamation, or inflammatory content
    - Drowning out others' opinions. Don't post from multiple accounts or coordinate with others.

    7- Hate speech:
    It's not allowed to express hatred for people based on characteristics like:
    - Race
    - Ethnicity
    - Nationality
    - Gender
    - Gender identity
    - Sexual orientation
    - Religion
    - Age
    - Disability
    It's also not allowed to promote organizations that use such hate speech.

    8- Sexual content:
    It's OK to discuss sex and sensuality products sold on Amazon. The same goes for products with sexual content (books, movies). That said, we still don't allow profanity or obscene language. We also don't allow content with nudity or sexually explicit images or descriptions.

    9- External links
    We allow links to other products on Amazon, but not to external sites. Don't post links to phishing or other malware sites. We don't allow URLs with referrer tags or affiliate codes.

    10- Ads or promotional content:
    Don't post content if its main purpose is to promote a company, website, author, or special offer.

    11- Conflicts of interest:
    It's not allowed to create, edit, or post content about your own products or services. The same goes for services offered by:
    - Friends
    - Relatives
    - Employers
    - Business associates
    - Competitors

    12- Solicitations:
    If you ask others to post content about your products, keep it neutral. For example, don't try to influence them into leaving a positive rating or review.
    Don't offer, request, or accept compensation for creating, editing, or posting content. Compensations include free and discounted products, refunds, and reimbursements. Don't try to manipulate the Amazon Verified Purchase badge by offering reviewers special pricing or reimbursements.
    Have a financial or close personal connection to a brand, seller, author, or artist?:
    - It’s OK to post content other than reviews and questions and answers, but you need to clearly disclose your connection. However, brands or businesses can’t participate in the community in ways that divert Amazon customers to non-Amazon websites, applications, services, or channels. This includes ads, special offers, and “calls to action” used to conduct marketing or sales transactions. If you post content about your own products or services through a brand, seller, author, or artist account, additional labeling isn’t necessary.
    - Authors and publishers can continue to give readers free or discounted copies of their books if they don't require a review in exchange or try to influence the review.

    13- Plagiarism, infringement, or impersonation:
    Only post your own content or content you have permission to use on Amazon. This includes text, images, and videos. You're not allowed to:
    - Post content that infringes on others' intellectual property (including copyrights, trademarks, patents, trade secrets) or other proprietary rights
    - Interact with community members in ways that infringe on others' intellectual property or proprietary rights
    - Impersonate someone or an organization

    14- Illegal activities:
    Don't post content that encourages illegal activity like:
    - Violence
    - Illegal drug use
    - Underage drinking
    - Child or animal abuse
    - Fraud
    We don't allow content that advocates or threatens physical or financial harm to yourself or others. This includes terrorism. Jokes or sarcastic comments about causing harm aren't allowed.
    It's also not allowed to offer fraudulent goods, services, promotions, or schemes (make money fast, pyramid).
    It's not allowed to encourage the dangerous misuse of a product.

    ```
    Does the following review violate any of the 14 Amazon's rules guidelines above? If you are not sure, just say I don't know, don't try to make up an answer.'''
'''
'''''''''

# Connect to the PostgreSQL database
conn = psycopg2.connect(
    host=db_host,
    port=db_port,
    database=db_name,
    user=db_user,
    password=db_password
)

def openAI():
    try:
        from langchain.prompts.few_shot import FewShotPromptTemplate
        from langchain.prompts.prompt import PromptTemplate

        # Read the CSV file
        with open("csv-gpt.csv", "r") as file:
            csv_reader = csv.DictReader(file)
            title_column = None
            body_column = None

            # Find the title and body columns
            for column in csv_reader.fieldnames:
                if column.lower() == "title":
                    title_column = column
                elif column.lower() == "body":
                    body_column = column

            # Check if the title and body columns are found
            if title_column is None or body_column is None:
                print("Title and/or body columns not found in the CSV file.")
                return

            # Process each row in the CSV file
            for row in csv_reader:
                # Extract the title and body from the CSV row
                title = row[title_column]
                body = row[body_column]

                # Combine the title and body columns with a comma separator
                review = f"{title}, {body}"

                # Create a dictionary with the extracted values
                result = {'review': review}
                examples = [result]

                example_prompt = PromptTemplate(input_variables=["review"],
                                        template="Review: '''{review}'''\nStatus: \nReason: ")

                few_shot_template = FewShotPromptTemplate(
                    examples=examples,
                    example_prompt=example_prompt,
                    prefix=guidelines_prompt,
                    suffix="Review: '''{input}",
                    input_variables=["input"]
                )

                # chat_llm = ChatOpenAI(temperature=0.8)
                llm_chain = LLMChain(llm=chat_llm, prompt=few_shot_template)

                answer = llm_chain.run(review)
            
                print(f"Review: {review}\nStatus: {answer.strip()}")

    except IOError as e:
        print("Error reading the CSV file:", e)

    except Exception as e:
        print("An error occurred:", e)
        traceback.print_exc()



# review = sheet()
# create()
openAI()

