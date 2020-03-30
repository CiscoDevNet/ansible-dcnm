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

import socket
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
                    invalid_params.append('{} : Required parameter not found'.format(item))
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
                elif type == 'ipv4':
                    address = item.split('/')[0]
                    try:
                        socket.inet_aton(address)
                    except socket.error:
                        invalid_params.append('{} : Invalid IPv4 address syntax'.format(item))
                    if address.count('.') != 3:
                        invalid_params.append('{} : Invalid IPv4 address syntax'.format(item))
            valid_params_dict[param] = item
        normalized.append(valid_params_dict)

    return(normalized, invalid_params)


def get_fabric_inventory_details(module, fabric):
    method = 'GET'
    path = '/rest/control/fabrics/{}/inventory'.format(fabric)

    ip_sn = dict()
    response = dcnm_send(module, method, path)

    if response.get('RETURN_CODE') == 404:
        # RC 404 - Object not found
        return ip_sn
    if response.get('RETURN_CODE') >= 400:
        # Handle additional return codes as needed but for now raise
        # for any error other then 404.
        raise Exception(response)

    for device in response.get('DATA'):
        ip = device.get('ipAddress')
        sn = device.get('serialNumber')
        ip_sn.update({ip: sn})

    return ip_sn


def dcnm_send(module, method, path, json_data=None):

    conn = Connection(module._socket_path)
    return conn.send_request(method, path, json_data)
