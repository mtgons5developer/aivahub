import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')
os.environ['OPENAI_API_KEY'] = openai_api_key

# Retrieve the PostgreSQL connection details from environment variables
# db_host = os.getenv('HOST')
# db_port = os.getenv('DB_PORT')
db_name = os.getenv('DATABASE')
db_user = os.getenv('DB_USER')
db_password = os.getenv('PASSWORD')
cloud_sql_connection_name = 'review-tool-388312:us-central1:blackwidow'

app = Flask(__name__)

# Configure the SQLAlchemy database URI
db_uri = f'postgresql+psycopg2://{db_user}:{db_password}@/{db_name}?host=/cloudsql/{cloud_sql_connection_name}'

# Configure the Flask app to use the database
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define a model for your database table
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

    def __repr__(self):
        return f'<User {self.name}>'

# Define a route for your Flask application
@app.route('/')
def hello():
    # Perform a database query
    users = User.query.all()
    
    # Display the queried data
    result = ', '.join([user.name for user in users])
    return f'Hello, Users: {result}'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

