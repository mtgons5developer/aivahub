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

# Create a cursor object
cur = conn.cursor()

# Specify the CSV file path
csv_file_path = 'csv/final2.csv'

# Read the CSV file into a Pandas DataFrame
df = pd.read_csv(csv_file_path)

# Get the column names from the DataFrame
columns = df.columns.tolist()

# Generate the CREATE TABLE query
table_name = 'tune_data2'
column_definitions = ', '.join(f'"{col}" VARCHAR' for col in columns)
create_table_query = f'CREATE TABLE IF NOT EXISTS {table_name} ({column_definitions});'

# Execute the CREATE TABLE query
cur.execute(create_table_query)

# Insert the data into the PostgreSQL table
for row in df.itertuples(index=False):
    insert_query = f'INSERT INTO {table_name} VALUES ({", ".join("%s" for _ in columns)});'
    cur.execute(insert_query, row)

# Commit the changes and close the cursor and connection
cur.close()
conn.close()