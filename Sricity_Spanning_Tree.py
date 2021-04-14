import login
import requests
from pprint import pprint
from netmiko import ConnectHandler
import concurrent.futures

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


amdb_data = get_inv_solarwinds_live()

ip = []

for swip in amdb_data :
    if swip.get ( 'IPAM_Code' )=='INHY4' and 'switch' in swip.get ( 'Network_Function', '' ).lower ( ) :
        ip.append(swip['IP_Address'])

# pprint (ip)

def Sricity(my_ip):
    my_dev = { 'host' : my_ip , 'username' : login.username , 'password' : login.password , 'secret' : login.password ,
               'device_type' : 'cisco_ios' }
    session = ConnectHandler ( **my_dev )
    session.enable ( )
    prompt = session.find_prompt ( )
    output = session.send_command ( 'show spanning-tree vlan 1-1000 summary' , expect_string = prompt ,
                                    delay_factor = 10 )
    # filename = f"{my_ip}_cisco.txt"
    with open ( 'INHY4_2.txt' , 'a' ) as f :
        f.writelines ( prompt + '' + my_ip + '\n' + output + '\n' + '\n' + '\n')


    session.disconnect ( )

with concurrent.futures.ThreadPoolExecutor (max_workers = 100) as mainexecutor :
    for my_ip in ip:
        mainexecutor.submit(Sricity, my_ip)


