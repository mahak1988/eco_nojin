import http.server, socketserver, os, sys, threading

root = sys.argv[1]
port = int(sys.argv[2])
os.chdir(root)


class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", port), H)
print(f"سرو روی {port} — ریشه: {root}", flush=True)
httpd.serve_forever()
