from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_send,
)

dcnm_contracts_get_paths = {
    11: {},
    12: {
        "NDFC_CONTRACT_GET": "/appcenter/cisco/ndfc/api/v1/security/fabrics/{}/contracts",
        "NDFC_CONTRACT_CREATE": "/appcenter/cisco/ndfc/api/v1/security/fabrics/{}/contracts",
        "NDFC_CONTRACT_DELETE": "/appcenter/cisco/ndfc/api/v1/security/fabrics/{}/contracts/bulkDelete",
        "NDFC_CONTRACT_MODIFY": "/appcenter/cisco/ndfc/api/v1/security/fabrics/{}/contracts/{}"
    },
}

# Some of the key names used in playbook is different from what is expected in payload. Translate such keys
xlate_key = {
    "contract_name": "contractName",
    "description": "description",
    "rules": "rules",
    "direction": "direction",
    "action": "action",
    "protocol_name": "protocolName",
}


def dcnm_contracts_utils_get_paths(dcnm_version):

    return dcnm_contracts_get_paths[dcnm_version]


def dcnm_contracts_utils_get_contracts_info(self, elem):

    if elem:
        if elem.get("contractName", None):
            contract_name = elem["contractName"]
        else:
            contract_name = elem["contract_name"]
        path = self.paths["NDFC_CONTRACT_GET"] + '/' + contract_name
        contracts = {}
    else:
        path = self.paths["NDFC_CONTRACT_GET"]
        contracts = []

    path = path.format(self.fabric)
    resp = dcnm_send(self.module, "GET", path)

    if (
        resp
        and (resp["RETURN_CODE"] == 200)
        and (resp["MESSAGE"] == "OK")
        and resp["DATA"]
    ):
        if elem:
            contracts = [resp["DATA"]]
        else:
            contracts = resp["DATA"]

        for contract in contracts:
            if "fabricName" in contract:
                del contract["fabricName"]
            if "associationCount" in contract:
                del contract["associationCount"]
            if contract.get("rules", None):
                for rule in contract["rules"]:
                    if "uuid" in rule:
                        del rule["uuid"]
                    if "matchSummary" in rule:
                        del rule["matchSummary"]

        if elem:
            return contracts[0]
        else:
            return contracts

    return contracts


def dcnm_contracts_utils_get_payload_elem(self, key, sel_info):

    pl_sel_info = []
    for elem in sel_info:
        pl_elem = {}
        for k in elem:
            pl_elem[xlate_key[k]] = elem[k]
        pl_sel_info.append(pl_elem)
    return pl_sel_info


def dcnm_contracts_utils_get_contracts_payload(self, contracts_info):

    contracts_payload = {}

    for key in contracts_info:
        if key == "rules" and contracts_info[key]:
            sel_info = dcnm_contracts_utils_get_payload_elem(self, key, contracts_info[key])
            contracts_payload[xlate_key[key]] = sel_info
        else:
            contracts_payload[xlate_key[key]] = contracts_info[key]

    return contracts_payload


def dcnm_contracts_utils_compare_want_and_have(self, want):

    match_have = dcnm_contracts_utils_get_matching_have(self, want)

    for melem in match_have:
        return dcnm_contracts_utils_compare_contracts_objects(self, want, melem)

    return "NDFC_CONTRACTS_CREATE", []


def dcnm_contracts_utils_get_matching_want(self, contracts_info):

    match_want = [
        want
        for want in self.want
        if (contracts_info["contractName"] == want["contractName"])
    ]

    return match_want


def dcnm_contracts_utils_get_matching_have(self, want):

    match_have = [
        have
        for have in self.have
        if (have["contractName"] == want["contractName"])
    ]

    return match_have


def dcnm_contracts_utils_compare_contracts_objects(self, wobj, hobj):

    mismatch = False

    for key in wobj:
        if str(hobj.get(key, None)) != str(wobj.get(key, None)):
            if key == "rules":
                if (
                    self.module.params["state"] == "replaced" or
                    self.module.params["state"] == "overridden"
                ):
                    if len(hobj["rules"]) != len(wobj["rules"]):
                        mismatch = True
                if not mismatch:
                    for rule in wobj["rules"]:
                        if rule not in hobj["rules"]:
                            mismatch = True
                            break
            else:
                mismatch = True
                break

    if mismatch:
        return "NDFC_CONTRACTS_MERGE", hobj
    else:
        return "NDFC_CONTRACTS_EXIST", []


def dcnm_contracts_utils_get_delete_payload(self, elem):

    return elem["contractName"]


def dcnm_contracts_utils_get_delete_list(self):

    del_list = []

    # Get all security contract information present
    contracts_info = dcnm_contracts_utils_get_contracts_info(self, None)

    if contracts_info == []:
        return []

    # If this info is not included in self.want, then go ahead and add it to del_list. Otherwise
    # ignore this pair, since new configuration is included for this pair in the playbook.
    for contract in contracts_info:
        want = dcnm_contracts_utils_get_matching_want(self, contract)
        if want == []:
            if contract not in del_list:
                del_list.append(contract)

    return del_list


def dcnm_contracts_utils_get_all_filtered_contracts_objects(self):

    contracts_list = dcnm_contracts_utils_get_contracts_info(self, None)

    # If filters are provided, use the values to build the appropriate list.
    if self.contracts_info == []:
        return contracts_list
    else:
        contracts_filtered_list = []
        filter_keys = set().union(*(d.values() for d in self.contracts_info))

        for elem in contracts_list:

            match = False

            if (elem.get("contractName", 0) != 0) and (
                elem["contractName"] in filter_keys
            ):
                match = True

            if not match:
                continue

            if elem not in contracts_filtered_list:
                contracts_filtered_list.append(elem)

    return contracts_filtered_list


def dcnm_contracts_utils_process_delete_payloads(self):

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
        path = self.paths["NDFC_CONTRACT_DELETE"]
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


def dcnm_contracts_utils_process_payloads_list(self, payload_list, command, path):

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
            mod_path = path.format(self.fabric, elem["contractName"])

            resp = dcnm_send(self.module, command, mod_path, json_payload)

    if resp != []:
        self.result["response"].append(resp)
    if resp and resp.get("RETURN_CODE") != 200:
        resp["CHANGED"] = self.changed_dict[0]
        self.module.fail_json(msg=resp)
    else:
        flag = True

    return flag


def dcnm_contracts_utils_process_create_payloads(self):

    """
    Routine to push create payloads to DCNM server.

    Parameters:
        None

    Returns:
        True if create payloads are successfully pushed to server
        False otherwise
    """

    create_path = self.paths["NDFC_CONTRACT_CREATE"].format(self.fabric)

    return dcnm_contracts_utils_process_payloads_list(self, self.diff_create, "POST", create_path)


def dcnm_contracts_utils_process_modify_payloads(self):

    """
    Routine to push modify payloads to DCNM server.

    Parameters:
        None

    Returns:
        True if modified payloads are successfully pushed to server
        False otherwise
    """

    modify_path = self.paths["NDFC_CONTRACT_MODIFY"]

    return dcnm_contracts_utils_process_payloads_list(self, self.diff_modify, "PUT", modify_path)
