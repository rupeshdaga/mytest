import openpyxl
import login
import requests



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

if __name__ == '__main__':
    while True :
        user_input = input ('Do you wish to run some commands on SW data: ').lower ()
        if user_input == 'yes' :
            patch = get_inv_solarwinds_live ()
            site_name = input (f'Please enter the site name: ')



        elif user_input == 'no' :
            print ("you haven't try the program")
            break