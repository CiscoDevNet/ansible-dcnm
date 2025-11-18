# Copyright (c) 2020-2022 Cisco and/or its affiliates.
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
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import socket
import json
import time
import html
import re
import os
import sys
from ansible.module_utils.common import validation
from ansible.module_utils.connection import Connection

# Any third party module must be imported as shown. If not ansible sanity tests will fail
try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

dcnm_paths = {
    11: {"TEMPLATE_WITH_NAME": "/rest/config/templates/{}"},
    12: {
        "TEMPLATE_WITH_NAME": "/appcenter/cisco/ndfc/api/v1/configtemplate/rest/config/templates/{}"
    },
}

dcnm_template_type_xlations = {
    "string": "str",
    "string[]": "list",
    "integer": "int",
    "long": "int",
    "ipV4Address": "ipv4",
    "ipV6Address": "ipv6",
    "ipAddress": "ipv4",
    "interfaceRange": "list",
    "boolean": "bool",
    "enum": "str",
    "ipV4AddressWithSubnet": "ipv4_subnet",
    "ipV6AddressWithSubnet": "ipv6_subnet",
}


def validate_ip_address_format(type, item, invalid_params):

    if (type == "ipv4_subnet") or (type == "ipv4"):
        addr_type = "IPv4"
        addr_family = socket.AF_INET
        mask_len = 32
    if (type == "ipv6_subnet") or (type == "ipv6"):
        addr_type = "IPv6"
        addr_family = socket.AF_INET6
        mask_len = 128

    if item.strip() != "":
        address = item.split("/")[0]
        if "subnet" in type:
            if "/" in item:
                subnet = item.split("/")[1]
                if not subnet or int(subnet) > mask_len:
                    invalid_params.append(
                        "{0} : Invalid {1} gw/subnet syntax".format(item, addr_type)
                    )
            else:
                invalid_params.append(
                    "{0} : Invalid {1} gw/subnet syntax".format(item, addr_type)
                )
        try:
            socket.inet_pton(addr_family, address)
        except socket.error:
            invalid_params.append(
                "{0} : Invalid {1} address syntax".format(item, addr_type)
            )


def find_extra_params(param_list, spec):
    """
    Checks for extra parameters in each dictionary of a list
    when compared against a specification dictionary.

    Args:
        param_list: A list of dictionaries containing parameters.
        spec: A dictionary where keys are the valid parameter names.

    Returns:
        A list of extra parameters found. If a parameter is found in
        multiple dictionaries in the list, it will appear multiple
        times in the result.
    """
    invalid_params = []
    spec_keys = set(spec.keys())

    for params in param_list:
        param_keys = set(params.keys())
        extra_keys = param_keys - spec_keys
        if extra_keys:
            invalid_params.extend(list(extra_keys))

    return invalid_params


def validate_list_of_dicts(param_list, spec, module=None, check_extra_params=False):
    """Validate/Normalize playbook params. Will raise when invalid parameters found.
    param_list: a playbook parameter list of dicts
    spec: an argument spec dict
          e.g. spec = dict(ip=dict(required=True, type='ipv4'),
                           foo=dict(type='str', default='bar'))
    return: list of normalized input data
    """
    v = validation
    normalized = []
    invalid_params = []
    if check_extra_params:
        invalid_params = find_extra_params(param_list, spec)
    for list_entry in param_list:
        valid_params_dict = {}
        for param in spec:
            item = list_entry.get(param)
            if item is None:
                if spec[param].get("required"):
                    invalid_params.append(
                        "{0} : Required parameter not found".format(param)
                    )
                else:
                    item = spec[param].get("default")
            else:
                type = spec[param].get("type")
                if type == "str":
                    item = v.check_type_str(item)
                    if spec[param].get("length_max"):
                        if 1 <= len(item) <= spec[param].get("length_max"):
                            pass
                        elif param == "vrf_name" and (
                            len(item) <= spec[param].get("length_max")
                        ):
                            pass
                        else:
                            invalid_params.append(
                                "{0}:{1} : The string exceeds the allowed "
                                "range of max {2} char".format(
                                    param, item, spec[param].get("length_max")
                                )
                            )
                elif type == "int":
                    item = v.check_type_int(item)
                    min_value = 1
                    if spec[param].get("range_min") is not None:
                        min_value = spec[param].get("range_min")
                    if spec[param].get("range_max"):
                        if min_value <= item <= spec[param].get("range_max"):
                            pass
                        else:
                            invalid_params.append(
                                "{0}:{1} : The item exceeds the allowed "
                                "range of max {2}".format(
                                    param, item, spec[param].get("range_max")
                                )
                            )
                elif type == "bool":
                    item = v.check_type_bool(item)
                elif type == "list":
                    item = v.check_type_list(item)
                elif type == "dict":
                    item = v.check_type_dict(item)
                elif (
                    (type == "ipv4_subnet")
                    or (type == "ipv4")
                    or (type == "ipv6_subnet")
                    or (type == "ipv6")
                ):
                    validate_ip_address_format(type, item, invalid_params)

                choice = spec[param].get("choices")
                if choice:
                    if item not in choice:
                        invalid_params.append(
                            "{0} : Invalid choice [ {0} ] provided for param [ {1} ]".format(
                                item, param
                            )
                        )

                no_log = spec[param].get("no_log")
                if no_log:
                    if module is not None:
                        module.no_log_values.add(item)
                    else:
                        msg = "\n\n'{0}' is a no_log parameter".format(param)
                        msg += "\nAnsible module object must be passed to this "
                        msg += "\nfunction to ensure it is not logged\n\n"
                        raise Exception(msg)

            valid_params_dict[param] = item
        normalized.append(valid_params_dict)

    return normalized, invalid_params


def get_fabric_inventory_details(module, fabric):

    inventory_data = {}
    rc = False
    method = "GET"
    path = "/rest/control/fabrics/{0}/inventory".format(fabric)

    conn = Connection(module._socket_path)
    if conn.get_version() == 12:
        path = "/appcenter/cisco/ndfc/api/v1/lan-fabric" + path
        path += "/switchesByFabric"

    count = 1
    while rc is False:

        response = dcnm_send(module, method, path)

        if not response.get("RETURN_CODE"):
            rc = True
            module.fail_json(msg=response)

        if response.get("RETURN_CODE") == 404:
            # RC 404 - Object not found
            rc = True
            return inventory_data

        if response.get("RETURN_CODE") == 401:
            # RC 401: Server not reachable. Retry a few times
            if count <= 20:
                count = count + 1
                rc = False
                time.sleep(0.1)
                continue

            raise Exception(response)
        elif response.get("RETURN_CODE") >= 400:
            # Handle additional return codes as needed but for now raise
            # for any error other then 404.
            raise Exception(response)

        for device_data in response.get("DATA"):

            if device_data.get("ipAddress", "") != "":
                key = device_data.get("ipAddress")
            else:
                key = device_data.get("logicalName")
            inventory_data[key] = device_data
        rc = True
    return inventory_data


def get_ip_sn_dict(inventory_data):

    ip_sn = {}
    hn_sn = {}

    for device_key in inventory_data.keys():
        ip = inventory_data[device_key].get("ipAddress")
        sn = inventory_data[device_key].get("serialNumber")
        hn = inventory_data[device_key].get("logicalName")

        if ip != "":
            ip_sn.update({ip: sn})
        hn_sn.update({hn: sn})

    return ip_sn, hn_sn


# This call is mainly used while configuraing multisite fabrics.
# It maps the switch IP Address/Serial No. in the multisite inventory
# data to respective member site fabric name to which it was actually added.
def get_ip_sn_fabric_dict(inventory_data):
    """
    Maps the switch IP Address/Serial No. in the multisite inventory
    data to respective member site fabric name to which it was actually added.

    Parameters:
        inventory_data: Fabric inventory data

    Returns:
        dict: Switch ip - fabric_name mapping
        dict: Switch serial_no - fabric_name mapping
    """
    ip_fab = {}
    sn_fab = {}

    for device_key in inventory_data.keys():
        ip = inventory_data[device_key].get("ipAddress")
        sn = inventory_data[device_key].get("serialNumber")
        fabric_name = inventory_data[device_key].get("fabricName")
        ip_fab.update({ip: fabric_name})
        sn_fab.update({sn: fabric_name})

    return ip_fab, sn_fab


def get_ip_fabric_dict(inventory_data):
    """
    Maps the switch ip address to the switch's member fabric.

    Parameters:
        inventory_data: Fabric inventory data

    Raises:

        ValueError, if inventory_data does not contain ipAddress
        or fabricName.

    Returns:
        dict: Switch ip address - fabric_name mapping
    """
    mapping_dict = {}
    for device_key in inventory_data.keys():
        ip_address = inventory_data[device_key].get("ipAddress")
        fabric_name = inventory_data[device_key].get("fabricName")
        if ip_address is None:
            msg = "Cannot parse ipAddress from inventory_data:"
            msg += f"{json.dumps(inventory_data, indent=4, sort_keys=True)}"
            raise ValueError(msg)
        if fabric_name is None:
            msg = "Cannot parse fabricName from inventory_data:"
            msg += f"{json.dumps(inventory_data, indent=4, sort_keys=True)}"
            raise ValueError(msg)
        mapping_dict.update({ip_address: fabric_name})
    return copy.deepcopy(mapping_dict)


def get_sn_fabric_dict(inventory_data):
    """
    Maps the switch serial number to the switch's member fabric.

    Parameters:
        inventory_data: Fabric inventory data

    Raises:

        ValueError, if inventory_data does not contain serialNumber
        or fabricName.

    Returns:
        dict: Switch serial number - fabric_name mapping
    """
    mapping_dict = {}
    for device_key in inventory_data.keys():
        serial_number = inventory_data[device_key].get("serialNumber")
        fabric_name = inventory_data[device_key].get("fabricName")
        if serial_number is None:
            msg = "Cannot parse serial_number from inventory_data:"
            msg += f"{json.dumps(inventory_data, indent=4, sort_keys=True)}"
            raise ValueError(msg)
        if fabric_name is None:
            msg = "Cannot parse fabric_name from inventory_data:"
            msg += f"{json.dumps(inventory_data, indent=4, sort_keys=True)}"
            raise ValueError(msg)
        mapping_dict.update({serial_number: fabric_name})
    return copy.deepcopy(mapping_dict)


# sw_elem can be ip_addr, hostname, dns name or serial number. If the given
# sw_elem is ip_addr, then it is returned as is. If DNS or hostname then a DNS
# lookup is performed to get the IP address to be returned. If not ip_sn
# database (if not none) is looked up to find the mapping IP address which is
# returned
def dcnm_get_ip_addr_info(module, sw_elem, ip_sn, hn_sn):

    msg_dict = {"Error": ""}
    msg = 'Given switch elem = "{}" is not a valid one for this fabric\n'
    msg1 = (
        'Given switch elem = "{}" cannot be validated, provide a valid ip_sn object\n'
    )

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

    if ip_addr == []:
        # Given element is not an IP address. Try DNS or
        # hostname
        try:
            addr_info = socket.getaddrinfo(sw_elem, 0, socket.AF_INET, 0, 0, 0)
            if None is ip_sn:
                return addr_info[0][4][0]
            if addr_info:
                if addr_info[0][4][0] in ip_sn.keys():
                    return addr_info[0][4][0]
                else:
                    msg_dict["Error"] = msg.format(sw_elem)
                    raise module.fail_json(msg=json.dumps(msg_dict))
        except socket.gaierror:
            if None is ip_sn:
                msg_dict["Error"] = msg1.format(sw_elem)
                raise module.fail_json(msg=json.dumps(msg_dict))
            # This means that the given element is neither an IP
            # address nor a DNS name.
            # First look up hn_sn. Get the serial number and look up ip_sn to
            # get the IP address.
            sno = None
            if None is not hn_sn:
                sno = hn_sn.get(sw_elem, None)
            if sno is not None:
                ip_addr = [k for k, v in ip_sn.items() if v == sno]
            else:
                ip_addr = [k for k, v in ip_sn.items() if v == sw_elem]
            if ip_addr:
                return ip_addr[0]
            else:
                msg_dict["Error"] = msg.format(sw_elem)
                raise module.fail_json(msg=json.dumps(msg_dict))
    else:
        # Given sw_elem is an ip_addr. check if this is valid
        if None is ip_sn:
            return ip_addr
        if ip_addr in ip_sn.keys():
            return ip_addr
        else:
            msg_dict["Error"] = msg.format(sw_elem)
            raise module.fail_json(msg=json.dumps(msg_dict))


# This call is used to get the details of the given fabric from the DCNM
def get_fabric_details(module, fabric):
    """
    Used to get the details of the given fabric from the DCNM

    Parameters:
        module: Data for module under execution
        fabric: Fabric name

    Returns:
        dict: Fabric details
    """
    fabric_data = {}
    rc = False
    method = "GET"
    path = "/rest/control/fabrics/{0}".format(fabric)

    conn = Connection(module._socket_path)
    if conn.get_version() == 12:
        path = "/appcenter/cisco/ndfc/api/v1/lan-fabric" + path

    count = 1
    while rc is False:

        response = dcnm_send(module, method, path)

        if not response.get("RETURN_CODE"):
            rc = True
            module.fail_json(msg=response)

        if response.get("RETURN_CODE") == 404:
            # RC 404 - Object not found
            rc = True
            return fabric_data

        if response.get("RETURN_CODE") == 401:
            # RC 401: Server not reachable. Retry a few times
            if count <= 20:
                count = count + 1
                rc = False
                time.sleep(0.1)
                continue

            raise Exception(response)
        elif response.get("RETURN_CODE") >= 400:
            # Handle additional return codes as needed but for now raise
            # for any error other then 404.
            raise Exception(response)

        fabric_data = response.get("DATA")
        rc = True

    return fabric_data


def dcnm_send(module, method, path, data=None, data_type="json"):

    conn = Connection(module._socket_path)

    if data_type == "json":
        return conn.send_request(method, path, data)
    elif data_type == "urlencoded":
        return conn.send_urlencoded_request(method, path, data)
    elif data_type == "text":
        return conn.send_txt_request(method, path, data)


def dcnm_reset_connection(module):

    conn = Connection(module._socket_path)

    return conn.login(conn.get_option("remote_user"), conn.get_option("password"))


def dcnm_version_supported(module):
    """
    Query DCNM/NDFC and return the major software version

    Parameters:
        module: String representing the module

    Returns:
        int: Major software version for DCNM/NDFC
    """

    method = "GET"
    supported = None
    data = None

    paths = [
        "/fm/fmrest/about/version",
        "/appcenter/cisco/ndfc/api/about/version",
    ]
    for path in paths:
        response = dcnm_send(module, method, path)
        if response["RETURN_CODE"] == 200:
            data = response.get("DATA")
            break

    if data:
        # Parse version information
        # Examples:
        #   11.5(1), 12.0.1a'
        # For these examples 11 or 12 would be returned
        raw_version = data["version"]

        if raw_version == "DEVEL":
            raw_version = "11.5(1)"

        regex = r"^(\d+)\.\d+"
        mo = re.search(regex, raw_version)
        if mo:
            supported = int(mo.group(1))

    if supported is None:
        msg = (
            "Unable to determine the DCNM/NDFC Software Version, "
            + "RESP = "
            + str(response)
        )
        module.fail_json(msg=msg)

    return supported


def parse_response(response):

    if response.get("ERROR") == "Not Found" and response["RETURN_CODE"] == 404:
        return True, False
    if response["RETURN_CODE"] != 200 or response["MESSAGE"] != "OK":
        return False, True
    return False, False


def dcnm_get_url(module, fabric, path, items, module_name):
    """
    Query DCNM/NDFC and return query values.
    Some queries like network/vrf queries send thier names
    as part of URL. This method sends multiple queries and returns
    a consolidated response if the url exceeds 6144 characters.

    Parameters:
        module: String representing the module
        fabric: String representing the fabric
        path: String representing the path to query
        items: String representing query items
        module_name: String representing the name of calling module

    Returns:
        dict: Response DATA from DCNM/NDFC
    """

    method = "GET"
    send_count = 1

    # NDFC/DCNM12 can handle urls upto 6144 characters.
    # The size here represents the total size of all item names.
    # The number 5900 has been arrived after making some room
    # for query path(url)
    if sys.getsizeof(items) > 5900:
        if (sys.getsizeof(items) % 5900) == 0:
            send_count = sys.getsizeof(items) / 5900
        else:
            send_count = sys.getsizeof(items) // 5900 + 1

    itemlist = items.split(",")

    iter = 0
    while iter < send_count:
        if send_count == 1:
            url = path.format(fabric, items)
        elif iter != (send_count - 1):
            itemstr = ",".join(
                itemlist[
                    (iter * (len(itemlist) // send_count)): (
                        (iter + 1) * (len(itemlist) // send_count)
                    )
                ]
            )
            url = path.format(fabric, itemstr)
        else:
            itemstr = ",".join(itemlist[iter * (len(itemlist) // send_count):])
            url = path.format(fabric, itemstr)

        att_objects = dcnm_send(module, method, url)

        missing_fabric, not_ok = parse_response(att_objects)

        if missing_fabric or not_ok:
            msg1 = "Fabric {0} not present on DCNM".format(fabric)
            msg2 = "Unable to find " "{0}: {1} under fabric: {2}".format(
                module_name, items[:-1], fabric
            )

            module.fail_json(msg=msg1 if missing_fabric else msg2)
            return

        if iter == 0:
            attach_objects = att_objects
        else:
            attach_objects["DATA"].extend(att_objects["DATA"])

        iter += 1

    return attach_objects


def dcnm_load_mapping_data():

    path = os.path.join("./", "{0}.json".format("type_mappings"))

    with open(path) as f:
        data = f.read()

    try:
        j_data = json.loads(data)
    except Exception:
        pass

    return j_data


def dcnm_get_template_details(module, version, name):

    resp = dcnm_send(
        module, "GET", dcnm_paths[version]["TEMPLATE_WITH_NAME"].format(name)
    )

    if resp and resp["RETURN_CODE"] == 200 and resp["MESSAGE"] == "OK" and resp["DATA"]:
        if resp["DATA"]["name"] == name:
            return resp["DATA"]
        else:
            return []


def dcnm_update_arg_specs(mspec, arg_specs):
    """
    Update argument specifications based on module specification dependencies.

    ## Summary

    Evaluates boolean dependency expressions to determine if parameters are required.

    ## Raises

    - None
    """
    comparison_ops = {
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
        ">": lambda a, b: a > b,
        "<": lambda a, b: a < b,
        ">=": lambda a, b: a >= b,
        "<=": lambda a, b: a <= b,
    }

    pat = re.compile(r"(\w+)\s*([<>=!]{1,2})\s*(\w+)")

    for as_key in arg_specs:
        item = arg_specs[as_key]

        if item["required"] not in [True, False]:
            # Parse the dependency expression
            expr = item["required"]

            # Normalize true/false to boolean values
            expr = expr.replace("true", "True").replace("false", "False")

            # Split by && and || operators, tracking which operator was used
            parts = []
            operators = []

            # Split while preserving operator information
            if "&&" in expr and "||" in expr:
                # Handle mixed operators (would need more complex logic)
                # For now, fall back to simple evaluation
                pass
            elif "&&" in expr:
                parts = [p.strip() for p in expr.split("&&")]
                operators = ["and"] * (len(parts) - 1)
            elif "||" in expr:
                parts = [p.strip() for p in expr.split("||")]
                operators = ["or"] * (len(parts) - 1)
            else:
                parts = [expr.strip()]

            # Evaluate each part
            results = []
            for part in parts:
                part = part.strip("() ")
                match = pat.search(part)

                if match:
                    key = match[1]
                    op = match[2]
                    value_str = match[3]

                    # Convert string "True"/"False" to boolean
                    if value_str in ("True", "False"):
                        expected_value = value_str == "True"
                    else:
                        expected_value = value_str

                    # Get actual value from mspec
                    actual_value = mspec.get(key) if mspec else None

                    # Evaluate the comparison
                    if op in comparison_ops:
                        results.append(comparison_ops[op](actual_value, expected_value))
                    else:
                        results.append(False)
                else:
                    # Direct True/False value
                    results.append(part == "True")

            # Combine results based on operators
            if not operators:
                item["required"] = results[0] if results else False
            else:
                final_result = results[0]
                for i, op in enumerate(operators):
                    if op == "and":
                        final_result = final_result and results[i + 1]
                    else:  # "or"
                        final_result = final_result or results[i + 1]
                item["required"] = final_result


def dcnm_get_template_specs(module, name, version):

    template_payload = dcnm_get_template_details(module, version, name)

    if template_payload:

        pb_template = {name: {}, name + "_spec": {}, name + "_playbook": {}}

        # 'policy': {'required': 'True', 'type': 'str', 'choices': ['int_vlan', 'int_vlan_admin_state'], 'range_min': 8, 'range_max': 256}
        for p in template_payload["parameters"]:

            pb_template[name][p["name"]] = ""
            pb_template[name + "_playbook"][p["name"]] = ""
            pb_template[name + "_spec"][p["name"]] = {}
            pname_len = len(p["name"])

            pb_template[name][p["name"]] += html.unescape(
                " " * (40 - pname_len)
                + "# Description: "
                + p["annotations"].get("Description", "NA")
            )

            if "IsShow" in p["annotations"]:
                pb_template[name][p["name"]] += ", Mandatory: " + p["annotations"][
                    "IsShow"
                ].replace('"', "")
                pb_template[name + "_spec"][p["name"]]["required"] = p["annotations"][
                    "IsShow"
                ].replace('"', "")
            else:
                # If 'defaultValue' is included, then the object can be marked as optional.
                if p["metaProperties"].get("defaultValue", None) is not None:
                    pb_template[name][p["name"]] += ", Mandatory: False"
                    pb_template[name + "_spec"][p["name"]]["required"] = False
                else:
                    pb_template[name][p["name"]] += ", Mandatory: " + str(
                        not (p["optional"])
                    )
                    pb_template[name + "_spec"][p["name"]]["required"] = bool(
                        not (p["optional"])
                    )

            if p["metaProperties"].get("min", None) is not None:
                pb_template[name][p["name"]] += ", Min: " + str(
                    p["metaProperties"]["min"]
                )
                pb_template[name + "_spec"][p["name"]]["range_min"] = int(
                    p["metaProperties"]["min"]
                )
            if p["metaProperties"].get("max", None) is not None:
                pb_template[name][p["name"]] += ", Max: " + str(
                    p["metaProperties"]["max"]
                )
                pb_template[name + "_spec"][p["name"]]["range_max"] = int(
                    p["metaProperties"]["max"]
                )
            if p["metaProperties"].get("minLength", None) is not None:
                pb_template[name][p["name"]] += ", MinLen: " + str(
                    p["metaProperties"]["minLength"]
                )
                pb_template[name + "_spec"][p["name"]]["range_min"] = int(
                    p["metaProperties"]["minLength"]
                )
            if p["metaProperties"].get("maxLength", None) is not None:
                pb_template[name][p["name"]] += ", MaxLen: " + str(
                    p["metaProperties"]["maxLength"]
                )
                pb_template[name + "_spec"][p["name"]]["range_max"] = int(
                    p["metaProperties"]["maxLength"]
                )
            if p["metaProperties"].get("validValues", None) is not None:
                pb_template[name][p["name"]] += ", ValidValues: " + str(
                    str(p["metaProperties"]["validValues"]).split(",")
                )
                pb_template[name + "_spec"][p["name"]]["choices"] = str(
                    p["metaProperties"]["validValues"]
                ).split(",")
            if p.get("parameterType", None) is not None:
                pb_template[name][p["name"]] += (
                    ", Type: " + dcnm_template_type_xlations[str(p["parameterType"])]
                )
                pb_template[name + "_spec"][p["name"]]["type"] = (
                    dcnm_template_type_xlations[p["parameterType"]]
                )
                if p.get("parameterType") == "string[]":
                    pb_template[name][p["name"]] += ", elements: " + "str"
                    pb_template[name + "_spec"][p["name"]]["type"] = (
                        dcnm_template_type_xlations[p["parameterType"]]
                    )
                    pb_template[name + "_spec"][p["name"]]["elements"] = "str"

            if p["metaProperties"].get("defaultValue", None) is not None:
                pb_template[name][p["name"]] += ", Default: " + str(
                    p["metaProperties"]["defaultValue"].replace('""', "")
                )
                if pb_template[name + "_spec"][p["name"]]["type"] == "int":
                    if p["metaProperties"]["defaultValue"] == "":
                        pb_template[name + "_spec"][p["name"]]["default"] = p[
                            "metaProperties"
                        ]["defaultValue"].replace('""', "")
                    else:
                        pb_template[name + "_spec"][p["name"]]["default"] = int(
                            p["metaProperties"]["defaultValue"]
                        )
                else:
                    pb_template[name + "_spec"][p["name"]]["default"] = p[
                        "metaProperties"
                    ]["defaultValue"].replace('""', "")
            else:
                pb_template[name][p["name"]] += ", Default: ''"
                pb_template[name + "_spec"][p["name"]]["default"] = ""

        return pb_template


# The following functions are used for uploading images to DCNM. We use "requests" module to send multi-part-frames to DCNM
# which requires, auth headers and the correct URL. The requests.post method will encode the multi-part-frames appropriately
# and sends the fragments to DCNM/NDFC. It requires a complete path, all headers and the file to be uploaded.
def dcnm_get_protocol_and_address(module):

    conn = Connection(module._socket_path)

    url_prefix = conn.get_url_connection()
    split_url = url_prefix.split(":")

    return [split_url[0], split_url[1]]


def dcnm_get_auth_token(module):

    conn = Connection(module._socket_path)
    return conn.get_token()


def dcnm_post_request(path, hdrs, verify_flag, upload_files):

    resp = requests.post(path, headers=hdrs, verify=verify_flag, files=upload_files)
    json_resp = resp.json()
    if json_resp:
        json_resp["RETURN_CODE"] = resp.status_code
        json_resp["DATA"] = json_resp["message"]
        json_resp["METHOD"] = "POST"
        json_resp["REQUEST_PATH"] = path
        json_resp.pop("message")
    return json_resp


def find_dict_in_list_by_key_value(search: list, key: str, value: str):
    """
    # Summary

    Find a dictionary in a list of dictionaries.


    ## Raises

    None

    ## Parameters

    -   search: A list of dict
    -   key: The key to lookup in each dict
    -   value: The desired matching value for key

    ## Returns

    Either the first matching dict or None

    ## Usage

    ```python
    content = [{"foo": "bar"}, {"foo": "baz"}]

    match = find_dict_in_list_by_key_value(search=content, key="foo", value="baz")
    print(f"{match}")
    # -> {"foo": "baz"}

    match = find_dict_in_list_by_key_value(search=content, key="foo", value="bingo")
    print(f"{match}")
    # -> None
    ```
    """
    match = (d for d in search if d[key] == value)
    return next(match, None)


def search_nested_json(obj, search_string):
    """
    # Summary

    Recursively flattens a nested dictionary or list and searches all values
    for the given search_string.

    ## Raises

    None

    ## Parameters

    -   obj (dict or list): The dictionary or list to flatten.
    -   search_string (string): string to search in the values.

    ## Returns

    true or false, based on the presence of the search
    string in the nested json values.

    ## Usage

    ```python
    content = {
        "key1": "value1",
        "key2": {
            "subkey1": "subvalue1",
            "subkey2": ["item1", "item2", "search_string"],
        },
        "key3": ["item3", {"subkey3": "search_string"}],
    }
    search_string = "search_string"
    result = search_nested_json(content, search_string)
    print(result)
    # -> True

    search_string = "not_found"
    result = search_nested_json(content, search_string)
    print(result)
    # -> False
    ```

    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                if search_nested_json(v, search_string):
                    return True
            else:
                if isinstance(v, (str)) and search_string in v.lower():
                    return True
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                if search_nested_json(item, search_string):
                    return True
            else:
                if isinstance(item, (str)) and search_string in item.lower():
                    return True
    elif isinstance(obj, str):
        if search_string in obj.lower():
            return True
    return False


def has_partial_dhcp_config(server):
    """
    # Summary

    Check if a DHCP server has incomplete configuration (IP address set but no VRF or vice versa).

    ## Raises

    None

    ## Parameters

    -   server (dict): A dictionary representing the DHCP server configuration.

    ## Returns

    -   bool: True if the server has partial configuration, False otherwise.

    ## Usage

    ```python
    server1 = {
        "srvr_ip": "ip_address",
        "srvr_vrf": "vrf_name"
        }
    result1 = has_partial_dhcp_config(server1)
    print(result1)
    # -> False (complete configuration)

    server2 = {
        "srvr_ip": "ip_address"
        }
    result2 = has_partial_dhcp_config(server2)
    print(result2)
    # -> True (partial configuration)

    server3 = {
        "srvr_vrf": "vrf_name"
        }
    result3 = has_partial_dhcp_config(server3)
    print(result3)
    # -> True (partial configuration)
    """
    ip = server.get("srvr_ip")
    vrf = server.get("srvr_vrf")
    return bool(ip) != bool(vrf)
