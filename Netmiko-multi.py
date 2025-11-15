from netmiko import ConnectHandler
from getpass import getpass

R1= '192.168.247.141'
R2= '192.168.247.141'
R3 = '192.168.247.147'
Router_List= [R1,R2,R3]

Username = input('Please Enter Your Username:')
Password= input('Please Enter Your Password:')

for router in Router_List:
    device_temp = {

        'device_type':'cisco_ios',
        'host':router,
        'username':Username,
        'password':Password

    }

    SSh = ConnectHandler(**device_temp)
    print('#'*75 + '\n'+'Connection EST with '+ router + '\n' + '#'*75 + '\n')
    Commands = ['inter lo30','ip address 192.168.100.1 255.255.255.0','no shut']
    Loopback = SSh.send_config_set(Commands)
    print(Loopback)
    inter_brief = SSh.send_command('sh ip inter bri')
    print(inter_brief)



