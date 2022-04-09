from ncclient import manager

xe = {
    'host': '192.168.247.147',
    'port':'830',
    'username':'admin',
    'password':'cisco',
    'hostkey_verify':False
}


netconf = manager.connect(**xe)
print('Netconf Connection EST with '+ xe['host'])

for i in netconf.server_capabilities:
    print(i)