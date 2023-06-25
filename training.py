import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

model = GPT2LMHeadModel.from_pretrained('gpt2')
tokenizer = GPT2Tokenizer.from_pretrained('gpt2')

tokenizer.pad_token = tokenizer.eos_token  # Select an existing token as the padding token
# or
tokenizer.add_special_tokens({'pad_token': '[PAD]'})  # Add a new token '[PAD]' as the padding token


dataset_text = [
    "Great product but not great fit It seems a lot of the reviewers don’t understand that swim diapers are not meant to hold pee. It’s super cute and nicely built but my son is skinny and only weighs 25 lbs. even on the biggest snap settings it kept falling down his waist and left very deep imprints on his skin. Besides the fit everything else was great. Will probably have to return as it doesn’t seem to comfortable on him.",
    "Used only once, and it did its job of keeping poo in the diaper and out of the pool -- which is why I gave it 2 stars. But I washed it immediately after, according to the care instructions, and it kept a permanent poop smell. I washed it 2 more times by machine and 2 more times by hand -- no luck. It still stinks so bad I can't bring myself to put it on my child again.It also fits too tight, even on the loosest setting, on my 50th percentile (normal weight) 1 year old. Bright red marks/indentations around the thighs, can't be comfortable.For what I paid for it, I'm very disappointed in its functionality.",
    "Don't make the mistake of putting baby in these and placing them in your lap! I ended up soaked. I was waiting a short time while other babies were being dressed - maybe 10 minutes. I know I cant expect them to act like a regular diaper but thought they would manage a little urine before I could get her in the water. Will stick with disposable swim diapers from now on. Will give Two stars because they appear to be well made and cute but unfortunately that doesn't do it for me.",
    "I like these, but it leaves kind of deep indentations on my 18 month old's skin from the snaps. They are a little too snug on her, even at the loosest setting.",
    "I don't usually write bad reviews. My son wasn't in this an hour and peed all over himself while we had his pool up and sprinklers going in the yard. Son is 14 months. Had the diaper on pretty tight to the point it left red marks when I took it off. Just on the second notch. He has a pretty small waist. Can't see how a normal toddler would feel comfortable even in the first notch... I think letting him go commando would have been more proficient than these. Definitely not something I would put on him at the public pool. I bought two with high hopes. Disappointed. I'll stick to my Little Swimmer disposables after trying these...",
    "So cute! But we had to return because it did not fit our 2 year old (36lbs).",
    "I bought this product for my 7 month old so she could sit in a baby pool. I put her in it then in her carseat to drive to the park and when i took her out of her carseat she was soaking wet and my carseat was too- she was wet with pee because this diaper doesnt absorb anything! She also had pooped and she was a mess. Just from the short ride over there! I threw the diaper away because ill never use it again",
    "Put this on my son and then sat him on my lap. He peed and it went straight through on to me as if he were naked. What?! I checked to make sure it was on snuggly and so did my husband. It happened again at the pool. I went back to iplay. There’s isn’t adjustable but it works.",
    "Cute but small. It just barely fits my 1.5 year old who is 25lbs.",
    "I bought this because I heard great things about it from the reviews. Every time we use it my sons diaper is soaked when we get out of the pool and it weighs him down while swimming. I watched the “how to use” video on their site so I know I’m using it correctly.",
    "It gave my son a blister where the buttons are. I tried it again and it gave him bad red marks. My son is only 8 months old.",
    "Unfortunately we were 0/2 with this diaper. Used it twice, and within a minute of putting it on, urine had leaked through the whole thing. Waste of money."
]


# inputs = tokenizer.batch_encode_plus(dataset_text, padding='longest', truncation=True, max_length=512, return_tensors='pt')
inputs = tokenizer.batch_encode_plus(dataset_text, padding='longest', truncation=True, max_length=256, return_tensors='pt')

learning_rate = 0.001
optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)

loss_function = torch.nn.CrossEntropyLoss()

num_epochs = 10

for epoch in range(num_epochs):
    optimizer.zero_grad()
    outputs = model(**inputs)
    loss = outputs.loss
    loss.backward()
    optimizer.step()

model.save_pretrained('model_training/model')

