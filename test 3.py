from pprint import pprint
import login
from netmiko import ConnectHandler
import concurrent.futures
import queue
import requests
import openpyxl
import xlrd


ip = '10.87.20.1'

x = []

my_device={'host': ip, 'username': login.username, 'password': login.password,
            'secret': login.password, 'device_type': 'cisco_ios', 'global_delay_factor': 10
            }
rupesh=ConnectHandler ( **my_device )
prompt=rupesh.find_prompt ( )
output=rupesh.send_command ('dir all-filesystems', expect_string = prompt, use_textfsm = True, delay_factor = 5 )

for i in range (len (output)):
    if 'c3750e-universalk9npe-mz.150-2.SE11.bin' in output[i]['name']:
        print (f"flash is  {output[i]['file_system'].strip('/')}")


#
# for item in output:
#     if '16.12.03a' in item ['name']:
#         print (f"Image already present ")
#         break
#
# else:
#     output2 = rupesh.send_command ('show version',expect_string = prompt, use_textfsm = True, delay_factor = 5 )
#     if output2[0]['version'] > '16':
#         print ("delete command is request platform clean")
#
#     elif  output2[0]['version'] < '16':
#         print ("delete command is software clean")


rupesh.disconnect()
# for i in range (len(x)):
#
#     if x[i] == 'c3560c405ex-universalk9-mz.152-2.E9.bin':
#         print ("Match Found")
#         continue
#     else:
#
#         command = f'delete /force /recursive flash:{x[i]}'
#
#         print (command)
#




