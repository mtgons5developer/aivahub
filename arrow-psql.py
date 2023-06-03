import os
import pyarrow.flight as fl
import pyarrow as pa
import psycopg2
import random
import string

from dotenv import load_dotenv

load_dotenv()

sheet_link = os.getenv('GOOGLE_SHEET')
pg_host = os.getenv('HOST')
pg_port = 5432
pg_db = os.getenv('DATABASE')
pg_user = os.getenv('USER')
pg_password = os.getenv('PASSWORD')

# Connect to PostgreSQL
conn = psycopg2.connect(host=pg_host, port=pg_port, dbname=pg_db, user=pg_user, password=pg_password)

# Define FlightInfo handler
def get_flight_info(context, criteria):
    # Create FlightInfo instance
    flight_info = fl.FlightInfo()

    # Set FlightDescriptor
    descriptor = fl.FlightDescriptor.for_path("customers")
    flight_info.endpoints.extend([descriptor])

    # Return FlightInfo
    return flight_info

# Define FlightDataReader handler
def do_get(context, ticket):
    # Get the FlightDescriptor from the ticket
    descriptor = fl.FlightDescriptor.deserialize_pandas(ticket)

    # Check if the FlightDescriptor is for the "customers" table
    if descriptor.path == "customers":
        # Generate 10 random names and emails
        new_data = []
        for _ in range(10):
            name = ''.join(random.choice(string.ascii_letters) for _ in range(8))
            email = ''.join(random.choice(string.ascii_lowercase) for _ in range(8)) + '@example.com'
            new_data.append((name, email))

        # Execute SQL query to insert the new data into the "customers" table
        cursor = conn.cursor()
        cursor.executemany("INSERT INTO customers (name, email) VALUES (%s, %s)", new_data)
        conn.commit()

    # Create an empty Arrow table
    schema = pa.schema([
        pa.field('name', pa.string()),
        pa.field('email', pa.string())
    ])
    table = pa.Table.from_pandas(pd.DataFrame(), schema=schema)

    # Create a FlightData instance
    data = fl.FlightData(table)

    # Return the FlightData instance
    return data

# Create a FlightServer instance
server = fl.FlightServer()

# Define FlightInfo and FlightDataReader handlers
server.register_endpoint("customers", get_flight_info)
server.register_action("customers", do_get)

# Start the FlightServer
server.run()
