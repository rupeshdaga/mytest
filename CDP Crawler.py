import concurrent.futures
import time
import login
import requests
from netmiko import ConnectHandler
from pprint import pprint
import textfsm

#
# def logout(myiplog):
#     try:
#         res2.append(myiplog)
#         my_device = {'host': myiplog , 'username': 'Backdoor' , 'password': 'QtUtPAeRWrYz95Fq',
#                      'secret': 'QtUtPAeRWrYz95Fq' , 'device_type': 'cisco_ios' , 'global_delay_factor': 10}
#         session = ConnectHandler ( **my_device )
#         prompt = session.find_prompt ( )
#         output = session.send_command ( 'show cdp neighbors detail' , expect_string = prompt , delay_factor = 10 ,
#                                         use_textfsm = True )
#         # res2.append ( myiplog )
#
#         for result in output:
#             if f"{ipam}-A" in result ['destination_host'] or f"{ipam}-C" in result ['destination_host'] or f"{ipam}-D" in result ['destination_host']:
#                 ip_list2.append ( result ['management_ip'] )
#         session.disconnect ( )
#         for ip2 in ip_list2:
#             if ip2 in res2:
#                 return (res2)
#             else:
#                 logout(ip2)
#     except Exception as ex:
#         print ( f'\n\t ! Login into {myiplog} failed.' , end = '' )
#
#         print ( '\n\t' + myiplog + '---' + str ( type ( ex ).__name__ ) + '---' + str ( ex.args ) , end = '' )



def crawling(myip):

    try:

        my_device = { 'host': myip , 'username': login.username , 'password': login.password ,
                      'secret': login.password , 'device_type': 'cisco_ios' , 'global_delay_factor': 10}


        session = ConnectHandler ( **my_device )
        prompt = session.find_prompt ( )
        output = session.send_command ('show cdp neighbors detail' , expect_string = prompt , delay_factor = 10 , use_textfsm = True )
        res.append ( myip )
        pprint ( f"My first initial response is {res}" )
        for result in output:

            if 'Switch' in result ['software_version']:
                ip_list.append (result ['management_ip'])

        session.disconnect()
        iplist=list(set(ip_list))
        pprint ( f" My buildup IP list {iplist}" )
        for ip2 in iplist:
            if ip2 not in res:
                print (f" My IF LOOP IP address {ip2}")
                crawling (ip2)
            else:
                continue

        return (f" Final response is {res}")

    except Exception as ex :

        print (f'\n\t ! Login into {myip} failed.',end='')
        print ('\n\t' + myip+ '---' + str (type (ex).__name__) + '---' + str (ex.args),end='')



if __name__ == '__main__':
    res2 = []
    ip_list2 = []
    ip_list = []
    myiplist = []
    res = []
    logout=[]
    main_ip = []
    fail_ip_list=[]

    # ipam = input ( f" Please enter IPAM Code: " ).upper()

    user_input_ip = input ( f" Please enter IP address: " )


    resultlist = crawling ( user_input_ip)

    # for ip in resultlist:
    #     if ip not in res:
    #         res.append(ip)
    #         crawling(ip)

    # resultlist2 = logout()
    # pprint (res)
    # main_ip = res + res2

    # for ip3 in res + res2:
    #     if ip3 not in main_ip:
    #         main_ip.append(ip3)
    pprint (resultlist)
    # pprint (res)

    # my_device = { 'host' : user_input_ip,'username' : login.username,'password' : login.password,'secret' : login.password,
    #               'device_type' : 'cisco_ios', 'global_delay_factor' : 8}
    # session = ConnectHandler (**my_device)
    #
    # prompt = session.find_prompt ()
    #
    # output = session.send_command ('show cdp neighbors detail', expect_string = prompt, use_textfsm = True, delay_factor = 5 )

    # for ip in ip_list:
    #     funny = crawling(ip)
    #     ip_list.append(funny)

# for abcd in output :
#     if 'AIR' in abcd ['platform']:
#         ip_dict = { 'Capa' : abcd [ 'capabilities' ] ,'Device_IP' : abcd [ 'management_ip' ] ,
#                     'Local_Port' : abcd [ 'local_port' ] , 'Model_number' : abcd [ 'platform' ] ,
#                     'Device_HOSTNAME' : abcd [ 'destination_host' ] ,'Software_Version' : abcd [ 'software_version' ] ,
#                     'Switch_IP' : '10.87.80.14' }
#
#         pprint (ip_dict)

# pprint (output)


#
# for item in output:
#     # pprint (item)
#     if 'ernet' in item['intf'] and 'up' in item ['status']:
#
#         access = session.send_command (f"show access-session interface {item['intf']} detail ",expect_string=prompt)
#         if 'Status:  Authorized' in access :
#             print (f" This interafce {item [ 'intf' ]} is Authorized")
#         elif 'Status:  Unauthorized' in access :
#             print (f" This interface {item [ 'intf' ]} is Unauthorized")
#         else :
#             print (f" This inteface {item [ 'intf' ]} has output + ' ' +  {access}")
#
#
#     elif 'ernet' in item['intf'] and 'down' in item ['status']:
#         print (f" Interface { item['intf'] } is down")
#
#         # intf_list.append(intf_dict)
#


# for item in range (len(output)):

# if 'Ethernet' in output[0]['intf']:
#     print (output[0]['intf'])

# my_device = { 'host' : '10.87.80.13','username' : login.username,'password' : login.password,
#               'secret' : login.password,
#               'device_type' : 'cisco_ios','global_delay_factor' : 8 }
# session = ConnectHandler (**my_device)
#
# prompt = session.find_prompt ()

# access = session.send_command (f"show access-session interface {output [0] [ 'intf' ]} detail | i Status",
#                                expect_string = prompt)
#
# if 'Status:  Authorized' in access :
#     print (f" This interface {output [0] [ 'intf' ]} is fully authorized")


# int_dict = { 'interface' : output[item]['intf']}
# intf_list.append(int_dict)
