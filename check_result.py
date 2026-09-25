import json

from validation.result import Status, TestResult


def demonstrate_result():
    results = []

    for loss_percent in (0.0, 5.0):
        maximum_loss = 0.0
        status = (
            Status.PASS
            if loss_percent <= maximum_loss
            else Status.FAIL
        )

        result = TestResult(
            test_id="DEMO-001",
            test_name="SIMULATED connectivity",
            dut_host="example.invalid",
            status=status,
            configuration={"packet_count": 20},
            requirement={"max_packet_loss_percent": maximum_loss},
            measurement={"packet_loss_percent": loss_percent},
            duration_seconds=0.0,
            diagnostics=[
                "Synthetic data: no network traffic was sent."
            ],
        )
        results.append(result.to_dict())

    print(json.dumps(results, indent=2, allow_nan=False))


if __name__ == "__main__":
    demonstrate_result()