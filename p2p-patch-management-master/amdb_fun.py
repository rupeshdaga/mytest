import requests
import os
import ipaddress


solarwinds_url = 'https://solarwinds.mdlz.com:17778/SolarWinds/InformationService/v3/Json/Query?query=SELECT%20OrionNodes.NodeId,%20OrionNodes.CustomProperties.Region,%20OrionNodes.CustomProperties.Sub_Region,%20OrionNodes.CustomProperties.Country,%20OrionNodes.CustomProperties.Site,%20OrionNodes.CustomProperties.IPAM_Code,%20OrionNodes.Caption,%20OrionNodes.IP_Address,%20OrionNodes.Status,%20OrionNodes.CustomProperties.Network_Function,%20OrionNodes.CustomProperties.Site_Type,%20OrionNodes.CustomProperties.Site_Operating_Hours,%20OrionNodes.CustomProperties.Site_Metal_Rating,%20OrionNodes.CustomProperties.ManagedBy,%20OrionNodes.SysName,%20OrionNodes.Location,%20OrionNodes.Contact,%20OrionNodes.MachineType,%20OrionNodes.Vendor,%20OrionNodes.LastBoot,%20OrionNodes.IOSVersion%20From%20Orion.Nodes%20AS%20OrionNodes'


def get_inv_solarwinds_live(uname=os.environ.get('MDLZ_SW_USER'), pasw=os.environ.get('MDLZ_SW_PASS'), solarwinds_url='https://solarwinds.mdlz.com:17778/SolarWinds/InformationService/v3/Json/Query?query=SELECT%20OrionNodes.NodeId,%20OrionNodes.CustomProperties.Region,%20OrionNodes.CustomProperties.Sub_Region,%20OrionNodes.CustomProperties.Country,%20OrionNodes.CustomProperties.Site,%20OrionNodes.CustomProperties.IPAM_Code,%20OrionNodes.Caption,%20OrionNodes.IP_Address,%20OrionNodes.Status,%20OrionNodes.CustomProperties.Network_Function,%20OrionNodes.CustomProperties.Site_Type,%20OrionNodes.CustomProperties.Site_Operating_Hours,%20OrionNodes.CustomProperties.Site_Metal_Rating,%20OrionNodes.CustomProperties.ManagedBy,%20OrionNodes.SysName,%20OrionNodes.Location,%20OrionNodes.Contact,%20OrionNodes.MachineType,%20OrionNodes.Vendor,%20OrionNodes.LastBoot,%20OrionNodes.IOSVersion%20From%20Orion.Nodes%20AS%20OrionNodes'):
    """
    this function takes your username and password, goes to SolarWinds and pulls entire AMDB
    if successful, it will return a list of dictionaries
    otherwise, returns a blank list
    """
    print('Attempting to download data from SolarWinds...')
    r = requests.get(solarwinds_url, auth=(uname, pasw), verify=False)
    if r.status_code == 200:
        print('Got data from SolarWinds!')
        jas = r.json()
        r.close()
        return jas.get('results', [])
    else:
        print(f"Something went wrong... Couldn't load data from SolarWinds. Status Code: {r.status_code}")
    return []


def get_swdata_from_sw(uname=os.environ.get('MDLZ_SW_USER'),
                       pasw=os.environ.get('MDLZ_SW_PASS'),
                       filter_net_fun='switch',
                       filter_man_by='hcl',
                       filter_vend_list=('cisco'),
                       ):
    """
    this function filters solarwinds and returns a dictionary with keys as IP Address of switches
    """
    iplist = dict()
    sw_data = get_inv_solarwinds_live(uname, pasw)

    my_sw_id = 0
    for itm in sw_data:
        if itm.get('ManagedBy') is None:
            continue
        if itm.get('Network_Function') is None:
            continue
        if itm.get('Vendor') is None:
            continue
        if itm.get('IP_Address') is None:
            continue

        if filter_net_fun not in itm.get('Network_Function', 'not_found').lower():
            continue
        if filter_man_by not in itm.get('ManagedBy', 'not_found').lower():
            continue
        if itm.get('Vendor', 'not_found').lower() in filter_vend_list:
            try:
                locip = ipaddress.ip_address(itm.get('IP_Address', 'not_found'))
                if iplist.get(str(locip)) is None:
                    iplist[str(locip)] = dict()
                    iplist[str(locip)]['IPAM'] = itm.get('IPAM_Code', 'not_found')
                    iplist[str(locip)]['NET_FUN'] = itm.get('Network_Function', 'not_found')
                    iplist[str(locip)]['REGION'] = itm.get('Region', 'not_found')
                    iplist[str(locip)]['SUB_REGION'] = itm.get('Sub_Region', 'not_found')
                    iplist[str(locip)]['COUNTRY'] = itm.get('Country', 'not_found')
                    iplist[str(locip)]['CITY'] = itm.get('Site', 'not_found')
                    iplist[str(locip)]['SITE'] = itm.get('Site', 'not_found')
                    iplist[str(locip)]['MAN_BY'] = itm.get('ManagedBy', 'not_found')
                    iplist[str(locip)]['OEM'] = itm.get('Vendor', 'not_found')
                    iplist[str(locip)]['IPAM_HN'] = itm.get('SysName', 'not_found')
                    my_sw_id += 1
                    iplist[str(locip)]['SW_ID'] = my_sw_id
                    if 'cisco' in itm.get('Vendor', 'not_found').lower():
                        iplist[str(locip)]['AUTO_OEM'] = 'cisco_SSH'
                    if itm.get('Status', '0') == 1:
                        iplist[str(locip)]['SW_ST'] = True
                    else:
                        iplist[str(locip)]['SW_ST'] = False
            except:
                print('Ran into error get_swdata_from_sw')

    print(f"Found {len(iplist)} entries")
    return iplist


if __name__ == '__main__':
    input('Please execute auto_patch.py')
