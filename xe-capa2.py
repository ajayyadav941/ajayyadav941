from ncclient import manager
from getpass import getpass
from xml.dom.minidom import parseString

Username = input('Enter Your Username:')
Password = input('Enter Your Password:')

if Username == 'admin' and Password=='cisco':
    xe = {
        'host': '192.168.247.147',
        'port':'830',
        'username':Username,
        'password':Password,
        'hostkey_verify':False
    }


    netconf = manager.connect(**xe)
    print('#'*75+'\n'+ 'Netconf Connection EST with '+ xe['host'] + '\n'+ '#'*75)
    running_config= netconf.get_config(source= 'running')
    pretty_config = parseString(running_config.xml).toprettyxml()
    print(pretty_config)

else:
    print('Please Check Usernmae/Password')

