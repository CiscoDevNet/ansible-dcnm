from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_send,
)


dcnm_protocols_get_paths = {
    11: {},
    12: {
        "NDFC_PROTOCOL_GET": "/appcenter/cisco/ndfc/api/v1/security/fabrics/{}/protocols",
        "NDFC_PROTOCOL_CREATE": "/appcenter/cisco/ndfc/api/v1/security/fabrics/{}/protocols",
        "NDFC_PROTOCOL_DELETE": "/appcenter/cisco/ndfc/api/v1/security/fabrics/{}/protocols/bulkDelete",
        "NDFC_PROTOCOL_MODIFY": "/appcenter/cisco/ndfc/api/v1/security/fabrics/{}/protocols/{}"
    },
}

# Some of the key names used in playbook is different from what is expected in payload. Translate such keys
xlate_key = {
    "protocol_name": "protocolName",
    "description": "description",
    "match_all": "matchType",
    "match": "matchItems",
    "type": "type",
    "protocol_options": "protocolOptions",
    "fragments": "onlyFragments",
    "stateful": "stateful",
    "source_port_range": "srcPortRange",
    "destination_port_range": "dstPortRange",
    "tcp_flags": "tcpFlags",
    "dscp": "dscp",
}


def dcnm_protocols_utils_get_paths(dcnm_version):

    return dcnm_protocols_get_paths[dcnm_version]


def dcnm_protocols_utils_get_protocols_info(self, elem):

    if elem:
        if elem.get("protocolName", None):
            proto_name = elem["protocolName"]
        else:
            proto_name = elem["protocol_name"]
        path = self.paths["NDFC_PROTOCOL_GET"] + '/' + proto_name
        protocols = {}
    else:
        path = self.paths["NDFC_PROTOCOL_GET"]
        protocols = []

    path = path.format(self.fabric)
    resp = dcnm_send(self.module, "GET", path)

    if (
        resp
        and (resp["RETURN_CODE"] == 200)
        and (resp["MESSAGE"] == "OK")
        and resp["DATA"]
    ):
        if elem:
            protocols = [resp["DATA"]]
        else:
            protocols = resp["DATA"]

        for protocol in protocols:
            if "fabricName" in protocol:
                del protocol["fabricName"]
            if "associatedContractCount" in protocol:
                del protocol["associatedContractCount"]
            if "matchItems" in protocol:
                for match in protocol["matchItems"]:
                    if "matchSummary" in match:
                        del match["matchSummary"]
                    if match.get("protocolOptions", None):
                        match["protocolOptions"] = match["protocolOptions"].lower()
                    if match.get("type", None):
                        match["type"] = match["type"].lower()

        if elem:
            return protocols[0]
        else:
            return protocols

    return protocols


def dcnm_protocols_utils_get_payload_elem(self, key, sel_info):

    pl_sel_info = []
    for elem in sel_info:
        pl_elem = {}
        for k in elem:
            pl_elem[xlate_key[k]] = elem[k]
        pl_sel_info.append(pl_elem)
    return pl_sel_info


def dcnm_protocols_utils_get_protocols_payload(self, protocols_info):

    protocols_payload = {}

    for key in protocols_info:
        if key == "match" and protocols_info[key]:
            sel_info = dcnm_protocols_utils_get_payload_elem(self, key, protocols_info[key])
            protocols_payload[xlate_key[key]] = sel_info
        else:
            if key == "match_all":
                protocols_payload[xlate_key[key]] = "any"
            else:
                protocols_payload[xlate_key[key]] = protocols_info[key]
    return protocols_payload


def dcnm_protocols_utils_compare_want_and_have(self, want):

    match_have = dcnm_protocols_utils_get_matching_have(self, want)

    for melem in match_have:
        return dcnm_protocols_utils_compare_protocols_objects(self, want, melem)

    return "NDFC_PROTOCOLS_CREATE", []


def dcnm_protocols_utils_get_matching_want(self, protocols_info):

    match_want = [
        want
        for want in self.want
        if (protocols_info["protocolName"] == want["protocolName"])
    ]

    return match_want


def dcnm_protocols_utils_get_matching_have(self, want):

    match_have = [
        have
        for have in self.have
        if (have["protocolName"] == want["protocolName"])
    ]

    return match_have


def dcnm_protocols_utils_compare_protocols_objects(self, wobj, hobj):

    mismatch = False

    for key in wobj:
        if str(hobj.get(key, None)) != str(wobj.get(key, None)):
            if key == "matchItems":
                if (
                    self.module.params["state"] == "replaced" or
                    self.module.params["state"] == "overridden"
                ):
                    if len(wobj["matchItems"]) != len(hobj["matchItems"]):
                        mismatch = True
                if not mismatch:
                    for match in wobj["matchItems"]:
                        if match not in hobj["matchItems"]:
                            mismatch = True
                            break
            else:
                mismatch = True

    if mismatch:
        return "NDFC_PROTOCOLS_MERGE", hobj
    else:
        return "NDFC_PROTOCOLS_EXIST", []


def dcnm_protocols_utils_get_delete_payload(self, elem):

    return elem["protocolName"]


def dcnm_protocols_utils_get_delete_list(self):

    del_list = []

    # Get all security protocol information present
    protocols_info = dcnm_protocols_utils_get_protocols_info(self, None)

    if protocols_info == []:
        return []

    # If this info is not included in self.want, then go ahead and add it to del_list. Otherwise
    # ignore this pair, since new configuration is included for this pair in the playbook.
    for protocol in protocols_info:
        want = dcnm_protocols_utils_get_matching_want(self, protocol)
        if want == []:
            if protocol not in del_list:
                del_list.append(protocol)

    return del_list


def dcnm_protocols_utils_get_all_filtered_protocols_objects(self):

    protocols_list = dcnm_protocols_utils_get_protocols_info(self, None)

    # If filters are provided, use the values to build the appropriate list.
    if self.protocols_info == []:
        playbook_payload = []
        for elem in protocols_list:
            if "fabricName" in elem:
                del elem["fabricName"]
            if "associatedContractCount" in elem:
                del elem["associatedContractCount"]
            if elem.get("matchItems", None):
                for match in elem["matchItems"]:
                    if "matchSummary" in match:
                        del match["matchSummary"]
            playbook_payload.append(elem)

        return playbook_payload
    else:
        protocols_filtered_list = []
        filter_keys = set().union(*(d.values() for d in self.protocols_info))

        for elem in protocols_list:

            match = False

            if (elem.get("protocolName", 0) != 0) and (
                elem["protocolName"] in filter_keys
            ):
                match = True

            if not match:
                continue

            if "fabricName" in elem:
                del elem["fabricName"]
            if "associatedContractCount" in elem:
                del elem["associatedContractCount"]
            if elem.get("matchItems", None):
                for match in elem["matchItems"]:
                    if "matchSummary" in match:
                        del match["matchSummary"]

            if elem not in protocols_filtered_list:
                protocols_filtered_list.append(elem)

    return protocols_filtered_list


def dcnm_protocols_utils_process_delete_payloads(self):

    """
    Routine to push delete payloads to DCNM server. This routine implements required error checks and retry mechanisms to handle
    transient errors.

    Parameters:
        None

    Returns:
        None
    """

    resp = None
    delete_flag = False

    if self.diff_delete:
        path = self.paths["NDFC_PROTOCOL_DELETE"]
        path = path.format(self.fabric)

        json_payload = json.dumps(self.diff_delete)

        resp = dcnm_send(self.module, "POST", path, json_payload)

        if resp != []:
            self.result["response"].append(resp)

        if resp and resp.get("RETURN_CODE") != 200:
            resp["CHANGED"] = self.changed_dict[0]
            self.module.fail_json(msg=resp)
        else:
            delete_flag = True

    return delete_flag


def dcnm_protocols_utils_process_payloads_list(self, payload_list, command, path):

    """
    Routine to push payloads from the given list to DCNM server. This routine implements required error checks and retry mechanisms to handle
    transient errors.

    Parameters:
        None

    Returns:
        None
    """

    resp = None
    flag = False

    if command == "POST":
        action = "CREATE"
    elif command == "PUT":
        action = "MODIFY"

    json_payload = None
    if payload_list == []:
        return flag

    if action == "CREATE":
        json_payload = json.dumps(payload_list)
        resp = dcnm_send(self.module, command, path, json_payload)
    else:
        for elem in payload_list:
            json_payload = json.dumps(elem)
            mod_path = path.format(self.fabric, elem["protocolName"])
            resp = dcnm_send(self.module, command, mod_path, json_payload)

    if resp != []:
        self.result["response"].append(resp)
    if resp and resp.get("RETURN_CODE") != 200:
        resp["CHANGED"] = self.changed_dict[0]
        self.module.fail_json(msg=resp)
    else:
        flag = True

    return flag


def dcnm_protocols_utils_process_create_payloads(self):

    """
    Routine to push create payloads to DCNM server.

    Parameters:
        None

    Returns:
        True if create payloads are successfully pushed to server
        False otherwise
    """

    create_path = self.paths["NDFC_PROTOCOL_CREATE"].format(self.fabric)

    return dcnm_protocols_utils_process_payloads_list(self, self.diff_create, "POST", create_path)


def dcnm_protocols_utils_process_modify_payloads(self):

    """
    Routine to push modify payloads to DCNM server.

    Parameters:
        None

    Returns:
        True if modified payloads are successfully pushed to server
        False otherwise
    """

    modify_path = self.paths["NDFC_PROTOCOL_MODIFY"]

    return dcnm_protocols_utils_process_payloads_list(self, self.diff_modify, "PUT", modify_path)
