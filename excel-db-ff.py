import os
import pandas as pd
import psycopg2
import sys
import time
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
import csv

load_dotenv()

# Retrieve the PostgreSQL connection details from environment variables
db_host = os.getenv('HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DATABASE')
db_user = os.getenv('DB_USER')
db_password = os.getenv('PASSWORD')

def connect_to_database():
    retry_count = 0
    max_retries = 10
    retry_delay = 5  # seconds

    while retry_count < max_retries:
        try:
            conn = psycopg2.connect(
                user=db_user,
                password=db_password,
                host=db_host,
                port=db_port,
                database=db_name
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            print('Connected to Cloud SQL PostgreSQL database')
            return conn
        except Error as e:
            print('Error connecting to Cloud SQL PostgreSQL database:', e)
            retry_count += 1
            print(f'Retrying connection ({retry_count}/{max_retries})...')
            time.sleep(retry_delay)

# Connect to the database
conn = connect_to_database()

# Check if the connection was successful
if conn is None:
    print('Unable to connect to the database. Exiting...')
    sys.exit(1)

conn.autocommit = True

# Read the CSV file
csv_file = 'csv/final2.csv'  # Replace with your actual CSV file name
df = pd.read_csv(csv_file)

# Combine "Title" and "Body" columns into "review" column
df['review'] = df['Title'] + ', ' + df['Body']

# Check if each "review" already exists in the table
existing_reviews = set()
with conn.cursor() as cursor:
    cursor.execute("SELECT review FROM tune_data4;")
    rows = cursor.fetchall()
    existing_reviews = set(row[0] for row in rows)

# Insert each row into the "tune_data4" table if it doesn't already exist
with conn.cursor() as cursor:
    for index, row in df.iterrows():
        review = row['review']
        if review not in existing_reviews:
            try:
                values = (review, row['ai_reason'], row['ai_status'], row['ai_result'], row['human_reason'], row['human_status'], row['human_result'])
                insert_query = "INSERT INTO tune_data4 (review, ai_reason, ai_status, ai_result, human_reason, human_status, human_result) VALUES (%s, %s, %s, %s, %s, %s, %s);"
                cursor.execute(insert_query, values)
            except psycopg2.errors.StringDataRightTruncation as e:
                print(f'Error: {e}')
                print('Skipping row due to data truncation.')
                continue

print('Data insertion complete.')
