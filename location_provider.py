"""Location source boundary used by the risk scoring service.

The scorer depends on this interface rather than on Android APIs or a GPS SDK.
The current HTTP demo adapts the request payload; tests can inject fixed virtual
coordinates, and a future Android client can implement the same contract around
its real GPS collector.
"""

from __future__ import annotations

from typing import Any, Protocol


class LocationProvider(Protocol):
    def get_location(self, payload: dict[str, Any]) -> dict[str, float] | None:
        """Return the GPS coordinate used for this scoring request."""


class RequestPayloadLocationProvider:
    """Adapter for the location sample sent to the demo HTTP endpoint."""

    def get_location(self, payload: dict[str, Any]) -> dict[str, float] | None:
        location = payload.get("gps_location")
        if not isinstance(location, dict):
            return None
        try:
            return {"lat": float(location["lat"]), "lon": float(location["lon"])}
        except (KeyError, TypeError, ValueError):
            return None
