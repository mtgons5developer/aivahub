import pyarrow.flight as fl

# Specify the location of the FlightServer
location = fl.Location.for_grpc_tcp('localhost', 12233)  # Replace with the appropriate host and port

# Create a FlightClient instance
client = fl.FlightClient(location)

# Perform a health check by listing available flights
try:
    flight_info = client.list_flights()
    print("FlightServer is running.")
except fl.FlightUnavailableError:
    print("FlightServer is not running.")
