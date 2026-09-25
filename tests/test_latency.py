import unittest
from subprocess import CompletedProcess
from unittest.mock import patch

from validation.latency import test_latency
from validation.networking import MeasurementError
from validation.result import Status


class LatencyDecisionTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "dut": {"name": "synthetic-dut", "host": "192.0.2.10"},
            "latency": {
                "packet_count": 20,
                "packet_sizes": [64],
                "max_average_latency_ms": 50,
                "max_packet_loss_percent": 0,
            },
        }

    def assess(self, average=20, received=20, maximum=90):
        measurement = {
            "packets_transmitted": 20,
            "packets_received": received,
            "packets_lost": 20 - received,
            "packet_loss_percent": (20 - received) / 20 * 100,
            "minimum_latency_ms": 5 if received else None,
            "average_latency_ms": average,
            "maximum_latency_ms": maximum if received else None,
            "payload_bytes": 64,
        }

        completed = CompletedProcess(
            args=["ping.exe"],
            returncode=0,
            stdout="Synthetic output",
            stderr="",
        )

        with patch(
            "validation.latency.run_windows_ping",
            return_value=completed,
        ), patch(
            "validation.latency.parse_windows_latency",
            return_value=measurement,
        ):
            return test_latency(self.config, 64)

    def test_average_below_limit_passes_despite_high_maximum(self):
        result = self.assess(average=20, maximum=90)
        self.assertEqual(result.status, Status.PASS)

    def test_average_equal_to_limit_passes(self):
        result = self.assess(average=50)
        self.assertEqual(result.status, Status.PASS)

    def test_average_above_limit_fails(self):
        result = self.assess(average=51)
        self.assertEqual(result.status, Status.FAIL)
        self.assertTrue(
            any("Average RTT" in text for text in result.diagnostics)
        )

    def test_packet_loss_fails_even_with_low_latency(self):
        result = self.assess(average=10, received=19)
        self.assertEqual(result.status, Status.FAIL)
        self.assertEqual(result.measurement["packet_loss_percent"], 5)

    def test_no_replies_fails_even_when_loss_is_allowed(self):
        self.config["latency"]["max_packet_loss_percent"] = 100
        result = self.assess(average=None, received=0)
        self.assertEqual(result.status, Status.FAIL)

    def test_missing_threshold_is_error_without_sending_ping(self):
        self.config["latency"]["max_average_latency_ms"] = None

        with patch("validation.latency.run_windows_ping") as ping:
            result = test_latency(self.config, 64)

        self.assertEqual(result.status, Status.ERROR)
        self.assertEqual(result.measurement, {})
        ping.assert_not_called()

    def test_measurement_failure_is_error(self):
        with patch(
            "validation.latency.run_windows_ping",
            side_effect=MeasurementError("Synthetic tool failure"),
        ):
            result = test_latency(self.config, 64)

        self.assertEqual(result.status, Status.ERROR)
        self.assertEqual(result.measurement, {})
        self.assertIn("Synthetic tool failure", result.diagnostics)


if __name__ == "__main__":
    unittest.main()