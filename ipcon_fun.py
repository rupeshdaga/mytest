import concurrent.futures
import os
import time
import netmiko
import datetime
import queue
import re
from pathlib import Path
import patchmgmt_fun
from tqdm import tqdm


_DEL_FILE_FLAG = False
_MAX_P2P_LAN_TRANSFER = 5
_DEL_BIN_FILE_SIZE = 9999999
_CHECK_SW_MD5 = re.compile(r"=\s+(\S+)")
_FIRMWARE_FOLDER = Path('.', 'Firmware')
_GLOBAL_MAX_LOOPS = 500000


def copy_threader(iplist, copyfile_list, uname=os.environ.get('MDLZ_USER'), pasw=os.environ.get('MDLZ_PASS'), maxwork=100):
    print('=' * 50)
    print('=' * 50)
    print('=' * 50)
    print('=' * 50)

    _START_TIME = datetime.datetime.now()
    pipe = queue.Queue()

    # STEP 1 - Ensure IOS is available on Primary switch
    netmiko.log.debug('>>>>> Initiating IOS copy to primary switch <<<<<')
    print('>>>>> Initiating IOS copy to primary switch <<<<<')
    while True:
        #a- initiate a file transfer to primary switches
        netmiko.log.debug('>>>>> Firing up threader to push file to primary switch <<<<<')
        print('>>>>> Firing up threader to push file to primary switch <<<<<')
        with concurrent.futures.ThreadPoolExecutor(max_workers=maxwork) as mainexecutor:
            for ios_file in copyfile_list:
                primary_sw_ip = copyfile_list[ios_file]['primary']
                if not iplist[primary_sw_ip]['LOGIN_DATA']['MD5_VERIFIED_NEW_FIRMWARE']:
                    print(f'::::: {primary_sw_ip} ::::: Initiating a IOS {ios_file} transfer')
                    mainexecutor.submit(push_firmware_to_switch,
                                        primary_sw_ip,
                                        uname,
                                        pasw,
                                        iplist[primary_sw_ip]['LOGIN_DATA']['PATCH_MGMT_INFO']['PATCH_MGMT_FILE'],
                                        iplist[primary_sw_ip]['LOGIN_DATA']['FILE_SYS_LIST'][0],
                                        pipe,
                                        )
        while not pipe.empty():
            tempdatatup = pipe.get()
            iplist[tempdatatup[0]]['TRANSFER_DATA'] = tempdatatup[1]
        #b- check if file copied successfully. if not, swap primary switch with a different secondary switch
        netmiko.log.debug('>>>>> Checking if all primary switches got software <<<<<')
        print('>>>>> Checking if all primary switches got software <<<<<')
        for ios_file in copyfile_list:
            primary_sw_ip = copyfile_list[ios_file]['primary']
            if iplist[primary_sw_ip]['LOGIN_DATA']['MD5_VERIFIED_NEW_FIRMWARE']:
                continue
            if iplist[primary_sw_ip].get('TRANSFER_DATA', {}):
                if iplist[primary_sw_ip]['TRANSFER_DATA'].get('file_exists', False) and iplist[primary_sw_ip]['TRANSFER_DATA'].get('file_verified', False):
                    iplist[primary_sw_ip]['LOGIN_DATA']['MD5_VERIFIED_NEW_FIRMWARE'] = iplist[primary_sw_ip]['LOGIN_DATA']['FILE_SYS_LIST'][0].strip('/') + ios_file
                    continue
            copyfile_list[ios_file]['secondary'].append(primary_sw_ip)
            copyfile_list[ios_file]['primary'] = copyfile_list[ios_file]['secondary'][0]
            del copyfile_list[ios_file]['secondary'][0]

        #c- if all primary switches have a MD5 verified file then go to next step, else try again
        breakout_flag = True
        for ios_file in copyfile_list:
            primary_sw_ip = copyfile_list[ios_file]['primary']
            if not iplist[primary_sw_ip]['LOGIN_DATA']['MD5_VERIFIED_NEW_FIRMWARE']:
                breakout_flag = False
                netmiko.log.debug(f"!!!!! File {ios_file} needs to be pushed again. !!!!!")
                print(f"!!!!! File {ios_file} needs to be pushed again. !!!!!")
        if breakout_flag:
            netmiko.log.debug('>>>>> Confirmed all primary switches are good to go <<<<<')
            print('>>>>> Confirmed all primary switches are good to go <<<<<')
            break
        time.sleep(60)
    netmiko.log.debug('>>>>> Done with IOS copy to primary switch <<<<<')
    print('>>>>> Done with IOS copy to primary switch <<<<<')

    # STEP 2 - Enable local TFTP server (IF no secondary switch for this ios, skip this step)
    netmiko.log.debug('>>>>> Enabling TFTP server on primary switch <<<<<')
    print('>>>>> Enabling TFTP server on primary switch <<<<<')
    with concurrent.futures.ThreadPoolExecutor(max_workers=maxwork) as mainexecutor:
        for ios_file in copyfile_list:
            primary_sw_ip = copyfile_list[ios_file]['primary']
            if copyfile_list[ios_file]['secondary']:
                mainexecutor.submit(enable_disable_local_tftp_server,
                                    primary_sw_ip,
                                    uname,
                                    pasw,
                                    ios_file,
                                    iplist[primary_sw_ip]['LOGIN_DATA']['FILE_SYS_LIST'][0],
                                    True,
                                    )

    # STEP 3 - Get Secondary switches to load IOS from primary (limit of 5 local switches at a time)
    netmiko.log.debug('>>>>> Getting secondary switches to load IOS from primary switch <<<<<')
    print('>>>>> Getting secondary switches to load IOS from primary switch <<<<<')
    with concurrent.futures.ThreadPoolExecutor(max_workers=_MAX_P2P_LAN_TRANSFER) as mainexecutor:
        for ios_file in copyfile_list:
            primary_sw_ip = copyfile_list[ios_file]['primary']
            for secondary_sw_ip in copyfile_list[ios_file]['secondary']:
                mainexecutor.submit(copy_from_primary_switch,
                                    secondary_sw_ip,
                                    uname,
                                    pasw,
                                    primary_sw_ip,
                                    ios_file,
                                    iplist[secondary_sw_ip]['LOGIN_DATA']['FILE_SYS_LIST'][0],
                                    iplist[secondary_sw_ip]['LOGIN_DATA']['PATCH_MGMT_INFO']['PATCH_MGMT_MD5'],
                                    pipe,
                                    )
    while not pipe.empty():
        tempdatatup = pipe.get()
        iplist[tempdatatup[0]]['IOS_COPY'] = tempdatatup[1]
    for ios_file in copyfile_list:
        for secondary_sw_ip in copyfile_list[ios_file]['secondary']:
            if iplist[secondary_sw_ip]['IOS_COPY']:
                iplist[secondary_sw_ip]['LOGIN_DATA']['MD5_VERIFIED_NEW_FIRMWARE'] = iplist[secondary_sw_ip]['LOGIN_DATA']['FILE_SYS_LIST'][0].strip('/') + ios_file

    # STEP 4 - Disable local TFTP server (IF no secondary switch for this ios, skip this step)
    netmiko.log.debug('>>>>> Disabling TFTP server on primary switch <<<<<')
    print('>>>>> Disabling TFTP server on primary switch <<<<<')
    with concurrent.futures.ThreadPoolExecutor(max_workers=maxwork) as mainexecutor:
        for ios_file in copyfile_list:
            primary_sw_ip = copyfile_list[ios_file]['primary']
            if copyfile_list[ios_file]['secondary']:
                mainexecutor.submit(enable_disable_local_tftp_server,
                                    primary_sw_ip,
                                    uname,
                                    pasw,
                                    ios_file,
                                    iplist[primary_sw_ip]['LOGIN_DATA']['FILE_SYS_LIST'][0],
                                    False,
                                    )

    # STEP 5a - IOS> if stack size is 1, we are done
    # STEP 5b - IOS> copy files to other switches in same stack
    # STEP 5c - IOS-XE INSTALL mode> we are done. software install required before reboot
    # STEP 5d - IOS-XE BUNDLE mode> Software expand required
    netmiko.log.debug('>>>>> Applying final touches to IOS stacks or IOS-XE Bundle mode switches <<<<<')
    print('>>>>> Applying final touches to IOS stacks or IOS-XE Bundle mode switches <<<<<')
    with concurrent.futures.ThreadPoolExecutor(max_workers=maxwork) as mainexecutor:
        for ip in iplist:
            if iplist[ip]['LOGIN_DATA']['PATCH_MGMT_INFO']['NOT_ON_PM_FLAG'] and iplist[ip]['LOGIN_DATA']['MD5_VERIFIED_NEW_FIRMWARE']:
                if iplist[ip]['LOGIN_DATA']['CISCO_DEV_TYPE_XE']:
                    # if IOS-XE, check mode
                    if iplist[ip]['LOGIN_DATA']['IOS_MODE'] == 'BUNDLE':
                        # if Bundle mode, expand software
                        mainexecutor.submit(ios_xe_expand_software,
                                            ip,
                                            uname,
                                            pasw,
                                            iplist[ip]['LOGIN_DATA']['MD5_VERIFIED_NEW_FIRMWARE'],
                                            pipe,
                                            )
                    else:
                        # if Install mode, ios install before reboot is required
                        iplist[ip]['IOS_READY'] = True
                else:
                    # initiate tranfer to other switches
                    if iplist[ip]['LOGIN_DATA']['STACK_COUNT'] > 1:
                        mainexecutor.submit(copy_ios_to_stack,
                                            ip,
                                            uname,
                                            pasw,
                                            iplist[ip]['LOGIN_DATA']['MD5_VERIFIED_NEW_FIRMWARE'],
                                            iplist[ip]['LOGIN_DATA']['FILE_SYS_LIST'],
                                            pipe,
                                            )
                    else:
                        # if single switch, no need to copy to any other file system
                        iplist[ip]['IOS_READY'] = True

    while not pipe.empty():
        tempdatatup = pipe.get()
        iplist[tempdatatup[0]]['IOS_READY'] = tempdatatup[1]

    print("\nDone with Copy Threader " + str(datetime.datetime.now() - _START_TIME))
    print('=' * 50)
    print('=' * 50)
    print('=' * 50)
    print('=' * 50)
    return


def copy_ios_to_stack(ip, uname, pasw, ios_file, file_sys_list, pipe, retry_list=(1, 2, 4, 8)):
    """
    this function copies IOS from one switch to another
    @param ip: IP address of switch
    @param uname: username to login
    @param pasw: password to login
    @param ios_file: IOS file to copy
    @param file_sys_list: file systems to copy files to
    @param pipe: queue to send back information to threader
    @param retry_list: retry with variable local delay factor
    @return: copy status
    """
    for retry_ld in retry_list:
        try:
            device = netmiko.ConnectHandler(**{'device_type': 'cisco_ios',
                                               'host': ip,
                                               'username': uname,
                                               'password': pasw,
                                               'global_delay_factor': retry_ld,
                                               })


            for file_sys in file_sys_list[1:]:
                if _DEL_FILE_FLAG:
                    netmiko.log.debug(f"\n::::: {ip}-copy_ios_to_stack ::::: sending command 'copy {ios_file} {file_sys.strip('/')}'")
                    op = device.send_command(f"copy {ios_file} {file_sys.strip('/')}",
                                             max_loops=_GLOBAL_MAX_LOOPS,
                                             delay_factor=retry_ld * 32,
                                             expect_string=r"(filename|\#)",
                                             )
                    if 'filename' in op:
                        netmiko.log.debug(f"\n::::: {ip}-copy_ios_to_stack ::::: sending enter")
                        op += device.send_command('\n',
                                                  max_loops=_GLOBAL_MAX_LOOPS,
                                                  delay_factor=retry_ld * 32,
                                                  expect_string=r"\#",
                                                  )
                else:
                    print(f"\n::::: {ip} ::::: sending 'copy {ios_file} {file_sys.strip('/')}'")

            netmiko.log.debug(f"\n::::: {ip}-copy_ios_to_stack ::::: disconnecting")
            device.disconnect()
            pipe.put((ip, True))
            return

        except Exception as ex:
            print(f"\n::::: {ip}-copy_ios_to_stack ::::: {str(type(ex).__name__)} ; {str(ex.args)}")
            continue

    pipe.put((ip, False))
    return


def ios_xe_expand_software(ip, uname, pasw, ios_file, pipe, retry_list=(1, 2, 4, 8)):
    """

    @param ip: IP address of switch
    @param uname: username to login
    @param pasw: password to login
    @param ios_file: IOS file to copy
    @param pipe: queue to send back information to threader
    @param retry_list: retry with variable local delay factor
    @return: ios expansion status
    """
    for retry_ld in retry_list:
        try:
            device = netmiko.ConnectHandler(**{'device_type': 'cisco_ios',
                                               'host': ip,
                                               'username': uname,
                                               'password': pasw,
                                               'global_delay_factor': retry_ld,
                                               })
            if _DEL_FILE_FLAG:
                netmiko.log.debug(f"\n::::: {ip}-ios_xe_expand_software ::::: sending command 'software expand file {ios_file}'")
                op = device.send_command(f"software expand file {ios_file}",
                                         max_loops=_GLOBAL_MAX_LOOPS,
                                         delay_factor=retry_ld * 32,
                                         expect_string=r"(proceed|\#)")
                if '% Invalid input' in op:
                    netmiko.log.debug(f"\n::::: {ip}-ios_xe_expand_software ::::: sending command 'request platform software package expand switch all file {ios_file} force'")
                    op = device.send_command(f"request platform software package expand switch all file {ios_file} force",
                                             max_loops=_GLOBAL_MAX_LOOPS,
                                             delay_factor=retry_ld * 32,
                                             expect_string=r"(proceed|\#)")
                if 'Operation aborted' in op:
                    device.disconnect()
                    pipe.put((ip, False))
                    return
                device.send_command('\ny\n\n')

                netmiko.log.debug(f"\n::::: {ip}-ios_xe_expand_software ::::: disconnecting")
                device.disconnect()
                pipe.put((ip, True))
                return
            else:
                print(f"\n::::: {ip} ::::: software expand file {ios_file}")
                print(f"\n::::: {ip} ::::: request platform software package expand switch all file {ios_file} force")
                device.disconnect()
                pipe.put((ip, True))
                return

        except Exception as ex:
            print(f"\n::::: {ip}-ios_xe_expand_software ::::: {str(type(ex).__name__)} ; {str(ex.args)}")
            continue

    pipe.put((ip, False))
    return


def copy_from_primary_switch(ip, uname, pasw, tftp_svr, ios_file, file_sys, md5_checksum, pipe, retry_list=(4, 8, 16, 32)):
    """
    enables switches to copy file from tftp server
    @param ip: IP address of switch
    @param uname: username to login
    @param pasw: password to login
    @param tftp_svr: IP address of tftp server
    @param ios_file: IOS file to copy
    @param file_sys: file system to save file to
    @param md5_checksum: MD5 checksum of IOS file
    @param pipe: queue to send back information to threader
    @param retry_list: retry with variable local delay factor
    @return:
    """
    for retry_ld in retry_list:
        try:
            device = netmiko.ConnectHandler(**{'device_type': 'cisco_ios',
                                               'host': ip,
                                               'username': uname,
                                               'password': pasw,
                                               'global_delay_factor': retry_ld,
                                               })
            if _DEL_FILE_FLAG:
                cmd_set = ['ip tftp blocksize 8192', 'line vty 0 15', 'exec-timeout 1080']
                netmiko.log.debug(f"\n::::: {ip}-copy_from_primary_switch ::::: sending config set '{cmd_set}'")
                device.send_config_set(cmd_set, cmd_verify=False)

                netmiko.log.debug(f"\n::::: {ip}-copy_from_primary_switch ::::: sending command 'copy tftp://{tftp_svr}/{ios_file} {file_sys.strip('/')}'")
                op = device.send_command(f"copy tftp://{tftp_svr}/{ios_file} {file_sys.strip('/')}",
                                         max_loops=_GLOBAL_MAX_LOOPS,
                                         delay_factor=retry_ld*32,
                                         expect_string=r"(filename|\#)",
                                         )
                if 'filename' in op:
                    netmiko.log.debug(f"\n::::: {ip}-copy_from_primary_switch ::::: sending enter")
                    op += device.send_command('\n',
                                              max_loops=_GLOBAL_MAX_LOOPS,
                                              delay_factor=retry_ld*32,
                                              expect_string=r"\#",
                                              )
                netmiko.log.debug(f"\n::::: {ip}-copy_from_primary_switch ::::: sending command 'verify /md5 {file_sys.strip('/')}{ios_file}'")
                raw_md5_check = device.send_command(f"verify /md5 {file_sys.strip('/')}{ios_file}",
                                                    max_loops=_GLOBAL_MAX_LOOPS,
                                                    delay_factor=retry_ld*32,
                                                    )
                if _CHECK_SW_MD5.search(raw_md5_check):
                    if _CHECK_SW_MD5.search(raw_md5_check)[1] == md5_checksum:
                        cmd_set = ['line vty 0 15', 'exec-timeout 15']
                        netmiko.log.debug(f"\n::::: {ip}-copy_from_primary_switch ::::: sending config set '{cmd_set}'")
                        device.send_config_set(cmd_set, cmd_verify=False)
                        device.disconnect()
                        pipe.put((ip, True))
                        return
                    else:
                        continue

            else:
                print(f"\n::::: {ip} ::::: sending 'ip tftp blocksize 8192', 'line vty 0 15', 'exec-timeout 1080'")
                print(f"\n::::: {ip} ::::: copy tftp://{tftp_svr}/{ios_file} {file_sys.strip('/')}")
                print(f"\n::::: {ip} ::::: sending 'line vty 0 15', 'exec-timeout 15'")

                netmiko.log.debug(f"\n::::: {ip}-copy_from_primary_switch ::::: disconnecting")
                device.disconnect()
                pipe.put((ip, True))
                return
        except Exception as ex:
            print(f"\n::::: {ip}-copy_from_primary_switch ::::: {str(type(ex).__name__)} ; {str(ex.args)}")
            continue

    pipe.put((ip, False))
    return


def enable_disable_local_tftp_server(ip, uname, pasw, ios_file, file_sys, enable_tftp, retry_list=(1, 2, 4, 8)):
    """
    enables or disables tftp server
    @param ip: IP address of switch
    @param uname: username to login
    @param pasw: password to login
    @param ios_file: IOS file to enable
    @param file_sys: file system on switch
    @param enable_tftp: True to enable, False to disable
    @param retry_list: retry with variable local delay factor
    @return: nothing
    """
    for retry_ld in retry_list:
        try:
            device = netmiko.ConnectHandler(**{'device_type': 'cisco_ios',
                                               'host': ip,
                                               'username': uname,
                                               'password': pasw,
                                               'global_delay_factor': retry_ld,
                                               })
            if enable_tftp:
                cmd_set = ['ip tftp blocksize 8192',
                           f"tftp-server {file_sys.strip('/')}{ios_file}",
                           ]
            else:
                cmd_set = [f"no tftp-server {file_sys.strip('/')}{ios_file}"]
            if _DEL_FILE_FLAG:
                netmiko.log.debug(f"\n::::: {ip}-enable_disable_local_tftp_server ::::: sending config set '{cmd_set}'")
                op = device.send_config_set(cmd_set, cmd_verify=False)
            else:
                print(f"\n::::: {ip} ::::: sending  {cmd_set} commands to switch")

            netmiko.log.debug(f"\n::::: {ip}-enable_disable_local_tftp_server ::::: disconnecting")
            device.disconnect()
            return
        except Exception as ex:
            print(f"\n::::: {ip}-enable_disable_local_tftp_server ::::: {str(type(ex).__name__)} ; {str(ex.args)}")
            continue

    return


def push_firmware_to_switch(ip, uname, pasw, ios_file, file_sys, pipe, retry_list=(1, 1, 2, 2, 4, 4, 8, 8)):
    """
    Sends firmware file to switch
    @param ip: IP address of switch
    @param uname: username to login
    @param pasw: password to login
    @param ios_file: IOS file to copy
    @param file_sys: file location on switch
    @param pipe: queue to send back information to threader
    @param retry_list: retry with variable local delay factor
    @return: dictionary
    """
    transfer = {
                'file_exists': False,
                'file_transferred': False,
                'file_verified': False,
                }
    for retry_ld in retry_list:
        try:
            device = netmiko.ConnectHandler(**{'device_type': 'cisco_ios',
                                               'host': ip,
                                               'username': uname,
                                               'password': pasw,
                                               'global_delay_factor': retry_ld,
                                               })
            if _DEL_FILE_FLAG:
                device.send_config_set(['line vty 0 15', 'exec-timeout 1080'], cmd_verify=False)
                netmiko.log.debug(f"\n::::: {ip}-push_firmware_to_switch ::::: sending 'line vty 0 15', 'exec-timeout 1080'")

                transfer = netmiko.file_transfer(device,
                                                 source_file=Path(_FIRMWARE_FOLDER, ios_file),
                                                 dest_file=ios_file,
                                                 direction='put',
                                                 file_system=file_sys,
                                                 )
                netmiko.log.debug(f"\n::::: {ip}-push_firmware_to_switch ::::: sending file {Path(_FIRMWARE_FOLDER, ios_file)}")

                device.send_config_set(['line vty 0 15', 'exec-timeout 15'], cmd_verify=False)
                netmiko.log.debug(f"\n::::: {ip}-push_firmware_to_switch ::::: sending 'line vty 0 15', 'exec-timeout 15'")
            else:
                print(f"\n::::: {ip}-push_firmware_to_switch ::::: sending 'line vty 0 15', 'exec-timeout 1080'")
                print(f"\n::::: {ip}-push_firmware_to_switch ::::: sending file {Path(_FIRMWARE_FOLDER, ios_file)}")
                print(f"\n::::: {ip}-push_firmware_to_switch ::::: sending 'line vty 0 15', 'exec-timeout 15'")
                transfer = {
                    'file_exists': True,
                    'file_transferred': True,
                    'file_verified': True,
                }

            netmiko.log.debug(f"\n::::: {ip}-push_firmware_to_switch ::::: disconnecting")
            device.disconnect()
            pipe.put((ip, transfer))
            return
        except Exception as ex:
            print(f"\n::::: {ip}-push_firmware_to_switch ::::: {str(type(ex).__name__)} ; {str(ex.args)}")
            continue
    pipe.put((ip, {}))
    return


def main_threader(iplist, patchmgmt_data, uname, pasw, maxwork=100):
    """
    this function will create multiple threads to collect data from switch
    :param iplist: dictionary with key as IP address of switch
    :param patchmgmt_data: patchmanagement data
    :param uname: username to login into switches
    :param pasw: password to login into switches
    :param maxwork: max number of threads to run simultaniously
    :return: updates iplist dictionary with additional data collected by threads
    """

    print('=' * 50)
    print('=' * 50)
    print('=' * 50)
    print('=' * 50)

    _START_TIME = datetime.datetime.now()
    pipe = queue.Queue()

    with tqdm(len(iplist)) as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=maxwork) as mainexecutor:
            # for ip in iplist:
            #     mainexecutor.submit(get_version_info, ip, iplist[ip]['SW_ID'], uname, pasw, pipe, patchmgmt_data)
            threads = [mainexecutor.submit(get_version_info, ip, uname, pasw, pipe, patchmgmt_data) for ip in iplist]
            for future in concurrent.futures.as_completed(threads):
                result = future.result()
                pbar.update(1)

    while not pipe.empty():
        tempdatatup = pipe.get()
        iplist[tempdatatup[0]]['LOGIN_DATA'] = tempdatatup[1]

    print("\nDone with Main Threader " + str(datetime.datetime.now() - _START_TIME))
    print('=' * 50)
    print('=' * 50)
    print('=' * 50)
    print('=' * 50)
    return


def get_version_info(ip, uname, pasw, pipe, patchmgmt_data, chassis_model_list=('6807', '4503', '4506', '4507', '4509', '6509'), retry_list=(1, 2, 4, 8)):
    """
    :param ip: IP address of switch
    :param uname: username to login into switches
    :param pasw: password to login into switches
    :param pipe: queue to send data back to main application
    :param patchmgmt_data: patchmanagement data from sheet
    :param chassis_model_list: list of supported chassis
    :param retry_list: local delay factor retry list
    :return: sends data back to main thread via pipe. returns nothing
    """
    localswdict = {'LOGIN_FAIL_FLAG': True,
                   'LOGIN_FAIL_COMM': '',
                   'CISCO_DEV_TYPE_XE': False,
                   'IOS_MODE': 'BUNDLE',
                   'RUN_IMAGE': '',
                   'STACK_COUNT': 0,
                   'MD5_VERIFIED_NEW_FIRMWARE': '',
                   'COPY_REQUIRED': False,
                   'FILE_SYS_LIST': [],
                   'SH_VER_TEXTFSM': [],
                   'SH_VER': '',
                   'SH_INV_TEXTFSM': [],
                   'DIR_TEXTFSM': [],
                   }
    for retry_ld in retry_list:
        try:
            device = netmiko.ConnectHandler(**{'device_type': 'cisco_ios',
                                               'host': ip,
                                               'username': uname,
                                               'password': pasw,
                                               'global_delay_factor': retry_ld,
                                               })
            netmiko.log.debug(f"\n::::: {ip}-get_version_info ::::: Sending 'show version' without TextFSM")
            localswdict['SH_VER'] = device.send_command("show version", use_textfsm=False)
            if 'Cisco' not in localswdict['SH_VER']:
                pipe.put((ip, localswdict))
                return

            # Get Version information
            netmiko.log.debug(f"\n::::: {ip}-get_version_info ::::: Sending 'show version' with TextFSM")
            localswdict['SH_VER_TEXTFSM'] = device.send_command("show version",
                                                                use_textfsm=True,
                                                                textfsm_template=Path('.', 'TextFSMTemplates',
                                                                                      'cisco_ios_show_version.textfsm'))
            if not isinstance(localswdict['SH_VER_TEXTFSM'], list):
                localswdict['SH_VER_TEXTFSM'] = device.send_command("show version",
                                                                    delay_factor=retry_ld * 2,
                                                                    use_textfsm=True,
                                                                    textfsm_template=Path('.', 'TextFSMTemplates',
                                                                                          'cisco_ios_show_version'
                                                                                          '.textfsm'))
                if not isinstance(localswdict['SH_VER_TEXTFSM'], list):
                    localswdict['SH_VER_TEXTFSM'] = list()

            # Get directory information
            netmiko.log.debug(f"\n::::: {ip}-get_version_info ::::: Sending 'dir all-filesystems' with TextFSM")
            localswdict['DIR_TEXTFSM'] = device.send_command("dir all-filesystems",
                                                             use_textfsm=True,
                                                             textfsm_template=Path('.', 'TextFSMTemplates',
                                                                                   'cisco_ios_dir.textfsm'))
            if not isinstance(localswdict['DIR_TEXTFSM'], list):
                localswdict['DIR_TEXTFSM'] = device.send_command("dir all-filesystems",
                                                                 delay_factor=retry_ld * 2,
                                                                 use_textfsm=True,
                                                                 textfsm_template=Path('.', 'TextFSMTemplates',
                                                                                       'cisco_ios_dir.textfsm'))
                if not isinstance(localswdict['DIR_TEXTFSM'], list):
                    localswdict['DIR_TEXTFSM'] = list()

            get_inv_flag = False
            for ver in localswdict['SH_VER_TEXTFSM']:
                for hw in ver.get('hardware', []):
                    for chassis_model in chassis_model_list:
                        if chassis_model in hw:
                            get_inv_flag = True

            if get_inv_flag:
                netmiko.log.debug(f"\n::::: {ip}-get_version_info ::::: Sending 'show inventory' with TextFSM")
                localswdict['SH_INV_TEXTFSM'] = device.send_command("show inventory",
                                                                    use_textfsm=True,
                                                                    textfsm_template=Path('.', 'TextFSMTemplates',
                                                                                          'cisco_ios_show_inventor'
                                                                                          'y.textfsm'))
                if not isinstance(localswdict['SH_INV_TEXTFSM'], list):
                    localswdict['SH_INV_TEXTFSM'] = device.send_command("show inventory",
                                                                        delay_factor=retry_ld * 2,
                                                                        use_textfsm=True,
                                                                        textfsm_template=Path('.', 'TextFSMTemplates',
                                                                                              'cisco_ios_show_inventory'
                                                                                              '.textfsm'))
                    if not isinstance(localswdict['SH_INV_TEXTFSM'], list):
                        localswdict['SH_INV_TEXTFSM'] = list()

            # lets check if SCP server is enabled
            netmiko.log.debug(f"\n::::: {ip}-get_version_info ::::: Sending 'show running-config | i ip scp server enable'")
            if 'ip scp server enable' not in device.send_command('show running-config | i ip scp server enable',
                                                                 max_loops=_GLOBAL_MAX_LOOPS,
                                                                 delay_factor=retry_ld * 32,
                                                                 ):
                device.send_config_set(['ip scp server enable'])
                device.save_config()

            # check if switch is running IOS or IOS-XE
            if 'Cisco IOS-XE software' in localswdict['SH_VER']:
                localswdict['CISCO_DEV_TYPE_XE'] = True

            for ver in localswdict['SH_VER_TEXTFSM']:
                # if switch is running IOS-XE check if Install mode or Bundle mode
                if localswdict['CISCO_DEV_TYPE_XE']:
                    if ver.get('running_image', '') == 'packages.conf':
                        localswdict['IOS_MODE'] = 'INSTALL'
                localswdict['RUN_IMAGE'] = ver.get('running_image', '')
                localswdict['STACK_COUNT'] = len(ver.get('hardware', []))
                break

            #find all file systems
            for file in localswdict['DIR_TEXTFSM']:
                if re.search('^(slave)?(boot)?flash-?\d?:', file.get('file_system', '')):
                    if file.get('file_system', '') not in localswdict['FILE_SYS_LIST']:
                        localswdict['FILE_SYS_LIST'].append(file.get('file_system', ''))
                if re.search('^(slave)?bootdisk-?\d?:', file.get('file_system', '')):
                    if file.get('file_system', '') not in localswdict['FILE_SYS_LIST']:
                        localswdict['FILE_SYS_LIST'].append(file.get('file_system', ''))

            # lets get patch management information
            localswdict['PATCH_MGMT_INFO'] = patchmgmt_fun.check_patch_mgmt_for_version(localswdict['SH_VER_TEXTFSM'],
                                                                                         localswdict['SH_INV_TEXTFSM'],
                                                                                         patchmgmt_data)

            # check if software copy is required
            if localswdict['PATCH_MGMT_INFO']['NOT_ON_PM_FLAG']:
                if not localswdict['CISCO_DEV_TYPE_XE']:
                    # for filesys in localswdict['FILE_SYS_LIST']:
                    for dirfile in localswdict['DIR_TEXTFSM']:
                        # if dirfile.get('file_system') == filesys:
                        if dirfile.get('name', '') == localswdict['PATCH_MGMT_INFO']['PATCH_MGMT_FILE']:
                            netmiko.log.debug(f"\n::::: {ip}-get_version_info ::::: Sending 'verify /md5 {dirfile.get('file_system', '')}{dirfile.get('name', '')}'")
                            raw_md5_check = device.send_command(f"verify /md5 {dirfile.get('file_system', '')}{dirfile.get('name', '')}",
                                                                max_loops=_GLOBAL_MAX_LOOPS,
                                                                delay_factor=retry_ld * 32,
                                                                )
                            if _CHECK_SW_MD5.search(raw_md5_check):
                                if _CHECK_SW_MD5.search(raw_md5_check)[1] == localswdict['PATCH_MGMT_INFO']['PATCH_MGMT_MD5']:
                                    localswdict['MD5_VERIFIED_NEW_FIRMWARE'] = f"{dirfile.get('file_system', '').strip('/')}{dirfile.get('name', '')}"
                                    localswdict['COPY_REQUIRED'] = False
                                    break
                                else:
                                    if _DEL_FILE_FLAG:
                                        netmiko.log.debug(f"\n::::: {ip}-get_version_info ::::: MD5 check failed! Sending 'delete /force {dirfile.get('file_system', '')}{dirfile.get('name', '')}'")
                                        device.send_command(f"delete /force {dirfile.get('file_system', '')}{dirfile.get('name', '')}",
                                                            max_loops=_GLOBAL_MAX_LOOPS,
                                                            )
                                    else:
                                        print(f"\n::::: {ip} ::::: MD5 check failed! Sending delete /force {dirfile.get('file_system', '')}{dirfile.get('name', '')}\n", end='')
                    else:
                        localswdict['COPY_REQUIRED'] = True
                else:
                    for dirfile in localswdict['DIR_TEXTFSM']:
                        if dirfile.get('name', '') == localswdict['PATCH_MGMT_INFO']['PATCH_MGMT_FILE']:
                            netmiko.log.debug(f"\n::::: {ip}-get_version_info ::::: Sending 'verify /md5 {dirfile.get('file_system', '')}{dirfile.get('name', '')}'")
                            raw_md5_check = device.send_command(f"verify /md5 {dirfile.get('file_system', '')}{dirfile.get('name', '')}",
                                                                max_loops=_GLOBAL_MAX_LOOPS,
                                                                delay_factor=retry_ld * 32,
                                                                )
                            if _CHECK_SW_MD5.search(raw_md5_check):
                                if _CHECK_SW_MD5.search(raw_md5_check)[1] == localswdict['PATCH_MGMT_INFO']['PATCH_MGMT_MD5']:
                                    localswdict['MD5_VERIFIED_NEW_FIRMWARE'] = f"{dirfile.get('file_system', '').strip('/')}{dirfile.get('name', '')}"
                                    localswdict['COPY_REQUIRED'] = False
                                    break
                                else:
                                    if _DEL_FILE_FLAG:
                                        netmiko.log.debug(f"\n::::: {ip}-get_version_info ::::: MD5 check failed! Sending 'delete /force {dirfile.get('file_system', '')}{dirfile.get('name', '')}'")
                                        device.send_command(f"delete /force {dirfile.get('file_system', '')}{dirfile.get('name', '')}",
                                                            max_loops=_GLOBAL_MAX_LOOPS,
                                                            )
                                    else:
                                        print(f"\n::::: {ip} ::::: MD5 check failed! Sending delete /force {dirfile.get('file_system', '')}{dirfile.get('name', '')}\n", end='')
                            localswdict['COPY_REQUIRED'] = True
                    else:
                        localswdict['COPY_REQUIRED'] = True

            # use IOS-XE based cleanup method to remove old files/packages
            if localswdict['CISCO_DEV_TYPE_XE']:
                if localswdict['IOS_MODE'] == 'INSTALL':
                    if localswdict['COPY_REQUIRED']:
                        if _DEL_FILE_FLAG:
                            netmiko.log.debug(f"\n::::: {ip}-get_version_info ::::: Sending 'software clean'")
                            op = device.send_command('software clean',
                                                     max_loops=_GLOBAL_MAX_LOOPS,
                                                     delay_factor=retry_ld * 32,
                                                     expect_string=r"(proceed|\#)")
                            if '% Invalid input' in op:
                                netmiko.log.debug(f"\n::::: {ip}-get_version_info ::::: Sending 'request platform software package clean switch all'")
                                op = device.send_command('request platform software package clean switch all',
                                                         max_loops=_GLOBAL_MAX_LOOPS,
                                                         delay_factor=retry_ld * 32,
                                                         expect_string=r"(proceed|\#)")
                            if 'proceed' in op:
                                netmiko.log.debug(f"\n::::: {ip}-get_version_info ::::: Sending 'y'")
                                device.send_command("y", expect_string=r"\#")
                        else:
                            print(f"\n::::: {ip} ::::: IOS-XE software cleanup\n", end='')
                else:
                    for filesys in localswdict['FILE_SYS_LIST']:
                        if _DEL_FILE_FLAG:
                            netmiko.log.debug(f"\n::::: {ip}-get_version_info ::::: deleting old packages 'delete /force {filesys}cat3k*.pkg'")
                            device.send_command(f"delete /force {filesys}cat3k*.pkg",
                                                max_loops=_GLOBAL_MAX_LOOPS,
                                                )
                            netmiko.log.debug(f"\n::::: {ip}-get_version_info ::::: deleting old packages 'delete /force {filesys}cat9k*.pkg'")
                            device.send_command(f"delete /force {filesys}cat9k*.pkg",
                                                max_loops=_GLOBAL_MAX_LOOPS,
                                                )
                            netmiko.log.debug(f"\n::::: {ip}-get_version_info ::::: deleting old packages 'delete /force {filesys}packages.conf'")
                            device.send_command(f"delete /force {filesys}packages.conf",
                                                max_loops=_GLOBAL_MAX_LOOPS,
                                                )
                        else:
                            print(f"\n::::: {ip}-get_version_info ::::: deleting old packages 'delete /force {filesys}cat3k*.pkg'")
                            print(f"\n::::: {ip}-get_version_info ::::: deleting old packages 'delete /force {filesys}cat9k*.pkg'")
                            print(f"\n::::: {ip}-get_version_info ::::: deleting old packages 'delete /force {filesys}packages.conf'")

                    for dirfile in localswdict['DIR_TEXTFSM']:
                        if dirfile.get('name', '') in localswdict['RUN_IMAGE']:
                            continue
                        if dirfile.get('name', '') in localswdict['PATCH_MGMT_INFO']['PATCH_MGMT_FILE']:
                            continue
                        if re.search('\.bin$', dirfile.get('name', '')):
                            if int(dirfile.get('size', '')) > _DEL_BIN_FILE_SIZE:
                                if _DEL_FILE_FLAG:
                                    netmiko.log.debug(f"\n::::: {ip}-get_version_info ::::: Unnecessary file found! Sending 'delete /force {dirfile.get('file_system', '')}{dirfile.get('name', '')}'")
                                    device.send_command(f"delete /force {dirfile.get('file_system', '')}{dirfile.get('name', '')}",
                                                        max_loops=_GLOBAL_MAX_LOOPS,
                                                        )
                                else:
                                    print(f"\n::::: {ip} ::::: Unnecessary file found! Sending delete /force {dirfile.get('file_system', '')}{dirfile.get('name', '')}\n", end='')

            # IOS clean up (if limited space)
            else:
                for filesys in localswdict['FILE_SYS_LIST']:
                    for dirfile in localswdict['DIR_TEXTFSM']:
                        if dirfile.get('file_system') == filesys:
                            if int(dirfile.get('total_free', '')) < int(localswdict['PATCH_MGMT_INFO']['PATCH_MGMT_SIZE']):
                                # if filename appears in running image, skip it
                                if dirfile.get('name', '') in localswdict['RUN_IMAGE']:
                                    continue
                                if dirfile.get('name', '') in localswdict['PATCH_MGMT_INFO']['PATCH_MGMT_FILE']:
                                    continue
                                if 'd' in dirfile.get('permissions', '') and ('-universal' in dirfile.get('name', '') or
                                                                      '-ipbase' in dirfile.get('name', '') or
                                                                      '-ipservices' in dirfile.get('name', '') or
                                                                      '-lanbase' in dirfile.get('name', '') or
                                                                      '-lanlite' in dirfile.get('name', '')
                                                                      ):
                                    if _DEL_FILE_FLAG:
                                        netmiko.log.debug(f"\n::::: {ip}-get_version_info ::::: Sending 'delete /recursive /force {dirfile.get('file_system', '')}{dirfile.get('name', '')}'")
                                        device.send_command(f"delete /recursive /force {dirfile.get('file_system', '')}{dirfile.get('name', '')}",
                                                            max_loops=_GLOBAL_MAX_LOOPS,
                                                            )
                                    else:
                                        print(f"\n::::: {ip} ::::: delete /recursive /force {dirfile.get('file_system', '')}{dirfile.get('name', '')}\n", end='')
                                if re.search('\.bin$', dirfile.get('name', '')):
                                    if int(dirfile.get('size', '')) > _DEL_BIN_FILE_SIZE:
                                        if _DEL_FILE_FLAG:
                                            netmiko.log.debug(f"\n::::: {ip}-get_version_info ::::: Unnecessary file found! Sending 'delete /force {dirfile.get('file_system', '')}{dirfile.get('name', '')}'")
                                            device.send_command(f"delete /force {dirfile.get('file_system', '')}{dirfile.get('name', '')}",
                                                                max_loops=_GLOBAL_MAX_LOOPS,
                                                                )
                                        else:
                                            print(f"\n::::: {ip} ::::: Unnecessary file found! Sending delete /force {dirfile.get('file_system', '')}{dirfile.get('name', '')}\n", end='')
                            else:
                                break

            localswdict['LOGIN_FAIL_FLAG'] = False
            netmiko.log.debug(f"\n::::: {ip}-get_version_info ::::: disconnecting")
            device.disconnect()
            pipe.put((ip, localswdict))
            return

        except Exception as ex:
            localswdict['LOGIN_FAIL_COMM'] += f"\n{str(type(ex).__name__)} ; {str(ex.args)}"
            print(f"\n::::: {ip}-get_version_info ::::: {str(type(ex).__name__)} ; {str(ex.args)}")
    pipe.put((ip, localswdict))
    return


if __name__ == '__main__':
    input('Please execute auto_patch.py')
    '''
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname).4s | %(funcName)s() : %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    pipe = queue.Queue()
    get_version_info('10.65.0.90',
                     os.environ.get('MDLZ_USER'),
                     os.environ.get('MDLZ_PASS'),
                     pipe,
                     patchmgmt_data=patchmgmt_fun.patchmgmtdata(),
                     )
    push_firmware_to_switch('10.65.0.20',
                            os.environ.get('MDLZ_USER'),
                            os.environ.get('MDLZ_PASS'),
                            'cat3k_caa-universalk9.16.12.03a.SPA.bin',
                            'flash:',
                            pipe)
    input('press enter to continue')
    from pprint import pprint
    pprint(pipe.get())
    pass
    #'''
