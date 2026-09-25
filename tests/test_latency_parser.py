import unittest

from validation.networking import (
    MeasurementError,
    parse_windows_latency,
)


def make_output(reply, received, latency_summary=""):
    return (
        "Pinging 192.0.2.10 with 64 bytes of data:\n"
        f"{reply}\n"
        "\nPing statistics for 192.0.2.10:\n"
        f"    Packets: Sent = 1, Received = {received}, "
        f"Lost = {1 - received} ({100 * (1 - received)}% loss),\n"
        f"{latency_summary}\n"
    )


class LatencyParserTests(unittest.TestCase):
    def test_submillisecond_reply_is_not_an_exact_sample(self):
        output = make_output(
            "Reply from 192.0.2.10: bytes=64 time<1ms TTL=64",
            1,
            "Minimum = 0ms, Maximum = 0ms, Average = 0ms",
        )

        result = parse_windows_latency(output, 1, 64)

        self.assertEqual(result["packets_received"], 1)
        self.assertEqual(result["submillisecond_reply_count"], 1)
        self.assertEqual(result["average_latency_ms"], 0)
        self.assertIn("whole milliseconds", result["latency_source"])

    def test_no_replies_has_no_latency(self):
        output = make_output("Request timed out.", 0)

        result = parse_windows_latency(output, 1, 64)

        self.assertEqual(result["packet_loss_percent"], 100)
        self.assertIsNone(result["minimum_latency_ms"])
        self.assertIsNone(result["average_latency_ms"])
        self.assertIsNone(result["maximum_latency_ms"])

    def test_missing_latency_summary_is_rejected(self):
        output = make_output(
            "Reply from 192.0.2.10: bytes=64 time=5ms TTL=64",
            1,
        )

        with self.assertRaises(MeasurementError):
            parse_windows_latency(output, 1, 64)

    def test_wrong_payload_is_rejected(self):
        output = make_output(
            "Reply from 192.0.2.10: bytes=32 time=5ms TTL=64",
            1,
            "Minimum = 5ms, Maximum = 5ms, Average = 5ms",
        )

        with self.assertRaises(MeasurementError):
            parse_windows_latency(output, 1, 64)


if __name__ == "__main__":
    unittest.main()