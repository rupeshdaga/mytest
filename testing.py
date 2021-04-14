from netmiko import ConnectHandler
import login
from pprint import pprint

def Crawlmysite (ip):
    my_device = {
        'host': ip,'username': login.username,'password': login.password,'secret': login.password,
        'device_type': 'cisco_ios','global_delay_factor': 15
    }
    rupesh = ConnectHandler (**my_device)
    prompt = rupesh.find_prompt ( )

    output = rupesh.send_command ('show cdp neighbors detail',use_textfsm = True,expect_string = prompt,
        delay_factor = 10)

    for i in range (len (output)):
        if 'Switch' in output [ i ] [ 'software_version' ]:
            xyz.append(output [ i ] [ 'management_ip' ])

    for myip in xyz:
        if ip == myip:
            continue
        else:

    return (xyz)



if __name__ == '__main__':

    xyz = []

    ip = input("Please provide Ip address of site: ")

    abc = Crawlmysite (ip)

    print (abc)





