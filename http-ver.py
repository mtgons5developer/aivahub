import requests

response = requests.options('http://192.168.0.24:8443')

# Check the 'server' response header to get the HTTP version
http_version = response.headers.get('server')

print('Server HTTP version:', http_version)
