from http.server import BaseHTTPRequestHandler
import socketserver
import sys

PORT = 8080

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        code = self.path.split('code=')[1]
        print(code)
        sys.exit()

with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    httpd.serve_forever()
