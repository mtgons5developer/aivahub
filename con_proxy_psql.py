import os
import psycopg2

# Retrieve the Cloud SQL connection details from environment variables
db_host = '127.0.01'
db_port = '3306'
db_user = 'postgres'
db_password = 'potatoaivarock'
db_name = 'aivahub'

# Create a connection using the Cloud SQL Proxy socket
conn = psycopg2.connect(
    host=db_host,
    port=db_port,
    user=db_user,
    password=db_password,
    dbname=db_name
)

# Execute SQL queries or perform database operations using the connection
cursor = conn.cursor()
cursor.execute("SELECT * FROM my_table")
result = cursor.fetchall()
for row in result:
    print(row)

# Close the connection
conn.close()

