from netmiko import ConnectHandler
from ttp_templates import parse_output
import login
import openpyxl
from pprint import pprint
import time
import re
import requests


def get_inv_solarwinds_live(uname=login.username , pasw=login.password ,
                            solarwinds_url='https://solarwinds.mdlz.com:17778/SolarWinds/InformationService/v3/Json/Query?query=SELECT%20OrionNodes.NodeId,%20OrionNodes.CustomProperties.Region,%20OrionNodes.CustomProperties.Sub_Region,%20OrionNodes.CustomProperties.Country,%20OrionNodes.CustomProperties.Site,%20OrionNodes.CustomProperties.IPAM_Code,%20OrionNodes.Caption,%20OrionNodes.IP_Address,%20OrionNodes.Status,%20OrionNodes.CustomProperties.Network_Function,%20OrionNodes.CustomProperties.Site_Type,%20OrionNodes.CustomProperties.Site_Operating_Hours,%20OrionNodes.CustomProperties.Site_Metal_Rating,%20OrionNodes.CustomProperties.ManagedBy,%20OrionNodes.SysName,%20OrionNodes.Location,%20OrionNodes.Contact,%20OrionNodes.MachineType,%20OrionNodes.Vendor,%20OrionNodes.LastBoot,%20OrionNodes.IOSVersion%20From%20Orion.Nodes%20AS%20OrionNodes') :
    print ( 'Attempting to download data from SolarWinds...' )
    r=requests.get ( solarwinds_url , auth = (uname , pasw) , verify = False )
    if r.status_code == 200 :
        print ( 'Got data from SolarWinds!' )
        jas=r.json ( )
        r.close ( )
        return jas.get ( 'results' , [ ] )
    else :
        print ( f"Something went wrong... Couldn't load data from SolarWinds. Status Code: {r.status_code}" )
    return []


if __name__ == '__main__' :

    code=[ ]

    wapcmd = []

    ip_hcl_cisco=[ ]

    amdb=get_inv_solarwinds_live ( )

    for icode in amdb :
        code.append ( icode [ 'IPAM_Code' ] )

    ipam=input ( f" Please enter Site IPAM Code:" ).upper ( )

    if ipam in code :
        for item in amdb :
            if item [ 'IPAM_Code' ] == ipam and "Switch" in item [ 'Network_Function' ] and item ['Vendor' ] == "Cisco" :
                ip_hcl_cisco.append ( item [ 'IP_Address' ] )

    for ip in ip_hcl_cisco:
        my_device={ 'host' : ip , 'username' : login.username , 'password' : login.password ,
                'secret' : login.password , 'device_type' : 'cisco_ios' , 'global_delay_factor' : 8 }

        rupesh=ConnectHandler ( **my_device )

        prompt=rupesh.find_prompt ( )
        print ('******************* ' + ip + '  **********************')
        ou=rupesh.send_command ( "show cdp neighbors " , expect_string = prompt , use_textfsm = True , delay_factor = 10)

        # pprint ( ou )

        for description in ou:
            if  f"{ipam}-A" in description ['neighbor'] or  f"{ipam}-C" in description ['neighbor'] or  f"{ipam}-D" in description ['neighbor']:
                cmd = [f"interface {description['local_interface']}", f"desc MI_CONN WITH-SW-{description['neighbor'].strip('.mdlz.net')}_{description['neighbor_interface']}"]
                print (cmd)
                desc = rupesh.send_config_set(cmd, delay_factor = 2)
                print (desc)
            elif f"{ipam}-W" in description ['neighbor']:
                wapcmd=[f"interface {description [ 'local_interface' ]}", f"desc MI_CONN WITH-WAP_{description [ 'neighbor' ].strip ( '.mdlz.net' )}_{description ['neighbor_interface']}"]
                print (wapcmd)
                descwap=rupesh.send_config_set (wapcmd , delay_factor = 10)

        save = rupesh.send_command('wr mem', expect_string = prompt, delay_factor = 2)
        print (save)
        rupesh.disconnect ()

