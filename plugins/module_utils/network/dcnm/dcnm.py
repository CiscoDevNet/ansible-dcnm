#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

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
            valid_params_dict[param] = item
        normalized.append(valid_params_dict)

    return normalized, invalid_params


def get_fabric_inventory_details(module, fabric):

    rc = False
    method = 'GET'
    path = '/rest/control/fabrics/{}/inventory'.format(fabric)

    ip_sn = {}

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
            return ip_sn

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

        for device in response.get('DATA'):
            ip = device.get('ipAddress')
            sn = device.get('serialNumber')
            ip_sn.update({ip: sn})
            rc = True

    return ip_sn


def dcnm_get_ip_addr_info(sw_elem, ip_sn):

    msg_dict = {'Error': ''}
    msg = 'Given switch elem = "{}" is not a valid one for this fabric\n'
    msg1 = 'Given switch elem = "{}" cannot be validated, provide a valid ip_sn object\n'

    ip_addr = re.findall(r'\d+\.\d+\.\d+\.\d+', sw_elem)
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
                    raise Exception(json.dumps(msg_dict))
        except socket.gaierror:
            if (None is ip_sn):
                msg_dict['Error'] = msg1.format(sw_elem)
                raise Exception(json.dumps(msg_dict))
            # This means that the given element is neither an IP
            # address nor a host/DNS name. Assume that be a
            # Serial number. Loop up the ip_sn and verify that it is
            # a valid one. Else raise an error
            ip_addr = [k for k, v in ip_sn.items() if v == sw_elem]
            if (ip_addr):
                return ip_addr[0]
            else:
                msg_dict['Error'] = msg.format(sw_elem)
                raise Exception(json.dumps(msg_dict))
    else:
        if (None is ip_sn):
            return ip_addr[0]
        if (ip_addr[0] in ip_sn.keys()):
            return ip_addr[0]
        else:
            msg_dict['Error'] = msg.format(sw_elem)
            raise Exception(json.dumps(msg_dict))


def dcnm_send(module, method, path, json_data=None):

    conn = Connection(module._socket_path)
    return conn.send_request(method, path, json_data)
