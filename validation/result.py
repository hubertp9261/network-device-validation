from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum


class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"


@dataclass
class TestResult:
    test_id: str
    test_name: str
    dut_host: str
    status: Status
    configuration: dict
    requirement: dict
    measurement: dict
    duration_seconds: float
    diagnostics: list[str] = field(default_factory=list)
    recorded_at_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self):
        result = asdict(self)
        result["status"] = self.status.value
        return result