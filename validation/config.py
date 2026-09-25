import json
from pathlib import Path


class ConfigError(ValueError):
    """The configuration could not be loaded or contains invalid settings."""


def require_object(parent, key):
    value = parent.get(key)
    if not isinstance(value, dict):
        raise ConfigError(f"{key} must be a JSON object")
    return value


def require_number(parent, key, minimum, maximum, *, integer=False):
    value = parent.get(key)
    allowed_types = (int,) if integer else (int, float)

    # Exact types deliberately exclude True and False.
    if type(value) not in allowed_types:
        kind = "an integer" if integer else "a number"
        raise ConfigError(f"{key} must be {kind}")

    if not minimum <= value <= maximum:
        raise ConfigError(
            f"{key} must be between {minimum} and {maximum}"
        )


def load_config(path):
    path = Path(path)

    try:
        with path.open(encoding="utf-8-sig") as file:
            config = json.load(file)
    except (OSError, UnicodeError, ValueError) as exc:
        raise ConfigError(f"Could not load {path}: {exc}") from exc

    if not isinstance(config, dict):
        raise ConfigError("The configuration must be a JSON object")

    dut = require_object(config, "dut")
    connectivity = require_object(config, "connectivity")

    for key in ("name", "host"):
        value = dut.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ConfigError(f"dut.{key} must be a nonempty string")
        dut[key] = value.strip()

    require_number(dut, "ssh_port", 1, 65535, integer=True)
    require_number(
        connectivity, "packet_count", 1, 1000, integer=True
    )
    require_number(
        connectivity, "max_packet_loss_percent", 0, 100
    )
    require_number(config, "connection_timeout_seconds", 0.1, 60)

    return config