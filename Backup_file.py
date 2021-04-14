import login
from netmiko import ConnectHandler
from datetime import datetime

with open('devices.txt') as f:
    devices = f.read().splitlines()


for ip in devices:

    cisco_device = {
           'device_type': 'cisco_ios',
           'host': ip,
           'username': login.username,
           'password': login.password,
           'port': 22,
           'secret': login.password,
           'verbose': True
           }
    connection = ConnectHandler(**cisco_device)
    print('Entering the enable mode...')
    connection.enable()

    cmd = '''
    do term len 0
    do show run
    do show ip int brief
    do show version
    do show cdp neigh
    do show cdp neigh de
    do show vtp password
    do show int desc | i MI
    do show interface status
    do show vtp status
    end
    wr mem'''

    print (cmd.split('\n'))
    output = connection.send_config_set(cmd.split('\n'), delay_factor= 100, max_loops = 1500)
    # print(output)

    # creating the backup filename (hostname_date_backup.txt)
    prompt = connection.find_prompt()
    hostname = prompt[0:-1]
    # print(hostname)

    # getting the current date (year-month-day)

    now = datetime.now()
    year = now.year
    month = now.month
    day = now.day

    # creating the backup filename (hostname_date_backup.txt)
    filename = f'{ip}_{year}-{month}-{day}_backupV2.1.txt'

    # writing the backup to the file
    with open(filename, 'a') as backup:
        backup.write(output)
        print(f'Backup of {hostname} completed successfully')
        print('#' * 30)


    print('Closing connection')
    connection.disconnect()