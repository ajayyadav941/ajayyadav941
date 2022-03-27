from netmiko import ConnectHandler

R1= '192.168.247.141'
R2= '192.168.247.142'
R3 = '192.168.247.143'
Router_List= [R1,R2,R3]

for router in Router_List:
    device_temp = {

        'device_type':'cisco_ios',
        'host':router,
        'username':'ajay',
        'password':'123456789'

    }

    SSh = ConnectHandler(**device_temp)
    print('#'*75 + '\n'+'Connection EST with '+ router + '\n' + '#'*75 + '\n')
    Commands = ['inter lo30','ip address 192.168.100.1 255.255.255.0','no shut']
    Loopback = SSh.send_config_set(Commands)
    print(Loopback)
    inter_brief = SSh.send_command('sh ip inter bri')
    print(inter_brief)



