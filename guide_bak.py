guidelines_prompt = '''
''Does the following review comply with all 14 of Amazon's guidelines? If not, which guideline(s) does it potentially violate?

    1- Seller, Order, or Shipping Feedback:
    -Focus on the product, not individual experiences related to sellers, ordering, or shipping. Avoid discussing seller performance, customer service, ordering issues, returns, refunds, shipping packaging, product condition, and shipping cost/delivery speed.
    Why? The purpose of community content is to provide information about the product. While we value feedback on sellers and packaging, we encourage you to share such feedback through appropriate channels other than reviews or questions and answers.\n

    2- Comments about Pricing or Availability:
    -Comment on pricing only if it directly relates to the product's value. Comments based on individual experiences or specific store availability are not allowed.
    Why? The community's purpose is to share product-specific feedback that will be relevant to all customers.\n

    3- Content written in unsupported languages:
    -Write content in English or Spanish, as Amazon only supports these languages.
    Why? The requirement to write content in English or Spanish is aimed at aligning with Amazon's language support. By emphasizing the use of supported languages, the community ensures that the content is useful and compatible with the specific Amazon site. Writing in the appropriate language maintains consistency and enables effective communication with a broader audience. This approach helps create a consistent and accessible experience for users across different Amazon sites.\n
    
    4- Repetitive Text, Spam, or Pictures Created with Symbols:
    Avoid repetitive text, nonsense/gibberish, content consisting of punctuation marks or symbols, and ASCII art.
    Why? The purpose of contributions is to provide helpful and relevant information to the community. Repetitive text, spam, and content that lacks substance or meaningful value detract from the overall usefulness and readability of the platform.\n

    5- Private Information:
    -Do not share personal information or invade others' privacy, including phone numbers, email addresses, mailing addresses, license plate numbers, data source names, and order numbers.
    Why? Respecting privacy is crucial to maintain a safe and secure environment. Sharing personal information can lead to unintended consequences or potential misuse. Please refrain from posting any content that compromises privacy, both yours and others'.\n

    6- Profanity or Harassment:
    -Maintain a respectful tone, avoid profanity, obscenities, name-calling, harassment, personal attacks, and inflammatory content.
    Why? Promoting a respectful and inclusive environment fosters constructive discussions. Avoiding profanity, harassment, and personal attacks ensures that conversations remain civil and beneficial for everyone involved.\n

    7- Hate Speech:
    -Expressing hatred based on characteristics such as race, ethnicity, nationality, gender, gender identity, sexual orientation, religion, age, and disability is strictly prohibited.
    Why? Creating a safe and inclusive environment is paramount. By disallowing hate speech and the promotion of such organizations, we ensure that our platform remains respectful, tolerant, and free from discrimination.\n

    8- Sexual Content:
    -Discussions about sex-related products are allowed, but profanity, explicit language, nudity, and sexually explicit images or descriptions are not allowed.
    Why? Allowing discussions about sex-related products while maintaining a respectful atmosphere is essential. By prohibiting profanity, explicit images, and descriptions, we ensure that the community remains appropriate and comfortable for all users.\n

    9- External Links:
    -Links to other Amazon products are permitted, but external site links, phishing/malware-infected websites, and URLs with referrer tags or affiliate codes are not allowed.
    Why? Allowing links to other products on Amazon enables users to access additional information. However, prohibiting external links ensures the safety and security of our community by preventing potential malicious content or unauthorized tracking through referrer tags and affiliate codes.\n

    10- Ads or Promotional Content:
    -Avoid content primarily serving the purpose of promoting a company, website, author, or special offer. Focus on providing genuine and helpful information.
    Why? The primary objective of the community is to facilitate informative discussions and share knowledge. By discouraging ads or promotional content, we ensure that the platform remains focused on valuable contributions rather than overt advertising.\n

    11- Conflicts of Interest:
    -Prohibited from creating, editing, or posting content about your own products/services or those offered by friends, relatives, employers, business associates, or competitors.
    Why? Upholding a fair and unbiased environment is crucial. By avoiding conflicts of interest, we maintain the integrity and authenticity of the community's content, ensuring that discussions are driven by genuine experiences and unbiased perspectives.\n

    12- Solicitations:
    -Ensure neutral requests for others to post content, avoid influencing positive ratings/reviews, and prohibit compensation for content creation. Clear disclosure is required for financial or close personal connections.
    Why? Maintaining transparency, fairness, and unbiased opinions is fundamental to the integrity of the community. By discouraging solicitations and ensuring clear disclosure of connections, we foster an environment that promotes authentic engagement and trust among users.\n

    13- Plagiarism, Infringement, or Impersonation:
    -Only post content you own or have permission to use, avoid infringing on others' intellectual property rights, and prevent impersonation.
    Why? Respecting intellectual property rights and preventing impersonation is crucial to maintain a fair and trustworthy community. By discouraging plagiarism, infringement, and impersonation, we ensure that original content is shared, intellectual property is respected, and individuals are not misrepresented.\n

    14- Illegal Activities:
    -Prohibited from posting content promoting violence, illegal drug use, underage drinking, child/animal abuse, fraudulent activities, and content advocating harm or participating in dangerous schemes.
    Why? Upholding legal and ethical standards is of utmost importance. By prohibiting content that promotes illegal activities, harm, or fraud, we maintain a safe and trustworthy community where users can engage responsibly and contribute to meaningful discussions.\n

    Always provide status: Only state Compliant or Violation for Status.
    Always provide reason: State why it was in Violation or why it is Compliant as Reason:
    Always provide result: If Compliant set Result: 'NO', don't add anything. If in Violation set Result: 'YES', don't add anything. The "Result" is assigned as "Maybe" to convey uncertainty or ambiguity. END'''

'''
'''''''''