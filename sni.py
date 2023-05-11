import ssl
import socket


hostname = 'shiatv.net'
port = 443
sock = socket.create_connection((hostname, port))
context = ssl.create_default_context()
context.set_alpn_protocols(['h2', 'http/1.1'])
conn = context.wrap_socket(sock, server_hostname=hostname)

print(f'{conn.cipher()[0]}\n{conn.cipher()[1]}\n{conn.selected_alpn_protocol()}')

sock.close()