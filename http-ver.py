import ssl
from flask import Flask

app = Flask(__name__)

# Route definition
@app.route('/')
def hello_world():
    return 'Hello, World!'

if __name__ == '__main__':
    # Enable self-signed SSL
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain('certificate.crt', 'private.key')

    # Run the Flask application
    app.run(ssl_context=context, host='0.0.0.0', port=8443)
