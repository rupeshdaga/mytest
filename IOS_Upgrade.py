import requests
import login
from netmiko import ConnectHandler
from pprint import pprint

def get_inv_solarwinds_live(uname=login.username , pasw=login.password, solarwinds_url='https://solarwinds.mdlz.com:17778/SolarWinds/InformationService/v3/Json/Query?query=SELECT%20OrionNodes.NodeId,%20OrionNodes.CustomProperties.Region,%20OrionNodes.CustomProperties.Sub_Region,%20OrionNodes.CustomProperties.Country,%20OrionNodes.CustomProperties.Site,%20OrionNodes.CustomProperties.IPAM_Code,%20OrionNodes.Caption,%20OrionNodes.IP_Address,%20OrionNodes.Status,%20OrionNodes.CustomProperties.Network_Function,%20OrionNodes.CustomProperties.Site_Type,%20OrionNodes.CustomProperties.Site_Operating_Hours,%20OrionNodes.CustomProperties.Site_Metal_Rating,%20OrionNodes.CustomProperties.ManagedBy,%20OrionNodes.SysName,%20OrionNodes.Location,%20OrionNodes.Contact,%20OrionNodes.MachineType,%20OrionNodes.Vendor,%20OrionNodes.LastBoot,%20OrionNodes.IOSVersion%20From%20Orion.Nodes%20AS%20OrionNodes'):
    print('Attempting to download data from SolarWinds...')
    r = requests.get(solarwinds_url, auth=(uname, pasw), verify=False)
    if r.status_code == 200:
        #print('Got data from SolarWinds!')
        jas = r.json()
        r.close()
        return jas.get('results', [])

    else:
        print(f"Something went wrong... Couldn't load data from SolarWinds. Status Code: {r.status_code}")
    return []

def Managed_BY(output):
    ip_hcl=list()
    ipam_code = input (" Please enter ipam code of site: ").upper()
    for item in output: #Convert to function upto line 26
        if item['IPAM_Code'] == ipam_code:
            if item['ManagedBy'] == 'HCL':
                if item['Vendor'] == 'Cisco':
                    ip_hcl.append(item['IP_Address'])

    for ip in ip_hcl : # Try Multitasking
        my_device = {'host' : ip, 'username' : login.username, 'password' : login.password, 'secret' : login.password,
                     'device_type' : 'cisco_ios'}
        session = ConnectHandler(**my_device)
        session.enable()
        prompt = session.find_prompt()
        print ('********************* ' + ip + ' ********************' )
        my_output = session.send_command('show version', expect_string = prompt, use_textfsm = True, delay_factor =  5)
        for x in my_output :
            switch = x['hardware']
            version = x['version']

            for SW in switch :
                if SW[ 3 :8 ] == 'C3650' :
                    if version != '16.12.3a' :
                        out=session.send_command('dir flash:' , expect_string = prompt , use_textfsm = True ,
                                             delay_factor = 50)
                        for memory in out :
                            if int(memory[ 'total_free' ]) > int (479561268):
                                print (f'Free space available for switch {prompt} with ip {ip}')
                                print ('Model is ' + SW[3:8])
                                break
                            else:
                                print ("clean up required, cleaning the free space")
                                break
                    break

                elif SW[3:8] == 'C2960':
                    if version != '15.4.E8' :
                        out=session.send_command('dir flash:' , expect_string = prompt , use_textfsm = True ,
                                             delay_factor = 50)
                        for memory in out :
                            if int(memory[ 'total_free' ]) > int (11000000):
                                print (f'Free space available for switch {prompt} with ip {ip}')
                                print ('Model is ' + SW[ 3 :8 ])
                                break
                            else:
                                print (f" Flash memory free space is {memory['total_free']} ")

                        break
                elif SW[3:8] == 'C3750':
                    if version != '15.4.E8':
                        out=session.send_command('dir flash:' , expect_string = prompt , use_textfsm = True ,
                                                 delay_factor = 50)
                        for memory in out :
                            if int(memory[ 'total_free' ]) > int(11000000) :
                                print(f'Free space available for switch {prompt} with ip {ip}')
                                print ('Model is ' + SW[ 3 :8 ])

                                #print (prompt)
                                break
                            else :
                                print(f" Flash memory free space is {memory[ 'total_free' ]} ")
                                break
                        break
        session.disconnect()





if __name__ == '__main__':
    while True :
        user_input = input ('Do you wish to run some commands on SW data: ').lower ()
        if user_input == 'yes' :
            output = get_inv_solarwinds_live ()
            Managed_BY(output)

        elif user_input == 'no' :
            print ("you haven't try the program")