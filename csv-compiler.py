import os
import csv

def compile_csv_files(folder_path, output_file_path):
    # Get a list of all CSV files in the folder
    csv_files = [file for file in os.listdir(folder_path) if file.endswith(".csv")]

    # Check if there are any CSV files in the folder
    if not csv_files:
        print("No CSV files found in the folder.")
        return

    # Open the output CSV file in write mode
    with open(output_file_path, 'w', newline='') as output_file:
        writer = csv.writer(output_file)

        # Iterate over each CSV file and write its contents to the output file
        for file in csv_files:
            file_path = os.path.join(folder_path, file)

            # Open the CSV file in read mode
            with open(file_path, 'r') as csv_file:
                reader = csv.reader(csv_file)

                # Write the rows from the CSV file
                writer.writerows(reader)

    print("CSV files compiled successfully into", output_file_path)

# Usage example
folder_path = 'csv/'
output_file_path = 'output.csv'
compile_csv_files(folder_path, output_file_path)
