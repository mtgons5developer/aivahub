import csv

def extract_columns(csv_file_path, output_file_path):
    with open(csv_file_path, 'r') as file:
        reader = csv.DictReader(file)
        columns = reader.fieldnames + ["status", "reason", "result"]

        # Create a list to store the rows with rating 4 or 5
        output_rows = []

        # Iterate over each row and add to output_rows if the rating is 4 or 5
        for row in reader:
            rating = row["Rating"]
            if rating and (rating == "4" or rating == "5"):
                row["status"] = "N/A"
                row["reason"] = "N/A"
                row["result"] = "N/A"
                output_rows.append(row)
            else:
                row["status"] = ""
                row["reason"] = ""
                row["result"] = ""
                output_rows.append(row)

    # Write the output_rows to the output file
    with open(output_file_path, 'w', newline='') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(output_rows)

    print("Output file created successfully.")

# Usage example
csv_file_path = 'csv/B00UFJNVTS - Heat Resistant Oven Mitts (2 pack)_ High Temperatu 2023-06-07.csv'
output_file_path = 'csv/output.csv'
extract_columns(csv_file_path, output_file_path)
