def test_r1_can_ping_r2_loopback(r1_connection):
    output = r1_connection.send_command("ping -c 3 2.2.2.2")
    print("\nR1 -> R2 Loopback Ping:")
    print(output)
    assert "0% packet loss" in output


def test_r2_can_ping_r1_loopback(r2_connection):
    output = r2_connection.send_command("ping -c 3 1.1.1.1")
    print("\nR2 -> R1 Loopback Ping:")
    print(output)
    assert "0% packet loss" in output
