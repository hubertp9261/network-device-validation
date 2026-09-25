import logging
from time import perf_counter

from validation.networking import (
    MeasurementError,
    parse_windows_latency,
    run_windows_ping,
)
from validation.result import Status, TestResult


logger = logging.getLogger(__name__)


def test_latency(config, payload_bytes):
    settings = config["latency"]
    host = config["dut"]["host"]
    count = settings["packet_count"]
    maximum_average = settings["max_average_latency_ms"]
    maximum_loss = settings["max_packet_loss_percent"]
    reply_timeout_ms = 2000

    started = perf_counter()
    measurement = {}
    diagnostics = []

    logger.info("NET-002 started: payload_bytes=%s", payload_bytes)

    try:
        if maximum_average is None:
            raise MeasurementError(
                "Latency assessment requires max_average_latency_ms. "
                "Use check_payloads.py for baseline collection."
            )

        completed = run_windows_ping(
            host,
            count,
            reply_timeout_ms=reply_timeout_ms,
            payload_bytes=payload_bytes,
        )

        diagnostics.append(
            f"Ping process exit code: {completed.returncode}"
        )
        if completed.stderr.strip():
            diagnostics.append(
                f"Ping stderr: {completed.stderr.strip()}"
            )

        measurement = parse_windows_latency(
            completed.stdout,
            expected_count=count,
            expected_payload_bytes=payload_bytes,
        )

        failures = []
        average = measurement["average_latency_ms"]
        loss = measurement["packet_loss_percent"]

        if measurement["packets_received"] == 0:
            failures.append("No echo replies; latency is unavailable.")
        elif average > maximum_average:
            failures.append(
                f"Average RTT {average} ms exceeds "
                f"allowed {maximum_average} ms."
            )

        if loss > maximum_loss:
            failures.append(
                f"Packet loss {loss:.2f}% exceeds "
                f"allowed {maximum_loss:.2f}%."
            )

        diagnostics.extend(failures)
        status = Status.FAIL if failures else Status.PASS

    except MeasurementError as exc:
        status = Status.ERROR
        diagnostics.append(str(exc))
        logger.error("NET-002 measurement/setup error: %s", exc)

    result = TestResult(
        test_id="NET-002",
        test_name=f"IPv4 latency ({payload_bytes}-byte payload)",
        dut_host=host,
        status=status,
        configuration={
            "packet_count": count,
            "payload_bytes": payload_bytes,
            "reply_timeout_ms": reply_timeout_ms,
            "ip_version": 4,
        },
        requirement={
            "minimum_echo_replies": 1,
            "max_average_latency_ms": maximum_average,
            "max_packet_loss_percent": maximum_loss,
        },
        measurement=measurement,
        duration_seconds=perf_counter() - started,
        diagnostics=diagnostics,
    )

    logger.info(
        "NET-002 completed: payload_bytes=%s status=%s measurement=%s",
        payload_bytes,
        result.status.value,
        result.measurement,
    )
    return result