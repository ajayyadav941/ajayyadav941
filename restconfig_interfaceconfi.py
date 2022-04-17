import requests
from requests.auth import HTTPBasicAuth
import json
from getpass import getpass

xe_username= input('Please Enter your Username: ')
xe_password= input('Enter your Password: ')


xe_url= 'https://192.168.247.147/restconf/data/ietf-interfaces:interfaces'
xe_cred = HTTPBasicAuth(username=xe_username,password=xe_password)
xe_headers = {'accept':'application/yang-data+json'}

payload = {
        "ietf-interfaces:interfaces": {
        "name": "Loopback20",
        'description':'AJAY',
        "type": "iana-if-type:softwareLoopback",
        "enabled": True,
        "ietf-ip:ipv4": {
            'address':[
                {
                    'ip':'10.100.200.1',
                    'netmask':'255.255.255.0'
                }
            ]
        },
    },
  }

interface_config =requests.post(url=xe_url, auth=xe_cred, headers=xe_headers, data = json.dumps(payload), verify=False)

if interface_config.status_code == 201:

    print('Your Status Code is '+str(interface_config.status_code)+'\n')
    print('Interface Config Done Successfully...!')
else:
    print('Your Status Code is ' + str(interface_config.status_code) + '\n')
    print(interface_config.text)

