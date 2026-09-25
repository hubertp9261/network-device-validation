import logging
from time import perf_counter

from validation.networking import (
    MeasurementError,
    parse_windows_ping,
    run_windows_ping,
)
from validation.result import Status, TestResult


logger = logging.getLogger(__name__)


def test_connectivity(config):
    host = config["dut"]["host"]
    count = config["connectivity"]["packet_count"]
    maximum_loss = config["connectivity"]["max_packet_loss_percent"]
    reply_timeout_ms = 2000

    started = perf_counter()
    measurement = {}
    diagnostics = []

    logger.info("NET-001 started: host=%s", host)

    try:
        completed = run_windows_ping(host, count, reply_timeout_ms)

        diagnostics.append(
            f"Ping process exit code: {completed.returncode}"
        )

        if completed.stderr.strip():
            diagnostics.append(
                f"Ping stderr: {completed.stderr.strip()}"
            )

        measurement = parse_windows_ping(
            completed.stdout,
            expected_count=count,
        )

        has_reply = measurement["packets_received"] > 0
        loss_ok = measurement["packet_loss_percent"] <= maximum_loss

        status = Status.PASS if has_reply and loss_ok else Status.FAIL

        if not has_reply:
            diagnostics.append("No successful echo replies from the DUT.")

        if not loss_ok:
            diagnostics.append(
                f"Packet loss {measurement['packet_loss_percent']:.2f}% "
                f"exceeds allowed {maximum_loss:.2f}%."
            )

    except MeasurementError as exc:
        status = Status.ERROR
        diagnostics.append(str(exc))
        logger.error("NET-001 measurement error: %s", exc)

    result = TestResult(
        test_id="NET-001",
        test_name="IPv4 connectivity",
        dut_host=host,
        status=status,
        configuration={
            "packet_count": count,
            "reply_timeout_ms": reply_timeout_ms,
            "ip_version": 4,
            "payload_bytes": 32,
        },
        requirement={
            "minimum_echo_replies": 1,
            "max_packet_loss_percent": maximum_loss,
        },
        measurement=measurement,
        duration_seconds=perf_counter() - started,
        diagnostics=diagnostics,
    )

    logger.info(
        "NET-001 completed: status=%s duration=%.2fs measurement=%s",
        result.status.value,
        result.duration_seconds,
        result.measurement,
    )
    return result