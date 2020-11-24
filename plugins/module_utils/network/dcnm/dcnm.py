#!/usr/bin/python
#
# Copyright (c) 2020 Cisco and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import socket
import json
import time
from ansible.module_utils.common import validation
from ansible.module_utils.connection import Connection

def validate_list_of_dicts(param_list, spec):
    """ Validate/Normalize playbook params. Will raise when invalid parameters found.
    param_list: a playbook parameter list of dicts
    spec: an argument spec dict
          e.g. spec = dict(ip=dict(required=True, type='ipv4'),
                           foo=dict(type='str', default='bar'))
    return: list of normalized input data
    """
    v = validation
    normalized = []
    invalid_params = []
    for list_entry in param_list:
        valid_params_dict = {}
        for param in spec:
            item = list_entry.get(param)
            if item is None:
                if spec[param].get('required'):
                    invalid_params.append('{} : Required parameter not found'.format(param))
                else:
                    item = spec[param].get('default')
            else:
                type = spec[param].get('type')
                if type == 'str':
                    item = v.check_type_str(item)
                    if spec[param].get('length_max'):
                        if 1 <= len(item) <= spec[param].get('length_max'):
                            pass
                        else:
                            invalid_params.append('{}:{} : The string exceeds the allowed '
                                                  'range of max {} char'.format(param, item,
                                                                                spec[param].get('length_max')))
                elif type == 'int':
                    item = v.check_type_int(item)
                    if spec[param].get('range_max'):
                        if 1 <= item <= spec[param].get('range_max'):
                            pass
                        else:
                            invalid_params.append('{}:{} : The item exceeds the allowed '
                                                  'range of max {}'.format(param, item,
                                                                           spec[param].get('range_max')))
                elif type == 'bool':
                    item = v.check_type_bool(item)
                elif type == 'list':
                    item = v.check_type_list(item)
                elif type == 'dict':
                    item = v.check_type_dict(item)
                elif ((type == 'ipv4_subnet') or (type == 'ipv4')):
                    address = item.split('/')[0]
                    if type == 'ipv4_subnet':
                        if '/' in item:
                            subnet = item.split('/')[1]
                            if not subnet or int(subnet) > 32:
                                invalid_params.append('{} : Invalid IPv4 gw/subnet syntax'.format(item))
                        else:
                            invalid_params.append('{} : Invalid IPv4 gw/subnet syntax'.format(item))
                    try:
                        socket.inet_aton(address)
                    except socket.error:
                        invalid_params.append('{} : Invalid IPv4 address syntax'.format(item))
                    if address.count('.') != 3:
                        invalid_params.append('{} : Invalid IPv4 address syntax'.format(item))

                choice = spec[param].get('choices')
                if choice:
                    if item not in choice:
                        invalid_params.append('{} : Invalid choice provided'.format(item))

            valid_params_dict[param] = item
        normalized.append(valid_params_dict)

    return normalized, invalid_params


def get_fabric_inventory_details(module, fabric):

    inventory_data = {}
    rc = False
    method = 'GET'
    path = '/rest/control/fabrics/{}/inventory'.format(fabric)

    count = 1
    while (rc is False):

        response = dcnm_send(module, method, path)

        with open("dcnm_fab.log", "w") as f:
            f.write("FAB RESP = {}\n".format(response))
        if not response.get('RETURN_CODE'):
            rc = True
            module.fail_json(msg=response)

        if response.get('RETURN_CODE') == 404:
            # RC 404 - Object not found
            rc = True
            return inventory_data

        if response.get('RETURN_CODE') == 401:
            # RC 401: Server not reachable. Retry a few times
            if (count <= 20):
                count = count + 1
                rc = False
                time.sleep(0.1)
                continue
            else:
                raise Exception(response)
        elif response.get('RETURN_CODE') >= 400:
            # Handle additional return codes as needed but for now raise
            # for any error other then 404.
            raise Exception(response)

        for device_data in response.get('DATA'):
            key = device_data.get('ipAddress')
            inventory_data[key] = device_data
        rc = True

    return inventory_data


def get_ip_sn_dict(inventory_data):

    ip_sn = {}
    hn_sn = {}

    for device_key in inventory_data.keys():
        ip = inventory_data[device_key].get('ipAddress')
        sn = inventory_data[device_key].get('serialNumber')
        hn = inventory_data[device_key].get('logicalName')
        ip_sn.update({ip: sn})
        hn_sn.update({hn: sn})

    return ip_sn, hn_sn


# sw_elem can be ip_addr, hostname, dns name or serial number. If the given
# sw_elem is ip_addr, then it is returned as is. If DNS or hostname then a DNS
# lookup is performed to get the IP address to be returned. If not ip_sn
# database (if not none) is looked up to find the mapping IP address which is
# returned
def dcnm_get_ip_addr_info(module, sw_elem, ip_sn, hn_sn):

    msg_dict = {'Error': ''}
    msg = 'Given switch elem = "{}" is not a valid one for this fabric\n'
    msg1 = 'Given switch elem = "{}" cannot be validated, provide a valid ip_sn object\n'

    # Check if the given sw_elem is a v4 ip_addr
    try:
        socket.inet_pton(socket.AF_INET, sw_elem)
        ip_addr = sw_elem
    except socket.error:
        # Check if the given sw_elem is a v6 ip_addr
        try:
            socket.inet_pton(socket.AF_INET6, sw_elem)
            ip_addr = sw_elem
        except socket.error:
            # Not legal
            ip_addr = []
    if (ip_addr == []):
        # Given element is not an IP address. Try DNS or
        # hostname
        try:
            addr_info = socket.getaddrinfo(sw_elem, 0, socket.AF_INET, 0, 0, 0)
            if (None is ip_sn):
                return addr_info[0][4][0]
            if addr_info:
                if (addr_info[0][4][0] in ip_sn.keys()):
                    return addr_info[0][4][0]
                else:
                    msg_dict['Error'] = msg.format(sw_elem)
                    raise module.fail_json(msg=json.dumps(msg_dict))
        except socket.gaierror:
            if (None is ip_sn):
                msg_dict['Error'] = msg1.format(sw_elem)
                raise module.fail_json(msg=json.dumps(msg_dict))
            # This means that the given element is neither an IP
            # address nor a DNS name.
            # First look up hn_sn. Get the serial number and look up ip_sn to
            # get the IP address.
            sno = None
            if (None is not hn_sn):
                sno = hn_sn.get(sw_elem, None)
            if (sno is not None):
                ip_addr = [k for k, v in ip_sn.items() if v == sno]
            else:
                ip_addr = [k for k, v in ip_sn.items() if v == sw_elem]
            if (ip_addr):
                return ip_addr[0]
            else:
                msg_dict['Error'] = msg.format(sw_elem)
                raise module.fail_json(msg=json.dumps(msg_dict))
    else:
        # Given sw_elem is an ip_addr. check if this is valid
        if (None is ip_sn):
            return ip_addr
        if (ip_addr in ip_sn.keys()):
            return ip_addr
        else:
            msg_dict['Error'] = msg.format(sw_elem)
            raise module.fail_json(msg=json.dumps(msg_dict))

# def dcnm_get_ip_addr_info(sw_elem, ip_sn):
#
#     msg_dict = {'Error': ''}
#     msg = 'Given switch elem = "{}" is not a valid one for this fabric\n'
#     msg1 = 'Given switch elem = "{}" cannot be validated, provide a valid ip_sn object\n'
#
#     ip_addr = re.findall(r'\d+\.\d+\.\d+\.\d+', sw_elem)
#     if (ip_addr == []):
#         # Given element is not an IP address. Try DNS or
#         # hostname
#         try:
#             addr_info = socket.getaddrinfo(sw_elem, 0, socket.AF_INET, 0, 0, 0)
#             if (None is ip_sn):
#                 return addr_info[0][4][0]
#             if addr_info:
#                 if (addr_info[0][4][0] in ip_sn.keys()):
#                     return addr_info[0][4][0]
#                 else:
#                     msg_dict['Error'] = msg.format(sw_elem)
#                     raise Exception(json.dumps(msg_dict))
#         except socket.gaierror:
#             if (None is ip_sn):
#                 msg_dict['Error'] = msg1.format(sw_elem)
#                 raise Exception(json.dumps(msg_dict))
#             # This means that the given element is neither an IP
#             # address nor a host/DNS name. Assume that be a
#             # Serial number. Loop up the ip_sn and verify that it is
#             # a valid one. Else raise an error
#             ip_addr = [k for k, v in ip_sn.items() if v == sw_elem]
#             if (ip_addr):
#                 return ip_addr[0]
#             else:
#                 msg_dict['Error'] = msg.format(sw_elem)
#                 raise Exception(json.dumps(msg_dict))
#     else:
#         if (None is ip_sn):
#             return ip_addr[0]
#         if (ip_addr[0] in ip_sn.keys()):
#             return ip_addr[0]
#         else:
#             msg_dict['Error'] = msg.format(sw_elem)
#             raise Exception(json.dumps(msg_dict))


def dcnm_send(module, method, path, data=None, data_type='json'):

    conn = Connection(module._socket_path)

    if (data_type == 'json'):
        return conn.send_request(method, path, data)
    elif (data_type == 'text'):
        return conn.send_txt_request(method, path, data)
