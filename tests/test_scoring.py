import unittest

from server import score_report


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


if __name__ == "__main__":
    unittest.main()
