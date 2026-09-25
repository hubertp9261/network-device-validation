import logging
import subprocess
import sys
import ipaddress
import re

logger = logging.getLogger(__name__)


class MeasurementError(RuntimeError):
    """A measurement could not be completed reliably."""


def run_windows_ping(host, packet_count, reply_timeout_ms=2000):
    if sys.platform != "win32":
        raise MeasurementError(
            "This ping implementation requires Windows Python."
        )

    command = [
        "ping.exe",
        "-4",
        "-n", str(packet_count),
        "-w", str(reply_timeout_ms),
        host,
    ]

    # Allow for each reply timeout, packet spacing, and startup overhead.
    process_timeout = (
        packet_count * (reply_timeout_ms / 1000 + 1) + 10
    )

    logger.info(
        "Running ping: host=%s count=%s reply_timeout_ms=%s",
        host,
        packet_count,
        reply_timeout_ms,
    )

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=process_timeout,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise MeasurementError(
            f"Ping did not finish within {process_timeout:.0f} seconds"
        ) from exc
    except OSError as exc:
        raise MeasurementError(f"Could not launch ping: {exc}") from exc

    logger.info("Ping process finished: exit_code=%s", completed.returncode)
    return completed

def parse_windows_ping(output, expected_count):
    target_match = re.search(
        r"^Ping statistics for ([0-9.]+):\s*$",
        output,
        re.MULTILINE,
    )
    summary_match = re.search(
        r"Packets: Sent = (\d+), Received = (\d+), Lost = (\d+)",
        output,
    )

    if target_match is None or summary_match is None:
        raise MeasurementError(
            "Missing Windows IPv4 ping summary. "
            "Expected complete English-language output."
        )

    try:
        target = str(ipaddress.IPv4Address(target_match.group(1)))
    except ipaddress.AddressValueError as exc:
        raise MeasurementError("Invalid target IP in ping output") from exc

    sent, windows_received, windows_lost = map(
        int, summary_match.groups()
    )

    if (
        sent != expected_count
        or sent <= 0
        or windows_received + windows_lost != sent
    ):
        raise MeasurementError("Ping packet counts are inconsistent")

    reply_pattern = re.compile(
        rf"^Reply from {re.escape(target)}: "
        r"bytes=\d+ time[=<]\d+ms TTL=\d+\s*$",
        re.MULTILINE,
    )
    echo_replies = len(reply_pattern.findall(output))

    if echo_replies > windows_received:
        raise MeasurementError(
            "Echo reply count exceeds the Windows received count"
        )

    unsuccessful = sent - echo_replies

    return {
        "target_ip": target,
        "packets_transmitted": sent,
        "packets_received": echo_replies,
        "packets_lost": unsuccessful,
        "packet_loss_percent": unsuccessful / sent * 100,
        "windows_reported_received": windows_received,
    }