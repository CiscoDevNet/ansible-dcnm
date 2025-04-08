#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
"""
# Summary

Serialization/Deserialization functions for LanAttachment and InstanceValuesInternal objects.
"""
import json
from ast import literal_eval
from dataclasses import asdict, dataclass, field


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
        return json.dumps(self.__dict__)

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
        return InstanceValuesInternal(
            loopbackIpV6Address=instance_values["loopbackIpV6Address"],
            loopbackId=instance_values["loopbackId"],
            deviceSupportL3VniNoVlan=instance_values["deviceSupportL3VniNoVlan"],
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
        return json.dumps(json.dumps(self.__dict__))

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

    # pylint: disable=too-many-instance-attributes
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
