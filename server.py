#!/usr/bin/env python3
"""Local demo API for a server-side location risk scoring prototype."""

from __future__ import annotations

import json
import math
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from location_provider import LocationProvider, RequestPayloadLocationProvider
from scenarios import SCENARIOS, get_scenario_payload

WEB_INDEX = Path(__file__).with_name("web") / "index.html"


def distance_km(a: dict[str, Any], b: dict[str, Any]) -> float:
    """Great-circle distance between two {lat, lon} coordinates."""
    lat1, lon1 = math.radians(float(a["lat"])), math.radians(float(a["lon"]))
    lat2, lon2 = math.radians(float(b["lat"])), math.radians(float(b["lon"]))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0 * 2 * math.asin(min(1.0, math.sqrt(h)))


def score_report(
    payload: dict[str, Any],
    location_provider: LocationProvider | None = None,
) -> dict[str, Any]:
    """Score supplied signals using an injectable location source.

    The default provider adapts the HTTP request. Tests can pass a fake provider
    so scoring does not depend on a physical GPS device.
    """
    score = 0
    signals: list[dict[str, Any]] = []

    def add(code: str, points: int, detail: str) -> None:
        nonlocal score
        score += points
        signals.append({"code": code, "points": points, "detail": detail})

    if payload.get("mock_location") is True:
        add("MOCK_LOCATION", 25, "客户端报告定位结果带有 mock 标记。")

    integrity = payload.get("integrity", {})
    # In production, this field must come from a server-verified Play Integrity token.
    if integrity.get("verified") is True:
        verdicts = set(integrity.get("device_verdicts", []))
        if "MEETS_DEVICE_INTEGRITY" not in verdicts and "MEETS_VIRTUAL_INTEGRITY" not in verdicts:
            add("DEVICE_INTEGRITY_LOW", 30, "已验证的完整性结果未满足可接受的设备完整性判定。")
    elif integrity:
        signals.append({"code": "INTEGRITY_UNVERIFIED", "points": 0,
                        "detail": "完整性字段尚未由服务端验证，本次不计入风险分。"})

    provider = location_provider or RequestPayloadLocationProvider()
    gps = provider.get_location(payload)
    ip = payload.get("ip_location")
    if gps and ip:
        gap = distance_km(gps, ip)
        if gap > 3000:
            add("GPS_IP_MISMATCH", 10, f"GPS 与 IP 估算位置相距约 {gap:.0f} km；仅作为弱风险信号。")

    wifi = payload.get("wifi", {})
    if wifi.get("environment_changed") is True:
        add("WIFI_ENV_CHANGED", 8, "Wi-Fi 环境摘要与近期记录不同；未上传原始 BSSID。")

    points = payload.get("trajectory", [])
    for previous, current in zip(points, points[1:]):
        try:
            elapsed = (float(current["timestamp_s"]) - float(previous["timestamp_s"]))
            if elapsed <= 0:
                add("TIME_ORDER_INVALID", 15, "轨迹时间戳重复或倒序。")
                continue
            moved_km = distance_km(previous, current)
            speed_kmh = moved_km / elapsed * 3600
            if speed_kmh > 1000:
                add("IMPOSSIBLE_SPEED", 35, f"相邻定位点推算速度约 {speed_kmh:.0f} km/h。")
            elif speed_kmh > 250:
                add("HIGH_SPEED", 12, f"相邻定位点推算速度约 {speed_kmh:.0f} km/h。")
        except (KeyError, TypeError, ValueError):
            add("TRAJECTORY_INVALID", 5, "轨迹点缺少有效坐标或时间戳。")

    if payload.get("sensor_state") == "stationary" and len(points) >= 2:
        try:
            latest, previous = points[-1], points[-2]
            if distance_km(latest, previous) > 0.2:
                add("SENSOR_GPS_CONFLICT", 15, "传感器报告静止，但短时间内 GPS 位移超过 200 m。")
        except (KeyError, TypeError, ValueError):
            pass

    score = min(score, 100)
    if score >= 80:
        action = "拒绝位置敏感操作"
    elif score >= 60:
        action = "要求重新验证"
    elif score >= 30:
        action = "增加采样频率并观察"
    else:
        action = "允许，继续常规监测"
    return {"risk_score": score, "action": action, "signals": signals,
            "disclaimer": "演示评分结果；生产环境应由服务端验证完整性令牌并结合业务场景校准阈值。"}


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: dict[str, Any]) -> None:
        raw = json.dumps(body, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/":
            try:
                raw = WEB_INDEX.read_bytes()
            except OSError:
                return self._send(500, {"error": "demo_page_unavailable"})
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if self.path == "/scenarios":
            scenarios = [
                {"name": name, "payload": get_scenario_payload(name)}
                for name in SCENARIOS
            ]
            return self._send(200, {"scenarios": scenarios})
        if self.path == "/health":
            return self._send(200, {"status": "ok", "service": "location-risk-demo"})
        self._send(404, {"error": "not_found", "hint": "GET /, GET /health, or POST /score"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/score":
            return self._send(404, {"error": "not_found"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size <= 0 or size > 1_000_000:
                return self._send(400, {"error": "body_size_invalid"})
            payload = json.loads(self.rfile.read(size))
            if not isinstance(payload, dict):
                return self._send(400, {"error": "json_object_required"})
            self._send(200, score_report(payload))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send(400, {"error": "invalid_json"})

    def log_message(self, fmt: str, *args: Any) -> None:
        print("%s - %s" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    print("Location risk demo listening on http://127.0.0.1:8000")
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
