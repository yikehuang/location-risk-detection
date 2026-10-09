#!/usr/bin/env python3
"""Send a synthetic Bristol-to-London jump to the local scoring API."""

import json
from urllib.request import Request, urlopen

payload = {
    "mock_location": False,
    "integrity": {"verified": True, "device_verdicts": []},
    "gps_location": {"lat": 51.4545, "lon": -2.5879},
    "ip_location": {"lat": 51.5072, "lon": -0.1276},
    "wifi": {"environment_changed": False},
    "sensor_state": "stationary",
    "trajectory": [
        {"lat": 51.4545, "lon": -2.5879, "timestamp_s": 1000},
        {"lat": 51.5072, "lon": -0.1276, "timestamp_s": 1005},
    ],
}
request = Request("http://127.0.0.1:8000/score", data=json.dumps(payload).encode(),
                  headers={"Content-Type": "application/json"}, method="POST")
with urlopen(request, timeout=5) as response:
    print(response.read().decode())
