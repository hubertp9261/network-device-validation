import argparse
import json
import logging
from pathlib import Path

from validation.config import ConfigError, load_config
from validation.connectivity import test_connectivity
from validation.latency import test_latency
from validation.logging_setup import configure_logging
from validation.result import Status


PROJECT_ROOT = Path(__file__).resolve().parent
logger = logging.getLogger("validation.runner")


def main():
    parser = argparse.ArgumentParser(
        description="Network device validation lab"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "config" / "test_config.json",
        help="Path to a configuration JSON file",
    )
    args = parser.parse_args()

    configure_logging(PROJECT_ROOT / "logs" / "validation.log")
    logger.info("Validation run started")

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        logger.error("Configuration rejected: %s", exc)
        return 2

    results = [test_connectivity(config)]

    for size in config["latency"]["packet_sizes"]:
        results.append(test_latency(config, size))

    counts = {
        status: sum(result.status == status for result in results)
        for status in Status
    }

    if counts[Status.ERROR]:
        overall = Status.ERROR
        exit_code = 2
    elif counts[Status.FAIL]:
        overall = Status.FAIL
        exit_code = 1
    else:
        overall = Status.PASS
        exit_code = 0

    print("\nNETWORK DEVICE VALIDATION")
    print(f"DUT: {config['dut']['name']} ({config['dut']['host']})")

    for result in results:
        print(
            f"{result.test_id} {result.test_name}: "
            f"{result.status.value}"
        )

        if result.status != Status.PASS:
            for diagnostic in result.diagnostics:
                print(f"  {diagnostic}")

    print(
        f"\nPassed: {counts[Status.PASS]} | "
        f"Failed: {counts[Status.FAIL]} | "
        f"Errors: {counts[Status.ERROR]} | "
        f"Total: {len(results)}"
    )
    print(f"Overall: {overall.value}")

    report = {
        "dut": config["dut"],
        "overall_status": overall.value,
        "counts": {
            status.value: counts[status]
            for status in Status
        },
        "results": [result.to_dict() for result in results],
    }

    print("\nStructured results:")
    print(json.dumps(report, indent=2, allow_nan=False))

    logger.info(
        "Validation run completed: overall=%s passed=%s failed=%s errors=%s",
        overall.value,
        counts[Status.PASS],
        counts[Status.FAIL],
        counts[Status.ERROR],
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())