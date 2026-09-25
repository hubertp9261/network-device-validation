from pathlib import Path

from validation.config import load_config
from validation.logging_setup import configure_logging
from validation.networking import parse_windows_ping, run_windows_ping


PROJECT_ROOT = Path(__file__).resolve().parent


def main():
    configure_logging(PROJECT_ROOT / "logs" / "validation.log")
    config = load_config(PROJECT_ROOT / "config" / "test_config.json")

    completed = run_windows_ping(
        host=config["dut"]["host"],
        packet_count=config["connectivity"]["packet_count"],
    )

    print(f"\nPing process exit code: {completed.returncode}")
    print("\n--- Standard output ---")
    print(completed.stdout)

    measurement = parse_windows_ping(
        completed.stdout,
        expected_count=config["connectivity"]["packet_count"],
    )

    print("\n--- Parsed measurement ---")
    for name, value in measurement.items():
        print(f"{name}: {value}")

    if completed.stderr:
        print("\n--- Standard error ---")
        print(completed.stderr)


if __name__ == "__main__":
    main()