import argparse
import json
import logging
from pathlib import Path

from validation.config import ConfigError, load_config
from validation.connectivity import test_connectivity
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

    result = test_connectivity(config)

    print("\nNETWORK DEVICE VALIDATION")
    print(f"DUT: {config['dut']['name']} ({result.dut_host})")
    print(f"{result.test_id} {result.test_name}: {result.status.value}")

    for diagnostic in result.diagnostics:
        print(f"  {diagnostic}")

    print("\nStructured result:")
    print(json.dumps(result.to_dict(), indent=2, allow_nan=False))

    logger.info("Validation run completed: %s", result.status.value)

    if result.status == Status.ERROR:
        return 2
    if result.status == Status.FAIL:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())