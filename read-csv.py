import os

# Path to the folder containing the CSV files
folder_path = 'csv'

# Output file to store the names of the read files
output_file = 'read_files.txt'

# Open the output file in write mode
with open(output_file, 'w') as f_out:
    # Iterate over the files in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith('.csv'):
            # Build the full file path
            file_path = os.path.join(folder_path, filename)
            # Read the contents of the file
            # Here, you can add your own logic to process the CSV file contents if needed
            # For this example, we are just writing the file name into the output file
            f_out.write(filename + '\n')

# Print a message indicating the operation is complete
print("File names have been written to", output_file)
