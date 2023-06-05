import os
import csv
import time
import psycopg2

from dotenv import load_dotenv

load_dotenv()

# Retrieve the PostgreSQL connection details from environment variables
db_host = os.getenv('HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DATABASE')
db_user = os.getenv('USER')
db_password = os.getenv('PASSWORD')

# Connect to the PostgreSQL database
conn = psycopg2.connect(
    host=db_host,
    port=db_port,
    database=db_name,
    user=db_user,
    password=db_password
)

# Function to detect the number of columns in a CSV file
def detect_column_count(file_path):
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        first_row = next(reader)
        return len(first_row)

# Function to read CSV files from a directory and create a PostgreSQL table for each file
def read_csv_files(directory):
    cursor = conn.cursor()

    # Create a file to store the names of the files that have been read
    output_file_path = "files_read.txt"
    processed_files = set()

    if os.path.exists(output_file_path):
        with open(output_file_path, "r") as output_file:
            processed_files = set(output_file.read().splitlines())

    while True:
        # Get all CSV files in the directory
        files = [f for f in os.listdir(directory) if f.endswith('.csv')]

        for file_name in files:
            # Check if the file has been read before
            if file_name in processed_files:
                continue

            file_path = os.path.join(directory, file_name)
            column_count = detect_column_count(file_path)

            # Extract the table name from the file name (excluding the extension)
            table_name = os.path.splitext(file_name)[0]

            # Create the PostgreSQL table if it doesn't exist
            create_table_query = f'CREATE TABLE IF NOT EXISTS "{table_name}" ('

            for i in range(column_count):
                create_table_query += f'column{i+1} VARCHAR,'
            
            create_table_query = create_table_query.rstrip(',') + ');'

            cursor.execute(create_table_query)
            conn.commit()

            # Insert data from the CSV file into the PostgreSQL table
            with open(file_path, 'r') as csv_file:
                csv_reader = csv.reader(csv_file)
                next(csv_reader)  # Skip the header row

                insert_query = f'INSERT INTO "{table_name}" VALUES ({", ".join(["%s"] * column_count)})'

                for row in csv_reader:
                    cursor.execute(insert_query, row)
                    conn.commit()

            # Add the file name to the set of processed files
            processed_files.add(file_name)

        # Write the processed files back to the output file
        with open(output_file_path, "w") as output_file:
            output_file.write('\n'.join(processed_files))

        # Sleep for 1 minute before checking for new files again
        # time.sleep(60)
        quit()

    conn.close()

# Specify the directory containing the CSV files
csv_directory = "/Users/datax/aivahub/csv"

# Call the function to read CSV files and insert data into PostgreSQL tables
read_csv_files(csv_directory)
