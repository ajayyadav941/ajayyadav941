def run_frr_command(connection, command):
    return connection.send_command(f'vtysh -c "{command}"')


def test_r1_bgp_neighbor(r1_connection):
    output = run_frr_command(r1_connection, "show ip bgp summary")
    print("\nR1 BGP Summary:")
    print(output)
    assert "BGP router identifier 1.1.1.1" in output
    assert "local AS number 65001" in output
    assert "10.1.100.2" in output
    assert "65002" in output
    assert "Active" not in output
    assert "Idle" not in output
    assert "(Policy)" not in output


def test_r2_bgp_neighbor(r2_connection):
    output = run_frr_command(r2_connection, "show ip bgp summary")
    print("\nR2 BGP Summary:")
    print(output)
    assert "BGP router identifier 2.2.2.2" in output
    assert "local AS number 65002" in output
    assert "10.1.100.1" in output
    assert "65001" in output
    assert "Active" not in output
    assert "Idle" not in output
    assert "(Policy)" not in output


def test_r1_learns_r2_loopback(r1_connection):
    output = run_frr_command(r1_connection, "show ip route bgp")
    print("\nR1 BGP Routes:")
    print(output)
    assert "2.2.2.2/32" in output
    assert "10.1.100.2" in output


def test_r2_learns_r1_loopback(r2_connection):
    output = run_frr_command(r2_connection, "show ip route bgp")
    print("\nR2 BGP Routes:")
    print(output)
    assert "1.1.1.1/32" in output
    assert "10.1.100.1" in output
