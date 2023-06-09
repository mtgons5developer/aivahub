from flask import Flask, request
from google.cloud import storage

app = Flask(__name__)

@app.route('/upload-to-gcs', methods=['POST'])
def upload_to_gcs():
    file = request.files.get('file')
    if file:
        # Upload the file to your GCS bucket
        bucket_name = "schooapp2022.appspot.com"
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(file.filename)
        blob.upload_from_file(file)

        return 'File uploaded successfully'

    return 'No file provided', 400

if __name__ == '__main__':
    app.run()
