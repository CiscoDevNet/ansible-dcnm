import inspect
import json
import logging
import re

from .inventory_serial_number_to_fabric_name import InventorySerialNumberToFabricName
from .inventory_serial_number_to_ipv4 import InventorySerialNumberToIpv4
from .model_controller_response_vrfs_switches_v12 import (
    ControllerResponseVrfsSwitchesDataItem,
    ControllerResponseVrfsSwitchesExtensionPrototypeValue,
    ControllerResponseVrfsSwitchesV12,
    ControllerResponseVrfsSwitchesVrfLiteConnProtoItem,
)
from .model_payload_vrfs_attachments import PayloadVrfsAttachments, PayloadVrfsAttachmentsLanAttachListItem, PayloadVrfsAttachmentsLanAttachListInstanceValues
from .model_playbook_vrf_v12 import PlaybookVrfModelV12
from .serial_number_to_vrf_lite import SerialNumberToVrfLite


class DiffAttachToControllerPayload:
    """
    # Summary

    - Transmute diff_attach to a list of PayloadVrfsAttachments models.
    - For each model, update its lan_attach_list
        - Set vlan to 0
        - Set the fabric name to the child fabric name, if fabric is MSD
        - Update vrf_lite extensions with information from the switch

    ## Raises

    - ValueError if diff_attach cannot be mutated

    ## Usage
    ```python
    instance = DiffAttachToControllerPayload()
    instance.diff_attach = diff_attach
    instance.fabric_type = fabric_type
    instance.fabric_inventory = get_fabric_inventory_details(self.module, self.fabric)
    instance.commit()
    payload_models = instance.payload_models
    payload = instance.payload
    ```

    Where:

    - `diff_attach` is a list of dictionaries representing the VRF attachments.
    - `fabric_name` is the name of the fabric.
    - `fabric_type` is the type of the fabric (e.g., "MFD" for multisite fabrics).
    - `fabric_inventory` is a dictionary containing inventory details for `fabric_name`

    ## inventory

    ```json
    {
        "10.10.10.224": {
            "ipAddress": "10.10.10.224",
            "logicalName": "dt-n9k1",
            "serialNumber": "XYZKSJHSMK1",
            "switchRole": "leaf"
        }
    }
    ```
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        # Set self._sender to list to avoid pylint not-callable error
        self._sender: callable = list
        self._diff_attach: list[dict] = []
        self._fabric_name: str = ""
        # TODO: remove self.fabric_type once we use fabric_inventory.fabricTechnology for fabric_type
        self._fabric_type: str = ""
        self._fabric_inventory: dict = {}
        self._ansible_module = None  # AndibleModule instance
        self._payload: str = ""
        self._payload_model: list[PayloadVrfsAttachments] = []
        self._playbook_models: list = []

        self.serial_number_to_fabric_name = InventorySerialNumberToFabricName()
        self.serial_number_to_ipv4 = InventorySerialNumberToIpv4()
        self.serial_number_to_vrf_lite = SerialNumberToVrfLite()

    def log_list_of_models(self, model_list: list, by_alias: bool = False) -> None:
        """
        # Summary

        Log a list of Pydantic models.
        """
        caller = inspect.stack()[1][3]
        for index, model in enumerate(model_list):
            msg = f"caller: {caller}: by_alias={by_alias}, index {index}. "
            msg += f"{json.dumps(model.model_dump(by_alias=by_alias), indent=4, sort_keys=True)}"
            self.log.debug(msg)

    def commit(self) -> None:
        """
        # Summary

        - Transmute diff_attach to a list of PayloadVrfsAttachments models.
        - For each model, update its lan_attach_list
          - Set vlan to 0
          - Set the fabric name to the child fabric name, if fabric is MSD
          - Update vrf_lite extensions with information from the switch

        ## Raises

        - ValueError if diff_attach cannot be mutated
        - ValueError if diff_attach is empty when commit() is called
        - ValueError if instance.payload_model is accessed before commit() is called
        - ValueError if instance.payload is accessed before commit() is called
        """
        caller = inspect.stack()[1][3]
        method_name = inspect.stack()[0][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}."
        self.log.debug(msg)

        if not self.sender:
            msg = f"{self.class_name}.{caller}: "
            msg += "Set instance.sender before calling commit()."
            self.log.debug(msg)
            raise ValueError(msg)

        if not self.diff_attach:
            msg = f"{self.class_name}.{method_name}: {caller}: "
            msg += "diff_attach is empty. "
            msg += "Set instance.diff_attach before calling commit()."
            self.log.debug(msg)
            raise ValueError(msg)

        if not self.fabric_inventory:
            msg = f"{self.class_name}.{method_name}: {caller}: "
            msg += "Set instance.fabric_inventory before calling commit()."
            self.log.debug(msg)
            raise ValueError(msg)

        if not self.playbook_models:
            msg = f"{self.class_name}.{method_name}: {caller}: "
            msg += "Set instance.playbook_models before calling commit()."
            self.log.debug(msg)
            raise ValueError(msg)

        if not self.ansible_module:
            msg = f"{self.class_name}.{method_name}: {caller}: "
            msg += "Set instance.ansible_module before calling commit()."
            self.log.debug(msg)
            raise ValueError(msg)

        self.serial_number_to_fabric_name.fabric_inventory = self.fabric_inventory
        self.serial_number_to_ipv4.fabric_inventory = self.fabric_inventory

        self.serial_number_to_vrf_lite.playbook_models = self.playbook_models
        self.serial_number_to_vrf_lite.fabric_inventory = self.fabric_inventory
        self.serial_number_to_vrf_lite.commit()

        msg = f"Received diff_attach: {json.dumps(self.diff_attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        diff_attach_list: list[PayloadVrfsAttachments] = [
            PayloadVrfsAttachments(
                vrfName=item.get("vrfName"),
                lanAttachList=[
                    PayloadVrfsAttachmentsLanAttachListItem(
                        deployment=lan_attach.get("deployment"),
                        extensionValues=lan_attach.get("extensionValues"),
                        fabric=lan_attach.get("fabric") or lan_attach.get("fabricName"),
                        freeformConfig=lan_attach.get("freeformConfig"),
                        instanceValues=PayloadVrfsAttachmentsLanAttachListInstanceValues(**json.loads(lan_attach.get("instanceValues"))if lan_attach.get("instanceValues") else {}),
                        serialNumber=lan_attach.get("serialNumber"),
                        vlan=lan_attach.get("vlan") or lan_attach.get("vlanId") or 0,
                        vrfName=lan_attach.get("vrfName"),
                    )
                    for lan_attach in item.get("lanAttachList")
                    if item.get("lanAttachList") is not None
                ],
            )
            for item in self.diff_attach
            if self.diff_attach
        ]

        payload_model: list[PayloadVrfsAttachments] = []
        for vrf_attach_payload in diff_attach_list:
            new_lan_attach_list = self.update_lan_attach_list_model(vrf_attach_payload)
            vrf_attach_payload.lan_attach_list = new_lan_attach_list
            payload_model.append(vrf_attach_payload)

        msg = f"Setting payload_model: type(payload_model[0]): {type(payload_model[0])} length: {len(payload_model)}."
        self.log.debug(msg)
        self.log_list_of_models(payload_model, by_alias=True)

        self._payload_model = payload_model
        self._payload = json.dumps([model.model_dump(exclude_unset=True, by_alias=True) for model in payload_model])

    def update_lan_attach_list_model(self, diff_attach: PayloadVrfsAttachments) -> list[PayloadVrfsAttachmentsLanAttachListItem]:
        """
        # Summary

        - Update the lan_attach_list in each PayloadVrfsAttachments
          - Set vlan to 0
          - Set the fabric name to the child fabric name, if fabric is MSD
          - Update vrf_lite extensions with information from the switch

        ## Raises

        - ValueError if diff_attach cannot be mutated
        """
        diff_attach = self.update_lan_attach_list_vlan(diff_attach)
        diff_attach = self.update_lan_attach_list_fabric_name(diff_attach)
        diff_attach = self.update_lan_attach_list_vrf_lite(diff_attach)
        return diff_attach.lan_attach_list

    def update_lan_attach_list_vlan(self, diff_attach: PayloadVrfsAttachments) -> PayloadVrfsAttachments:
        """
        # Summary

        Set PayloadVrfsAttachments.lan_attach_list.vlan to 0 and return the updated
        PayloadVrfsAttachments instance.

        ## Raises

        - None
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}."
        self.log.debug(msg)

        new_lan_attach_list = []
        for vrf_attach in diff_attach.lan_attach_list:
            vrf_attach.vlan = 0
            new_lan_attach_list.append(vrf_attach)
        diff_attach.lan_attach_list = new_lan_attach_list
        msg = f"Returning updated diff_attach: {json.dumps(diff_attach.model_dump(), indent=4, sort_keys=True)}"
        self.log.debug(msg)
        return diff_attach

    def update_lan_attach_list_fabric_name(self, diff_attach: PayloadVrfsAttachments) -> PayloadVrfsAttachments:
        """
        # Summary

        Update PayloadVrfsAttachments.lan_attach_list.fabric and return the updated
        PayloadVrfsAttachments instance.

        - If fabric_type is not MFD, return the diff_attach unchanged
        - If fabric_type is MFD, replace diff_attach.lan_attach_list.fabric with child fabric name

        ## Raises

        - None
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}."
        self.log.debug(msg)

        new_lan_attach_list = []
        for vrf_attach in diff_attach.lan_attach_list:
            vrf_attach.fabric = self.get_vrf_attach_fabric_name(vrf_attach)
            new_lan_attach_list.append(vrf_attach)

        diff_attach.lan_attach_list = new_lan_attach_list
        msg = f"Returning updated diff_attach: {json.dumps(diff_attach.model_dump(), indent=4, sort_keys=True)}"
        self.log.debug(msg)
        return diff_attach

    def update_lan_attach_list_vrf_lite(self, diff_attach: PayloadVrfsAttachments) -> PayloadVrfsAttachments:
        """
        - If the switch is not a border switch, fail the module
        - Get associated extension_prototype_values (ControllerResponseVrfsSwitchesExtensionPrototypeValue) from the switch
        - Update vrf lite extensions with information from the extension_prototype_values

        ## Raises

        - fail_json: If the switch is not a border switch
        """
        caller = inspect.stack()[1][3]
        method_name = inspect.stack()[0][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}."
        self.log.debug(msg)

        new_lan_attach_list = []
        msg = f"len(diff_attach.lan_attach_list): {len(diff_attach.lan_attach_list)}"
        self.log.debug(msg)
        msg = "diff_attach.lan_attach_list: "
        self.log.debug(msg)
        self.log_list_of_models(diff_attach.lan_attach_list)

        for lan_attach_item in diff_attach.lan_attach_list:
            serial_number = lan_attach_item.serial_number

            self.serial_number_to_vrf_lite.serial_number = serial_number
            if self.serial_number_to_vrf_lite.vrf_lite is None:
                new_lan_attach_list.append(lan_attach_item)
                continue

            # VRF Lite processing

            msg = f"lan_attach_item.extension_values: {lan_attach_item.extension_values}."
            self.log.debug(msg)

            ip_address = self.serial_number_to_ipv4.convert(lan_attach_item.serial_number)
            if not self.is_border_switch(lan_attach_item.serial_number):
                msg = f"{self.class_name}.{method_name}: "
                msg += f"caller {caller}. "
                msg += "VRF LITE cannot be attached to "
                msg += "non-border switch. "
                msg += f"ip: {ip_address}, "
                msg += f"serial number: {lan_attach_item.serial_number}"
                raise ValueError(msg)

            lite_objects_model = self.get_list_of_vrfs_switches_data_item_model(lan_attach_item)

            msg = f"ip_address {ip_address} ({lan_attach_item.serial_number}), "
            msg += f"lite_objects: length {len(lite_objects_model)}."
            self.log_list_of_models(lite_objects_model)

            if not lite_objects_model:
                msg = f"ip_address {ip_address} ({lan_attach_item.serial_number}), "
                msg += "No lite objects. Append lan_attach_item to new_attach_list and continue."
                self.log.debug(msg)
                new_lan_attach_list.append(lan_attach_item)
                continue

            extension_prototype_values = lite_objects_model[0].switch_details_list[0].extension_prototype_values
            msg = f"ip_address {ip_address} ({lan_attach_item.serial_number}), "
            msg += f"lite (list[ControllerResponseVrfsSwitchesExtensionPrototypeValue]). length: {len(extension_prototype_values)}."
            self.log.debug(msg)
            self.log_list_of_models(extension_prototype_values)

            lan_attach_item = self.update_vrf_attach_vrf_lite_extensions(lan_attach_item, extension_prototype_values)

            new_lan_attach_list.append(lan_attach_item)
        diff_attach.lan_attach_list = new_lan_attach_list

        msg = f"Returning updated diff_attach: {json.dumps(diff_attach.model_dump(), indent=4, sort_keys=True)}"
        self.log.debug(msg)
        return diff_attach

    def update_vrf_attach_vrf_lite_extensions(
        self, vrf_attach: PayloadVrfsAttachmentsLanAttachListItem, lite: list[ControllerResponseVrfsSwitchesExtensionPrototypeValue]
    ) -> PayloadVrfsAttachmentsLanAttachListItem:
        """
        # Summary

        Will replace update_vrf_attach_vrf_lite_extensions in the future.

        ## params

        -   vrf_attach
            A PayloadVrfsAttachmentsLanAttachListItem model containing extension_values to update.
        -   lite: A list of current vrf_lite extension models
            (ControllerResponseVrfsSwitchesExtensionPrototypeValue) from the switch

        ## Description

        1.  Merge the values from the vrf_attach object into a matching
            vrf_lite extension object (if any) from the switch.
        2.  Update the vrf_attach object with the merged result.
        3.  Return the updated vrf_attach object.

        If no matching ControllerResponseVrfsSwitchesExtensionPrototypeValue model is found,
        return the unmodified vrf_attach object.

        "matching" in this case means:

        1.  The extensionType of the switch's extension object is VRF_LITE
        2.  The IF_NAME in the extensionValues of the extension object
            matches the interface in vrf_attach.extension_values.
        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}."
        self.log.debug(msg)

        msg = "vrf_attach: "
        msg += f"{json.dumps(vrf_attach.model_dump(by_alias=False), indent=4, sort_keys=True)}"
        self.log.debug(msg)

        serial_number = vrf_attach.serial_number

        msg = f"serial_number: {serial_number}, "
        msg += f"Received list of lite_objects (list[ControllerResponseVrfsSwitchesExtensionPrototypeValue]). length: {len(lite)}."
        self.log.debug(msg)
        self.log_list_of_models(lite)

        ext_values = self.get_extension_values_from_lite_objects(lite)
        if ext_values is None:
            ip_address = self.serial_number_to_ipv4.convert(serial_number)
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += f"No VRF LITE capable interfaces found on switch {ip_address} ({serial_number})."
            self.log.debug(msg)
            self.ansible_module.fail_json(msg=msg)

        extension_values = json.loads(vrf_attach.extension_values)
        vrf_lite_conn = json.loads(extension_values.get("VRF_LITE_CONN", []))
        multisite_conn = json.loads(extension_values.get("MULTISITE_CONN", []))
        msg = f"type(extension_values): {type(extension_values)}, type(vrf_lite_conn): {type(vrf_lite_conn)}, type(multisite_conn): {type(multisite_conn)}"
        self.log.debug(msg)
        msg = f"vrf_attach.extension_values: {json.dumps(extension_values, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        msg = f"vrf_lite_conn: {json.dumps(vrf_lite_conn, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        msg = f"multisite_conn: {json.dumps(multisite_conn, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        matches: dict = {}
        user_vrf_lite_interfaces = []
        switch_vrf_lite_interfaces = []
        for item in vrf_lite_conn.get("VRF_LITE_CONN", []):
            item_interface = item.get("IF_NAME")
            user_vrf_lite_interfaces.append(item_interface)
            for ext_value in ext_values:
                ext_value_interface = ext_value.if_name
                switch_vrf_lite_interfaces.append(ext_value_interface)
                msg = f"item_interface: {item_interface}, "
                msg += f"ext_value_interface: {ext_value_interface}"
                self.log.debug(msg)
                if item_interface != ext_value_interface:
                    continue
                msg = "Found item: "
                msg += f"item[interface] {item_interface}, == "
                msg += f"ext_values.if_name {ext_value_interface}."
                self.log.debug(msg)
                msg = f"{json.dumps(item, indent=4, sort_keys=True)}"
                self.log.debug(msg)
                matches[item_interface] = {"user": item, "switch": ext_value}
        if not matches:
            ip_address = self.serial_number_to_ipv4.convert(serial_number)
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += "No matching interfaces with vrf_lite extensions "
            msg += f"found on switch {ip_address} ({serial_number}). "
            msg += "playbook vrf_lite_interfaces: "
            msg += f"{','.join(sorted(user_vrf_lite_interfaces))}. "
            msg += "switch vrf_lite_interfaces: "
            msg += f"{','.join(sorted(switch_vrf_lite_interfaces))}."
            self.log.debug(msg)
            raise ValueError(msg)

        msg = "Matching extension object(s) found on the switch. "
        self.log.debug(msg)

        extension_values = {"VRF_LITE_CONN": [], "MULTISITE_CONN": []}

        for interface, item in matches.items():
            user = item["user"]
            switch = item["switch"]
            msg = f"interface: {interface}: "
            self.log.debug(msg)
            msg = "item.user: "
            msg += f"{json.dumps(user, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            msg = "item.switch: "
            msg += f"{json.dumps(switch.model_dump(), indent=4, sort_keys=True)}"
            self.log.debug(msg)

            nbr_dict = {
                "IF_NAME": user.get("IF_NAME"),
                "DOT1Q_ID": str(user.get("DOT1Q_ID") or switch.dot1q_id),
                "IP_MASK": user.get("IP_MASK") or switch.ip_mask,
                "NEIGHBOR_IP": user.get("NEIGHBOR_IP") or switch.neighbor_ip,
                "NEIGHBOR_ASN": switch.neighbor_asn,
                "IPV6_MASK": user.get("IPV6_MASK") or switch.ipv6_mask,
                "IPV6_NEIGHBOR": user.get("IPV6_NEIGHBOR") or switch.ipv6_neighbor,
                "AUTO_VRF_LITE_FLAG": switch.auto_vrf_lite_flag,
                "PEER_VRF_NAME": user.get("PEER_VRF_NAME") or switch.peer_vrf_name,
                "VRF_LITE_JYTHON_TEMPLATE": user.get("Ext_VRF_Lite_Jython") or switch.vrf_lite_jython_template or "Ext_VRF_Lite_Jython",
            }
            extension_values["VRF_LITE_CONN"].append(nbr_dict)

        ms_con = {"MULTISITE_CONN": []}
        extension_values["MULTISITE_CONN"] = json.dumps(ms_con)
        extension_values["VRF_LITE_CONN"] = json.dumps({"VRF_LITE_CONN": extension_values["VRF_LITE_CONN"]})
        vrf_attach.extension_values = json.dumps(extension_values).replace(" ", "")

        msg = "Returning modified vrf_attach: "
        msg += f"{json.dumps(vrf_attach.model_dump(), indent=4, sort_keys=True)}"
        self.log.debug(msg)
        return vrf_attach

    def get_extension_values_from_lite_objects(
        self, lite: list[ControllerResponseVrfsSwitchesExtensionPrototypeValue]
    ) -> list[ControllerResponseVrfsSwitchesVrfLiteConnProtoItem]:
        """
        # Summary

        Given a list of lite objects (ControllerResponseVrfsSwitchesExtensionPrototypeValue), return:

        -   A list containing the extensionValues (ControllerResponseVrfsSwitchesVrfLiteConnProtoItem),
            if any, from these lite objects.
        -   An empty list, if the lite objects have no extensionValues

        ## Raises

        None
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}"
        self.log.debug(msg)

        extension_values_list: list[ControllerResponseVrfsSwitchesVrfLiteConnProtoItem] = []
        for item in lite:
            if item.extension_type != "VRF_LITE":
                continue
            extension_values_list.append(item.extension_values)

        msg = f"Returning extension_values_list (list[ControllerResponseVrfsSwitchesVrfLiteConnProtoItem]). length: {len(extension_values_list)}."
        self.log.debug(msg)
        self.log_list_of_models(extension_values_list)

        return extension_values_list

    def get_list_of_vrfs_switches_data_item_model(
        self, lan_attach_item: PayloadVrfsAttachmentsLanAttachListItem
    ) -> list[ControllerResponseVrfsSwitchesDataItem]:
        """
        # Summary

        Will replace get_list_of_vrfs_switches_data_item_model() in the future.
        Retrieve the IP/Interface that is connected to the switch with serial_number

        PayloadVrfsAttachmentsLanAttachListItem must contain at least the following fields:

        - fabric: The fabric to search
        - serial_number: The serial_number of the switch
        - vrf_name: The vrf to search
        """
        caller = inspect.stack()[1][3]
        method_name = inspect.stack()[0][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}."
        self.log.debug(msg)

        msg = f"lan_attach_item: {json.dumps(lan_attach_item.model_dump(by_alias=False), indent=4, sort_keys=True)}"
        self.log.debug(msg)

        verb = "GET"
        path = "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics"
        path += f"/{lan_attach_item.fabric}/vrfs/switches?vrf-names={lan_attach_item.vrf_name}&serial-numbers={lan_attach_item.serial_number}"
        msg = f"verb: {verb}, path: {path}"
        self.log.debug(msg)
        lite_objects = self.sender(self.ansible_module, verb, path)

        if lite_objects is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{caller}: Unable to retrieve lite_objects."
            raise ValueError(msg)

        try:
            response = ControllerResponseVrfsSwitchesV12(**lite_objects)
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{caller}: Unable to parse response: {error}"
            raise ValueError(msg) from error

        msg = f"Returning list of VrfSwitchesDataItem. length {len(response.DATA)}."
        self.log.debug(msg)
        self.log_list_of_models(response.DATA)

        return response.DATA

    def get_vrf_attach_fabric_name(self, vrf_attach: PayloadVrfsAttachmentsLanAttachListItem) -> str:
        """
        # Summary

        For multisite fabrics, return the name of the child fabric returned by
        `self.serial_number_to_fabric[serial_number]`

        ## params

        - `vrf_attach`

        A PayloadVrfsAttachmentsLanAttachListItem model.
        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}."
        self.log.debug(msg)

        msg = "Received vrf_attach: "
        msg += f"{json.dumps(vrf_attach.model_dump(by_alias=True), indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if self.fabric_type != "MFD":
            msg = f"FABRIC_TYPE {self.fabric_type} is not MFD. "
            msg += f"Returning unmodified fabric name {vrf_attach.fabric}."
            self.log.debug(msg)
            return vrf_attach.fabric

        msg = f"fabric_type: {self.fabric_type}, "
        msg += f"vrf_attach.fabric: {vrf_attach.fabric}."
        self.log.debug(msg)

        serial_number = vrf_attach.serial_number

        if serial_number is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += "Unable to parse vrf_attach.serial_number. "
            msg += f"{json.dumps(vrf_attach.model_dump(by_alias=False), indent=4, sort_keys=True)}"
            self.log.debug(msg)
            raise ValueError(msg)

        try:
            child_fabric_name = self.serial_number_to_fabric_name.convert(serial_number)
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += f"Error retrieving child fabric name for serial_number {serial_number}. "
            msg += f"Error detail: {error}"
            self.log.debug(msg)
            raise ValueError(msg) from error

        msg = f"serial_number: {serial_number}. "
        msg += f"Returning child_fabric_name: {child_fabric_name}. "
        self.log.debug(msg)

        return child_fabric_name

    def is_border_switch(self, serial_number) -> bool:
        """
        # Summary

        Given a switch serial_number:

        -   Return True if the switch is a border switch
        -   Return False otherwise
        """
        is_border = False
        ip_address = self.serial_number_to_ipv4.convert(serial_number)
        role = self.fabric_inventory[ip_address].get("switchRole", "")
        re_result = re.search(r"\bborder\b", role.lower())
        if re_result:
            is_border = True
        return is_border

    @property
    def diff_attach(self) -> list[dict]:
        """
        Return the diff_attach list, containing dictionaries representing the VRF attachments.
        """
        return self._diff_attach

    @diff_attach.setter
    def diff_attach(self, value: list[dict]):
        self._diff_attach = value

    @property
    def fabric_type(self) -> str:
        """
        Return the fabric_type.
        This should be set before calling commit().

        TODO: remove this property once we use fabric_inventory.fabricTechnology for fabric_type.
        """
        if self._fabric_type is None:
            raise ValueError("Set instance.fabric_type before calling instance.commit.")
        return self._fabric_type

    @fabric_type.setter
    def fabric_type(self, value: str):
        """
        Set the fabric type
        """
        self._fabric_type = value

    @property
    def fabric_inventory(self) -> dict:
        """
        Return the fabric inventory, which maps IP addresses to switch details.
        """
        return self._fabric_inventory

    @fabric_inventory.setter
    def fabric_inventory(self, value: dict):
        """
        Set the fabric map, which maps serial numbers to fabric names.
        Used to determine the child fabric name for multisite fabrics.
        """
        self._fabric_inventory = value

    @property
    def ansible_module(self):
        """
        Return the AnsibleModule instance.
        """
        return self._ansible_module

    @ansible_module.setter
    def ansible_module(self, value):
        """
        Set the AnsibleModule instance.
        """
        self._ansible_module = value

    @property
    def payload_model(self) -> list[PayloadVrfsAttachments]:
        """
        Return the payload as a list of PayloadVrfsAttachments.
        """
        if not self._payload_model:
            msg = f"{self.class_name}: payload_model is not set. Call commit() before accessing payload_model."
            raise ValueError(msg)
        return self._payload_model

    @property
    def payload(self) -> str:
        """
        Return the payload as a JSON string.
        """
        if not self._payload:
            msg = f"{self.class_name}: payload is not set. Call commit() before accessing payload."
            raise ValueError(msg)
        return self._payload

    @property
    def playbook_models(self) -> list[PlaybookVrfModelV12]:
        """
        Return the list of playbook models (list[PlaybookVrfModelV12]).
        This should be set before calling commit().
        """
        return self._playbook_models

    @playbook_models.setter
    def playbook_models(self, value):
        if not isinstance(value, list):
            raise TypeError("playbook_models must be a list of validated playbook configuration models.")
        self._playbook_models = value

    @property
    def sender(self) -> callable:
        """
        Return sender.
        """
        return self._sender

    @sender.setter
    def sender(self, value: callable):
        """
        Set sender.
        """
        self._sender = value
