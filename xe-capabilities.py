Disct = [{'sourceip':'192.168.1.1', 'sourceprt':'333', 'destinationip':'10.0.0.1', 'destinationprt':'44', 'proto':'tcp'},
{'sourceip':'192.168.1.2', 'sourceprt':'332', 'destinationip':'10.0.0.1', 'destinationprt':'445', 'proto':'udp'},
{'sourceip':'192.168.1.3', 'sourceprt':'335', 'destinationip':'10.0.0.1', 'destinationprt':'443', 'proto':'tCP'},
{'sourceip':'192.168.1.4', 'sourceprt':'336', 'destinationip':'10.0.0.1', 'destinationprt':'441', 'proto':'TCP'},
{'sourceip':'192.168.1.5', 'sourceprt':'338', 'destinationip':'10.0.0.1', 'destinationprt':'434', 'proto':'UDP'}]


for i in Disct:
    print(i.keys())
    print(i.values())