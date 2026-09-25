import json
from pathlib import Path

from validation.config import load_config
from validation.logging_setup import configure_logging
from validation.networking import (
    MeasurementError,
    parse_windows_latency,
    run_windows_ping,
)


PROJECT_ROOT = Path(__file__).resolve().parent


def main():
    configure_logging(PROJECT_ROOT / "logs" / "validation.log")
    config = load_config(PROJECT_ROOT / "config" / "test_config.json")
    settings = config["latency"]
    rows = []

    print("Baseline collection only: no latency PASS/FAIL assessment.")

    for size in settings["packet_sizes"]:
        print(f"\nMeasuring {size}-byte payload...", flush=True)

        try:
            completed = run_windows_ping(
                host=config["dut"]["host"],
                packet_count=settings["packet_count"],
                payload_bytes=size,
            )

            measurement = parse_windows_latency(
                completed.stdout,
                expected_count=settings["packet_count"],
                expected_payload_bytes=size,
            )

        except MeasurementError as exc:
            print(f"Measurement error for {size} bytes: {exc}")
            return 2

        rows.append(measurement)
        print(json.dumps(measurement, indent=2, allow_nan=False))

    print("\nBASELINE SUMMARY — reported round-trip times")
    print(
        f"{'Payload B':>9} {'Replies':>9} {'Loss %':>8} "
        f"{'Min ms':>8} {'Avg ms':>8} {'Max ms':>8}"
    )

    for row in rows:
        replies = (
            f"{row['packets_received']}/{row['packets_transmitted']}"
        )
        minimum = row["minimum_latency_ms"]
        average = row["average_latency_ms"]
        maximum = row["maximum_latency_ms"]

        print(
            f"{row['payload_bytes']:>9} "
            f"{replies:>9} "
            f"{row['packet_loss_percent']:>8.1f} "
            f"{str(minimum) if minimum is not None else 'N/A':>8} "
            f"{str(average) if average is not None else 'N/A':>8} "
            f"{str(maximum) if maximum is not None else 'N/A':>8}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())