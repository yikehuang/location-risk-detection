import unittest

from server import score_report
from location_provider import FixedLocationProvider, ScenarioLocationProvider, SequenceLocationProvider
from scenarios import get_scenario_payload


class FakeLocationProvider:
    """Inject a virtual coordinate without relying on a GPS device."""

    def __init__(self, coordinate):
        self.coordinate = coordinate

    def get_location(self, payload):
        return self.coordinate


class LocationDependencyInjectionTests(unittest.TestCase):
    def test_fake_coordinate_is_used_instead_of_request_gps(self):
        payload = {
            "gps_location": {"lat": 51.4545, "lon": -2.5879},
            "ip_location": {"lat": 51.5072, "lon": -0.1276},
        }
        fake_location = {"lat": 31.2304, "lon": 121.4737}

        report = score_report(payload, FakeLocationProvider(fake_location))

        mismatch = next(signal for signal in report["signals"]
                        if signal["code"] == "GPS_IP_MISMATCH")
        self.assertEqual(mismatch["points"], 10)
        self.assertIn("km", mismatch["detail"])

    def test_default_provider_reads_http_payload(self):
        payload = {
            "gps_location": {"lat": 51.4545, "lon": -2.5879},
            "ip_location": {"lat": 51.4546, "lon": -2.5880},
        }

        report = score_report(payload)

        self.assertFalse(any(signal["code"] == "GPS_IP_MISMATCH"
                             for signal in report["signals"]))

    def test_fixed_provider_returns_a_copy(self):
        provider = FixedLocationProvider({"lat": 31.2304, "lon": 121.4737})
        point = provider.get_location({})
        point["lat"] = 0
        self.assertEqual(provider.get_location({})["lat"], 31.2304)

    def test_sequence_provider_replays_points_and_fails_when_exhausted(self):
        provider = SequenceLocationProvider([
            {"lat": 51.4545, "lon": -2.5879},
            {"lat": 51.5072, "lon": -0.1276},
        ])
        self.assertEqual(provider.get_location({})["lat"], 51.4545)
        self.assertEqual(provider.get_location({})["lat"], 51.5072)
        with self.assertRaises(IndexError):
            provider.get_location({})

    def test_scenario_provider_selects_the_named_virtual_coordinate(self):
        provider = ScenarioLocationProvider({
            "bristol": [{"lat": 51.4545, "lon": -2.5879}],
            "shanghai": [{"lat": 31.2304, "lon": 121.4737}],
        })
        report = score_report(
            {"scenario": "shanghai", "ip_location": {"lat": 51.4545, "lon": -2.5879}},
            provider,
        )
        self.assertTrue(any(signal["code"] == "GPS_IP_MISMATCH"
                            for signal in report["signals"]))

    def test_synthetic_teleport_scenario_triggers_speed_signal(self):
        report = score_report(get_scenario_payload("teleport"))
        self.assertTrue(any(signal["code"] == "IMPOSSIBLE_SPEED"
                            for signal in report["signals"]))

    def test_unknown_scenario_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown scenario"):
            get_scenario_payload("unknown")


if __name__ == "__main__":
    unittest.main()
