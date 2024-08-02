from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import time
import ipaddress

from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_send,
    validate_list_of_dicts,
    dcnm_get_ip_addr_info,
)

# Some of the key names used in playbook is different from what is expected in payload. Translate such keys
xlate_key = {
    "group_name": "groupName",
    "group_id": "groupId",
    "vrf_name": "vrfName",
    "type": "type",
    "ip": "ip",
    "network": "network",
    "ip_selectors": "ipSelectors",
    "switch": "switch",
    "network_selectors": "networkSelectors",
    "vm_uuid_selectors": "vmUuidSelectors",
}

rev_xlate_key = {
    "groupName": "group_name",
    "groupId": "group_id",
    "vrfName": "vrf_name",
    "type": "type",
    "ip": "ip",
    "switch": "switch",
    "network": "network",
    "ipSelectors": "ip_selectors",
    "networkSelectors": "network_selectors",
    "vmUuidSelectors": "vm_uuid_selectors",
}

dcnm_sgrp_paths = {
    11: {},
    12: {
        "SGRP_GET_GROUP": "/appcenter/cisco/ndfc/api/v1/security/fabrics/{}/groups",
        "SGRP_GET_GROUP_WITH_ID": "/appcenter/cisco/ndfc/api/v1/security/fabrics/{}/groups/{}",
        "SGRP_ALLOC_GROUP_ID": "/appcenter/cisco/ndfc/api/v1/security/fabrics/{}/groups/reservedId",
        "SGRP_CREATE_GROUP": "/appcenter/cisco/ndfc/api/v1/security/fabrics/{}/groups",
        "SGRP_UPDATE_GROUP": "/appcenter/cisco/ndfc/api/v1/security/fabrics/{}/groups",
        "SGRP_DELETE_GROUP": "/appcenter/cisco/ndfc/api/v1/security/fabrics/{}/groups/bulkDelete",
        "SGRP_DEPLOY_GROUP_BY_VRFS": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/vrfs/deploy",
        "SGRP_DEPLOY_GROUP_BY_SWITCHES": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{}/config-deploy/{}?forceShowRun=false",
        "SGRP_GET_SYNC_STATUS": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{}/inventory/switchesByFabric",
        "SGRP_CFG_SAVE_GROUP": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{}/config-save",
        "FABRIC_ACCESS_MODE": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{}/accessmode",
    },
}


def dcnm_sgrp_utils_get_paths(version):
    return dcnm_sgrp_paths[version]


def dcnm_sgrp_utils_validate_profile(self, profile, arg_spec):

    sgrp_profile_info = []

    sgrp_profile_info, invalid_params = validate_list_of_dicts(
        profile, arg_spec
    )

    if invalid_params:
        mesg = "Invalid parameters in playbook: {0}".format(invalid_params)
        self.module.fail_json(msg=mesg)

    return sgrp_profile_info


def dcnm_sgrp_utils_check_if_meta(self, dev):

    for elem in self.meta_switches:
        if dev in elem:
            return True
    return False


def dcnm_sgrp_utils_validate_devices(self, cfg):

    for sw in cfg["switch"]:
        if sw not in self.managable:
            mesg = "Switch {0} is not Manageable".format(sw)
            self.module.fail_json(msg=mesg)

    for sw in cfg["switch"]:
        if dcnm_sgrp_utils_check_if_meta(self, sw):
            mesg = "Switch {0} is not Manageable".format(sw)
            self.module.fail_json(msg=mesg)


def dcnm_sgrp_utils_translate_config(self, cfg):

    if cfg.get("peerOneId", "") != "":
        cfg["peerOneId"] = dcnm_get_ip_addr_info(
            self.module, cfg["peerOneId"], self.ip_sn, self.hn_sn
        )
    if cfg.get("peerTwoId", "") != "":
        cfg["peerTwoId"] = dcnm_get_ip_addr_info(
            self.module, cfg["peerTwoId"], self.ip_sn, self.hn_sn
        )

    # In the current implementation we are not supporting the following fields:
    #  - clear_policy
    #  - isVpcPlus
    #  - isVTEPS
    # But as per template these are mandatory paremeters. So we will default these values to False
    # in the config.

    if cfg.get("profile", None) is not None:
        cfg["profile"]["clear_policy"] = False
        cfg["profile"]["isVpcPlus"] = False
        cfg["profile"]["isVTEPS"] = False


def dcnm_sgrp_utils_update_have(self, have):

    """
    Routine to update vertain keys in the given 'have' object to be consistent with 'want.

    Parameters:
        have (dict): Existing VPC pair information

    Returns:
        None
    """

    # 'template' and 'nv_pairs' are the keys which are not consistent with what we have in 'want'. Change these keys
    # appropriately.

    templateName = have.pop("template")
    nvPairs = have.pop("nv_pairs")

    have["templateName"] = templateName
    have["nvPairs"] = nvPairs


def dcnm_sgrp_utils_get_all_sgrp_info(self):

    """
    Routine to get existing information from DCNM.

    Parameters:
        None

    Returns:
        resp["DATA"] (dict): Security group information if available
        [] otherwise
    """

    # Get the Peer information first
    path = self.paths["SGRP_GET_GROUP"].format(self.fabric)

    resp = dcnm_send(self.module, "GET", path)

    self.log_msg(f"GET ALL RESP = {resp}\n")

    if (
        resp
        and (resp["RETURN_CODE"] == 200)
        and (resp["MESSAGE"] == "OK")
        and resp["DATA"]
    ):
        return resp["DATA"]
    else:
        return []


def dcnm_sgrp_utils_get_sgrp_info_with_name(self, name):

    """
    Routine to get existing information from DCNM with name.

    Parameters:
        name (int): Security group name corresponding to the group

    Returns:
        resp["DATA"] (dict): Security group information that matches the name
        [] otherwise
    """

    sgrp_info = dcnm_sgrp_utils_get_all_sgrp_info(self)

    # Return a group whose group name matches the given name.
    for sgrp in sgrp_info:
        if sgrp["groupName"] == name:
            self.log_msg(f"GET WITH NAME RESP = {sgrp}\n")
            return sgrp
    self.log_msg("GET WITH NAME RESP = []\n")
    return []


def dcnm_sgrp_utils_get_sgrp_info_from_dcnm(self, group_id):

    """
    Routine to get existing information from DCNM with group id.

    Parameters:
        group_id (int): Security group Id corresponding to the group

    Returns:
        resp["DATA"] (dict): Security group information obtained from the DCNM server if it exists
        [] otherwise
    """

    # Get the Peer information first
    path = self.paths["SGRP_GET_GROUP_WITH_ID"]
    path = path.format(self.fabric, group_id)

    resp = dcnm_send(self.module, "GET", path)

    self.log_msg(f"GET WITH ID RESP = {resp}\n")

    if (
        resp
        and (resp["RETURN_CODE"] == 200)
        and (resp["MESSAGE"] == "OK")
        and resp["DATA"]
    ):
        return resp["DATA"]
    else:
        return []


def dcnm_sgrp_utils_translate_sgrp_info(self, elem):

    return {
        "groupName": elem.get("group_name", ""),
        "groupId": elem.get("group_id", 0),
    }


def dcnm_sgrp_utils_get_sgrp_info(self, wobj):

    """
    Routine to get existing information from DCNM which matches the given object.

    Parameters:
        wobj (dict): Object information in 'want' format

    Returns:
        resp["DATA"] (dict): Security group information obtained from the DCNM server if it exists
        [] otherwise
    """

    # WANT objects may or may not include group ID. In case group ID is included in the wobj, then fetch the corresponding
    # group based on the ID.
    if wobj.get("groupId", 0) != 0:
        sgrp = dcnm_sgrp_utils_get_sgrp_info_from_dcnm(self, wobj["groupId"])

        self.log_msg(f"GET(GID) RESP = {sgrp}\n")
        # Check if the group names match. Otherwise it is an error
        if (
            sgrp != []
            and wobj.get("groupName", "") != ""
            and sgrp["groupName"] != wobj["groupName"]
        ):
            return []
        else:
            return sgrp
    else:
        # group ID is not included in the playbook. We will have to get all groups from the controller and match the same
        # by name. Group Id will be allocated during creation.
        return dcnm_sgrp_utils_get_sgrp_info_with_name(self, wobj["groupName"])


def dcnm_sgrp_utils_alloc_group_id(self):

    path = self.paths["SGRP_GET_GROUP_ID"]
    resp = dcnm_send(self.module, "GET", path)

    self.log_msg(f"GROUP ID RESP = {resp}\n")


def dcnm_sgrp_utils_get_payload_elem(self, key, sel_info):

    pl_sel_info = []
    for elem in sel_info:
        pl_elem = {}
        for k in elem:
            pl_elem[xlate_key[k]] = elem[k]
        pl_sel_info.append(pl_elem)
    return pl_sel_info


def dcnm_sgrp_utils_get_sgrp_payload(self, sgrp_info):

    # sgrp_payload = {"vmUuidSelectors": []}
    sgrp_payload = {}

    for key in sgrp_info:
        if key == "ip_selectors" or key == "network_selectors":
            sel_info = dcnm_sgrp_utils_get_payload_elem(
                self, key, sgrp_info[key]
            )
            sgrp_payload[xlate_key[key]] = sel_info
        else:
            sgrp_payload[xlate_key[key]] = sgrp_info[key]

    return sgrp_payload


def dcnm_sgrp_utils_get_matching_want(self, sgrp_info):

    match_want = [
        want
        for want in self.want
        if (
            (sgrp_info["groupId"] == want["groupId"])
            and (sgrp_info["groupName"] == want["groupName"])
        )
    ]

    return match_want


def dcnm_sgrp_utils_get_matching_have(self, want):

    match_have = [
        have
        for have in self.have
        if (
            (have["groupId"] == want["groupId"])
            and (have["groupName"] == want["groupName"])
        )
    ]

    return match_have


def dcnm_sgrp_utils_get_matching_cfg(self, want):

    match_cfg = [
        cfg
        for cfg in self.config
        if (
            (cfg.get("group_id", "") == want.get("groupId", ""))
            and (cfg["group_name"] == want["groupName"])
        )
    ]

    return match_cfg


def dcnm_sgrp_utils_merge_want_and_have(self, want, have, key):

    if want.get(key, []) == []:
        want[key] = have.get(key)
    elif have.get(key, []) == []:
        # Nothing to merge. Leave want as it is
        pass
    else:
        # Merge the contents of want and have. In this case the element identified by key is a list. So
        # add the contents together.
        want[key] += have[key]


def dcnm_sgrp_utils_update_sgrp_information(self, want, have, cfg):

    mergeable_fields = ["ipSelectors", "networkSelectors", "vmUuidSelectors"]

    for key in list(want.keys()):
        if cfg.get(rev_xlate_key[key], None) is None:
            # The given key from want is not included in the playbook config. Copy the
            # information corresponding to the key from have
            if key == "ipSelectors" or key == "networkSelectors" or key == "vmUuidSelectors":
                want[key] = have.get(key, [])
            else:
                want[key] = have.get(key, "")

            if key in mergeable_fields:
                want[key + "_defaulted"] = True
        else:
            if key in mergeable_fields:
                want[key + "_defaulted"] = False


def dcnm_sgrp_utils_compare_sgrp_selector_objects(
    self, selector, wsel, hsel, mismatch_reasons
):

    """
    Routine to compare have and want selector objects.

    Parameters:
        selector (str): Specifies if it is IP or NETWORK selector
        wsel (dict): Requested object information
        hsel (dict): Existing object information
    Returns:
        DCNM_SGRP_MATCH(str): - if given wsel information is already present in hsel
        DCNM_SGRP_MERGE(str): - if given wsel is not present or is different from hsel
        mismatch_reasons(list): updated list identifying objects that differed if required, [] otherwise
    """

    if wsel == [] and hsel == []:
        # Nothing to compare
        return

    if hsel == []:
        mismatch_reasons.append({"SELECTOR_MISMATCH": [wsel, hsel]})
        return

    # wsel and hsel are list of dicts. Every object in wsel must be comapred to every object in hsel.
    # If wsel element is not present in hsel list, then there is a mismatch. Otherwise no need to merge
    # wsel and hsel lists
    for welem in wsel[:]:
        for helem in hsel:
            if selector == "SGRP_IPSEL":
                if (
                    (welem["type"] == helem["type"])
                    and (
                        ipaddress.ip_network(welem["ip"], strict=False)
                        == ipaddress.ip_network(helem["ip"], strict=False)
                    )
                    and (welem["vrfName"] == helem["vrfName"])
                ):
                    if self.module.params["state"] == "merged":
                        wsel.remove(welem)
                    break
            elif selector == "SGRP_NETSEL":
                if (welem["network"] == helem["network"]) and (
                    welem["vrfName"] == helem["vrfName"]
                ):
                    if self.module.params["state"] == "merged":
                        wsel.remove(welem)
                    break
        else:
            # wsel and hsel differ. Flag a mismatch
            mismatch_reasons.append({"SELECTOR_ELEM_NOT_EXIST": [welem]})


def dcnm_sgrp_utils_compare_sgrp_objects(self, wobj, hobj):

    """
    Routine to compare have and want objects and update mismatch information.

    Parameters:
        wobj (dict): Requested object information
        hobj (dict): Existing object information
    Returns:
        DCNM_SGRP_EXIST(str): - if given vpc is same as that exists
        DCNM_SGRP_MERGE(str): - if given vpc exists but there are changes in parameters
        mismatch_reasons(list): a list identifying objects that differed if required, [] otherwise
        hobj(dict): existing object if required, [] otherwise
    """

    mismatch_reasons = []
    for key in wobj:

        if key == "switch":
            continue

        if "_defaulted" in key:
            continue

        if str(hobj.get(key, None)).lower() != str(wobj[key]).lower():
            if key == "ipSelectors" or key == "networkSelectors":
                continue

            # Differs in one of the params.
            mismatch_reasons.append(
                {key.upper() + "_MISMATCH": [wobj[key], hobj.get(key, None)]}
            )

    if wobj.get("ipSelectors", None) is not None:
        dcnm_sgrp_utils_compare_sgrp_selector_objects(
            self,
            "SGRP_IPSEL",
            wobj["ipSelectors"],
            hobj.get("ipSelectors", []),
            mismatch_reasons,
        )
    if wobj.get("networkSelectors", None) is not None:
        dcnm_sgrp_utils_compare_sgrp_selector_objects(
            self,
            "SGRP_NETSEL",
            wobj["networkSelectors"],
            hobj.get("networkSelectors", []),
            mismatch_reasons,
        )

    if mismatch_reasons != []:
        return "DCNM_SGRP_MERGE", mismatch_reasons, hobj
    else:
        return "DCNM_SGRP_EXIST", [], []


def dcnm_sgrp_utils_compare_want_and_have(self, want):

    """
    This routine finds an object in self.have that matches the given information. If the given
    object already exist then it is not added to the object list to be created on
    DCNM server in the current run. The given object is added to the list of objects to be
    created otherwise.

    Parameters:
        want : Object to be matched from self.have

    Returns:
        DCNM_SGRP_CREATE (str): - if a new object is to be created
        return value of  dcnm_sgrp_utils_compare_sgrp_objects
    """

    match_have = dcnm_sgrp_utils_get_matching_have(self, want)

    for melem in match_have:
        return dcnm_sgrp_utils_compare_sgrp_objects(self, want, melem)

    return "DCNM_SGRP_CREATE", [], []


def dcnm_sgrp_utils_get_delete_payload(self, elem):

    return elem["groupId"]


def dcnm_sgrp_utils_update_deploy_info(self, elem, deploy_object):

    # This routine updates the deploy list with a dictinary of key value pairs, where keys will be switch
    # serial numbers, and the values will be a list of all VRFs associated with the given elem. This can be
    # invoked for updating diff_deploy and diff_delete_deploy lists as well.

    # for delete state, switch is not a mandatory element. If switch is not included in the playbook, then apply
    # it for all switches.

    if elem.get("switch", None) is None:
        switch_list = self.ip_sn.keys()
    else:
        switch_list = elem["switch"]

    for sw_elem in switch_list:
        sno = self.ip_sn[sw_elem]
        if deploy_object.get(sno, None) is None:
            deploy_object[sno] = ""
        ipsel_vrfs = [sel["vrfName"] for sel in elem.get("ipSelectors", [])]
        netsel_vrfs = [
            sel["vrfName"] for sel in elem.get("networkSelectors", [])
        ]

        if deploy_object[sno] != "":
            cum_vrf_list = list(
                set(deploy_object[sno].split(",") + ipsel_vrfs + netsel_vrfs)
            )
        else:
            cum_vrf_list = list(set(ipsel_vrfs + netsel_vrfs))
        deploy_object[sno] = ",".join(cum_vrf_list)


def dcnm_sgrp_utils_get_sgrp_deploy_payload(self, elem, reason):

    # Security Groups uses switch or vrf level deploy to deploy the changes. Each of this case requires
    # a different payload. For switch level deploy case, we need the serial number of all switches. But for
    # vrf level deploy, we will need a dict with switches as keys and VRFs as a list of values for each of these
    # keys.

    if (
        (reason == "DCNM_SGRP_CREATE")
        or (reason == "DCNM_SGRP_MERGE")
        or (
            [
                sw_elem
                for sw_elem in elem["switch"]
                if self.sync_info.get(sw_elem, "Not-In-sync") != "In-Sync"
            ]
            != []
        )
        #           self.sync_info.get(sw_elem, "Not-In-Sync") != "In-Sync")
    ):
        dcnm_sgrp_utils_update_deploy_info(self, elem, self.diff_deploy)


def dcnm_sgrp_utils_process_delete_payloads(self):

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
        path = self.paths["SGRP_DELETE_GROUP"]
        path = path.format(self.fabric)

        json_payload = json.dumps(self.diff_delete)

        resp = dcnm_send(self.module, "POST", path, json_payload)

        self.log_msg(
            f"DELETE, PATH = {path}, RESP = {resp}. PL = {json_payload}\n"
        )

        if resp != []:
            self.result["response"].append(resp)

        if resp and resp.get("RETURN_CODE") != 200:
            resp["CHANGED"] = self.changed_dict[0]
            self.module.fail_json(msg=resp)
        else:
            delete_flag = True

    if delete_flag:
        dcnm_sgrp_utils_process_deploy_payloads(self, self.diff_delete_deploy)

    return delete_flag


def dcnm_sgrp_utils_process_payloads_list(
    self, payload_list, command, path, alloc_path
):

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

    # Create the bulk objects first
    if payload_list[0]["bulk"] != []:
        json_payload = json.dumps(payload_list[0]["bulk"])
        resp = dcnm_send(self.module, command, path, json_payload)

        self.log_msg(f"BULK {action} PL = {json_payload}, RESP = {resp}\n")

        if resp != []:
            self.result["response"].append(resp)
        if resp and resp.get("RETURN_CODE") != 200:
            resp["CHANGED"] = self.changed_dict[0]
            self.module.fail_json(msg=resp)
        else:
            flag = True

    # Create the bulk objects first
    for elem in payload_list[0]["individual"]:
        # Allocate a group ID if it is not provided
        if elem.get("groupId", 0) == 0:
            # Allocate a groupId and then create the group.
            resp = dcnm_send(self.module, "GET", alloc_path)

            self.log_msg(f"ALLOC RESP = {resp}\n")

            if resp != []:
                self.result["response"].append(resp)
            if resp and resp.get("RETURN_CODE") != 200:
                resp["CHANGED"] = self.changed_dict[0]
                self.module.fail_json(msg=resp)
            else:
                elem["groupId"] = resp["DATA"]["id"]

        if action == "MODIFY":
            json_payload = json.dumps(elem)
        else:
            json_payload = json.dumps([elem])

        if action == "CREATE":
            resp = dcnm_send(self.module, command, path, json_payload)
        else:
            resp = dcnm_send(
                self.module,
                command,
                path + "/" + str(elem["groupId"]),
                json_payload,
            )

        self.log_msg(
            f"INDIVIDUAL {action} PL = {json_payload}, RESP = {resp}\n"
        )

        if resp != []:
            self.result["response"].append(resp)
        if resp and resp.get("RETURN_CODE") != 200:
            resp["CHANGED"] = self.changed_dict[0]
            self.module.fail_json(msg=resp)
        else:
            flag = True

    return flag


def dcnm_sgrp_utils_process_create_payloads(self):

    """
    Routine to push create payloads to DCNM server.

    Parameters:
        None

    Returns:
        True if create payloads are successfully pushed to server
        False otherwise
    """

    create_path = self.paths["SGRP_CREATE_GROUP"].format(self.fabric)
    alloc_path = self.paths["SGRP_ALLOC_GROUP_ID"].format(self.fabric)

    return dcnm_sgrp_utils_process_payloads_list(
        self, self.diff_create, "POST", create_path, alloc_path
    )


def dcnm_sgrp_utils_process_modify_payloads(self):

    """
    Routine to push modify payloads to DCNM server.

    Parameters:
        None

    Returns:
        True if modified payloads are successfully pushed to server
        False otherwise
    """

    modify_path = self.paths["SGRP_UPDATE_GROUP"].format(self.fabric)
    alloc_path = self.paths["SGRP_ALLOC_GROUP_ID"].format(self.fabric)

    return dcnm_sgrp_utils_process_payloads_list(
        self, self.diff_modify, "PUT", modify_path, alloc_path
    )


def dcnm_sgrp_utils_get_sync_status(self):

    """
    Routine to get switch status information for a given fabric. This information can be processed to get
    the "In-Sync" status for the required switches.
    transient errors.

    Parameters:
        None

    Returns:
        'In-sync', if the switches configuration is "In-Sync" state, 'Not-In-Sync' otherwise
    """

    resp = None
    sync_info = {}

    path = self.paths["SGRP_GET_SYNC_STATUS"].format(self.fabric)

    resp = dcnm_send(self.module, "GET", path)

    self.log_msg(f"GET SYNC STATUS RESP = {resp}\n")

    if resp and (resp["RETURN_CODE"] != 200):
        resp["CHANGED"] = self.changed_dict[0]
        self.module.fail_json(msg=resp)
    else:
        for elem in resp["DATA"]:
            sync_info[elem["ipAddress"]] = elem["ccStatus"]
        return sync_info


def dcnm_sgrp_utils_save_config_changes(self):

    """
    Routine to save configuration changes for the given fabric.

    Parameters:
        None

    Returns:
        None
    """

    resp = None

    path = self.paths["SGRP_CFG_SAVE_GROUP"].format(self.fabric)

    resp = dcnm_send(self.module, "POST", path)

    self.log_msg(f"CONFG SAVE RESP = {resp}\n")

    if resp != []:
        self.result["response"].append(resp)

    if resp and (resp["RETURN_CODE"] != 200):
        resp["CHANGED"] = self.changed_dict[0]
        self.module.fail_json(msg=resp)


def dcnm_sgrp_utils_deploy_payload(self, deploy_info):

    """
    Routine to deploy a VPC switch pair to DCNM server.

    Parameters:
        None

    Returns:
        True if deploy succeded, False otherwise
    """

    resp = None
    json_payload = None
    deploy_flag = False
    path = ""

    if self.deploy == "switches":
        path = self.paths["SGRP_DEPLOY_GROUP_BY_SWITCHES"].format(
            self.fabric, ",".join(deploy_info.keys())
        )
        resp = dcnm_send(self.module, "POST", path)
    elif self.deploy == "vrfs":
        path = self.paths["SGRP_DEPLOY_GROUP_BY_VRFS"]
        json_payload = json.dumps(deploy_info)
        resp = dcnm_send(self.module, "POST", path, json_payload)

    if resp != []:
        self.result["response"].append(resp)

    self.log_msg(f"DEPLOY ELEM, PATH = {path},  RESP = {resp}\n")
    self.log_msg(f"DEPLOY ELEM, PL = {json_payload}\n")

    if resp and (resp["RETURN_CODE"] != 200):
        resp["CHANGED"] = self.changed_dict[0]
        self.module.fail_json(msg=resp)
    else:
        deploy_flag = True

    return deploy_flag, resp


def dcnm_sgrp_utils_get_ip_addr(self, seq_no):

    return self.sn_ip[seq_no]


def dcnm_sgrp_utils_process_deploy_payloads(self, deploy_info):

    """
    Routine to push deploy payloads to DCNM server. This routine implements required error checks and retry mechanisms to handle
    transient errors.

    Parameters:
        None

    Returns:
        None
    """

    resp = None
    deploy_flag = False
    sync_info = {}

    if deploy_info == {}:
        return deploy_flag

    rc, resp = dcnm_sgrp_utils_deploy_payload(self, deploy_info)
    if deploy_flag is not True:
        deploy_flag = rc

    if deploy_flag is True:
        retries = 0
        while retries < 20:

            sync_info = dcnm_sgrp_utils_get_sync_status(self)

            if sync_info == {}:
                continue

            deploy_keys = list(deploy_info.keys())
            for key in deploy_keys[:]:
                if sync_info.get(self.sn_ip[key], "Not-In-Sync") == "In-Sync":
                    # Switch is In-Sync state. Remove that from deploy list. We will retry for other switches if any
                    deploy_info.pop(key)

            if deploy_info == {}:
                break
            else:
                # rc, resp = dcnm_sgrp_utils_deploy_payload(self, deploy_info)
                # if deploy_flag is not True:
                #    deploy_flag = rc
                time.sleep(3)
                retries += 1
        else:
            resp["CHANGED"] = self.changed_dict[0]
            self.module.fail_json(
                msg=f"Switches {list(map(lambda x: self.sn_ip[x], deploy_info.keys()))} did not reach 'In-Sync' state after deploy\n"
            )

        if sync_info != {}:
            sync_info["RETURN_CODE"] = 200
            sync_info["MESSAGE"] = "OK"
            self.result["response"].append(sync_info)

    return deploy_flag


def dcnm_sgrp_utils_get_delete_list(self):

    del_list = []

    # Get all security group information present
    sgrp_info = dcnm_sgrp_utils_get_all_sgrp_info(self)

    if sgrp_info == []:
        return []

    # If this info is not included in self.want, then go ahead and add it to del_list. Otherwise
    # ignore this pair, since new configuration is included for this pair in the playbook.
    for sgrp in sgrp_info:
        # objects with groupType as "defaultgroup" cannot be deleted
        if sgrp["groupType"].lower() == "defaultgroup":
            continue
        want = dcnm_sgrp_utils_get_matching_want(self, sgrp)
        if want == []:
            if sgrp not in del_list:
                del_list.append(sgrp)

    return del_list


def dcnm_sgrp_utils_get_all_filtered_sgrp_objects(self):

    sgrp_list = dcnm_sgrp_utils_get_all_sgrp_info(self)

    # If filters are provided, use the values to build the appropriate list.
    if self.sgrp_info == []:
        return sgrp_list
    else:
        sgrp_filtered_list = []

        filter_values = set().union(*(d.values() for d in self.sgrp_info))

        for elem in self.sgrp_info:
            match_list = []

            self.log_msg(f"Processing ELEM = {elem}\n")

            match = [
                sgrp
                for sgrp in sgrp_list
                if (
                    (
                        elem.get("group_id", None) is None
                        or sgrp["groupId"] == elem["group_id"]
                    )
                    and (
                        elem.get("group_name", None) is None
                        or sgrp["groupName"] == elem["group_name"]
                    )
                )
            ]
            self.log_msg(f"MATCH = {match}\n")

            if match == []:
                continue

            if match[0] not in sgrp_filtered_list:
                sgrp_filtered_list.append(match[0])

    return sgrp_filtered_list
