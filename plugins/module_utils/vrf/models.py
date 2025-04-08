#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
# pylint: disable=line-too-long
# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-branches
"""
# Summary

Serialization/Deserialization functions for LanAttachment and InstanceValuesInternal objects.
"""
import json
from ast import literal_eval
from dataclasses import asdict, dataclass, field
from typing import Union


def to_lan_attachment_internal(obj):
    """
    Convert a dictionary to a LanAttachmentInternal object.
    """
    if obj.get("vlan"):
        obj["vlan"] = VlanId(obj["vlan"])
    if obj.get("instanceValues"):
        obj["instanceValues"] = InstanceValuesInternal(**obj["instanceValues"])
    return LanAttachmentInternal(**obj)


@dataclass
class VlanId:
    """
    # Summary

    VlanId object for network configuration.

    ## Keys

    -   `vlanId`, int

    ## Methods

    -   `dict` : Serialize the object to a dictionary.
    -   `dumps` : Serialize the object to a JSON string.

    ## Example

    ```python
    vlan_id = VlanId(vlanId=0)
    ```
    """

    vlanId: int

    def __post_init__(self):
        """
        # Summary

        Validate the attributes of the VlanId object.
        """
        if not isinstance(self.vlanId, int):
            raise ValueError("vlanId must be an integer")
        if self.vlanId < 0:
            raise ValueError("vlanId must be a positive integer")
        if self.vlanId > 4095:
            raise ValueError("vlanId must be less than or equal to 4095")


@dataclass
class InstanceValuesController:
    """
    # Summary

    Instance values for LanAttachmentController, in controller format.

    ## Keys

    -   `instanceValues`, str

    ## Methods

    -   `as_internal` : Serialize to internal format.

    ## Controller format

    The instanceValues field, as received by the controller, is a JSON string.

    ```json
    {
        "deployment": true,
        "entityName": "ansible-vrf-int2",
        "extensionValues": "",
        "fabric": "f1",
        "instanceValues": "{\"loopbackIpV6Address\":\"\",\"loopbackId\":\"\",\"deviceSupportL3VniNoVlan\":\"false\",\"switchRouteTargetImportEvpn\":\"\",\"loopbackIpAddress\":\"\",\"switchRouteTargetExportEvpn\":\"\"}",
        "isAttached": true,
        "is_deploy": true,
        "peerSerialNo": null,
        "serialNumber": "FOX2109PGD0",
        "vlan": 500,
        "vrfName": "ansible-vrf-int2"
    }
    ```

    ## Example

    ```python
    instance_values_controller = InstanceValuesController(
        instanceValues="{\"loopbackIpV6Address\":\"\",\"loopbackId\":\"\",\"deviceSupportL3VniNoVlan\":\"false\",\"switchRouteTargetImportEvpn\":\"\",\"loopbackIpAddress\":\"\",\"switchRouteTargetExportEvpn\":\"\"}"
    )

    print(instance_values.to_internal())
    ```
    """

    instanceValues: str

    def as_controller(self):
        """
        # Summary

        Serialize to controller format.
        """
        return json.dumps(self.__dict__["instanceValues"])

    def as_internal(self):
        """
        # Summary

        Serialize to internal format.
        """
        try:
            instance_values = literal_eval(self.instanceValues)
        except ValueError as error:
            msg = f"Invalid literal for evaluation: {self.instanceValues}"
            msg += f"error detail: {error}."
            raise ValueError(msg) from error

        if not isinstance(instance_values, dict):
            raise ValueError("Expected a dictionary")
        if "deviceSupportL3VniNoVlan" not in instance_values:
            raise ValueError("deviceSupportL3VniNoVlan is missing")
        if "loopbackId" not in instance_values:
            raise ValueError("loopbackId is missing")
        if "loopbackIpAddress" not in instance_values:
            raise ValueError("loopbackIpAddress is missing")
        if "loopbackIpV6Address" not in instance_values:
            raise ValueError("loopbackIpV6Address is missing")
        if "switchRouteTargetExportEvpn" not in instance_values:
            raise ValueError("switchRouteTargetExportEvpn is missing")
        if "switchRouteTargetImportEvpn" not in instance_values:
            raise ValueError("switchRouteTargetImportEvpn is missing")
        if instance_values["deviceSupportL3VniNoVlan"] in ["true", "True", True]:
            deviceSupportL3VniNoVlan = True
        elif instance_values["deviceSupportL3VniNoVlan"] in ["false", "False", False]:
            deviceSupportL3VniNoVlan = False
        else:
            raise ValueError("deviceSupportL3VniNoVlan must be a boolean")
        return InstanceValuesInternal(
            deviceSupportL3VniNoVlan=deviceSupportL3VniNoVlan,
            loopbackIpV6Address=instance_values["loopbackIpV6Address"],
            loopbackId=instance_values["loopbackId"],
            switchRouteTargetImportEvpn=instance_values["switchRouteTargetImportEvpn"],
            loopbackIpAddress=instance_values["loopbackIpAddress"],
            switchRouteTargetExportEvpn=instance_values["switchRouteTargetExportEvpn"],
        )


@dataclass
class InstanceValuesInternal:
    """
    # Summary

    Internal representation of the instanceValues field of the LanAttachment* objects.

    ## Keys

    -   `deviceSupportL3VniNoVlan`, bool
    -   `loopbackId`, str
    -   `loopbackIpAddress`, str
    -   `loopbackIpV6Address`, str
    -   `switchRouteTargetImportEvpn`, str
    -   `switchRouteTargetExportEvpn`, str

    ## Methods

    -   `dumps` : Serialize the object to a JSON string.
    -   `dict` : Serialize the object to a dictionary.

    ## Example

    ```python
    instance_values_internal = InstanceValuesInternal(
        deviceSupportL3VniNoVlan=False,
        loopbackId="",
        loopbackIpAddress="",
        loopbackIpV6Address="",
        switchRouteTargetImportEvpn="",
        switchRouteTargetExportEvpn=""
    )

    print(instance_values_internal.as_controller())
    print(instance_values_internal.as_internal())
    ```
    """

    loopbackId: str
    loopbackIpAddress: str
    loopbackIpV6Address: str
    switchRouteTargetImportEvpn: str
    switchRouteTargetExportEvpn: str
    deviceSupportL3VniNoVlan: bool = field(default=False)

    def as_controller(self):
        """
        # Summary

        Serialize to controller format.
        """
        return InstanceValuesController(
            instanceValues=json.dumps(self.__dict__, default=str)
        )
        # return json.dumps(json.dumps(self.__dict__))

    def as_internal(self):
        """
        # Summary

        Serialize to internal format.
        """
        return asdict(self)


@dataclass
class LanAttachmentInternal:
    """
    # Summary

    LanAttach object, internal format.

    ## Keys

    -   `deployment`, bool
    -   `export_evpn_rt`, str
    -   `extensionValues`, str
    -   `fabric`, str
    -   `freeformConfig`, str
    -   `import_evpn_rt`, str
    -   `instanceValues`, InstanceValuesInternal
    -   `serialNumber`, str
    -   `vlan`, int
    -   `vrfName`, str

    ## Methods

    -   `dict` : Serialize the object to a dictionary.
    -   `dumps` : Serialize the object to a JSON string.

    ## Example

    ```python
    lan_attachment = LanAttachment(
        deployment=True,
        export_evpn_rt="",
        extensionValues="",
        fabric="f1",
        freeformConfig="",
        import_evpn_rt="",
        instanceValues=InstanceValuesInternal(
            loopbackId="",
            loopbackIpAddress="",
            loopbackIpV6Address="",
            switchRouteTargetImportEvpn="",
            switchRouteTargetExportEvpn=""
        ),
        serialNumber="FOX2109PGCS",
        vlan=0,
        vrfName="ansible-vrf-int1"
    )

    print(lan_attachment.dumps())
    print(lan_attachment.dict())
    ```
    """

    deployment: bool
    export_evpn_rt: str
    extensionValues: str
    fabric: str
    freeformConfig: str
    import_evpn_rt: str
    instanceValues: InstanceValuesInternal
    serialNumber: str
    vrfName: str
    vlan: VlanId = field(default_factory=lambda: VlanId(0))

    def as_controller(self):
        """
        # Summary

        Serialize the object to controller format.
        """
        instance_values = self.instanceValues.as_controller()
        return {
            "deployment": self.deployment,
            "export_evpn_rt": self.export_evpn_rt,
            "extensionValues": self.extensionValues,
            "fabric": self.fabric,
            "freeformConfig": self.freeformConfig,
            "import_evpn_rt": self.import_evpn_rt,
            "instanceValues": instance_values,
            "serialNumber": self.serialNumber,
            "vlan": self.vlan.vlanId,
            "vrfName": self.vrfName,
        }

    def as_internal(self):
        """
        # Summary

        Serialize the object to internal format.
        """
        instance_values_internal = self.instanceValues.as_internal()
        as_dict = asdict(self)
        as_dict["instanceValues"] = instance_values_internal
        as_dict["vlan"] = self.vlan.vlanId
        return as_dict

    def __post_init__(self):
        """
        # Summary

        Validate the attributes of the LanAttachment object.
        """
        if not isinstance(self.deployment, bool):
            raise ValueError("deployment must be a boolean")
        if not isinstance(self.export_evpn_rt, str):
            raise ValueError("export_evpn_rt must be a string")
        if not isinstance(self.extensionValues, str):
            raise ValueError("extensionValues must be a string")
        if not isinstance(self.fabric, str):
            raise ValueError("fabric must be a string")
        if not isinstance(self.freeformConfig, str):
            raise ValueError("freeformConfig must be a string")
        if not isinstance(self.import_evpn_rt, str):
            raise ValueError("import_evpn_rt must be a string")
        if not isinstance(self.instanceValues, InstanceValuesInternal):
            raise ValueError("instanceValues must be of type InstanceValuesInternal")
        if not isinstance(self.serialNumber, str):
            raise ValueError("serialNumber must be a string")
        if not isinstance(self.vlan, VlanId):
            raise ValueError("vlan must be of type VlanId")
        if not isinstance(self.vrfName, str):
            raise ValueError("vrfName must be a string")


@dataclass
class LanAttachmentController:
    """
    # Summary

    LanAttachment object, controller format.

    This class accepts a lanAttachment object as received from the controller.

    ## Controller format

    ```json
    {
        "entityName": "ansible-vrf-int1",
        "fabricName": "f1",
        "instanceValues": "{\"loopbackId\": \"\", \"loopbackIpAddress\": \"\", \"loopbackIpV6Address\": \"\", \"switchRouteTargetImportEvpn\": \"\", \"switchRouteTargetExportEvpn\": \"\", \"deviceSupportL3VniNoVlan\": false}",
        "ipAddress": "172.22.150.113",
        "isLanAttached": true,
        "lanAttachState": "DEPLOYED",
        "peerSerialNo": null,
        "switchName": "cvd-1212-spine",
        "switchRole": "border spine",
        "switchSerialNo": "FOX2109PGD0",
        "vlanId": 500,
        "vrfId": 9008011,
        "vrfName": "ansible-vrf-int1",
    }
    ```

    ## Keys

    - entityName: str
    - fabricName: str
    - instanceValues: str
    - ipAddress: str
    - isLanAttached: bool
    - lanAttachState: str
    - perSerialNo: str
    - switchName: str
    - switchRole: str
    - switchSerialNo: str
    - vlanId: int
    - vrfId: int
    - vrfName: str

    ## Methods

    -   `as_controller` : Serialize to controller format.
    -   `as_internal` : Serialize to internal format.

    ## Example

    Assume a hypothetical function that returns the controller response
    to the following endpoint:

    /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabricName}/vrfs/attachments?vrf-names={vrfName}

    ```python
    vrf_response = get_vrf_attachments(**args)

    # Extract the first lanAttachment object from the response

    attachment_object: dict = vrf_response.json()[0]["lanAttachList"][0]

    # Feed the lanAttachment object to the LanAttachmentController class
    # to create a LanAttachmentController instance

    lan_attachment_controller = LanAttachmentController(**attachment_object)

    # Now you can use the instance to serialize the controller response
    # into either internal format or controller format

    print(lan_attachment_controller.as_controller())
    print(lan_attachment_controller.as_internal())

    # You can also populate the object with your own values

    lan_attachment_controller = LanAttachmentController(
        entityName="myVrf",
        fabricName="f1",
        instanceValues="{\"loopbackId\": \"\", \"loopbackIpAddress\": \"\", \"loopbackIpV6Address\": \"\", \"switchRouteTargetImportEvpn\": \"\", \"switchRouteTargetExportEvpn\": \"\", \"deviceSupportL3VniNoVlan\": false}",
        ipAddress="10.1.1.1",
        isLanAttached=True,
        lanAttachState="DEPLOYED",
        peerSerialNo=None,
        switchName="switch1",
        switchRole="border spine",
        switchSerialNo="FOX2109PGD0",
        vlanId=500,
        vrfId=1,
        vrfName="ansible-vrf-int2"
    )

    print(lan_attachment_controller.as_controller())
    print(lan_attachment_controller.as_internal())
    ```
    """

    entityName: str
    fabricName: str
    instanceValues: str
    ipAddress: str
    isLanAttached: bool
    lanAttachState: str
    peerSerialNo: str
    switchName: str
    switchRole: str
    switchSerialNo: str
    vlanId: int
    vrfId: int
    vrfName: str

    def as_controller(self):
        """
        # Summary
        Serialize the object to controller format.
        """
        return asdict(self)

    def as_internal(self):
        """
        # Summary

        Serialize the object to internal format.
        """
        try:
            instance_values = literal_eval(self.instanceValues)
        except ValueError as error:
            msg = f"Invalid literal for evaluation: {self.instanceValues}"
            msg += f"error detail: {error}."
            raise ValueError(msg) from error
        instance_values_internal = InstanceValuesInternal(**instance_values)
        internal = asdict(self)
        internal["instanceValues"] = instance_values_internal
        internal["vlan"] = VlanId(self.vlanId)
        return internal

    def __post_init__(self):
        """
        # Summary
        Validate the attributes of the LanAttachment object.
        """

        if not isinstance(self.entityName, str):
            raise ValueError("entityName must be a string")
        if not isinstance(self.fabricName, str):
            raise ValueError("fabricName must be a string")
        if not isinstance(self.instanceValues, str):
            raise ValueError("instanceValues must be a string")
        if not isinstance(self.ipAddress, str):
            raise ValueError("ipAddress must be a string")
        if not isinstance(self.isLanAttached, bool):
            raise ValueError("isLanAttached must be a boolean")
        if not isinstance(self.lanAttachState, str):
            raise ValueError("lanAttachState must be a string")
        if not isinstance(self.peerSerialNo, Union[str, None]):
            raise ValueError("peerSerialNo must be a string or None")
        if not isinstance(self.switchName, str):
            raise ValueError("switchName must be a string")
        if not isinstance(self.switchRole, str):
            raise ValueError("switchRole must be a string")
        if not isinstance(self.switchSerialNo, str):
            raise ValueError("switchSerialNo must be a string")
        if not isinstance(self.vlanId, int):
            raise ValueError("vlanId must be an integer")
        if not isinstance(self.vrfId, int):
            raise ValueError("vrfId must be an integer")
        if not isinstance(self.vrfName, str):
            raise ValueError("vrfName must be a string")

        if self.vlanId < 0:
            raise ValueError("vlanId must be a positive integer")
        if self.vlanId > 4095:
            raise ValueError("vlanId must be less than or equal to 4095")
        if self.vrfId < 0:
            raise ValueError("vrfId must be a positive integer")
        if self.vrfId > 9483873372:
            raise ValueError("vrfId must be less than or equal to 9483873372")
