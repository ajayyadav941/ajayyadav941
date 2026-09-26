from netmiko import ConnectHandler
from lab_config import LAB_USERNAME, LAB_PASSWORD, R1_HOST

r1 = {
    "device_type": "linux",
    "host": R1_HOST,
    "username": LAB_USERNAME,
    "password": LAB_PASSWORD,
}

connection = ConnectHandler(**r1)
print("Connected successfully to R1")
output = connection.send_command('vtysh -c "show ip bgp summary"')
print(output)
connection.disconnect()
