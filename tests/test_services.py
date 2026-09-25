import socket
import unittest
from unittest.mock import patch

from validation.result import Status
from validation.services import test_tcp_service


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "dut": {"host": "192.0.2.10"},
            "connection_timeout_seconds": 3,
        }

    def test_success_passes_and_closes_connection(self):
        with patch(
            "validation.services.socket.create_connection"
        ) as connect:
            result = test_tcp_service(self.config, "SSH", 22)

        self.assertEqual(result.status, Status.PASS)
        self.assertTrue(result.measurement["tcp_connection_established"])
        connect.assert_called_once_with(
            ("192.0.2.10", 22), timeout=3
        )
        connect.return_value.__exit__.assert_called_once()

    def test_refusal_and_timeout_fail(self):
        for error in (ConnectionRefusedError(), TimeoutError()):
            with self.subTest(error=type(error).__name__):
                with patch(
                    "validation.services.socket.create_connection",
                    side_effect=error,
                ):
                    result = test_tcp_service(self.config, "SSH", 22)

                self.assertEqual(result.status, Status.FAIL)
                self.assertFalse(
                    result.measurement["tcp_connection_established"]
                )
                self.assertTrue(result.diagnostics)

    def test_resolution_and_unexpected_errors_are_errors(self):
        for error in (
            socket.gaierror("Synthetic resolution failure"),
            OSError("Synthetic unexpected socket failure"),
        ):
            with self.subTest(error=type(error).__name__):
                with patch(
                    "validation.services.socket.create_connection",
                    side_effect=error,
                ):
                    result = test_tcp_service(self.config, "SSH", 22)

                self.assertEqual(result.status, Status.ERROR)
                self.assertEqual(result.measurement, {})
                self.assertTrue(result.diagnostics)


if __name__ == "__main__":
    unittest.main()