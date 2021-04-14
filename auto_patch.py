import amdb_fun
import ipcon_fun
import patchmgmt_fun
import sys
from copy import deepcopy
from pprint import pprint
import time
from pathlib import Path
import logging
import os
import getpass
logging.basicConfig(filename=Path('.', 'LogFolder', f'lll_{time.time()}.log'), filemode='w', level=logging.DEBUG)
logger = logging.getLogger("netmiko")


def generate_copy_list(iplist):
    """
    This function created a dictionary with keys as IOS files to be sent. Values contain primary IP selected for that
    IOS and list of secondary IP addresses
    @param iplist: IP list created by main threader
    @return: dictionary of IOS to be copied to site
    """
    localdict = {}
    for ip in iplist:
        if not iplist[ip]['LOGIN_DATA']['LOGIN_FAIL_FLAG']:
            if iplist[ip]['LOGIN_DATA']['PATCH_MGMT_INFO']['NOT_ON_PM_FLAG']:
                localdict.setdefault(iplist[ip]['LOGIN_DATA']['PATCH_MGMT_INFO']['PATCH_MGMT_FILE'],
                                     {'primary': '', 'secondary': []},
                                     )

    for ios_file in localdict:
        for ip in iplist:
            if not iplist[ip]['LOGIN_DATA']['LOGIN_FAIL_FLAG']:
                for dirfile in iplist[ip]['LOGIN_DATA']['DIR_TEXTFSM']:
                    if dirfile.get('name', '') == ios_file:
                        localdict[ios_file]['primary'] = ip
                        break

    for ios_file in localdict:
        if not localdict[ios_file]['primary']:
            for ip in iplist:
                if not iplist[ip]['LOGIN_DATA']['LOGIN_FAIL_FLAG']:
                    if ios_file == iplist[ip]['LOGIN_DATA']['PATCH_MGMT_INFO']['PATCH_MGMT_FILE']:
                        localdict[ios_file]['primary'] = ip
                        break

    for ip in iplist:
        if not iplist[ip]['LOGIN_DATA']['LOGIN_FAIL_FLAG']:
            if iplist[ip]['LOGIN_DATA']['PATCH_MGMT_INFO']['NOT_ON_PM_FLAG'] and \
               iplist[ip]['LOGIN_DATA']['COPY_REQUIRED']:
                if localdict[iplist[ip]['LOGIN_DATA']['PATCH_MGMT_INFO']['PATCH_MGMT_FILE']]['primary'] != ip:
                    localdict[iplist[ip]['LOGIN_DATA']['PATCH_MGMT_INFO']['PATCH_MGMT_FILE']]['secondary'].append(ip)

    return localdict


def mainfun():
    """
    Main entrance to application
    @return:
    """

    if os.environ.get('MDLZ_SW_USER') is None:
        while True:
            _SW_UNAME = input('Please enter Username to get data from SolarWinds> ')
            if _SW_UNAME:
                break
        while True:
            _SW_PASW = getpass.getpass('Please enter Password to get data from SolarWinds> ')
            if _SW_PASW:
                break
        while True:
            choice = input('Use same credentials to login into switch? [Y/n]')
            if choice.lower() == 'n':
                while True:
                    _UNAME = input('Please enter Username to get data from SolarWinds> ')
                    if _UNAME:
                        break
                while True:
                    _PASW = getpass.getpass('Please enter Password to get data from SolarWinds> ')
                    if _PASW:
                        break
            else:
                _UNAME = _SW_UNAME
                _PASW = _SW_PASW
    else:
        _UNAME = os.environ.get('MDLZ_USER')
        _PASW = os.environ.get('MDLZ_PASS')
        _SW_UNAME = os.environ.get('MDLZ_SW_USER')
        _SW_PASW = os.environ.get('MDLZ_SW_PASS')

    _PATCHMGMTDATA = patchmgmt_fun.patchmgmtdata('patchmgmtdata.xlsx')
    _SWITCH_INVENTORY = amdb_fun.get_swdata_from_sw(uname=_SW_UNAME, pasw=_SW_PASW)

    while True:
        ipam_code = input('Please enter IPAM code to proceed, exit or quit to leave> ')
        if ipam_code.lower() == 'quit' or ipam_code.lower() == 'exit':
            sys.exit()

        iplist = {}
        for ip in _SWITCH_INVENTORY:
            if _SWITCH_INVENTORY[ip]['IPAM'].lower() == ipam_code:
                iplist[ip] = deepcopy(_SWITCH_INVENTORY[ip])
        if not iplist:
            print(f"Couldn't find any switch belonging to IPAM code {ipam_code}")
            continue

        # lets get basic info from switches and clear space if required
        ipcon_fun.main_threader(iplist, _PATCHMGMTDATA, uname=_UNAME, pasw=_PASW)

        # for this site, find a primary switch (preferably without copy requirement)
        copy_list = generate_copy_list(iplist)

        pprint(copy_list)
        input('press any key to continue...')
        import pickle
        with open('results.pkl', 'wb') as pkl:
            pickle.dump(iplist, pkl, pickle.HIGHEST_PROTOCOL)

        ipcon_fun.copy_threader(iplist, copy_list, uname=_UNAME, pasw=_PASW)

    return


if __name__ == '__main__':
    mainfun()
