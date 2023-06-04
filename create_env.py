import os

def create():

    # Check if .env file exists
    if not os.path.isfile('.env'):
        # Open .env file in write mode
        with open('.env', 'w') as env_file:
            # Write the lines to the file
            env_file.write("OPENAI_API_KEY=\n")
            env_file.write("GOOGLE_SHEET='https://docs.google.com/spreadsheets/d/[Sheet-ID]/edit?usp=sharing'\n")
            env_file.write("HOST='localhost'\n")
            env_file.write("DATABASE=''\n")
            env_file.write("USER=''\n")
            env_file.write("PASSWORD=''\n")

        print("Created .env file.")

    # else:
    #     print(".env file already exists.")
        