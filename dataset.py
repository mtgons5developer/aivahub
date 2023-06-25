import csv

csv_file_path = "csv/B00UFJNVTS - Heat Resistant Oven Mitts (2 pack)_ High Temperatu 2023-06-07.csv"
title_column_name = "Title"
body_column_name = "Body"
output_file_path = "dataset_output.txt"  # Specify the output file path

dataset_text = []

with open(csv_file_path, "r", encoding="utf-8") as file:
    csv_reader = csv.DictReader(file)
    for row in csv_reader:
        title = row[title_column_name]
        body = row[body_column_name]
        review_text = f"{title} {body}"
        dataset_text.append(review_text)

# Write the dataset_text to the output file
with open(output_file_path, "w", encoding="utf-8") as output_file:
    for review_text in dataset_text:
        output_file.write(review_text + "\n")

print("Dataset text has been written to the output file.")
