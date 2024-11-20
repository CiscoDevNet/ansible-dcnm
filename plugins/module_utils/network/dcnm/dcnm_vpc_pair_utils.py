from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import time

from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_send,
    validate_list_of_dicts,
    dcnm_get_ip_addr_info,
)

dcnm_vpc_pair_paths = {
    11: {},
    12: {
        "VPC_PAIR_GET_PATH": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/vpcpair/inventory?switchId={}",
        "VPC_PAIR_GET_POLICY_PATH": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/vpcpair/policy?serialNumber={}",
        "VPC_PAIR_GET_SYNC_STATUS": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{}/inventory/switchesByFabric",
        "VPC_PAIR_CREATE_PATH": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/vpcpair",
        "VPC_PAIR_UPDATE_PATH": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/vpcpair",
        "VPC_PAIR_DELETE_PATH": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/vpcpair?serialNumber={}",
        "VPC_PAIR_DEPLOY_PATH": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{}/config-deploy/{}?forceShowRun=false",
        "VPC_PAIR_CFG_SAVE_PATH": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{}/config-save",
        "VPC_PEER_LINK_GET_PATH": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/vpcpair/recommendation?serialNumber={}&useVirtualPeerlink=true",
        "FABRIC_ACCESS_MODE": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{}/accessmode",
    },
}


def dcnm_vpc_pair_utils_get_paths(version):
    return dcnm_vpc_pair_paths[version]


def dcnm_vpc_pair_utils_update_common_spec(self, common_spec):

    if (
        self.src_fabric_info["fabricTechnology"] == "LANClassic"
        or self.src_fabric_info["fabricTechnology"] == "External"
    ):
        # For Classic and External fabrics, 'profile' and 'templateName' are mandatory parameters
        common_spec["profile"]["required"] = True
        common_spec["templateName"]["required"] = True


def dcnm_vpc_pair_utils_validate_profile(self, profile, arg_spec):

    vpc_pair_profile_info = []

    # Only LANClassic/External fabrics require profile information.

    if (
        self.src_fabric_info["fabricTechnology"] == "LANClassic"
        or self.src_fabric_info["fabricTechnology"] == "External"
    ):

        vpc_pair_profile_info, invalid_params = validate_list_of_dicts(
            [profile], arg_spec
        )

        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(invalid_params)
            self.module.fail_json(msg=mesg)

    return vpc_pair_profile_info


def dcnm_vpc_pair_utils_translate_config(self, cfg):

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


def dcnm_vpc_pair_utils_update_other_information(self):

    """
    Routine to update 'self' with serial number to switch DB Id translation information.

    Parameters:
        None

    Returns:
        None
    """

    sn_swid = {}

    for device_key in self.inventory_data.keys():
        sn = self.inventory_data[device_key].get("serialNumber", None)
        swid = self.inventory_data[device_key].get("switchDbID", None)

        if sn is not None and swid is not None:
            sn_swid.update({sn: swid})
    self.sn_swid = sn_swid


def dcnm_vpc_pair_utils_translate_vpc_pair_info(self, elem):

    elem["peerOneId"] = self.ip_sn[elem.get("peerOneId", None)]
    elem["peerTwoId"] = self.ip_sn[elem.get("peerTwoId", None)]

    return elem


def dcnm_vpc_pair_utils_update_have(self, have):

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


def dcnm_vpc_pair_utils_get_vpc_pair_info_from_dcnm(self, swid):

    """
    Routine to get existing information from DCNM with serial number and switch DB id.

    Parameters:
        swid (int): Switch DB Id corresponding to one of the peers
                    in the required VPC pair

    Returns:
        resp["DATA"] (dict): VPC information obtained from the DCNM server if it exists
        [] otherwise
    """

    # Get the Peer information first
    path = self.paths["VPC_PAIR_GET_PATH"]
    path = path.format(swid)

    resp = dcnm_send(self.module, "GET", path)

    if (
        resp
        and (resp["RETURN_CODE"] == 200)
        and (resp["MESSAGE"] == "OK")
        and resp["DATA"]
    ):
        peerOneId = resp["DATA"].get("peerOneSerialNumber", None)
        peerTwoId = resp["DATA"].get("peerTwoSerialNumber", None)
        peerOneDbId = resp["DATA"].get("peerOneDbId", None)
        peerTwoDbId = resp["DATA"].get("peerTwoDbId", None)
    else:
        return []

    # Get useVirtualPeerlink information
    path = self.paths["VPC_PEER_LINK_GET_PATH"]
    path = path.format(peerOneId)

    resp = dcnm_send(self.module, "GET", path)

    if (
        resp
        and (resp["RETURN_CODE"] == 200)
        and (resp["MESSAGE"] == "OK")
        and resp["DATA"]
    ):
        useVirtualPeerlink = resp["DATA"][0].get("useVirtualPeerlink", None)
    else:
        return []

    # Get the Profile information now and combine both the first response data and the current one to
    # form the 'have' object. There is no direct call to get this combined information.
    path = self.paths["VPC_PAIR_GET_POLICY_PATH"]
    path = path.format(peerOneId)

    resp = dcnm_send(self.module, "GET", path)

    if (
        resp
        and (resp["RETURN_CODE"] == 200)
        and (resp["MESSAGE"] == "OK")
        and resp["DATA"]
    ):
        resp["DATA"]["peerOneId"] = peerOneId
        resp["DATA"]["peerTwoId"] = peerTwoId
        resp["DATA"]["peerOneDbId"] = peerOneDbId
        resp["DATA"]["peerTwoDbId"] = peerTwoDbId
        resp["DATA"]["useVirtualPeerlink"] = useVirtualPeerlink

        # Some of the fields in 'have' may be different than what is sent in CREATE/UPDATE/DELETE payloads to DCNM. Update these
        # fields,if any, so that all keys are consistent between 'want' and 'have'. This will be necessary for compare function to
        # work properly.
        dcnm_vpc_pair_utils_update_have(self, resp["DATA"])
        return resp["DATA"]
    else:
        return []


def dcnm_vpc_pair_utils_get_vpc_pair_info(self, wobj):

    """
    Routine to get existing information from DCNM which matches the given object.

    Parameters:
        wobj (dict): Object information in 'want' format

    Returns:
        resp["DATA"] (dict): VPC information obtained from the DCNM server if it exists
        [] otherwise
    """

    return dcnm_vpc_pair_utils_get_vpc_pair_info_from_dcnm(
        self, self.sn_swid.get(wobj["peerOneId"], None)
    )


def dcnm_vpc_pair_utils_get_vpc_pair_payload(self, vpc_pair_info):

    vpc_pair_payload = {}

    for key in vpc_pair_info:
        if key != "profile":
            vpc_pair_payload[key] = vpc_pair_info[key]
        else:
            vpc_pair_payload["nvPairs"] = vpc_pair_info[key]
            vpc_pair_payload["nvPairs"]["FABRIC_NAME"] = self.fabric

            # Though arg_spec mentions member interfaces to be a list, the actual payload must carry a string. Do the
            # required translation
            vpc_pair_payload["nvPairs"]["PEER1_MEMBER_INTERFACES"] = ",".join(
                vpc_pair_info[key]["PEER1_MEMBER_INTERFACES"]
            )
            vpc_pair_payload["nvPairs"]["PEER2_MEMBER_INTERFACES"] = ",".join(
                vpc_pair_info[key]["PEER2_MEMBER_INTERFACES"]
            )

    # VPC payload carries serial numbers for peerOneId and peerTwoId fields. Translate then approriatley now
    vpc_pair_payload["peerOneId"] = self.ip_sn[
        vpc_pair_info.get("peerOneId", None)
    ]
    vpc_pair_payload["peerTwoId"] = self.ip_sn[
        vpc_pair_info.get("peerTwoId", None)
    ]

    return vpc_pair_payload


def dcnm_vpc_pair_utils_get_matching_want(self, vpc_pair_info):

    match_want = [
        want
        for want in self.want
        if (
            (vpc_pair_info["peerOneId"] == want["peerOneId"])
            and (vpc_pair_info["peerTwoId"] == want["peerTwoId"])
        )
    ]

    return match_want


def dcnm_vpc_pair_utils_get_matching_have(self, want):

    match_have = [
        have
        for have in self.have
        if (
            (have["peerOneId"] == want["peerOneId"])
            and (have["peerTwoId"] == want["peerTwoId"])
        )
    ]

    return match_have


def dcnm_vpc_pair_utils_get_matching_cfg(self, want):

    match_cfg = [
        cfg
        for cfg in self.config
        if (
            (self.ip_sn.get(cfg["peerOneId"], None) == want["peerOneId"])
            and (self.ip_sn.get(cfg["peerTwoId"], None) == want["peerTwoId"])
        )
    ]

    return match_cfg


def dcnm_vpc_pair_utils_merge_want_and_have(self, want, have, key):

    if want.get(key, "") == "":
        want[key] = have.get(key)
    elif have.get(key, "") == "":
        # Nothing to merge. Leave want as it is
        pass
    else:
        # Merge is different for Member interfaces and Freeform config.
        if "_MEMBER" in key:
            want[key] = have.get(key) + "," + want[key]
        else:
            want[key] = have.get(key) + "\n" + want[key]


def dcnm_vpc_pair_utils_update_vpc_pair_information(self, want, have, cfg):

    # Some fields like Member interfaces and Freefrom config are mergeable i.e. information from 'want' must be merged with
    # whatever is existing in 'have' if the state is 'merged'
    mergeable_fields = [
        "PEER1_MEMBER_INTERFACES",
        "PEER2_MEMBER_INTERFACES",
        "PEER1_PO_CONF",
        "PEER2_PO_CONF",
        "PEER1_DOMAIN_CONF",
        "PEER2_DOMAIN_CONF",
    ]

    for key in list(want.keys()):

        if key == "nvPairs":
            continue

        if cfg.get(key, None) is None:
            # The given key from want is not included in the playbook config. Copy the
            # information corresponding to the key from have
            want[key] = have.get(key, None)
            if key in mergeable_fields:
                want[key + "_defaulted"] = True
        else:
            if key in mergeable_fields:
                want[key + "_defaulted"] = False

    if have.get("nvPairs", None) is None:
        # Nothing to merge.
        return

    if want.get("nvPairs", None) is not None:
        # compare the keys here and update appropriately
        for nv_key in list(want["nvPairs"].keys()):

            if (cfg.get("profile", None) is None) or (
                cfg["profile"].get(nv_key, None) is None
            ):
                want["nvPairs"][nv_key] = have["nvPairs"][nv_key]
                if nv_key in mergeable_fields:
                    want["nvPairs"][nv_key + "_defaulted"] = True
            else:
                if nv_key in mergeable_fields:
                    want["nvPairs"][nv_key + "_defaulted"] = False


def dcnm_vpc_pair_compare_vpc_pair_objects(self, wobj, hobj):

    """
    Routine to compare have and want objects and update mismatch information.

    Parameters:
        wobj (dict): Requested object information
        hobj (dict): Existing object information
    Returns:
        DCNM_VPC_PAIR_EXIST(str): - if given vpc is same as that exists
        DCNM_VPC_PAIR_MERGE(str): - if given vpc exists but there are changes in parameters
        mismatch_reasons(list): a list identifying objects that differed if required, [] otherwise
        hobj(dict): existing object if required, [] otherwise
    """

    mismatch_reasons = []
    for key in wobj:

        if "_defaulted" in key:
            continue

        if str(hobj.get(key, None)).lower() != str(wobj[key]).lower():
            if key == "nvPairs":
                continue

            # We found an object that matched all other key values, but differs in one of the params.
            mismatch_reasons.append(
                {key.upper() + "_MISMATCH": [wobj[key], hobj.get(key, None)]}
            )

    if wobj.get("nvPairs", None) is not None:

        for key in wobj["nvPairs"]:

            if "_defaulted" in key:
                continue

            if (
                str(hobj["nvPairs"].get(key, None)).lower()
                != str(wobj["nvPairs"][key]).lower()
            ):
                # We found an object that matched all other key values, but differs in one of the params.
                mismatch_reasons.append(
                    {
                        key.upper()
                        + "_MISMATCH": [
                            wobj["nvPairs"][key],
                            hobj["nvPairs"].get(key, None),
                        ]
                    }
                )

    if mismatch_reasons != []:
        return "DCNM_VPC_PAIR_MERGE", mismatch_reasons, hobj
    else:
        return "DCNM_VPC_PAIR_EXIST", [], []


def dcnm_vpc_pair_utils_compare_want_and_have(self, want):

    """
    This routine finds an object in self.have that matches the given information. If the given
    object already exist then it is not added to the object list to be created on
    DCNM server in the current run. The given object is added to the list of objects to be
    created otherwise.

    Parameters:
        want : Object to be matched from self.have

    Returns:
        DCNM_VPC_PAIR_CREATE (str): - if a new object is to be created
        return value of  dcnm_vpc_pair_compare_vpc_pair_objects
    """

    match_have = dcnm_vpc_pair_utils_get_matching_have(self, want)

    for melem in match_have:
        return dcnm_vpc_pair_compare_vpc_pair_objects(self, want, melem)

    return "DCNM_VPC_PAIR_CREATE", [], []


def dcnm_vpc_pair_utils_get_delete_payload(self, elem):

    return {"peerOneId": elem["peerOneId"], "peerTwoId": elem["peerTwoId"]}


def dcnm_vpc_pair_utils_get_delete_deploy_payload(self, elem):

    # VPC pairing uses switch level deploy to deploy the changes. This requires a 'fabric' name
    # and switches details. Fetch the 'fabric' from the 'elem' or 'self' and thr switches from
    # 'elem'

    return {
        "fabric": self.fabric,
        "peerOneId": elem["peerOneId"],
        "peerTwoId": elem["peerTwoId"],
    }


def dcnm_vpc_pair_utils_get_vpc_pair_deploy_payload(self, elem):

    # VPC pairing uses switch level deploy to deploy the changes. This requires a 'fabric' name
    # and switches details. Fetch the 'fabric' from the 'elem' or 'self' and thr switches from
    # 'elem'

    return {
        "fabric": self.fabric,
        "peerOneId": elem["peerOneId"],
        "peerTwoId": elem["peerTwoId"],
    }


def dcnm_vpc_pair_utils_delete_from_deploy_list(self, elem, deploy_list):

    """
    Routine to delete the given element from the deploy_list

    Parameters:
        elem (dict): Element to be deleted from the list
        deploy_list (list): List from where the 'elem' is to be deleted

    Returns:
        None
    """

    for ind in range(len(deploy_list)):
        if (elem["peerOneId"] == deploy_list[ind]["peerOneId"]) and (
            elem["peerTwoId"] == deploy_list[ind]["peerTwoId"]
        ):
            del deploy_list[ind]


def dcnm_vpc_pair_utils_process_delete_payloads(self):

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
    deploy_flag = False

    for elem in self.diff_delete:

        path = self.paths["VPC_PAIR_DELETE_PATH"]
        path = path.format(elem["peerOneId"])

        resp = dcnm_send(self.module, "DELETE", path)

        if resp != []:
            self.result["response"].append(resp)

        if resp and resp.get("RETURN_CODE") != 200:
            resp["CHANGED"] = self.changed_dict[0]
            self.module.fail_json(msg=resp)
        else:
            # Check if the pair is already in "unpaired state". In this case the response contains
            # 'VPC Pair could not be deleted'. If that is the case check if the switches are already in
            # 'In-Sync' state. If they are then no need to deploy for this case.

            if isinstance(resp["DATA"], str):
                if "VPC Pair could not be deleted" in resp["DATA"]:
                    sync_state = dcnm_vpc_pair_utils_get_sync_status(
                        self, elem
                    )
                    if sync_state == "In-Sync":
                        # No need to deploy for this pair
                        dcnm_vpc_pair_utils_delete_from_deploy_list(
                            self, elem, self.diff_delete_deploy
                        )
                else:
                    delete_flag = True
            else:
                delete_flag = True

    # VPC requires a deploy after delete. Check if the delete deploy paylaods are present and process them
    deploy_flag = dcnm_vpc_pair_utils_process_deploy_payloads(
        self, self.diff_delete_deploy
    )

    return deploy_flag or delete_flag


def dcnm_vpc_pair_utils_process_create_payloads(self):

    """
    Routine to push create payloads to DCNM server. This routine implements required error checks and retry mechanisms to handle
    transient errors.

    Parameters:
        None

    Returns:
        None
    """

    resp = None
    create_flag = False

    path = self.paths["VPC_PAIR_CREATE_PATH"]

    for elem in self.diff_create:

        json_payload = json.dumps(elem)
        resp = dcnm_send(self.module, "POST", path, json_payload)

        if resp != []:
            self.result["response"].append(resp)
        if resp and resp.get("RETURN_CODE") != 200:
            resp["CHANGED"] = self.changed_dict[0]
            self.module.fail_json(msg=resp)
        else:
            create_flag = True
    return create_flag


def dcnm_vpc_pair_utils_process_modify_payloads(self):

    """
    Routine to push modify payloads to DCNM server. This routine implements required error checks and retry mechanisms to handle
    transient errors.

    Parameters:
        None

    Returns:
        None
    """

    resp = None
    modify_flag = False

    for elem in self.diff_modify:

        path = self.paths["VPC_PAIR_UPDATE_PATH"]

        json_payload = json.dumps(elem)
        # Sample json_payload
        # '{"useVirtualPeerlink":true,"peerOneId":"FDO24020JMB","peerTwoId":"FDO24020JMT"}'

        resp = dcnm_send(self.module, "PUT", path, json_payload)

        if resp != []:
            self.result["response"].append(resp)

        if resp and resp.get("RETURN_CODE") != 200:
            resp["CHANGED"] = self.changed_dict[0]
            self.module.fail_json(msg=resp)
        else:
            modify_flag = True
    return modify_flag


def dcnm_vpc_pair_utils_get_sync_status(self, elem):

    """
    Routine to get switch status information for a given fabric. This information can be processed to get
    the "In-Sync" status for the required switches.
    transient errors.

    Parameters:
        None

    Returns:
        'In-sync', if the switches configuration is "In-Sync" state, 'Not-In-Sync' otherwise
    """

    switches = [self.sn_ip[elem["peerOneId"]], self.sn_ip[elem["peerTwoId"]]]
    resp = None

    path = self.paths["VPC_PAIR_GET_SYNC_STATUS"].format(self.fabric)

    resp = dcnm_send(self.module, "GET", path)

    if resp and (resp["RETURN_CODE"] != 200):
        resp["CHANGED"] = self.changed_dict[0]
        self.module.fail_json(msg=resp)

    # Check if all switches reached the "In-Sync" state
    for elem in resp["DATA"]:
        if elem["ipAddress"] in switches:
            if elem["ccStatus"] == "In-Sync":
                switches.remove(elem["ipAddress"])
    if switches:
        # There are some switches which were deployed during this run but did not reach "In-Sync" state. Retry
        # after a delay
        return "Not-In-Sync"
    else:
        return "In-Sync"


def dcnm_vpc_pair_utils_save_config_changes(self):

    """
    Routine to save configuration changes for the given fabric.

    Parameters:
        None

    Returns:
        None
    """

    resp = None

    path = self.paths["VPC_PAIR_CFG_SAVE_PATH"].format(self.fabric)

    resp = dcnm_send(self.module, "POST", path)

    if resp != []:
        self.result["response"].append(resp)

    if resp and (resp["RETURN_CODE"] != 200):
        resp["CHANGED"] = self.changed_dict[0]
        self.module.fail_json(msg=resp)


def dcnm_vpc_pair_utils_deploy_elem(self, elem):

    """
    Routine to deploy a VPC switch pair to DCNM server.

    Parameters:
        elem(dict): An object containing information relatd to switch pairs which are to be deployed

    Returns:
        True if deploy succeded, False otherwise
    """

    resp = None
    deploy_flag = False

    for peer in ["peerOneId", "peerTwoId"]:

        path = self.paths["VPC_PAIR_DEPLOY_PATH"].format(
            elem["fabric"], elem[peer]
        )

        resp = dcnm_send(self.module, "POST", path)

        if resp != []:
            self.result["response"].append(resp)

        if resp and (resp["RETURN_CODE"] != 200):
            resp["CHANGED"] = self.changed_dict[0]
            self.module.fail_json(msg=resp)
        else:
            deploy_flag = True

    return deploy_flag, resp


def dcnm_vpc_pair_utils_process_deploy_payloads(self, deploy_list):

    """
    Routine to push deploy payloads to DCNM server. This routine implements required error checks and retry mechanisms to handle
    transient errors.

    Parameters:
        deploy_list(list): List of elements to be deployed

    Returns:
        None
    """

    resp = None
    deploy_flag = False

    if deploy_list:
        # Perform a config-save first before config-deploy
        dcnm_vpc_pair_utils_save_config_changes(self)
    else:
        return deploy_flag

    for elem in deploy_list:
        rc, resp = dcnm_vpc_pair_utils_deploy_elem(self, elem)
        if deploy_flag is not True:
            deploy_flag = rc

    if deploy_flag is True:
        for elem in deploy_list:
            retries = 0
            while retries < 10:
                sync_state = dcnm_vpc_pair_utils_get_sync_status(self, elem)
                if sync_state != "In-Sync":
                    # Sometimes a deploy retry may be required. Retry deploy to see if things get normal
                    if retries and retries % 3 == 0:
                        rc, resp = dcnm_vpc_pair_utils_deploy_elem(self, elem)
                    time.sleep(1)
                    retries += 1
                else:
                    break
            else:
                resp["CHANGED"] = self.changed_dict[0]
                self.module.fail_json(
                    msg=f"Switches {[elem['peerOneId'], elem['peerTwoId']]} did not reach 'In-Sync' state after deploy\n"
                )
    return deploy_flag


def dcnm_vpc_pair_utils_get_delete_list(self):

    del_list = []
    swid_list = self.sn_swid.values()
    for swid in swid_list:

        # Get the VPC inventory using the swid.
        vpc_pair_info = dcnm_vpc_pair_utils_get_vpc_pair_info_from_dcnm(
            self, swid
        )

        if vpc_pair_info == []:
            continue

        # If this VPC info is not included in self.want, then go ahead and add it to del_list. Otherwise
        # ignore this pair, since new configuration is included for this pair in the playbook.
        want = dcnm_vpc_pair_utils_get_matching_want(self, vpc_pair_info)
        if want == []:
            if vpc_pair_info not in del_list:
                del_list.append(vpc_pair_info)

    return del_list


def dcnm_vpc_pair_utils_get_all_filtered_vpc_pair_pairs(self):

    vpc_pair_list = []

    # If filters are provided, use the values to build the appropriate list.
    if self.vpc_pair_info == []:
        swid_list = self.sn_swid.values()
        for swid in swid_list:
            vpc_pair_info = dcnm_vpc_pair_utils_get_vpc_pair_info_from_dcnm(
                self, swid
            )

            if vpc_pair_info == []:
                continue

            if vpc_pair_info not in vpc_pair_list:
                vpc_pair_list.append(vpc_pair_info)
    else:
        for elem in self.vpc_pair_info:

            if (elem.get("peerOneId", None) is not None) and (
                self.ip_sn.get(elem["peerOneId"], None) is not None
            ):
                swid = self.sn_swid.get(
                    self.ip_sn.get(elem["peerOneId"], None), None
                )
            elif (elem.get("peerTwoId", None) is not None) and (
                self.ip_sn.get(elem["peerTwoId"], None) is not None
            ):
                swid = self.sn_swid.get(
                    self.ip_sn.get(elem["peerTwoId"], None), None
                )
            else:
                swid = None

            if swid is None:
                continue

            # Get the VPC inventory using the swid.
            vpc_pair_info = dcnm_vpc_pair_utils_get_vpc_pair_info_from_dcnm(
                self, swid
            )

            if vpc_pair_info == []:
                continue

            # Check if the vpc_pair_info matches the filter. Note that in this block of code either
            # 'peerOneId' or peerTwoId' must be present
            if (
                (elem.get("peerOneId", None) is None)
                or (
                    vpc_pair_info["peerOneId"]
                    == self.ip_sn.get(elem["peerOneId"], None)
                )
                or (
                    vpc_pair_info["peerTwoId"]
                    == self.ip_sn.get(elem["peerOneId"], None)
                )
            ) and (
                (elem.get("peerTwoId", None) is None)
                or (
                    vpc_pair_info["peerOneId"]
                    == self.ip_sn.get(elem["peerTwoId"], None)
                )
                or (
                    vpc_pair_info["peerTwoId"]
                    == self.ip_sn.get(elem["peerTwoId"], None)
                )
            ):
                if vpc_pair_info not in vpc_pair_list:
                    vpc_pair_list.append(vpc_pair_info)

    return vpc_pair_list
