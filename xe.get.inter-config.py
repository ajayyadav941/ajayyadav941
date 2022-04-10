from ncclient import manager
from getpass import getpass
from xml.dom.minidom import parseString

#Password = input('Enter Your Password:')

xe = {
        'host': '192.168.247.147',
        'port':'830',
        'username':input("Enter Username: "),
        'password':getpass('Enter Your password: '),
        'hostkey_verify':False
}

interace_payload = '''

<config>
  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
      <name>Loopback15</name>
      <description>Configured by Ajay Using netconf</description>
      <type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">
           ianaift:softwareLoopback
      </type>
      <enabled>true</enabled>
      <ipv4 xmlns="urn:ietf:params:xml:ns:yang:ietf-ip">
        <address>
          <ip>10.1.1.1</ip>
          <netmask>255.255.255.252</netmask>
        </address>
      </ipv4>
    </interface>
  </interfaces>
</config>
'''


netconf = manager.connect(**xe)
print('#'*75+'\n'+ 'Netconf Connection EST with '+ xe['host'] + '\n'+ '#'*75)
interface_config= netconf.edit_config(interace_payload,target = 'running')
print(interface_config)