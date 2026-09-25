from validation.networking import MeasurementError, parse_windows_ping


# Synthetic fixture: an error response is not a successful echo reply.
unreachable_output = """\
Pinging 192.0.2.10 with 32 bytes of data:
Reply from 192.0.2.1: Destination host unreachable.

Ping statistics for 192.0.2.10:
    Packets: Sent = 1, Received = 1, Lost = 0 (0% loss),
"""

measurement = parse_windows_ping(unreachable_output, expected_count=1)

assert measurement["packets_received"] == 0
assert measurement["packet_loss_percent"] == 100.0
print("PASS: unreachable response does not count as an echo reply")

try:
    parse_windows_ping("Incomplete or unsupported output", expected_count=1)
except MeasurementError:
    print("PASS: unrecognized output is rejected")
else:
    raise AssertionError("Unrecognized output should have been rejected")