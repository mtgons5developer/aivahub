import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Retrieve the PostgreSQL connection details from environment variables
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')

# Connect to the PostgreSQL database
conn = psycopg2.connect(
    host=db_host,
    port=db_port,
    database=db_name,
    user=db_user,
    password=db_password
)

# Create a cursor to interact with the database
cursor = conn.cursor()

# Execute the query to retrieve the guidelines_prompt from the database
query = "SELECT guidelines FROM guidelines_prompt WHERE id = 1;"
cursor.execute(query)

# Fetch the result
result = cursor.fetchone()

# Close the cursor and the database connection
cursor.close()
conn.close()

# Extract the guidelines_prompt from the result
guidelines_prompt = result[0]

# Print the guidelines_prompt
print(guidelines_prompt)
