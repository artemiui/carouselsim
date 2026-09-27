"""Interactive Server & Simulation Backend for the EDSA Carousel Dashboard.

Serves static dashboard files over http://localhost:8000 and provides an API endpoint
POST /api/simulate to trigger dynamic SimPy discrete-event simulation runs with tweakable
times and parameters directly from the front end.
"""

from __future__ import annotations
import http.server
import socketserver
import webbrowser
import os
import sys
import json
import logging

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from edsa_carousel_sim.simulator_api import run_simulation_window

PORT = 8000
DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), "output"))


class SimulationDashboardHandler(http.server.SimpleHTTPRequestHandler):
    """Handles static files from output directory and POST requests to /api/simulate."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_POST(self):
        if self.path == '/api/simulate':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                params = json.loads(body.decode('utf-8')) if body else {}
                print(f"\n[API] Running simulation with parameters: {params}")
                snapshots, meta = run_simulation_window(params)
                
                response_data = {
                    'status': 'success',
                    'snapshots': snapshots,
                    'meta': meta
                }
                response_bytes = json.dumps(response_data).encode('utf-8')
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(response_bytes)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(response_bytes)
                print(f"[API] Simulation completed in {meta.get('elapsed_sec')}s. Sent {len(snapshots)} snapshots to dashboard.\n")
            except Exception as e:
                print(f"[API ERROR] {e}")
                err_bytes = json.dumps({'status': 'error', 'message': str(e)}).encode('utf-8')
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(err_bytes)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(err_bytes)
        else:
            self.send_error(404, "Endpoint not found")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


def main():
    if not os.path.exists(DIRECTORY):
        os.makedirs(DIRECTORY, exist_ok=True)

    dashboard = "dashboard.html" if os.path.exists(os.path.join(DIRECTORY, "dashboard.html")) else "dashboard_8am_11am.html"
    url = f"http://localhost:{PORT}/{dashboard}"
    
    print("\n" + "=" * 65)
    print(" EDSA CAROUSEL: INTERACTIVE SIMULATION SERVER & FRONT END")
    print("=" * 65)
    print(f" URL: {url}")
    print(f" API: http://localhost:{PORT}/api/simulate (Live SimPy Engine)")
    print(" Press Ctrl+C to stop the server")
    print("=" * 65 + "\n")

    try:
        webbrowser.open(url)
    except Exception:
        pass

    # Allow port reuse to avoid address already in use errors
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), SimulationDashboardHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()
