# -*- coding: utf-8 -*-
import json
from typing import Any, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VrfLiteConnProtoItem(BaseModel):
    asn: str = Field(alias="asn")
    auto_vrf_lite_flag: str = Field(alias="AUTO_VRF_LITE_FLAG")
    dot1q_id: str = Field(alias="DOT1Q_ID")
    enable_border_extension: str = Field(alias="enableBorderExtension")
    if_name: str = Field(alias="IF_NAME")
    ip_mask: str = Field(alias="IP_MASK")
    ipv6_mask: str = Field(alias="IPV6_MASK")
    ipv6_neighbor: str = Field(alias="IPV6_NEIGHBOR")
    mtu: str = Field(alias="MTU")
    neighbor_asn: str = Field(alias="NEIGHBOR_ASN")
    neighbor_ip: str = Field(alias="NEIGHBOR_IP")
    peer_vrf_name: str = Field(alias="PEER_VRF_NAME")
    vrf_lite_jython_template: str = Field(alias="VRF_LITE_JYTHON_TEMPLATE")


class ExtensionPrototypeValue(BaseModel):
    dest_interface_name: str = Field(alias="destInterfaceName")
    dest_switch_name: str = Field(alias="destSwitchName")
    extension_type: str = Field(alias="extensionType")
    extension_values: Union[VrfLiteConnProtoItem, str] = Field(
        default="", alias="extensionValues"
    )
    interface_name: str = Field(alias="interfaceName")

    @field_validator("extension_values", mode="before")
    @classmethod
    def preprocess_extension_values(cls, data: Any) -> Any:
        """
        Convert incoming data

        - If data is a JSON string, use json.loads() to convert to a dict.
        - If data is a dict, convert it to an VrfLiteConnProtoItem instance.
        - If data is already an VrfLiteConnProtoItem instance, return as-is.
        """
        if isinstance(data, str):
            if data == "":
                return ""
            data = json.loads(data)
        if isinstance(data, dict):
            data = VrfLiteConnProtoItem(**data)
        return data


class InstanceValues(BaseModel):
    """
    ```json
    {
        "loopbackId": "",
        "loopbackIpAddress": "",
        "loopbackIpV6Address": "",
        "switchRouteTargetExportEvpn": "5000:100",
        "switchRouteTargetImportEvpn": "5000:100"
    }
    ```
    """

    loopback_id: str = Field(alias="loopbackId")
    loopback_ip_address: str = Field(alias="loopbackIpAddress")
    loopback_ipv6_address: str = Field(alias="loopbackIpV6Address")
    switch_route_target_export_evpn: Optional[str] = Field(
        default="", alias="switchRouteTargetExportEvpn"
    )
    switch_route_target_import_evpn: Optional[str] = Field(
        default="", alias="switchRouteTargetImportEvpn"
    )


class MultisiteConnOuterItem(BaseModel):
    pass


class VrfLiteConnOuterItem(BaseModel):
    auto_vrf_lite_flag: str = Field(alias="AUTO_VRF_LITE_FLAG")
    dot1q_id: str = Field(alias="DOT1Q_ID")
    if_name: str = Field(alias="IF_NAME")
    ip_mask: str = Field(alias="IP_MASK")
    ipv6_mask: str = Field(alias="IPV6_MASK")
    ipv6_neighbor: str = Field(alias="IPV6_NEIGHBOR")
    neighbor_asn: str = Field(alias="NEIGHBOR_ASN")
    neighbor_ip: str = Field(alias="NEIGHBOR_IP")
    peer_vrf_name: str = Field(alias="PEER_VRF_NAME")
    vrf_lite_jython_template: str = Field(alias="VRF_LITE_JYTHON_TEMPLATE")


class MultisiteConnOuter(BaseModel):
    multisite_conn: List[MultisiteConnOuterItem] = Field(alias="MULTISITE_CONN")


class VrfLiteConnOuter(BaseModel):
    vrf_lite_conn: List[VrfLiteConnOuterItem] = Field(alias="VRF_LITE_CONN")


class ExtensionValuesOuter(BaseModel):
    vrf_lite_conn: VrfLiteConnOuter = Field(alias="VRF_LITE_CONN")
    multisite_conn: MultisiteConnOuter = Field(alias="MULTISITE_CONN")

    @field_validator("multisite_conn", mode="before")
    @classmethod
    def preprocess_multisite_conn(cls, data: Any) -> Any:
        """
        Convert incoming data

        - If data is a JSON string, use json.loads() to convert to a dict.
        - If data is a dict, convert it to an MultisiteConnOuter instance.
        - If data is already an MultisiteConnOuter instance, return as-is.
        """
        if isinstance(data, str):
            if data == "":
                return ""
            data = json.loads(data)
        if isinstance(data, dict):
            data = MultisiteConnOuter(**data)
        return data

    @field_validator("vrf_lite_conn", mode="before")
    @classmethod
    def preprocess_vrf_lite_conn(cls, data: Any) -> Any:
        """
        Convert incoming data

        - If data is a JSON string, use json.loads() to convert to a dict.
        - If data is a dict, convert it to an VrfLiteConnOuter instance.
        - If data is already an VrfLiteConnOuter instance, return as-is.
        """
        if isinstance(data, str):
            if data == "":
                return ""
            data = json.loads(data)
        if isinstance(data, dict):
            data = VrfLiteConnOuter(**data)
        return data


class SwitchDetails(BaseModel):
    error_message: Optional[str] = Field(alias="errorMessage")
    extension_prototype_values: Union[List[ExtensionPrototypeValue], str] = Field(
        default="", alias="extensionPrototypeValues"
    )
    extension_values: Union[ExtensionValuesOuter, str] = Field(
        default="", alias="extensionValues"
    )
    freeform_config: str = Field(alias="freeformConfig")
    instance_values: Optional[Union[InstanceValues, str]] = Field(
        default="", alias="instanceValues"
    )
    is_lan_attached: bool = Field(alias="islanAttached")
    lan_attached_state: str = Field(alias="lanAttachedState")
    peer_serial_number: Optional[str] = Field(alias="peerSerialNumber")
    role: str
    serial_number: str = Field(alias="serialNumber")
    switch_name: str = Field(alias="switchName")
    vlan: int = Field(alias="vlan", ge=2, le=4094)
    vlan_modifiable: bool = Field(alias="vlanModifiable")

    @field_validator("extension_prototype_values", mode="before")
    @classmethod
    def preprocess_extension_prototype_values(cls, data: Any) -> Any:
        """
        Convert incoming data

        - If data is a JSON string, use json.loads() to convert to a dict.
        - If data is a list, convert it to a list of ExtensionPrototypeValue instance.
        - If data is already an ExtensionPrototypeValue model, return as-is.
        """
        if isinstance(data, str):
            if data == "":
                return ""
            data = json.loads(data)
        if isinstance(data, list):
            for instance in data:
                if isinstance(instance, dict):
                    instance = ExtensionPrototypeValue(**instance)
        return data

    @field_validator("extension_values", mode="before")
    @classmethod
    def preprocess_extension_values(cls, data: Any) -> Any:
        """
        Convert incoming data

        - If data is a JSON string, use json.loads() to convert to a dict.
        - If data is a dict, convert it to an ExtensionValuesOuter instance.
        - If data is already an ExtensionValuesOuter instance, return as-is.
        """
        if isinstance(data, str):
            if data == "":
                return ""
            data = json.loads(data)
        if isinstance(data, dict):
            data = ExtensionValuesOuter(**data)
        return data

    @field_validator("instance_values", mode="before")
    @classmethod
    def preprocess_instance_values(cls, data: Any) -> Any:
        """
        Convert incoming data

        - If data is a JSON string, use json.loads() to convert to a dict.
        - If data is a dict, convert it to an InstanceValues instance.
        - If data is already an InstanceValues instance, return as-is.
        """
        if isinstance(data, str):
            if data == "":
                return ""
            data = json.loads(data)
        if isinstance(data, dict):
            data = InstanceValues(**data)
        return data


class DataItem(BaseModel):
    switch_details_list: List[SwitchDetails] = Field(alias="switchDetailsList")
    template_name: str = Field(alias="templateName")
    vrf_name: str = Field(alias="vrfName")


class ControllerResponseVrfsSwitchesV12(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True,
        validate_assignment=True,
        validate_by_alias=True,
        validate_by_name=True,
    )

    data: List[DataItem] = Field(alias="DATA")
    message: str = Field(alias="MESSAGE")
    method: str = Field(alias="METHOD")
    return_code: int = Field(alias="RETURN_CODE")
