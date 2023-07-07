import os
import pandas as pd

# Folder path containing the Excel files
folder_path = "xlsx/"

# Select the desired columns
selected_columns = ["Date", "Author", "Verified", "Helpful", "Title", "Body", "Rating", "Images", "Videos",
                    "URL", "Variation", "Style", "ai reason", "ai status", "ai result", "human reason",
                    "human status", "human result"]

# Create an empty list to store the DataFrames for each Excel file
dfs = []

# Iterate over the files in the folder
for filename in os.listdir(folder_path):
    if filename.endswith(".xlsx"):
        file_path = os.path.join(folder_path, filename)
        # Read the Excel file
        # Read the Excel file and skip the first row (assuming it contains the filter settings)
        df = pd.read_excel(file_path, skiprows=[0])
        # Select the desired columns
        df = df[selected_columns]
        # Append the DataFrame to the list
        dfs.append(df)

# Concatenate the DataFrames into a single DataFrame
combined_df = pd.concat(dfs, ignore_index=True)

# Write the combined DataFrame to a CSV file
combined_df.to_csv("output_file.csv", index=False)
