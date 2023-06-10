from flask import Flask, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost/database_name'  # Replace with your PostgreSQL database URI
db = SQLAlchemy(app)

class ProcessedCsv(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fileId = db.Column(db.String(100), unique=True)
    csvFile = db.Column(db.String(100))

@app.route('/status/<id>', methods=['GET'])
def get_status(id):
    # Query the database to check if there's a matching row with the provided ID
    result = ProcessedCsv.query.filter_by(fileId=id).first()

    if result:
        if result.csvFile:
            # If a CSV file exists in the 'csvFile' column, prepare and return the CSV file as the response
            headers = {'Content-Type': 'text/csv'}
            csv_response = make_response(result.csvFile)
            csv_response.headers = headers
            return csv_response
        else:
            # If the status is 'Processed', but there's no CSV file, return a JSON response indicating such
            return jsonify({'status': 'Processed (No CSV File)'})
    else:
        # If no matching row is found, return a JSON response indicating the status is 'Not Processed'
        return jsonify({'status': 'Not Processed'})

if __name__ == '__main__':
    app.run()