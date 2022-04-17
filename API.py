import requests
from requests.auth import HTTPBasicAuth

xe_url= 'https://192.168.247.147/restconf/data/ietf-interfaces:interfaces'
xe_cred = HTTPBasicAuth(username='admin',password='cisco')
xe_headers = {'accept':'application/yang-data+json'}
query = requests.get(url= xe_url,auth=xe_cred,headers=xe_headers,verify=False)
print('Your Status Code is '+str(query.status_code)+'\n')
print(query.text)