# Python-Automated Network Device Validation Lab

A Python command-line lab that validates a Raspberry Pi's network connectivity, packet loss, latency, and TCP service availability against configurable requirements.

The project applies a product-verification workflow to a small physical testbed: define requirements, configure stimulus, collect measurements, compare expected and actual behavior, and report actionable results. A Windows laptop acts as the test controller and a Linux Raspberry Pi acts as the device under test (DUT).

**Implemented:** seven live test cases, structured results, execution logs, and 20 automated framework tests. The implementation uses only the Python standard library.

## Test environment

```text
Windows laptop                    Local wireless network              Raspberry Pi
Python test controller  <-- Wi-Fi -->  Access point  <-- Wi-Fi -->  Linux DUT
        |                                                              |
        |                                                    ICMP echo / TCP 22
        v
Configuration -> Measurement -> Requirement comparison -> PASS / FAIL / ERROR
                                                        |
                                                        +-- Console summary
                                                        +-- JSON on console
                                                        +-- Execution log
```

Development and live verification used Windows Python 3.11.7 and a Raspberry Pi 3 Model B running Linux. The current suite runs in native Windows Python; WSL and iperf3 are not required.

## What the suite verifies

| Test | Stimulus and measurements | Acceptance criteria |
|---|---|---|
| NET-001: IPv4 connectivity | 20 ping requests with a 32-byte payload; successful echo replies and packet loss | At least one reply and loss at or below the configured maximum |
| NET-002: Parameterized latency | 20 requests per payload size: 64, 256, 512, 1024, and 1400 bytes; minimum, average, maximum RTT and loss | At least one reply, average RTT at or below the configured limit, and loss at or below the configured maximum |
| NET-004: TCP service availability | Connect to the configured port, defaulting to SSH port 22; record connection establishment time | A TCP connection is established using the configured socket timeout |

The default run produces **seven results**: one connectivity result, five latency results, and one TCP service result. NET-003 is reserved for a possible future throughput test.

TCP availability does not establish that SSH authentication works. Connection establishment time is also distinct from ping round-trip time.

## Quick start

### Prerequisites

- A Windows controller with Python 3.11 or later recommended; tested with 3.11.7.
- English-language Windows `ping.exe` output. The parser currently supports IPv4 only.
- A reachable DUT that responds to ICMP echo requests and has the intended TCP service listening.
- Git to clone the repository.

The live tests require no Python agent or project files on the Pi. Wireless client isolation or firewall rules can affect reachability even when both devices use the same Wi-Fi network.

### Set up the controller

Run in PowerShell:

```powershell
git clone https://github.com/hubertp9261/network-device-validation.git
cd network-device-validation
py -3 -m venv .venv
.\.venv\Scripts\python.exe --version
```

No third-party packages need to be installed. Calling the environment's Python directly avoids needing to activate it.

### Configure your DUT

Edit `config/test_config.json`. Replace `dut.host` with your Pi's current local IPv4 address; the repository's development address is not portable to another network.

Example configuration:

```json
{
  "dut": {
    "name": "raspberry-pi",
    "host": "192.0.2.10",
    "ssh_port": 22
  },
  "connectivity": {
    "packet_count": 20,
    "max_packet_loss_percent": 0
  },
  "latency": {
    "packet_count": 20,
    "packet_sizes": [64, 256, 512, 1024, 1400],
    "max_average_latency_ms": 50,
    "max_packet_loss_percent": 0
  },
  "connection_timeout_seconds": 3
}
```

`192.0.2.10` is a documentation example, not a working DUT address. Do not add passwords or SSH keys to the configuration; the suite does not need them.

Configuration validation rejects missing fields, invalid numeric ranges, duplicate payload sizes, and booleans used as numeric settings. Payload sizes represent ICMP data bytes, not total IP or Wi-Fi frame sizes.

The TCP timeout is configurable. Ping uses a separate two-second reply timeout and a bounded overall process timeout. With hostnames, DNS resolution and multiple connection attempts can extend total TCP test duration beyond the individual socket timeout; a numeric IPv4 address is recommended for this lab.

### Run the suite

```powershell
.\.venv\Scripts\python.exe runner.py
$LASTEXITCODE
```

A responsive default run takes approximately two minutes and sends 120 ping requests. Run without simultaneous throughput traffic when collecting an unloaded baseline.

To use another configuration:

```powershell
.\.venv\Scripts\python.exe runner.py --config path\to\your_config.json
```

## Results and diagnostics

| Outcome | Meaning | Runner exit code |
|---|---|---:|
| PASS | Every executed case meets its requirements | 0 |
| FAIL | At least one case violates a requirement, with no errors | 1 |
| ERROR | A configuration or measurement error prevents a valid assessment | 2 |

Errors take precedence in the overall status, while individual failures remain visible. A refused or timed-out TCP connection is an availability failure; address-resolution or unexpected socket errors are reported as errors.

Each test result includes its ID, DUT host, settings, requirements, measurements, status, diagnostics, duration, and UTC recording timestamp.

The runner prints a readable summary followed by structured JSON. **The entire console stream is not a standalone JSON document**, and report files are not automatically exported. Logs are appended to `logs/validation.log`; log timestamps use local time.

Example summary from a successful live run, with device details omitted:

```text
NET-001 IPv4 connectivity: PASS
NET-002 IPv4 latency (64-byte payload): PASS
NET-002 IPv4 latency (256-byte payload): PASS
NET-002 IPv4 latency (512-byte payload): PASS
NET-002 IPv4 latency (1024-byte payload): PASS
NET-002 IPv4 latency (1400-byte payload): PASS
NET-004 TCP service availability (SSH, port 22): PASS

Passed: 7 | Failed: 0 | Errors: 0 | Total: 7
Overall: PASS
```

## Measurement methodology and limitations

The initial baseline used 20 requests per payload size. Reported average RTTs were 15, 18, 16, 15, and 14 ms respectively, with no lost replies. A **provisional 50 ms average-RTT limit and 0% loss limit** were then selected for subsequent validation runs. These are lab criteria, not manufacturer specifications or statistically established service guarantees.

- Averages are assessed separately for each payload size. Maximum RTT is recorded but has no acceptance limit.
- With 20 requests, packet loss changes in increments of 5%. Zero observed loss does not establish a zero long-term loss rate.
- Windows reports whole-millisecond summary statistics. A reported `0 ms` is not proof of instantaneous delivery; `time<1ms` replies are counted separately.
- Latency statistics cover successful replies only. Runs with no replies retain unavailable latency as JSON `null` and fail the reachability requirement.
- The parser counts recognizable successful echo replies from the target rather than treating every received ICMP message as success. It rejects missing summaries and certain inconsistent outputs, but is not a general parser for every locale or ping variant.
- Results characterize the controller, wireless path, access point, and DUT together. They do not isolate Pi hardware performance or validate optical networking equipment.

An early setup check used Tailscale addresses. Interface and route inspection identified that path, after which local Wi-Fi addresses were used for the reported lab measurements. Verifying the traffic path was part of establishing a valid test environment.

For baseline collection without assigning latency PASS/FAIL:

```powershell
.\.venv\Scripts\python.exe check_payloads.py
```

The baseline helper accepts `max_average_latency_ms: null`; the main latency assessment reports an error until a numeric requirement is provided. Fix criteria before validation runs and investigate failures rather than adjusting thresholds simply to obtain a pass.

## Test the framework

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The current suite contains **20 test methods** covering connectivity decisions, latency boundaries, parser edge cases, TCP failure classification, and connection cleanup. Mocked network operations keep these tests independent of the Pi. Deliberately simulated error cases may emit error logs while the test suite still finishes with `OK`.

The 20 framework tests are distinct from the seven live network results. Additional manual check scripts exercise individual components and synthetic parser cases.

## Repository layout

```text
config/test_config.json     DUT settings and acceptance criteria
validation/config.py       Configuration loading and validation
validation/networking.py   Windows ping execution and parsing
validation/connectivity.py Connectivity assessment
validation/latency.py      Parameterized latency assessment
validation/services.py     TCP availability assessment
validation/result.py       Shared result model and status definitions
validation/logging_setup.py Console and file logging
tests/                     Automated framework tests
runner.py                  Sequential suite execution and reporting
check_*.py                 Manual development and baseline checks
```

Virtual environments, Python caches, logs, results, and `.env` are ignored by Git. Review generated output before sharing it because it can contain device addresses and local paths.

## Possible extensions

- Integrate iperf3 JSON throughput measurements. iperf3 was manually exercised during setup but is not part of the automated suite.
- Add a recorded, controlled failure-and-recovery demonstration.
- Export standalone JSON reports and compare repeated runs.
- Support additional ping locales or controller operating systems.

The current project deliberately remains a small command-line validation lab without a dashboard, database, or cloud deployment.
