import requests
from pprint import pprint
import login
import openpyxl
from netmiko import ConnectHandler
import xlrd
import concurrent.futures
import queue




def get_inv_solarwinds_live(uname=login.username, pasw=login.password,
                            solarwinds_url='https://solarwinds.mdlz.com:17778/SolarWinds/InformationService/v3/Json/Query?query=SELECT%20OrionNodes.NodeId,%20OrionNodes.CustomProperties.Region,%20OrionNodes.CustomProperties.Sub_Region,%20OrionNodes.CustomProperties.Country,%20OrionNodes.CustomProperties.Site,%20OrionNodes.CustomProperties.IPAM_Code,%20OrionNodes.Caption,%20OrionNodes.IP_Address,%20OrionNodes.Status,%20OrionNodes.CustomProperties.Network_Function,%20OrionNodes.CustomProperties.Site_Type,%20OrionNodes.CustomProperties.Site_Operating_Hours,%20OrionNodes.CustomProperties.Site_Metal_Rating,%20OrionNodes.CustomProperties.ManagedBy,%20OrionNodes.SysName,%20OrionNodes.Location,%20OrionNodes.Contact,%20OrionNodes.MachineType,%20OrionNodes.Vendor,%20OrionNodes.LastBoot,%20OrionNodes.IOSVersion%20From%20Orion.Nodes%20AS%20OrionNodes'):
    print('Attempting to download data from SolarWinds...')
    r = requests.get(solarwinds_url, auth=(uname, pasw), verify=False)
    if r.status_code == 200:
        print('Got data from SolarWinds!')
        jas = r.json()
        r.close()
        return jas.get('results', [])
    else :
        print (f"Something went wrong... Couldn't load data from SolarWinds. Status Code: {r.status_code}")
    return [ ]

def user_input (ipam_code):

    for item in amdb:
        if item ['IPAM_Code']== ipam_code and  'Switch' in item ['Network_Function'] and item ['Vendor'] == 'H3C' :
            ip_hcl_HP.append (item [ 'IP_Address' ])

    for item in amdb :
        if item [ 'IPAM_Code' ] == ipam_code and "Switch" in item [ 'Network_Function' ] and item ['Vendor' ] == "Cisco" :
            ip_hcl_cisco.append (item [ 'IP_Address' ])

    for item in amdb :
        if item [ 'IPAM_Code' ] == ipam_code and "Switch" in item [ 'Network_Function' ] and item ['Vendor' ] == "HPE" :
            ip_hcl_HPE.append ( item ['IP_Address'] )


    if len (ip_hcl_cisco) > 0:
        # print (len(ip_hcl_cisco))
        # pprint (ip_hcl_cisco)
        # with concurrent.futures.ThreadPoolExecutor(max_workers=20) as mainexecutor:
        for vip in ip_hcl_cisco:
            VERSION(vip)
        #  (VERSION,vip)

def VERSION (ipsw):
    my_device = { 'host' : ipsw,'username' : login.username,'password' : login.password,'secret' : login.password,
                  'device_type' : 'cisco_ios','global_delay_factor' : 8 }
    session = ConnectHandler ( **my_device )
    prompt = session.find_prompt ( )

    output = session.send_command ( "show int desc  ",expect_string = prompt,use_textfsm = True )
    print ( f" ******* First Switch {ipsw} **********" )
    for item in output :

        if 'Gi' in item [ 'port' ] and 'MI' in item [ 'descrip' ] :
            continue

        if 'Gi' in item [ 'port' ] and 'up' in item [ 'status' ] :

            access = session.send_command ( f"show access-session interface {item [ 'port' ]} detail " ,
                                            expect_string = prompt )

            if 'Status:  Unauthorized' in access :
                cmd = [ 'interface  ' + item['port'] , 'shut', 'no shut']
                print ( f" interface {item [ '' ]} " )
                access = session.send_config_set (cmd)
                print (access)

                # access = session.send_config_set ( 'shutdown' )
                # access = session.send_config_set ( 'no shutdown')
        #     else :
        #         print ( f" This interface {item [ 'intf' ]} has output '{access}' " )
        #
        #
        # elif 'ernet' in item [ 'intf' ] and 'down' in item [ 'status' ] :
        #     print ( f" Interface {item [ 'intf' ]} is down" )

    session.disconnect ( )


if __name__ == '__main__':
    ip_hcl_cisco = []
    ip_hcl_HP=[]
    ip_hcl_HPE=[]
    pid_sw = []
    ip_dict={}
    code = []
    _sw = []
    ou =[]
    amdb = get_inv_solarwinds_live ( )

    for ipam in amdb : #Getting Entire IPAM Code database here and appending in list
        code.append(ipam['IPAM_Code'])

    while True:
        ipam_code = input( f'Please enter IPAM code of site: ' ).upper( ) #Asking user Input for IPAM Code
        if ipam_code in code :
            print( 'IPAM code found, running the program further' )
            user_input(ipam_code)
            # pprint(pid_sw)
            break
        else :
            print ( 'Ipam code not found, please recheck the IPAM code' )