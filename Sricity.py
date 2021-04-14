import concurrent.futures
import time
import login
import requests
from netmiko import ConnectHandler

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

def run_cmd(swip, uname, passw):
    dev_info = {'device_type': 'cisco_ios',
                'host': swip,
                'username': uname,
                'password': passw,
                }
    device=ConnectHandler (**dev_info)
    prompt = device.enable ()
    try:
        log = device.send_command('show logg', expect_string = prompt)
        if 'STORM_CONTROL' in log or 'STORM-CONTROL' in log:
            print(f'{swip} has generate a storm control log')
        if 'storm' in log.lower():
            print(f'{swip} has generate a storm control log')
        device.disconnect()
    except Exception as ex:
        print(f'\n\t ! Login into {swip} failed.', end='')
        print('\n\t' + swip + '---' + str(type(ex).__name__) + '---' + str(ex.args), end='')
    return
amdb_data = get_inv_solarwinds_live()
for retry in range (50) :
    print (f'\n retry #{retry + 1}')
    with concurrent.futures.ThreadPoolExecutor (max_workers = 50) as mainexecutor :
        for swip in amdb_data :
            if swip.get ('IPAM_Code') == 'INHY4' and 'switch' in swip.get ('Network_Function' , '').lower () :
                mainexecutor.submit (run_cmd , swip[ 'IP_Address' ] , login.username , login.password)
    time.sleep (600)
