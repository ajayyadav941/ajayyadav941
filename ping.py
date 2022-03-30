import pingparsing
import os

def packetloss(ip):
    ping_parse = pingparsing.PingParsing()
    result = os.popen('ping -c 50 -n -i .2 W1 '+ ip).read()
    global ping_result
    ping_result = ping_parse.parse(result).as_dict()
    return (ping_result['packet_loss_rate'])

print(packetloss('8.8.8.8'))

#########################################

ping_parse = pingparsing.PingParsing()
Trans = pingparsing.PingTransmitter()
Trans.destination = '8.8.8.8'
Trans.count = 50
result = Trans.ping()
result_out = ping_parse.parse(result).as_dict()
print(result_out['packet_loss_rate'])
