"""Synthetic request payloads for repeatable risk-scoring demonstrations."""

from __future__ import annotations

from copy import deepcopy

BRISTOL = {"lat": 51.4545, "lon": -2.5879}
LONDON = {"lat": 51.5072, "lon": -0.1276}
SHANGHAI = {"lat": 31.2304, "lon": 121.4737}

SCENARIOS = {
    "normal-walk": {
        "mock_location": False,
        "gps_location": BRISTOL,
        "ip_location": {"lat": 51.4546, "lon": -2.5880},
        "sensor_state": "moving",
        "trajectory": [
            {**BRISTOL, "timestamp_s": 1000},
            {"lat": 51.4550, "lon": -2.5870, "timestamp_s": 1060},
        ],
    },
    "gps-drift": {
        "mock_location": False,
        "gps_location": {"lat": 51.4565, "lon": -2.5860},
        "ip_location": BRISTOL,
        "sensor_state": "stationary",
        "trajectory": [
            {**BRISTOL, "timestamp_s": 1000},
            {"lat": 51.4565, "lon": -2.5860, "timestamp_s": 1060},
        ],
    },
    "teleport": {
        "mock_location": False,
        "gps_location": LONDON,
        "ip_location": BRISTOL,
        "sensor_state": "stationary",
        "trajectory": [
            {**BRISTOL, "timestamp_s": 1000},
            {**LONDON, "timestamp_s": 1005},
        ],
    },
    "gps-ip-mismatch": {
        "mock_location": False,
        "gps_location": SHANGHAI,
        "ip_location": BRISTOL,
        "sensor_state": "moving",
        "trajectory": [{**SHANGHAI, "timestamp_s": 1000}],
    },
}


def get_scenario_payload(name: str) -> dict:
    """Return a copy so demo runs cannot mutate the shared fixture."""
    try:
        payload = deepcopy(SCENARIOS[name])
    except KeyError as exc:
        raise ValueError(f"unknown scenario: {name}") from exc
    payload["scenario"] = name
    payload["integrity"] = {"verified": True, "device_verdicts": ["MEETS_DEVICE_INTEGRITY"]}
    payload["wifi"] = {"environment_changed": False}
    return payload
