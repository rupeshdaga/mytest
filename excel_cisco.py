import openpyxl
import xlrd
from pprint import pprint
import login
from netmiko import ConnectHandler

wb = xlrd.open_workbook ('MGMT_IP')
sh = wb.sheet_by_index (0)
a = sh.nrows
_serial = [ ]

ab = xlrd.open_workbook ('AMDB')
shh = ab.sheet_by_index (0)
z = shh.nrows
_different = [ ]
blank_list = [ ]
ip_list=[]
ipam = []
s_num=[]
_serial_num = []
sitename=[]


# wb=xlrd.open_workbook ( 'Book1_SN.xlsx' )
# sh=wb.sheet_by_index ( 0 )
# a=sh.nrows
# _serial = []
#
#
# ab=xlrd.open_workbook ( 'S_num.xlsx' )
# shh=ab.sheet_by_index ( 0 )
# z=shh.nrows

blank_list=[]
for v in range (1, 62):
    blank_list.append(shh.cell_value (v, 0))
_different = []

for item1 in blank_list :
    for i in range ( 1 , a ) :
        if item1 in sh.cell_value(i, 14):
            ip_list = sh.cell_value (i , 9)
            ipam = sh.cell_value (i , 6)
            sitename = sh.cell_value(i, 4)
            with open ('logs.txt' , 'a', newline = '\n') as f:
                f.writelines(f' Serial number {item1} was found for location {sitename} with ipam code {ipam} and IP Address is {ip_list}' + '\n')

