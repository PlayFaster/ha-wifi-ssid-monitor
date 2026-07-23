"""Mock Supervisor Network API for development."""
# ruff: noqa: S104

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
                        {
                            "mac": "AA:BB:CC:DD:EE:01",
                            "ssid": "Mock_WiFi_24G",
                            "signal": 85,
                            "frequency": 2412,
                            "mode": "infra",
                        },
                        {
                            "mac": "AA:BB:CC:DD:EE:02",
                            "ssid": "Mock_WiFi_5G",
                            "signal": 65,
                            "frequency": 5180,
                            "mode": "infra",
                        },
                        {
                            "mac": "AA:BB:CC:DD:EE:03",
                            "ssid": "Mock_WiFi_6G",
                            "signal": 45,
                            "frequency": 6105,
                            "mode": "infra",
                        },
                        {
                            "mac": "AA:BB:CC:DD:EE:04",
                            "ssid": "",
                            "signal": 55,
                            "frequency": 2437,
                            "mode": "infra",
                        },
                        {
                            "mac": "AA:BB:CC:DD:EE:05",
                            "ssid": "Evil\u200bTwin",
                            "signal": 90,
                            "frequency": 2462,
                            "mode": "infra",
                        },
                    ]
                },
            }
            self.wfile.write(json.dumps(data).encode())

        elif "network/info" in self.path:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            data = {
                "result": "ok",
                "data": {
                    "interfaces": [
                        {"interface": "wlan0", "type": "wifi", "enabled": True},
                        {"interface": "eth0", "type": "ethernet", "enabled": True},
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
