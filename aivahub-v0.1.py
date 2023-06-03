import os
from langchain import OpenAI, LLMChain
from langchain.chat_models import ChatOpenAI
from g_sheet import sheet

from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')
os.environ['OPENAI_API_KEY'] = openai_api_key

from langchain.prompts.few_shot import FewShotPromptTemplate
from langchain.prompts.prompt import PromptTemplate
    
def openAI():
    # question = ""
    # message = ""
    # # summarize = openai.Completion.create(
    # # model="text-davinci-003",
    # # prompt=message,
    # # max_tokens=7,
    # # temperature=0
    # # )
    # # print(summarize)

    # sentiment = openai.Completion.create(
    # model="text-davinci-003", #ChatGPT options
    # prompt=question + message,
    # temperature=0,
    # max_tokens=60,
    # top_p=1,
    # frequency_penalty=0.5,
    # presence_penalty=0
    # )
    # print(sentiment)
    # print(question + message)

    examples = [
        {'review': "The product arrived in good condition, but I had a bad experience with the seller. They didn't respond to my messages and it took longer than expected to receive the product.", 
        'status': 'Violation', 
        'reason': 'Seller, order, or shipping feedback'},

        # {'review': "The product was fine, but the order was mixed up and I received the wrong color. The seller was helpful in resolving the issue, but it was still a hassle.", 
        #  'status': 'violation', 
        #  'reason': 'Seller, order, or shipping feedback'},
        # {'review': "The product was good, but the shipping cost was too high. It made the overall purchase more expensive than I had anticipated.", 
        #  'status': 'violation', 
        #  'reason': 'Seller, order, or shipping feedback'},

        {'review': "The product is decent, but I found a similar one for a lower price. It's not worth paying extra for this brand.",
        'status': 'Violation',
        'reason': 'Comments about pricing or availability'},
        
        {'review': "The product was out of stock for a while and I had to wait for it to become available again. It was frustrating, but I'm glad I finally got it.",
        'status': 'Violation',
        'reason': 'Comments about pricing or availability'},

        {'review': "It didn't fit as advertised and seems to be for a much smaller baby than the sizing claims.",
        'status': 'Not in violation',
        'reason': 'No violation of Amazon guidelines'},

        {'review': "Bu ürünü bir inceleme karşılığında ücretsiz aldım, bu yüzden görüşümü tuzla buz etmek istemeyebilirsiniz. Ürün iyi, ancak tam fiyatını öder miydim emin değilim.",
        'status': 'Violation',
        'reason': 'Content written in unsupported languages'},

        {'review': "My order didn’t do what I wanted </3 _(ツ)_/ ",
        'status': 'Violation',
        'reason': 'Repetitive text, spam, or pictures created with symbols'},

        {'review': "The product was fine, but I want more information. Call me at 123-456-7890..",
        'status': 'Violation',
        'reason': 'Private information'}
    ]

    example_prompt = PromptTemplate(input_variables=["review", "status", "reason"],
                                    template="Review: '''{review}'''\nStatus: {status}\nReason: {reason}")

    # print(example_prompt.format(**examples[0]))
    # print()
    # print(example_prompt.format(**examples[-1]))
    # print()
    # print(example_prompt.format(**examples[-4]))

    guidelines_prompt = '''Having the following Amazon guidelines about what's not allowed:

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
    Does the following review violate any of the 14 Amazon's rules guidelines above? if you are not sure, just say I don't know, don't try to make up an answer.'''

    few_shot_template = FewShotPromptTemplate(
        examples=examples,
        example_prompt=example_prompt,
        prefix=guidelines_prompt,
        suffix="Review: '''{input}'''\nStatus:",
        input_variables=["input"]
    )

    completion_llm = OpenAI(temperature=0.0)
    chat_llm = ChatOpenAI(temperature=0.1)
    llm_chain = LLMChain(llm=chat_llm, prompt=few_shot_template)

    # review = "It didn't fit as advertised and seems to be for a much smaller baby than the sizing claims."
    # review = "The product arrived in good condition, but I had a bad experience with the seller. They didn't respond to my messages and it took longer than expected to receive the product."
    # answer = llm_chain.run(review)

    # print(f"Review: {review}\nStatus: {answer.strip()}")

    # review = "نمت حفاضات العفن ، شعرت بخيبة أمل كبيرة"
    # review = "I’m furious. After days of having it dry, it became all powdery. I am fuming!! This was a gift for my parents and they loved it and now it’s crap!! I want my refund!! This is so disappointing I want to cry."
    # review = "Came out very nice we all loved it. 2 days pass n black spots here n there. Now wat looks like peace fuzz all over. Sad to have to throw away... would not buy again and ill tell ppl i recommended to try, not to spend there money."
    answer = llm_chain.run(review)

    print(f"Review: {review}\nStatus: {answer.strip()}")


review = sheet()
openAI()

# openai api fine_tunes.create -t test.jsonl -m ada --suffix "custom model name"
# {"prompt":"Portugal will be removed from the UK's green travel list from Tuesday, amid rising coronavirus cases and concern over a \"Nepal mutation of the so-called Indian variant\". It will join the amber list, meaning holidaymakers should not visit and returnees must isolate for 10 days...\n\n###\n\n", 
# "completion":" Portugal\nUK\nNepal mutation\nIndian variant END"}

# Case study: Product description based on a technical list of properties
# {"prompt":"Item=handbag, Color=army_green, price=$99, size=S->", 
# "completion":" This stylish small green handbag will add a unique touch to your look, without costing you a fortune."}