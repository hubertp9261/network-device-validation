import errno
import logging
import socket
from time import perf_counter

from validation.result import Status, TestResult


logger = logging.getLogger(__name__)


def test_tcp_service(config, service_name, port):
    host = config["dut"]["host"]
    timeout = config["connection_timeout_seconds"]
    started = perf_counter()
    measurement = {}
    diagnostics = []

    logger.info(
        "NET-004 started: service=%s host=%s port=%s timeout=%ss",
        service_name, host, port, timeout,
    )

    try:
        with socket.create_connection((host, port), timeout=timeout):
            measurement = {
                "tcp_connection_established": True,
                "connection_setup_ms": (perf_counter() - started) * 1000,
            }

        status = Status.PASS

    except ConnectionRefusedError:
        status = Status.FAIL
        measurement = {"tcp_connection_established": False}
        diagnostics.append(
            "Connection refused: no accepting listener, "
            "or the connection was actively rejected."
        )

    except TimeoutError:
        status = Status.FAIL
        measurement = {"tcp_connection_established": False}
        diagnostics.append(
            f"Connection attempt timed out after approximately {timeout}s. "
            "Possible causes include filtering or an unreachable device."
        )

    except socket.gaierror as exc:
        status = Status.ERROR
        diagnostics.append(f"Address resolution failed: {exc}")

    except OSError as exc:
        unreachable_codes = {
            errno.ENETUNREACH,
            errno.EHOSTUNREACH,
            10051,  # Windows: network unreachable
            10065,  # Windows: host unreachable
        }

        if (
            exc.errno in unreachable_codes
            or getattr(exc, "winerror", None) in unreachable_codes
        ):
            status = Status.FAIL
            measurement = {"tcp_connection_established": False}
            diagnostics.append(f"Network path unavailable: {exc}")
        else:
            status = Status.ERROR
            diagnostics.append(f"Socket operation failed: {exc}")

    result = TestResult(
        test_id="NET-004",
        test_name=f"TCP service availability ({service_name}, port {port})",
        dut_host=host,
        status=status,
        configuration={
            "port": port,
            "connection_timeout_seconds": timeout,
        },
        requirement={"tcp_connection_established": True},
        measurement=measurement,
        duration_seconds=perf_counter() - started,
        diagnostics=diagnostics,
    )

    logger.info(
        "NET-004 completed: service=%s status=%s diagnostics=%s",
        service_name, status.value, diagnostics,
    )
    return result