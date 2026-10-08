"""
Instagram Activity Tracker Server
Provides REST API endpoints and static file serving using standard library http.server.
No external dependencies required (zero pip install).

Endpoints:
- GET  /                                -> Serves frontend UI
- GET  /api/activity/liked              -> List of liked posts
- GET  /api/activity/saved              -> List of saved posts
- GET  /api/activity/visited-profiles   -> List of visited account profiles (based on liked & saved posts)
- GET  /api/posts                       -> List of all sample posts
- POST /api/posts/<id>/toggle-like      -> Toggle like state for post <id>
- POST /api/posts/<id>/toggle-save      -> Toggle save state for post <id>
- POST /api/reset                       -> Reset database to sample seed data
"""

import http.server
import json
import os
import re
import socket
import sys
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse

import database

PORT = 5000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")


class InstagramRequestHandler(http.server.BaseHTTPRequestHandler):
    """Handles HTTP requests for Instagram My Activity and Posts API."""

    def _send_json(self, data, status=200):
        response_bytes = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(response_bytes)

    def _send_file(self, filepath, content_type):
        if not os.path.exists(filepath):
            self.send_error(404, "File Not Found")
            return
        with open(filepath, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path == "":
            path = "/"

        # API Routes
        if path == "/api/activity/liked":
            posts = database.get_liked_posts()
            self._send_json({"success": True, "count": len(posts), "data": posts})
            return

        if path == "/api/activity/saved":
            posts = database.get_saved_posts()
            self._send_json({"success": True, "count": len(posts), "data": posts})
            return

        if path == "/api/activity/visited-profiles":
            profiles = database.get_visited_profiles()
            self._send_json({"success": True, "count": len(profiles), "data": profiles})
            return

        if path == "/api/posts":
            posts = database.get_posts()
            self._send_json({"success": True, "count": len(posts), "data": posts})
            return

        # Static File Routes
        if path == "/":
            self._send_file(os.path.join(STATIC_DIR, "index.html"), "text/html")
            return

        if path in ("/style.css", "/static/style.css"):
            self._send_file(os.path.join(STATIC_DIR, "style.css"), "text/css")
            return

        if path in ("/app.js", "/static/app.js"):
            self._send_file(os.path.join(STATIC_DIR, "app.js"), "application/javascript")
            return

        self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        # Reset Database
        if path == "/api/reset":
            database.reset_db()
            self._send_json({
                "success": True,
                "message": "Database reset to sample state successfully",
                "visited_profiles": database.get_visited_profiles()
            })
            return

        # Toggle Like: /api/posts/<id>/toggle-like
        match_like = re.match(r"^/api/posts/(\d+)/toggle-like$", path)
        if match_like:
            post_id = int(match_like.group(1))
            updated = database.toggle_like(post_id)
            if updated is None:
                self._send_json({"success": False, "error": "Post not found"}, status=404)
            else:
                visited = database.get_visited_profiles()
                self._send_json({
                    "success": True,
                    "post": updated,
                    "visited_profiles_count": len(visited),
                    "visited_profiles": visited
                })
            return

        # Toggle Save: /api/posts/<id>/toggle-save
        match_save = re.match(r"^/api/posts/(\d+)/toggle-save$", path)
        if match_save:
            post_id = int(match_save.group(1))
            updated = database.toggle_save(post_id)
            if updated is None:
                self._send_json({"success": False, "error": "Post not found"}, status=404)
            else:
                visited = database.get_visited_profiles()
                self._send_json({
                    "success": True,
                    "post": updated,
                    "visited_profiles_count": len(visited),
                    "visited_profiles": visited
                })
            return

        self.send_error(404, "Not Found")

    def log_message(self, format, *args):
        # Clean logging format
        sys.stderr.write(f"[{self.log_date_time_string()}] {args[0]} {args[1]} {args[2]}\n")


class DualStackServer(ThreadingHTTPServer):
    address_family = socket.AF_INET6

    def server_bind(self):
        try:
            self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        except (AttributeError, OSError):
            pass
        super().server_bind()


def run(port: int = PORT):
    database.init_db(seed=True)
    try:
        httpd = DualStackServer(("::", port), InstagramRequestHandler)
    except Exception:
        httpd = ThreadingHTTPServer(("", port), InstagramRequestHandler)

    print(f"Instagram Activity Tracker running at:")
    print(f"  -> http://localhost:{port}")
    print(f"  -> http://127.0.0.1:{port}")
    print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()


if __name__ == "__main__":
    port_to_use = PORT
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port_to_use = int(sys.argv[1])
    run(port_to_use)
