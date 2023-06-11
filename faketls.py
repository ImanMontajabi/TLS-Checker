import ssl
import socket

context = ssl.create_default_context()
context.set_alpn_protocols(['h2', 'http/1.1', 'h3'])

hostname = 'digikala.com'
port = 443

with socket.create_connection((hostname, port)) as sock:
    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
        print(ssock.verify_client_post_handshake)

