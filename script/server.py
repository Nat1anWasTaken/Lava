from http.server import BaseHTTPRequestHandler, HTTPServer
import socketserver

PORT = 8080

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        code = self.path.split('code=')[1]
        print(code)
        exit()

with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    httpd.serve_forever()
