from __future__ import annotations

import argparse
import http.server
import os
import socketserver
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent
os.chdir(PACKAGE_ROOT)


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        # OBS polls state.json frequently; suppress routine request spam.
        return


class ReusableThreadingTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main() -> None:
    parser = argparse.ArgumentParser(description="Crystal Guild OBS raid overlay server")
    parser.add_argument("--port", type=int, default=4350)
    parser.add_argument("--dir", default="overlay")
    args = parser.parse_args()
    root = Path(args.dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    os.chdir(root)
    with ReusableThreadingTCPServer(("127.0.0.1", args.port), QuietHandler) as httpd:
        print(f"Crystal Guild raid overlay: http://localhost:{args.port}/raid_overlay.html")
        print("Add that URL as an OBS Browser Source. Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
