import requests

import login

import concurrent.futures

from netmiko import ConnectHandler





def switch_login(ip):
    my_device = {'host' : ip, 'username' : login.username, 'password' : login.password, 'secret' : login.password,'device_type' : 'cisco_ios'}
    net_connect = ConnectHandler(**my_device)
    net_connect.enable()
    prompt = net_connect.find_prompt()
    out = net_connect.send_command('show run', delay_factor = 10)
    print (ip + '\n')
    print (out)

def get_inv_solarwinds_live(uname=login.username, pasw=login.password,
                            solarwinds_url='https://solarwinds.mdlz.com:17778/SolarWinds/InformationService/v3/Json/Query?query=SELECT%20OrionNodes.NodeId,%20OrionNodes.CustomProperties.Region,%20OrionNodes.CustomProperties.Sub_Region,%20OrionNodes.CustomProperties.Country,%20OrionNodes.CustomProperties.Site,%20OrionNodes.CustomProperties.IPAM_Code,%20OrionNodes.Caption,%20OrionNodes.IP_Address,%20OrionNodes.Status,%20OrionNodes.CustomProperties.Network_Function,%20OrionNodes.CustomProperties.Site_Type,%20OrionNodes.CustomProperties.Site_Operating_Hours,%20OrionNodes.CustomProperties.Site_Metal_Rating,%20OrionNodes.CustomProperties.ManagedBy,%20OrionNodes.SysName,%20OrionNodes.Location,%20OrionNodes.Contact,%20OrionNodes.MachineType,%20OrionNodes.Vendor,%20OrionNodes.LastBoot,%20OrionNodes.IOSVersion%20From%20Orion.Nodes%20AS%20OrionNodes'):
    print('Attempting to download data from SolarWinds...')
    r = requests.get(solarwinds_url, auth=(uname, pasw), verify=False)
    if r.status_code == 200:
        print('Got data from SolarWinds!')
        jas = r.json()
        r.close()
        output = jas.get('results', [])
        ip_hcl = list()
        for item in output :
            if item['ManagedBy'] == 'HCL' :
                if item['Site'] == 'Harrower Road' :
                    if item['Vendor'] == 'Cisco' :
                        ip_hcl.append(item['IP_Address'])
        with concurrent.futures.ThreadPoolExecutor(max_workers = 50) as mainexecutor :
            for swip in ip_hcl :
                mainexecutor.submit(switch_login, swip)


    else :
        print(f"Something went wrong... Couldn't load data from SolarWinds. Status Code: {r.status_code}")
    return []



get_inv_solarwinds_live()




