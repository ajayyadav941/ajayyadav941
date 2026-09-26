import os
from netmiko import ConnectHandler

password = os.getenv("LAB_PASSWORD")
if not password:
    raise RuntimeError("Set LAB_PASSWORD before running this script")

devices = [
    {"name": "R1", "device_type": "linux", "host": os.getenv("R1_HOST", "172.20.20.11"), "username": os.getenv("LAB_USERNAME", "root"), "password": password},
    {"name": "R2", "device_type": "linux", "host": os.getenv("R2_HOST", "172.20.20.12"), "username": os.getenv("LAB_USERNAME", "root"), "password": password},
]

for device in devices:
    name = device.pop("name")
    print("\n" + "=" * 60)
    print(f"Connecting to {name} - {device['host']}")
    print("=" * 60)
    try:
        connection = ConnectHandler(**device)
        print(f"\nSuccessfully connected to {name}")
        bgp_summary = connection.send_command('vtysh -c "show ip bgp summary"')
        bgp_routes = connection.send_command('vtysh -c "show ip route bgp"')
        print(f"\n{name} - BGP SUMMARY\n{bgp_summary}")
        print(f"\n{name} - BGP ROUTES\n{bgp_routes}")
        connection.disconnect()
    except Exception as error:
        print(f"\nFailed to connect to {name}: {error}")
