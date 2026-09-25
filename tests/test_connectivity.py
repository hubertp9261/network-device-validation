import unittest
from subprocess import CompletedProcess
from unittest.mock import patch

from validation.connectivity import test_connectivity
from validation.networking import MeasurementError
from validation.result import Status


def make_ping_output(replies):
    lines = [
        "Pinging 192.0.2.10 with 32 bytes of data:"
    ]

    for _ in range(replies):
        lines.append(
            "Reply from 192.0.2.10: bytes=32 time=5ms TTL=64"
        )

    for _ in range(2 - replies):
        lines.append("Request timed out.")

    lines.extend([
        "",
        "Ping statistics for 192.0.2.10:",
        (
            f"    Packets: Sent = 2, Received = {replies}, "
            f"Lost = {2 - replies} ({(2 - replies) * 50}% loss),"
        ),
    ])
    return "\n".join(lines)


class ConnectivityDecisionTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "dut": {"name": "synthetic-dut", "host": "192.0.2.10"},
            "connectivity": {
                "packet_count": 2,
                "max_packet_loss_percent": 0,
            },
        }

    def run_with_output(self, output):
        completed = CompletedProcess(
            args=["ping.exe"],
            returncode=0,
            stdout=output,
            stderr="",
        )

        with patch(
            "validation.connectivity.run_windows_ping",
            return_value=completed,
        ):
            return test_connectivity(self.config)

    def test_all_replies_pass(self):
        result = self.run_with_output(make_ping_output(2))

        self.assertEqual(result.status, Status.PASS)
        self.assertEqual(result.measurement["packet_loss_percent"], 0)

    def test_loss_above_limit_fails(self):
        result = self.run_with_output(make_ping_output(1))

        self.assertEqual(result.status, Status.FAIL)
        self.assertEqual(result.measurement["packet_loss_percent"], 50)
        self.assertTrue(
            any("exceeds allowed" in text for text in result.diagnostics)
        )

    def test_loss_equal_to_limit_passes(self):
        self.config["connectivity"]["max_packet_loss_percent"] = 50
        result = self.run_with_output(make_ping_output(1))

        self.assertEqual(result.status, Status.PASS)

    def test_no_replies_fails_even_when_all_loss_is_allowed(self):
        self.config["connectivity"]["max_packet_loss_percent"] = 100
        result = self.run_with_output(make_ping_output(0))

        self.assertEqual(result.status, Status.FAIL)
        self.assertEqual(result.measurement["packets_received"], 0)

    def test_unreadable_output_is_error(self):
        result = self.run_with_output("Unsupported output")

        self.assertEqual(result.status, Status.ERROR)
        self.assertEqual(result.measurement, {})
        self.assertTrue(result.diagnostics)

    def test_tool_failure_is_error(self):
        with patch(
            "validation.connectivity.run_windows_ping",
            side_effect=MeasurementError("Synthetic tool failure"),
        ):
            result = test_connectivity(self.config)

        self.assertEqual(result.status, Status.ERROR)
        self.assertIn("Synthetic tool failure", result.diagnostics)


if __name__ == "__main__":
    unittest.main()