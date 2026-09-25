import json
from pathlib import Path

from validation.config import load_config
from validation.latency import test_latency
from validation.logging_setup import configure_logging
from validation.result import Status


PROJECT_ROOT = Path(__file__).resolve().parent


def main():
    configure_logging(PROJECT_ROOT / "logs" / "validation.log")
    config = load_config(PROJECT_ROOT / "config" / "test_config.json")

    results = [
        test_latency(config, size)
        for size in config["latency"]["packet_sizes"]
    ]

    print("\nLATENCY VALIDATION RESULTS")
    for result in results:
        print(f"{result.test_name}: {result.status.value}")
        for diagnostic in result.diagnostics:
            print(f"  {diagnostic}")

    print("\nStructured results:")
    print(json.dumps(
        [result.to_dict() for result in results],
        indent=2,
        allow_nan=False,
    ))

    if any(result.status == Status.ERROR for result in results):
        return 2
    if any(result.status == Status.FAIL for result in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())