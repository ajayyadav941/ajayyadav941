from netmiko import ConnectHandler
from getpass import getpass

R1 = '192.168.247.141'
R2 = '192.168.247.142'
R3 = '192.168.247.143'

Router_List = [R1, R2, R3]

Username = input('Please Enter Your Username:')
Password = input('Please Enter Your Password:')


def interface_config():
    int_name = input('Please Enter The Interface Name:')
    ip_address = input('Please Enter the IP address:')
    sub_mask = input('Please Enter The Subnet Mask:')

    commands = ['interface ' + int_name, 'ip address ' + ip_address + ' ' + sub_mask]
    int_loopback = SSH.send_config_set(commands)
    print(int_loopback)

    int_brief = SSH.send_command('show ip inter bri')
    print(int_brief)


def ospf():
    ospf_proc_id = input('Please Enter Your OSPF Process ID:')
    ospf_router_id = input('Enter Your Router ID:')
    ospf_network_count = int(input('How Many Network To Advertise:'))

    for router in range(0, ospf_network_count):
        ospf_network_id = input('Enter Your Network ID:')
        ospf_wildcard_mask = input('Enter Your wildcard mask:')
        ospd_area_id = input('Enter Your Area ID:')
        command = ['router ospf ' + ospf_proc_id,
                   'router-id ' + ospf_router_id,
                   'network ' + ospf_network_id + ' ' + ospf_wildcard_mask + ' ' + 'area ' + ospd_area_id]
        ospf_confi = SSH.send_config_set(command)
        print(ospf_confi)


User_Choice1 = input('Welcome to Config Utility\n1. Interface Config\n2. OSPF Config\nPlease Make a Choice(1/2): ')
if User_Choice1 == '1':
    for router in Router_List:
        device_temp = {
            'device_type': 'cisco_ios',
            'host': router,
            'username': Username,
            'password': Password

        }

        SSH = ConnectHandler(**device_temp)
        print('#' * 75 + '\n' + 'Connecting To Router ' + router + '\n' + '#' * 75 + '\n')
        interface_config()
elif User_Choice1 == '2':
    for router in Router_List:
        device_temp = {
            'device_type': 'cisco_ios',
            'host': router,
            'username': Username,
            'password': Password
        }

        SSH = ConnectHandler(**device_temp)
        print('#' * 75 + '\n' + 'Connecting to Router ' + router + '\n' + '#' * 75 + '\n')

        ospf()
else:
    print('Invalid Input Detection\nPlease Try Again\nThank You...!!!')
