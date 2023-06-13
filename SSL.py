from flask import Flask
from flask_sslify import SSLify

app = Flask(__name__)

# Enable SSL with self-signed certificate
sslify = SSLify(app)

@app.route('/')
def index():

    return 'Hello, SSL!'


if __name__ == '__main__':
    # app.run(ssl_context='adhoc')
    app.run(ssl_context='adhoc', host='0.0.0.0', port=8443, threaded=True)
    # app.run(ssl_context=('/etc/ssl/certs/nginx-selfsigned.crt', '/etc/ssl/private/nginx-selfsigned.key'), port=8443)


# @app.route('/process/<string:ff_id>', methods=['GET'])
# def process_csv(ff_id):

# #     # Retrieve the file details from the request
#     new_filename = get_filename(ff_id)

#     if new_filename is not None:
#         # Call 1 to process the uploaded file
#         process_csv_and_openAI(bucket_name, new_filename, ff_id)
#         data = get_gpt_data(ff_id)
#         response_data = {
#             'status': 'complete',
#             'data': data
#         }

#         return jsonify(response_data), 200
#         # return jsonify({'File/GPT uploaded successfully:': data}), 200
#     else:
#         return jsonify({'error': 'Invalid file ID'}), 400

# def get_filename(ff_id):
#     try:
#         cursor = conn.cursor()
#         cursor.execute(
#             "SELECT filename FROM csv_upload WHERE id = %s",
#             (ff_id,)
#         )
#         # Fetch the result as a tuple
#         result = cursor.fetchone()

#         # Extract the value from the tuple
#         result = result[0]
            
#         return result
            
#     except Error as e:
#         print('Error retrieving file details:', e)