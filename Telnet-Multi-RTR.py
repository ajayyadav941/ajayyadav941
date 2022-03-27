from telnetlib import Telnet

R1= '192.168.247.138'
R2= '192.168.247.140'
R3= '192.168.247.139'

All_Router = [R1,R2,R3]

username= input('Enter the username: ')
password= input('Enter the password:')
for router in All_Router:

    if username == 'ajay' and password == '123456789':
        tn= Telnet(R1)

        tn.write(username.encode('ascii')+b'\n')
        tn.write(password.encode('ascii')+b'\n')
        print('#'*50)

        print('Connection EST with '+router)

        name= input('Enter the interface Name: ')
        ip = input('Enter the IP address for '+ name + ': ')
        mask = input("Enter the subnet Mask:")

        commands = '''
        config ter
        inter {int_name}
        ip address {int_ip} {int_mask}
        desc Connected to R1
        end
        exit
        '''.format(int_name= name,int_ip= ip,int_mask=mask)

        tn.write(commands.encode('ascii')+ b'\n')
        print(tn.read_all().decode('ascii'))
        print('#' * 50)
        print('Cofig done for ' + router)
print('All Router config done')



