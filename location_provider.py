"""Location source boundary used by the risk scoring service.

The scorer depends on this interface rather than on Android APIs or a GPS SDK.
The current HTTP demo adapts the request payload; tests can inject fixed virtual
coordinates, and a future Android client can implement the same contract around
its real GPS collector.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

Coordinate = dict[str, float]


class LocationProvider(Protocol):
    def get_location(self, payload: dict[str, Any]) -> dict[str, float] | None:
        """Return the GPS coordinate used for this scoring request."""


class FixedLocationProvider:
    """Return one fixed coordinate; intended for tests and local demos."""

    def __init__(self, coordinate: Coordinate):
        self.coordinate = {"lat": float(coordinate["lat"]), "lon": float(coordinate["lon"])}

    def get_location(self, payload: dict[str, Any]) -> Coordinate:
        return self.coordinate.copy()


class SequenceLocationProvider:
    """Replay coordinates in order, raising when a test consumes the whole path."""

    def __init__(self, coordinates: Sequence[Coordinate]):
        if not coordinates:
            raise ValueError("coordinates must not be empty")
        self._coordinates = tuple(
            {"lat": float(point["lat"]), "lon": float(point["lon"])}
            for point in coordinates
        )
        self._index = 0

    def get_location(self, payload: dict[str, Any]) -> Coordinate:
        if self._index >= len(self._coordinates):
            raise IndexError("location sequence exhausted")
        point = self._coordinates[self._index]
        self._index += 1
        return point.copy()


class ScenarioLocationProvider:
    """Select a fixed or replayed coordinate path by payload scenario name.

    This provider is for deterministic local tests and demonstrations. It does
    not change Android's system location or provide a production GPS source.
    """

    def __init__(self, scenarios: Mapping[str, Sequence[Coordinate]]):
        if not scenarios:
            raise ValueError("at least one scenario is required")
        self._providers = {
            name: SequenceLocationProvider(points)
            for name, points in scenarios.items()
        }

    def get_location(self, payload: dict[str, Any]) -> Coordinate | None:
        name = payload.get("scenario")
        provider = self._providers.get(name) if isinstance(name, str) else None
        if provider is None:
            return None
        return provider.get_location(payload)


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
