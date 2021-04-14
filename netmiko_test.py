from netmiko import ConnectHandler
from ttp_templates import parse_output
import login
import openpyxl
from pprint import pprint
import time
import re


my_device = {'host' : '10.87.80.1', 'username' : login.username , 'password' : login.password , 'secret' : login.password ,'device_type' : 'cisco_ios', 'global_delay_factor' : 6}
rupesh = ConnectHandler (**my_device)

prompt = rupesh.find_prompt ()
# print (prompt)
ou = rupesh.send_command ("show cdp neighbors  ", expect_string = prompt, use_textfsm = True, delay_factor = 10)

pprint (ou)
# empty_dict = {}
#
# emoty_list = []


for item in ou:
    if  item ['capability'] == 'S I':
        print ('Description as below')
        print (f"MI_CONN WITH-SW-{item['neighbor']}-{item['neighbor_interface']}")

rupesh.disconnect()

# x = []
#
# if len(ou[0]['hardware']) > 0:
#     print (f"This Switch {ou[0]['hostname']} is stack switch with count = {len(ou[0]['hardware'])}")

# pprint (ou)
#
# regex_model = re.compile(r'[Cc]isco\s(\S+).*memory.')
# model = regex_model.findall(ou)
#
# print (model)
#
# x = re.search(r"^Cisco(.*), Version (?P<model_num> \S+), .*$" , ou)
#
# print (x.groupdict())




# Below is very Importnat code for getting filesystem, use 'dir' command
# for item in ou:
#     x = item['file_system'].split('/')
#     print (x[0])
#     break
# pprint (ou)
# Below is the code for getting PID for Catalyst 4506 use 'show inventory' command
# for pid in ou:
#     if pid['pid'] == 'WS-C4506-E':
#         x = pid['pid']
#
#     if pid['pid'] == 'WS-X45-SUP7L-E':
#         y = pid['pid']
#
# pid_sw = x + '('+ y + ')'
# print (pid_sw)

rupesh.disconnect()


# x = [ { 'sunday': 'breakfast', 'monday' : 'superfast' }, {'tuesday': 'no food' , 'wednesday': 'homemade'} ]
#
# print (x[0]


