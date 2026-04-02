"""Mock Supervisor Network API for development."""

import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer

_LOGGER = logging.getLogger(__name__)


class MockSupervisorHandler(BaseHTTPRequestHandler):
    """Handles mock requests for the Supervisor Network API."""

    def do_GET(self):
        """Respond to GET requests with fake WiFi data."""
        if "accesspoints" in self.path:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            data = {
                "result": "ok",
                "data": {
                    "accesspoints": [
                        {"ssid": "Mock_WiFi_1", "signal": -50},
                        {"ssid": "Mock_WiFi_2", "signal": -60},
                        {"ssid": "MyNetwork1", "signal": -40},
                        {"ssid": "Hidden_Network", "signal": -80},
                    ]
                },
            }
            self.wfile.write(json.dumps(data).encode())
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    _LOGGER.info("Starting Mock Supervisor on port 80...")
    httpd = HTTPServer(("0.0.0.0", 80), MockSupervisorHandler)
    httpd.serve_forever()
