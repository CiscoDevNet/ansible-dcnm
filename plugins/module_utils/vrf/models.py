#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
"""
# Summary

Serialization/Deserialization functions for LanAttachment and InstanceValues objects.
"""
import json
from ast import literal_eval
from dataclasses import asdict, dataclass, field


def to_lan_attachment(obj):
    """
    Convert a dictionary to a LanAttachment object.
    """
    if obj.get("vlan"):
        obj["vlan"] = VlanId(obj["vlan"])
    if obj.get("instanceValues"):
        obj["instanceValues"] = InstanceValues(**obj["instanceValues"])
    return LanAttachment(**obj)


def literal_eval_dict(data):
    """
    Safely evaluate a string containing a Python literal or container display.
    """
    try:
        return literal_eval(data)
    except (ValueError, SyntaxError) as error:
        msg = f"Invalid literal for evaluation: {data}"
        msg += f"error detail: {error}."
        raise ValueError(msg) from error


def serialize_lan_attachment(data):
    """
    Serialize the LanAttachment object to a dictionary.
    """
    if isinstance(data, LanAttachment):
        return data.dict()
    raise ValueError("Expected a LanAttachment object")


def deserialize_lan_attachment(data):
    """
    Deserialize a dictionary to a LanAttachment object.
    """
    if isinstance(data, dict):
        instance_values = InstanceValues(**data.pop("instanceValues"))
        return LanAttachment(instanceValues=instance_values, **data)
    raise ValueError("Expected a dictionary")


def deserialize_instance_values(data):
    """
    Deserialize a dictionary to an InstanceValues object.
    """
    if isinstance(data, dict):
        return InstanceValues(**data)
    raise ValueError("Expected a dictionary")


def serialize_instance_values(data):
    """
    Serialize the InstanceValues object to a dictionary.
    """
    if isinstance(data, InstanceValues):
        return data.dict()
    raise ValueError("Expected an InstanceValues object")


def serialize_dict(data):
    """
    Serialize a dictionary to a JSON string.
    """
    if isinstance(data, dict):
        return json.dumps(data)
    raise ValueError("Expected a dictionary")


def deserialize_dict(data):
    """
    Deserialize a JSON string to a dictionary.
    """
    if isinstance(data, str):
        return json.loads(data)
    raise ValueError("Expected a JSON string")


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
class InstanceValues:
    """
    # Summary

    Instance values for the LanAttachment object.

    ## Keys

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
    instance_values = InstanceValues(
        loopbackId="",
        loopbackIpAddress="",
        loopbackIpV6Address="",
        switchRouteTargetImportEvpn="",
        switchRouteTargetExportEvpn=""
    )

    print(instance_values.dumps())
    print(instance_values.dict())
    ```
    """

    loopbackId: str
    loopbackIpAddress: str
    loopbackIpV6Address: str
    switchRouteTargetImportEvpn: str
    switchRouteTargetExportEvpn: str

    def to_str(self):
        """
        # Summary

        Serialize to a JSON string.
        """
        return serialize_dict(self.__dict__)

    def to_dict(self):
        """
        # Summary

        Serialize to a dictionary.
        """
        return asdict(self)


@dataclass
class LanAttachment:
    """
    # Summary

    LanAttach object.

    ## Keys

    -   `deployment`, bool
    -   `export_evpn_rt`, str
    -   `extensionValues`, str
    -   `fabric`, str
    -   `freeformConfig`, str
    -   `import_evpn_rt`, str
    -   `instanceValues`, InstanceValues
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
        instanceValues=InstanceValues(
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
    instanceValues: InstanceValues
    serialNumber: str
    vrfName: str
    vlan: VlanId = field(default_factory=lambda: VlanId(0))

    def to_dict(self):
        """
        # Summary

        Serialize the object to a dictionary.
        """
        instance_values_dict = self.instanceValues.to_dict()
        as_dict = asdict(self)
        as_dict["instanceValues"] = instance_values_dict
        as_dict["vlan"] = self.vlan.vlanId
        return as_dict

    def to_str(self):
        """
        # Summary

        Serialize the object to a JSON string.
        """
        instance_values = self.instanceValues.to_str()
        return json.dumps(
            {
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
        )

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
        if not isinstance(self.instanceValues, InstanceValues):
            raise ValueError("instanceValues must be of type InstanceValues")
        if not isinstance(self.serialNumber, str):
            raise ValueError("serialNumber must be a string")
        if not isinstance(self.vlan, VlanId):
            raise ValueError("vlan must be of type VlanId")
        if not isinstance(self.vrfName, str):
            raise ValueError("vrfName must be a string")
