import csv
from google.cloud import storage

def read_file_from_gcs(bucket_name, file_name):
    # Instantiate the client
    client = storage.Client()

    # Retrieve the bucket and file
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    # Download the file's content as a string
    content = blob.download_as_text()

    return content

# Provide the name of your bucket and the file you want to read
bucket_name = "schooapp2022.appspot.com"
file_name = "csv-gpt.csv"

# Read the file from Google Cloud Storage
file_content = read_file_from_gcs(bucket_name, file_name)

# Parse the CSV content
rows = csv.reader(file_content.splitlines())
header = next(rows)  # Extract the header row
print("CSV Header:", header)  # Print the header for debugging

# Find the indices of the required columns
column_indices = [header.index(column) for column in ["Title", "Body", "gpt_status", "gpt_reason"]]

# Iterate over the rows and extract the required columns
for row in rows:
    columns = [row[index] for index in column_indices]
    title, body, gpt_status, gpt_reason = columns
    # Do something with the extracted columns
    print(f"Title: {title}, Body: {body}, GPT Status: {gpt_status}, GPT Reason: {gpt_reason}")
    break
