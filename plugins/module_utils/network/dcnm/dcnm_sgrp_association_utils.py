from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import time
import logging

from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_send,
)

# Some of the key names used in playbook is different from what is expected in payload. Translate such keys
xlate_key = {
    "src_group_name": "srcGroupName",
    "dst_group_name": "dstGroupName",
    "src_group_id": "srcGroupId",
    "dst_group_id": "dstGroupId",
    "vrf_name": "vrfName",
    "contract_name": "contractName",
    "switch": "switch",
    "fabric": "fabricName",
}

rev_xlate_key = {
    "srcGroupName": "src_group_name",
    "dstGroupName": "dst_group_name",
    "srcGroupId": "src_group_id",
    "dstGroupId": "dst_group_id",
    "vrfName": "vrf_name",
    "contractName": "contract_name",
    "switch": "switch",
    "fabricName": "fabric",
}

dcnm_sgrp_association_paths = {
    11: {},
    12: {
        "SGRP_GET_GROUP": "/appcenter/cisco/ndfc/api/v1/security/fabrics/{}/groups",
        "SGRP_ASSOC_GET": "/appcenter/cisco/ndfc/api/v1/security/fabrics/{}/contractAssociations",
        "SGRP_ASSOC_CREATE": "/appcenter/cisco/ndfc/api/v1/security/fabrics/{}/contractAssociations",
        "SGRP_ASSOC_UPDATE": "/appcenter/cisco/ndfc/api/v1/security/fabrics/{}/contractAssociations",
        "SGRP_ASSOC_DELETE": "/appcenter/cisco/ndfc/api/v1/security/fabrics/{}/contractAssociations/bulkDelete",
        "SGRP_ASSOC_DEPLOY_BY_VRFS": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/vrfs/deploy",
        "SGRP_ASSOC_DEPLOY_BY_SWITCHES": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{}/config-deploy/{}?forceShowRun=false",
        "SGRP_ASSOC_GET_SYNC_STATUS": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{}/inventory/switchesByFabric",
        "FABRIC_ACCESS_MODE": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{}/accessmode",
    },
}


class Paths:
    def __init__(self):
        self.class_name = self.__class__.__name__
        self._version = None

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, value):
        self._version = value

    def commit(self):

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        if self._version is None:
            msg = f"{self.class_name}.commit(): "
            msg += "version is not set, which is required."
            raise ValueError(msg)

        self.paths = dcnm_sgrp_association_utils_get_paths(self._version)
        self.log.debug(f"Paths = {0}\n".format(self.paths))


def dcnm_sgrp_association_utils_get_all_sgrp_info(self):

    """
    Routine to get existing Security Groups information from DCNM.

    Parameters:
        None

    Returns:
        resp["DATA"] (dict): Security group information if available
        [] otherwise
    """

    path = self.paths["SGRP_GET_GROUP"].format(self.fabric)

    resp = dcnm_send(self.module, "GET", path)

    self.log.info(f"DCNM:Get All Security Groups Resp = {resp}\n")

    if (
        resp
        and (resp["RETURN_CODE"] == 200)
        and (resp["MESSAGE"] == "OK")
        and resp["DATA"]
    ):
        return resp["DATA"]
    else:
        return []


def dcnm_sgrp_association_utils_get_paths(version):
    return dcnm_sgrp_association_paths[version]


def dcnm_sgrp_association_utils_check_if_meta(self, dev):

    for elem in self.meta_switches:
        if dev in elem:
            return True
    return False


def dcnm_sgrp_association_utils_validate_devices(self, cfg):

    for sw in cfg["switch"]:
        if sw not in self.managable:
            mesg = "Switch {0} is not Manageable".format(sw)
            self.module.fail_json(msg=mesg)

    for sw in cfg["switch"]:
        if dcnm_sgrp_association_utils_check_if_meta(self, sw):
            mesg = "Switch {0} is not Manageable".format(sw)
            self.module.fail_json(msg=mesg)


def dcnm_sgrp_association_utils_get_all_sgrp_association_info(self):

    """
    Routine to get existing Group Associations information from DCNM.

    Parameters:
        None

    Returns:
        resp["DATA"] (dict): Security group information if available
        [] otherwise
    """

    # Get the Peer information first
    path = self.paths["SGRP_ASSOC_GET"].format(self.fabric)

    resp = dcnm_send(self.module, "GET", path)

    self.log.debug(f"DCNM:Get All SGRP Associations Resp = {0}\n".format(resp))

    if (
        resp
        and (resp["RETURN_CODE"] == 200)
        and (resp["MESSAGE"] == "OK")
        and resp["DATA"]
    ):
        return resp["DATA"]
    else:
        return []


def dcnm_sgrp_association_utils_translate_sgrp_association_info(self, elem):

    # Translate from playbook format to payload format
    return {
        "srcGroupName": elem.get("src_group_name", None),
        "dstGroupName": elem.get("dst_group_name", None),
        "srcGroupId": elem.get("src_group_id", None),
        "dstGroupId": elem.get("dst_group_id", None),
        "vrfName": elem.get("vrf_name", None),
        "contractName": elem.get("contract_name", None),
    }


def dcnm_sgrp_association_utils_get_sgrp_association_info(self, wobj):

    """
    Routine to get existing Security Group Association information from DCNM which matches the given object.

    Parameters:
        wobj (dict): Object information in 'want' format

    Returns:
        resp["DATA"] (dict): Security group association information obtained from the DCNM server if it exists
        [] otherwise
    """

    if self.sgrp_association_list == []:
        self.sgrp_association_list = dcnm_sgrp_association_utils_get_all_sgrp_association_info(
            self
        )

    for sgrp_association in self.sgrp_association_list:
        # Check if all the information match. Otherwise it is an error
        if (
            (
                (wobj.get("srcGroupName") is None)
                or (sgrp_association["srcGroupName"] == wobj["srcGroupName"])
            )
            and (
                (wobj.get("dstGroupName", None) is None)
                or (sgrp_association["dstGroupName"] == wobj["dstGroupName"])
            )
            and (
                (wobj.get("srcGroupId", None) is None)
                or (sgrp_association["srcGroupId"] == wobj["srcGroupId"])
            )
            and (
                (wobj.get("dstGroupId", None) is None)
                or (sgrp_association["dstGroupId"] == wobj["dstGroupId"])
            )
            and (
                (wobj.get("vrfName", None) is None)
                or (sgrp_association["vrfName"] == wobj["vrfName"])
            )
        ):
            return sgrp_association
    return []


def dcnm_sgrp_association_utils_get_sgrp_association_payload(
    self, sgrp_assoc_info
):

    sgrp_payload = {}
    srcGroupId = ""
    dstGroupId = ""

    if (sgrp_assoc_info.get("src_group_id", None) is None) or (
        sgrp_assoc_info.get("dst_group_id", None) is None
    ):
        if self.sgrp_info == {}:
            sgrp_list = dcnm_sgrp_association_utils_get_all_sgrp_info(self)
            [
                self.sgrp_info.update({sgrp["groupName"]: sgrp["groupId"]})
                for sgrp in sgrp_list
            ]

        if (
            self.sgrp_info.get(sgrp_assoc_info["src_group_name"], None)
            is not None
        ):
            srcGroupId = self.sgrp_info[sgrp_assoc_info["src_group_name"]]

        if (
            self.sgrp_info.get(sgrp_assoc_info["dst_group_name"], None)
            is not None
        ):
            dstGroupId = self.sgrp_info[sgrp_assoc_info["dst_group_name"]]
    else:
        srcGroupId = sgrp_assoc_info["src_group_id"]
        dstGroupId = sgrp_assoc_info["dst_group_id"]

    for key in sgrp_assoc_info:
        sgrp_payload[xlate_key[key]] = sgrp_assoc_info[key]
        sgrp_payload["fabricName"] = self.fabric
        sgrp_payload["srcGroupId"] = srcGroupId
        sgrp_payload["dstGroupId"] = dstGroupId

    return sgrp_payload


def dcnm_sgrp_association_utils_get_matching_want(self, sgrp_association_info):

    match_want = [
        want
        for want in self.want
        if (
            (
                (want.get("srcGroupName", "") == "")
                or (
                    sgrp_association_info["srcGroupName"]
                    == want["srcGroupName"]
                )
            )
            and (
                (want.get("dstGroupName", "") == "")
                or (
                    sgrp_association_info["dstGroupName"]
                    == want["dstGroupName"]
                )
            )
            and (
                (want.get("srcGroupId", "") == "")
                or (sgrp_association_info["srcGroupId"] == want["srcGroupId"])
            )
            and (
                (want.get("dstGroupId", "") == "")
                or (sgrp_association_info["dstGroupId"] == want["dstGroupId"])
            )
            and (
                (want.get("vrfName", "") == "")
                or (sgrp_association_info["vrfName"] == want["vrfName"])
            )
        )
    ]

    return match_want


def dcnm_sgrp_association_utils_get_matching_have(self, want):

    match_have = [
        have
        for have in self.have
        if (
            (
                (want.get("srcGroupName", "") == "")
                or (have["srcGroupName"] == want["srcGroupName"])
            )
            and (
                (want.get("dstGroupName", "") == "")
                or (have["dstGroupName"] == want["dstGroupName"])
            )
            and (
                (want.get("srcGroupId", "") == "")
                or (have["srcGroupId"] == want["srcGroupId"])
            )
            and (
                (want.get("dstGroupId", "") == "")
                or (have["dstGroupId"] == want["dstGroupId"])
            )
            and (
                (want.get("vrfName", "") == "")
                or (have["vrfName"] == want["vrfName"])
            )
        )
    ]

    return match_have


def dcnm_sgrp_association_utils_get_matching_cfg(self, want):

    match_cfg = [
        cfg
        for cfg in self.config
        if (
            (
                (cfg.get("src_group_name", "") == "")
                or (want["srcGroupName"] == cfg["src_group_name"])
            )
            and (
                (cfg.get("dst_group_name", "") == "")
                or (want["dstGroupName"] == cfg["dst_group_name"])
            )
            and (
                (cfg.get("src_group_id", "") == "")
                or (want["srcGroupId"] == cfg["src_group_id"])
            )
            and (
                (cfg.get("dst_group_id", "") == "")
                or (want["dstGroupId"] == cfg["dst_group_id"])
            )
            and (
                (cfg.get("vrf_name", "") == "")
                or (want["vrfName"] == cfg["vrf_name"])
            )
        )
    ]

    return match_cfg


def dcnm_sgrp_association_utils_update_sgrp_association_information(
    self, want, have, cfg
):

    for key in list(want.keys()):
        if cfg.get(rev_xlate_key[key], None) is None:
            # The given key from want is not included in the playbook config. Copy the
            # information corresponding to the key from have
            want[key] = have.get(key, "")


def dcnm_sgrp_association_utils_compare_sgrp_objects(self, wobj, hobj):

    """
    Routine to compare have and want objects and update mismatch information.

    Parameters:
        wobj (dict): Requested object information
        hobj (dict): Existing object information
    Returns:
        DCNM_SGRP_ASSOCIATION_EXIST(str): - if given Security Grouo Association is same as that exists
        DCNM_SGRP_ASSOCIATION_MERGE(str): - if given Security Grouo Association exists but there are changes in parameters
        mismatch_reasons(list): a list identifying objects that differed if required, [] otherwise
        hobj(dict): existing object if required, [] otherwise
    """

    mismatch_reasons = []
    for key in wobj:

        if key == "switch":
            continue

        if str(hobj.get(key, None)).lower() != str(wobj[key]).lower():
            # Differs in one of the params.
            mismatch_reasons.append(
                {key.upper() + "_MISMATCH": [wobj[key], hobj.get(key, None)]}
            )

    if mismatch_reasons != []:
        return "DCNM_SGRP_ASSOCIATION_MERGE", mismatch_reasons, hobj
    else:
        return "DCNM_SGRP_ASSOCIATION_EXIST", [], []


def dcnm_sgrp_association_utils_compare_want_and_have(self, want):

    """
    This routine finds an object in self.have that matches the given information. If the given
    object already exist then it is not added to the object list to be created on
    DCNM server in the current run. The given object is added to the list of objects to be
    created otherwise.

    Parameters:
        want : Object to be matched from self.have

    Returns:
        DCNM_SGRP_ASSOCIATION_CREATE (str): - if a new object is to be created
        return value of  dcnm_sgrp_association_utils_compare_sgrp_objects
    """

    match_have = dcnm_sgrp_association_utils_get_matching_have(self, want)

    for melem in match_have:
        return dcnm_sgrp_association_utils_compare_sgrp_objects(
            self, want, melem
        )

    return "DCNM_SGRP_ASSOCIATION_CREATE", [], []


def dcnm_sgrp_association_utils_get_delete_payload(self, elem):

    return elem["uuid"]


def dcnm_sgrp_association_utils_update_deploy_info(self, elem, deploy_object):

    # This routine updates the deploy list with a dictinary of key value pairs, where keys will be switch
    # serial numbers, and the values will be a list of all VRFs associated with the given elem. This can be
    # invoked for updating diff_deploy and diff_delete_deploy lists as well.

    # for delete state, switch is not a mandatory element. If switch is not included in the playbook, then apply
    # it for all switches.

    if elem.get("switch", None) is None:
        switch_list = self.ip_sn.keys()
    else:
        switch_list = elem["switch"]

    vrf_list = []
    for sw_elem in switch_list:
        sno = self.ip_sn[sw_elem]
        if deploy_object.get(sno, None) is None:
            deploy_object[sno] = ""

        if elem["vrfName"] not in vrf_list:
            vrf_list.append(elem["vrfName"])

        if deploy_object[sno] != "":
            cum_vrf_list = list(set(deploy_object[sno].split(",") + vrf_list))
        else:
            cum_vrf_list = list(set(vrf_list))

        deploy_object[sno] = ",".join(cum_vrf_list)


def dcnm_sgrp_association_utils_get_sgrp_association_deploy_payload(
    self, elem, reason
):

    # Security Groups uses switch or vrf level deploy to deploy the changes. Each of this case requires
    # a different payload. For switch level deploy case, we need the serial number of all switches. But for
    # vrf level deploy, we will need a dict with switches as keys and VRFs as a list of values for each of these
    # keys.

    if (
        (reason == "DCNM_SGRP_ASSOCIATION_CREATE")
        or (reason == "DCNM_SGRP_ASSOCIATION_MERGE")
        or (
            [
                sw_elem
                for sw_elem in elem["switch"]
                if self.sync_info.get(sw_elem, "Not-In-sync") != "In-Sync"
            ]
            != []
        )
    ):
        dcnm_sgrp_association_utils_update_deploy_info(
            self, elem, self.diff_deploy
        )


def dcnm_sgrp_association_utils_process_delete_payloads(self):

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
        path = self.paths["SGRP_ASSOC_DELETE"]
        path = path.format(self.fabric)

        json_payload = json.dumps(self.diff_delete)

        resp = dcnm_send(self.module, "POST", path, json_payload)

        self.log.info(
            f"DCNM:Delete Path = {path}, Resp = {resp}. Payload = {json_payload}\n"
        )

        if resp:
            self.result["response"].append(resp)

        if resp and resp.get("RETURN_CODE") != 200:
            resp["CHANGED"] = self.changed_dict[0]
            self.module.fail_json(msg=resp)
        else:
            delete_flag = True

    if delete_flag:
        dcnm_sgrp_association_utils_process_deploy_payloads(
            self, self.diff_delete_deploy
        )

    return delete_flag


def dcnm_sgrp_association_utils_process_payloads_list(
    self, payload_list, command, path
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
        # Creates can happen in bulk.
        json_payload = json.dumps(payload_list)
        resp = dcnm_send(self.module, command, path, json_payload)
        self.log.info(
            f"DCNM:Create Path = {path}, Resp = {resp}, Payload - {json_payload}\n"
        )
        if resp:
            self.result["response"].append(resp)
        if resp and resp.get("RETURN_CODE") != 200:
            resp["CHANGED"] = self.changed_dict[0]
            self.module.fail_json(msg=resp)
        else:
            flag = True
    elif command == "PUT":
        for elem in payload_list:
            uuid = elem.pop("uuid")
            json_payload = json.dumps(elem)
            resp = dcnm_send(
                self.module, command, path + "/" + str(uuid), json_payload
            )
            self.log.info(
                f"DCNM:Modify Path = {path}, Resp = {resp}, Payload = {json_payload}\n"
            )

            if resp:
                self.result["response"].append(resp)
            if resp and resp.get("RETURN_CODE") != 200:
                resp["CHANGED"] = self.changed_dict[0]
                self.module.fail_json(msg=resp)
            else:
                flag = True
    return flag


def dcnm_sgrp_association_utils_process_create_payloads(self):

    """
    Routine to push create payloads to DCNM server.

    Parameters:
        None

    Returns:
        True if create payloads are successfully pushed to server
        False otherwise
    """

    if self.diff_create == []:
        return

    create_path = self.paths["SGRP_ASSOC_CREATE"].format(self.fabric)

    return dcnm_sgrp_association_utils_process_payloads_list(
        self, self.diff_create, "POST", create_path
    )


def dcnm_sgrp_association_utils_process_modify_payloads(self):

    """
    Routine to push modify payloads to DCNM server.

    Parameters:
        None

    Returns:
        True if modified payloads are successfully pushed to server
        False otherwise
    """

    if self.diff_modify == []:
        return

    modify_path = self.paths["SGRP_ASSOC_UPDATE"].format(self.fabric)

    return dcnm_sgrp_association_utils_process_payloads_list(
        self, self.diff_modify, "PUT", modify_path
    )


def dcnm_sgrp_association_utils_get_sync_status(self):

    """
    Routine to get switch status information for a given fabric. This information can be processed to get
    the "In-Sync" status for the required switches.
    transient errors.

    Parameters:
        None

    Returns:
        sync_status containing the SYNC status of all switches
    """

    resp = None
    sync_info = {}

    path = self.paths["SGRP_ASSOC_GET_SYNC_STATUS"].format(self.fabric)

    resp = dcnm_send(self.module, "GET", path)

    self.log.info(f"DCNM:Get Switch SYNC Status Resp = {resp}\n")
    status_info = [
        {f"({d['ipAddress']} : {d['ccStatus']}"} for d in resp["DATA"]
    ]
    self.log.info(f"Status Info = {status_info}\n")

    if resp and (resp["RETURN_CODE"] != 200):
        resp["CHANGED"] = self.changed_dict[0]
        self.module.fail_json(msg=resp)
    else:
        for elem in resp["DATA"]:
            sync_info[elem["ipAddress"]] = elem["ccStatus"]
        return sync_info


def dcnm_sgrp_association_utils_deploy_payload(self, deploy_info):

    """
    Routine to deploy a Security Group Associations to DCNM server.

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
        path = self.paths["SGRP_ASSOC_DEPLOY_BY_SWITCHES"].format(
            self.fabric, ",".join(deploy_info.keys())
        )
        resp = dcnm_send(self.module, "POST", path)
    #   elif self.deploy == "vrfs":
    #       path = self.paths["SGRP_ASSOC_DEPLOY_BY_VRFS"]
    #       json_payload = json.dumps(deploy_info)
    #       resp = dcnm_send(self.module, "POST", path, json_payload)

    if resp:
        self.result["response"].append(resp)

    self.log.info(f"DCNM:Deploy Element Path = {path},  Resp = {resp}\n")
    self.log.info(f"Deploy Element Payload = {json_payload}\n")

    if resp and (resp["RETURN_CODE"] != 200):
        resp["CHANGED"] = self.changed_dict[0]
        self.module.fail_json(msg=resp)
    else:
        deploy_flag = True

    return deploy_flag, resp


def dcnm_sgrp_association_utils_process_deploy_payloads(self, deploy_info):

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

    rc, resp = dcnm_sgrp_association_utils_deploy_payload(self, deploy_info)
    if deploy_flag is not True:
        deploy_flag = rc

    if deploy_flag is True:
        retries = 0
        while retries < 20:

            sync_info = dcnm_sgrp_association_utils_get_sync_status(self)

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


def dcnm_sgrp_association_utils_get_delete_list(self):

    del_list = []

    if self.sgrp_association_list == []:
        # Get all security group information present
        sgrp_association_list = dcnm_sgrp_association_utils_get_all_sgrp_association_info(
            self
        )
    else:
        sgrp_association_list = self.sgrp_association_list

    if sgrp_association_list == []:
        return []

    # If this info is not included in self.want, then go ahead and add it to del_list. Otherwise
    # ignore this pair, since new configuration is included for this pair in the playbook.
    for sgrp_association in sgrp_association_list:
        want = dcnm_sgrp_association_utils_get_matching_want(
            self, sgrp_association
        )
        if want == []:
            if sgrp_association not in del_list:
                del_list.append(sgrp_association)

    return del_list


def dcnm_sgrp_association_utils_get_all_filtered_sgrp_association_objects(
    self
):

    if self.sgrp_association_list == []:
        sgrp_association_list = dcnm_sgrp_association_utils_get_all_sgrp_association_info(
            self
        )
    else:
        sgrp_association_list = self.sgrp_association_list

    # If filters are provided, use the values to build the appropriate list.
    if self.sgrp_association_info == []:
        return sgrp_association_list
    else:
        sgrp_filtered_list = []

        for elem in self.sgrp_association_info:
            match = [
                sgrp_association
                for sgrp_association in sgrp_association_list
                if (
                    (
                        elem.get("src_group_id", None) is None
                        or sgrp_association["srcGroupId"]
                        == elem["src_group_id"]
                    )
                    and (
                        elem.get("src_group_name", None) is None
                        or sgrp_association["srcGroupName"]
                        == elem["src_group_name"]
                    )
                    and (
                        elem.get("dst_group_id", None) is None
                        or sgrp_association["dstGroupId"]
                        == elem["dst_group_id"]
                    )
                    and (
                        elem.get("dst_group_name", None) is None
                        or sgrp_association["dstGroupName"]
                        == elem["dst_group_name"]
                    )
                    and (
                        elem.get("vrf_name", None) is None
                        or sgrp_association["vrfName"] == elem["vrf_name"]
                    )
                    and (
                        elem.get("contract_name", None) is None
                        or sgrp_association["contractName"]
                        == elem["contract_name"]
                    )
                )
            ]

            if match == []:
                continue

            for melem in match:
                if melem not in sgrp_filtered_list:
                    sgrp_filtered_list.append(melem)

    return sgrp_filtered_list
