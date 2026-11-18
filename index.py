"""
Vercel Serverless Entrypoint for SupeRR Scout.
Serves the Rajasthan Royals Web Portal and Unstop PDF Dossier.
Compatible with WSGI (app / application) and BaseHTTPRequestHandler (handler).
"""

import os
import mimetypes
from http.server import BaseHTTPRequestHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")


def get_static_file(path_info):
    """Resolve and return static file content and content type from public/."""
    clean_path = path_info.lstrip("/").split("?")[0]
    if not clean_path or clean_path == "/":
        clean_path = "index.html"

    target_path = os.path.normpath(os.path.join(PUBLIC_DIR, clean_path))
    # Prevent directory traversal
    if not target_path.startswith(PUBLIC_DIR) or not os.path.exists(target_path):
        target_path = os.path.join(PUBLIC_DIR, "index.html")

    mime_type, _ = mimetypes.guess_type(target_path)
    if not mime_type:
        mime_type = "application/octet-stream"

    with open(target_path, "rb") as f:
        content = f.read()

    return content, mime_type


# 1. BaseHTTPRequestHandler interface (Vercel standard for Python serverless)
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        content, mime_type = get_static_file(self.path)
        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        self.wfile.write(content)

    def do_HEAD(self):
        content, mime_type = get_static_file(self.path)
        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()


# 2. WSGI application interface (FastAPI/Flask/WSGI standard)
def app(environ, start_response):
    path_info = environ.get("PATH_INFO", "/")
    content, mime_type = get_static_file(path_info)
    status = "200 OK"
    response_headers = [
        ("Content-Type", mime_type),
        ("Content-Length", str(len(content))),
        ("Cache-Control", "public, max-age=3600")
    ]
    start_response(status, response_headers)
    return [content]


application = app
