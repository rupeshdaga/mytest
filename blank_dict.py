from typing import List, Any

import openpyxl
import xlrd
from pprint import pprint
import login
from netmiko import ConnectHandler

wb = xlrd.open_workbook ('Book1_SN.xlsx')
sh = wb.sheet_by_index (0)
a = sh.nrows
_serial = [ ]

ab = xlrd.open_workbook ('S_num.xlsx')
shh = ab.sheet_by_index (0)
z = shh.nrows
_different = [ ]
blank_list = [ ]
ip_list=[]
ipam = []
s_num=[]
_serial_num = []
sitename=[]
for v in range (1, 62) :
    blank_list.append(shh.cell_value (v, 0))
for i in range (1, a) :
    _serial.append(sh.cell_value (i, 14))

    ip_list = (sh.cell_value ( i, 9 ))

    ipam.append ( sh.cell_value ( i, 6 ) )
    sitename.append ( sh.cell_value ( i, 4 ) )
    filename = f'{s_num}_cisco.txt'
    try :
        my_device = { 'host' : ip_list, 'username' : login.username, 'password' : login.password,'secret' : login.password, 'device_type' : 'cisco_ios' }

        net_connect = ConnectHandler ( **my_device )
        net_connect.enable ( )
        prompt = net_connect.find_prompt ( )
        print ( prompt )
        output1 = net_connect.send_command ( 'show tech-supp', expect_string = prompt, delay_factor = 500, max_loops = 6000 )
        with open ( filename, 'a' ) as f :
            f.writelines ( output1 )
    except :
        print ( f"Connection timed out for {s_num} with IP {ip_list}" )

        for data in output1 :
            _serial_num.append ( data [ 'serial' ] )
            print ( f"Serial number {data [ 'serial' ]} for IP {ip_list} found" )


# pprint(_serial_num)

