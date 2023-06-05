import os
import csv
import time
import psycopg2

# Function to detect the number of columns in a CSV file
def detect_column_count(file_path):
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        first_row = next(reader)
        return len(first_row)

# Function to read CSV files from a directory and create a PostgreSQL table for each file
def read_csv_files(directory):
    conn = psycopg2.connect(database="your_database_name", user="your_username", password="your_password", host="your_host", port="your_port")
    cursor = conn.cursor()

    # Create a file to store the names of the files that have been read
    output_file = open("files_read.txt", "w")

    while True:
        # Get all CSV files in the directory
        files = [f for f in os.listdir(directory) if f.endswith('.csv')]

        for file_name in files:
            # Check if the file has been read before
            if file_name in output_file:
                continue

            file_path = os.path.join(directory, file_name)
            column_count = detect_column_count(file_path)

            # Extract the table name from the file name (excluding the extension)
            table_name = os.path.splitext(file_name)[0]

            # Create the PostgreSQL table
            create_table_query = f"CREATE TABLE {table_name} ("

            for i in range(column_count):
                create_table_query += f"column{i+1} VARCHAR,"
            
            create_table_query = create_table_query.rstrip(',') + ");"

            cursor.execute(create_table_query)
            conn.commit()

            # Write the file name to the output file
            output_file.write(file_name + '\n')
            output_file.flush()  # Flush the buffer to ensure the data is written immediately

        # Sleep for 1 minute before checking for new files again
        time.sleep(60)

    output_file.close()
    conn.close()

# Specify the directory containing the CSV files
csv_directory = "path/to/csv/folder"

# Call the function to read CSV files and create PostgreSQL tables
read_csv_files(csv_directory)
