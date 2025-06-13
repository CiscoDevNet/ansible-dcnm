# -*- coding: utf-8 -*-
"""
Validation model for controller responses related to the following endpoint:

Path: /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs/switches?vrf-names=ansible-vrf-int1&serial-numbers={serial1,serial2}
Verb: GET
"""
import json
from typing import Any, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .model_controller_response_generic_v12 import ControllerResponseGenericV12


class ControllerResponseVrfsSwitchesVrfLiteConnProtoItem(BaseModel):
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


class ControllerResponseVrfsSwitchesExtensionPrototypeValue(BaseModel):
    dest_interface_name: str = Field(alias="destInterfaceName")
    dest_switch_name: str = Field(alias="destSwitchName")
    extension_type: str = Field(alias="extensionType")
    extension_values: Union[ControllerResponseVrfsSwitchesVrfLiteConnProtoItem, str] = Field(default="", alias="extensionValues")
    interface_name: str = Field(alias="interfaceName")

    @field_validator("extension_values", mode="before")
    @classmethod
    def preprocess_extension_values(cls, data: Any) -> Any:
        """
        Convert incoming data

        - If data is a JSON string, use json.loads() to convert to a dict.
        - If data is a dict, convert it to an ControllerResponseVrfsSwitchesVrfLiteConnProtoItem instance.
        - If data is already an ControllerResponseVrfsSwitchesVrfLiteConnProtoItem instance, return as-is.
        """
        if isinstance(data, str):
            if data == "":
                return ""
            data = json.loads(data)
        if isinstance(data, dict):
            data = ControllerResponseVrfsSwitchesVrfLiteConnProtoItem(**data)
        return data


class ControllerResponseVrfsSwitchesInstanceValues(BaseModel):
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
    switch_route_target_export_evpn: Optional[str] = Field(default="", alias="switchRouteTargetExportEvpn")
    switch_route_target_import_evpn: Optional[str] = Field(default="", alias="switchRouteTargetImportEvpn")


class ControllerResponseVrfsSwitchesMultisiteConnOuterItem(BaseModel):
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


class ControllerResponseVrfsSwitchesMultisiteConnOuter(BaseModel):
    multisite_conn: List[ControllerResponseVrfsSwitchesMultisiteConnOuterItem] = Field(alias="MULTISITE_CONN")


class ControllerResponseVrfsSwitchesVrfLiteConnOuter(BaseModel):
    vrf_lite_conn: List[VrfLiteConnOuterItem] = Field(alias="VRF_LITE_CONN")


class ControllerResponseVrfsSwitchesExtensionValuesOuter(BaseModel):
    vrf_lite_conn: ControllerResponseVrfsSwitchesVrfLiteConnOuter = Field(alias="VRF_LITE_CONN")
    multisite_conn: ControllerResponseVrfsSwitchesMultisiteConnOuter = Field(alias="MULTISITE_CONN")

    @field_validator("multisite_conn", mode="before")
    @classmethod
    def preprocess_multisite_conn(cls, data: Any) -> Any:
        """
        Convert incoming data

        - If data is a JSON string, use json.loads() to convert to a dict.
        - If data is a dict, convert it to an ControllerResponseVrfsSwitchesMultisiteConnOuter instance.
        - If data is already an ControllerResponseVrfsSwitchesMultisiteConnOuter instance, return as-is.
        """
        if isinstance(data, str):
            if data == "":
                return ""
            data = json.loads(data)
        if isinstance(data, dict):
            data = ControllerResponseVrfsSwitchesMultisiteConnOuter(**data)
        return data

    @field_validator("vrf_lite_conn", mode="before")
    @classmethod
    def preprocess_vrf_lite_conn(cls, data: Any) -> Any:
        """
        Convert incoming data

        - If data is a JSON string, use json.loads() to convert to a dict.
        - If data is a dict, convert it to an ControllerResponseVrfsSwitchesVrfLiteConnOuter instance.
        - If data is already an ControllerResponseVrfsSwitchesVrfLiteConnOuter instance, return as-is.
        """
        if isinstance(data, str):
            if data == "":
                return ""
            data = json.loads(data)
        if isinstance(data, dict):
            data = ControllerResponseVrfsSwitchesVrfLiteConnOuter(**data)
        return data


class ControllerResponseVrfsSwitchesSwitchDetails(BaseModel):
    error_message: Union[str, None] = Field(alias="errorMessage")
    extension_prototype_values: Union[List[ControllerResponseVrfsSwitchesExtensionPrototypeValue], str] = Field(default="", alias="extensionPrototypeValues")
    extension_values: Union[ControllerResponseVrfsSwitchesExtensionValuesOuter, str, None] = Field(default="", alias="extensionValues")
    freeform_config: Union[str, None] = Field(alias="freeformConfig")
    instance_values: Optional[Union[ControllerResponseVrfsSwitchesInstanceValues, str, None]] = Field(default="", alias="instanceValues")
    is_lan_attached: bool = Field(alias="islanAttached")
    lan_attached_state: str = Field(alias="lanAttachedState")
    peer_serial_number: Union[str, None] = Field(alias="peerSerialNumber")
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
        - If data is a list, convert it to a list of ControllerResponseVrfsSwitchesExtensionPrototypeValue instance.
        - If data is already an ControllerResponseVrfsSwitchesExtensionPrototypeValue model, return as-is.
        """
        if isinstance(data, str):
            if data == "":
                return ""
            data = json.loads(data)
        if isinstance(data, list):
            for instance in data:
                if isinstance(instance, dict):
                    instance = ControllerResponseVrfsSwitchesExtensionPrototypeValue(**instance)
        return data

    @field_validator("extension_values", mode="before")
    @classmethod
    def preprocess_extension_values(cls, data: Any) -> Any:
        """
        Convert incoming data

        - If data is a JSON string, use json.loads() to convert to a dict.
        - If data is a dict, convert it to an ControllerResponseVrfsSwitchesExtensionValuesOuter instance.
        - If data is already an ControllerResponseVrfsSwitchesExtensionValuesOuter instance, return as-is.
        """
        if isinstance(data, str):
            if data == "":
                return ""
            data = json.loads(data)
        if isinstance(data, dict):
            data = ControllerResponseVrfsSwitchesExtensionValuesOuter(**data)
        return data

    @field_validator("instance_values", mode="before")
    @classmethod
    def preprocess_instance_values(cls, data: Any) -> Any:
        """
        Convert incoming data

        - If data is a JSON string, use json.loads() to convert to a dict.
        - If data is a dict, convert it to an ControllerResponseVrfsSwitchesInstanceValues instance.
        - If data is already an ControllerResponseVrfsSwitchesInstanceValues instance, return as-is.
        """
        if isinstance(data, str):
            if data == "":
                return ""
            data = json.loads(data)
        if isinstance(data, dict):
            data = ControllerResponseVrfsSwitchesInstanceValues(**data)
        return data


class ControllerResponseVrfsSwitchesDataItem(BaseModel):
    switch_details_list: List[ControllerResponseVrfsSwitchesSwitchDetails] = Field(alias="switchDetailsList")
    template_name: str = Field(alias="templateName")
    vrf_name: str = Field(alias="vrfName")


class ControllerResponseVrfsSwitchesV12(ControllerResponseGenericV12):
    """
    # Summary
    Validation model for the controller response to the following endpoint:
    Verb: POST

    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    DATA: List[ControllerResponseVrfsSwitchesDataItem]
    MESSAGE: str
    METHOD: str
    REQUEST_PATH: str
    RETURN_CODE: int
