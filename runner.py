import argparse
import logging
from pathlib import Path

from validation.config import ConfigError, load_config
from validation.logging_setup import configure_logging


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

    log_path = PROJECT_ROOT / "logs" / "validation.log"
    configure_logging(log_path)

    logger.info("Setup check started")

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        logger.error("Configuration rejected: %s", exc)
        return 2

    logger.info(
        "Configuration accepted for DUT %s (%s)",
        config["dut"]["name"],
        config["dut"]["host"],
    )
    logger.info("Setup check complete. No network tests were executed.")
    logger.info("Log file: %s", log_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())