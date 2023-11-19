from http.server import BaseHTTPRequestHandler
import socketserver
import sys

PORT = 8084


class Handler(BaseHTTPRequestHandler):
    def do_get(self):
        code = self.path.split('code=')[1]
        print(code)
        sys.exit()


with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    httpd.serve_forever()
