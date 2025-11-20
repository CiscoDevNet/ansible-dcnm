# -*- coding: utf-8 -*-
"""
Validation model for controller responses related to the following endpoint:

Path: /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs/switches?vrf-names=ansible-vrf-int1&serial-numbers={serial1,serial2}
Verb: GET
"""
import json
import traceback
from typing import Any, List, Optional, Union

try:
    from pydantic import BaseModel, ConfigDict, Field, field_validator

    HAS_PYDANTIC = True
    PYDANTIC_IMPORT_ERROR = None
except ImportError:
    HAS_PYDANTIC = False
    PYDANTIC_IMPORT_ERROR = traceback.format_exc()

    # Fallback: object base class
    BaseModel = object  # type: ignore[assignment]

    # Fallback: Field that does nothing
    def Field(*args, **kwargs):  # type: ignore[no-redef] # pylint: disable=unused-argument,invalid-name
        """Pydantic Field fallback when pydantic is not available."""
        return None

    # Fallback: ConfigDict that does nothing
    def ConfigDict(**kwargs):  # type: ignore[no-redef] # pylint: disable=unused-argument,invalid-name
        """Pydantic ConfigDict fallback when pydantic is not available."""
        return {}

    # Fallback: field_validator decorator that does nothing
    def field_validator(*args, **kwargs):  # type: ignore[no-redef] # pylint: disable=unused-argument,invalid-name
        """Pydantic field_validator fallback when pydantic is not available."""

        def decorator(func):
            return func

        return decorator


from .model_controller_response_generic_v12 import ControllerResponseGenericV12


class ControllerResponseVrfsSwitchesVrfLiteConnProtoItem(BaseModel):
    asn: Optional[str] = Field(default="", alias="asn")
    auto_vrf_lite_flag: Optional[str] = Field(default="", alias="AUTO_VRF_LITE_FLAG")
    dot1q_id: Optional[str] = Field(default="", alias="DOT1Q_ID")
    enable_border_extension: Optional[str] = Field(default="", alias="enableBorderExtension")
    if_name: Optional[str] = Field(default="", alias="IF_NAME")
    ip_mask: Optional[str] = Field(default="", alias="IP_MASK")
    ipv6_mask: Optional[str] = Field(default="", alias="IPV6_MASK")
    ipv6_neighbor: Optional[str] = Field(default="", alias="IPV6_NEIGHBOR")
    mtu: Optional[str] = Field(default="", alias="MTU")
    neighbor_asn: Optional[str] = Field(default="", alias="NEIGHBOR_ASN")
    neighbor_ip: Optional[str] = Field(default="", alias="NEIGHBOR_IP")
    peer_vrf_name: Optional[str] = Field(default="", alias="PEER_VRF_NAME")
    vrf_lite_jython_template: Optional[str] = Field(default="", alias="VRF_LITE_JYTHON_TEMPLATE")

    @classmethod
    def model_construct(cls, *args, **kwargs):  # pylint: disable=signature-differs
        """For ansible-sanity import tests. Construct model instance, with fallback for when pydantic is not available."""
        if HAS_PYDANTIC:
            return super().model_construct(*args, **kwargs)
        # Fallback: return self when pydantic is not available
        return cls()


class ControllerResponseVrfsSwitchesExtensionPrototypeValue(BaseModel):
    dest_interface_name: Optional[str] = Field(default="", alias="destInterfaceName")
    dest_switch_name: Optional[str] = Field(default="", alias="destSwitchName")
    extension_type: Optional[str] = Field(default="", alias="extensionType")
    extension_values: ControllerResponseVrfsSwitchesVrfLiteConnProtoItem = Field(
        default=ControllerResponseVrfsSwitchesVrfLiteConnProtoItem().model_construct(), alias="extensionValues"
    )
    interface_name: Optional[str] = Field(default="", alias="interfaceName")

    @field_validator("extension_values", mode="before")
    @classmethod
    def preprocess_extension_values(cls, data: Any) -> ControllerResponseVrfsSwitchesVrfLiteConnProtoItem:
        """
        Convert incoming data

        - If data is a JSON string, use json.loads() to convert to a dict.
        - If data is a dict, convert it to an ControllerResponseVrfsSwitchesVrfLiteConnProtoItem instance.
        - If data is already an ControllerResponseVrfsSwitchesVrfLiteConnProtoItem instance, return as-is.
        """
        if isinstance(data, str):
            if data == "":
                return ControllerResponseVrfsSwitchesVrfLiteConnProtoItem().model_construct()
            data = json.loads(data)
            return ControllerResponseVrfsSwitchesVrfLiteConnProtoItem(**data)
        if isinstance(data, dict):
            data = ControllerResponseVrfsSwitchesVrfLiteConnProtoItem(**data)
        return data

    @classmethod
    def model_construct(cls, *args, **kwargs):  # pylint: disable=signature-differs
        """For ansible-sanity import tests. Construct model instance, with fallback for when pydantic is not available."""
        if HAS_PYDANTIC:
            return super().model_construct(*args, **kwargs)
        # Fallback: return self when pydantic is not available
        return cls()


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

    loopback_id: Optional[str] = Field(default="", alias="loopbackId")
    loopback_ip_address: Optional[str] = Field(default="", alias="loopbackIpAddress")
    loopback_ipv6_address: Optional[str] = Field(default="", alias="loopbackIpV6Address")
    switch_route_target_export_evpn: Optional[str] = Field(default="", alias="switchRouteTargetExportEvpn")
    switch_route_target_import_evpn: Optional[str] = Field(default="", alias="switchRouteTargetImportEvpn")

    @classmethod
    def model_construct(cls, *args, **kwargs):  # pylint: disable=signature-differs
        """For ansible-sanity import tests. Construct model instance, with fallback for when pydantic is not available."""
        if HAS_PYDANTIC:
            return super().model_construct(*args, **kwargs)
        # Fallback: return self when pydantic is not available
        return cls()


class ControllerResponseVrfsSwitchesMultisiteConnOuterItem(BaseModel):
    @classmethod
    def model_construct(cls, *args, **kwargs):  # pylint: disable=signature-differs
        """For ansible-sanity import tests. Construct model instance, with fallback for when pydantic is not available."""
        if HAS_PYDANTIC:
            return super().model_construct(*args, **kwargs)
        # Fallback: return self when pydantic is not available
        return cls()


class VrfLiteConnOuterItem(BaseModel):
    # We set the default value to "NA", which we can check later in dcnm_vrf_v12.py
    # to ascertain whether the model was populated with switch data.
    auto_vrf_lite_flag: Optional[str] = Field(default="NA", alias="AUTO_VRF_LITE_FLAG")
    dot1q_id: Optional[str] = Field(default="", alias="DOT1Q_ID")
    if_name: Optional[str] = Field(default="", alias="IF_NAME")
    ip_mask: Optional[str] = Field(default="", alias="IP_MASK")
    ipv6_mask: Optional[str] = Field(default="", alias="IPV6_MASK")
    ipv6_neighbor: Optional[str] = Field(default="", alias="IPV6_NEIGHBOR")
    neighbor_asn: Optional[str] = Field(default="", alias="NEIGHBOR_ASN")
    neighbor_ip: Optional[str] = Field(default="", alias="NEIGHBOR_IP")
    peer_vrf_name: Optional[str] = Field(default="", alias="PEER_VRF_NAME")
    vrf_lite_jython_template: Optional[str] = Field(default="", alias="VRF_LITE_JYTHON_TEMPLATE")

    @classmethod
    def model_construct(cls, *args, **kwargs):  # pylint: disable=signature-differs
        """For ansible-sanity import tests. Construct model instance, with fallback for when pydantic is not available."""
        if HAS_PYDANTIC:
            return super().model_construct(*args, **kwargs)
        # Fallback: return self when pydantic is not available
        return cls()


class ControllerResponseVrfsSwitchesMultisiteConnOuter(BaseModel):
    multisite_conn: Optional[List[ControllerResponseVrfsSwitchesMultisiteConnOuterItem]] = Field(
        default=[ControllerResponseVrfsSwitchesMultisiteConnOuterItem().model_construct()], alias="MULTISITE_CONN"
    )

    @classmethod
    def model_construct(cls, *args, **kwargs):  # pylint: disable=signature-differs
        """For ansible-sanity import tests. Construct model instance, with fallback for when pydantic is not available."""
        if HAS_PYDANTIC:
            return super().model_construct(*args, **kwargs)
        # Fallback: return self when pydantic is not available
        return cls()


class ControllerResponseVrfsSwitchesVrfLiteConnOuter(BaseModel):
    vrf_lite_conn: Optional[List[VrfLiteConnOuterItem]] = Field(default=[VrfLiteConnOuterItem().model_construct()], alias="VRF_LITE_CONN")

    @classmethod
    def model_construct(cls, *args, **kwargs):  # pylint: disable=signature-differs
        """For ansible-sanity import tests. Construct model instance, with fallback for when pydantic is not available."""
        if HAS_PYDANTIC:
            return super().model_construct(*args, **kwargs)
        # Fallback: return self when pydantic is not available
        return cls()


class ControllerResponseVrfsSwitchesExtensionValuesOuter(BaseModel):
    vrf_lite_conn: Optional[ControllerResponseVrfsSwitchesVrfLiteConnOuter] = Field(
        default=ControllerResponseVrfsSwitchesVrfLiteConnOuter().model_construct(), alias="VRF_LITE_CONN"
    )
    multisite_conn: Optional[ControllerResponseVrfsSwitchesMultisiteConnOuter] = Field(
        default=ControllerResponseVrfsSwitchesMultisiteConnOuter().model_construct(), alias="MULTISITE_CONN"
    )

    @field_validator("multisite_conn", mode="before")
    @classmethod
    def preprocess_multisite_conn(cls, data: Any) -> ControllerResponseVrfsSwitchesMultisiteConnOuter:
        """
        Convert incoming data

        - If data is a JSON string, use json.loads() to convert to a dict.
        - If data is a dict, convert it to an ControllerResponseVrfsSwitchesMultisiteConnOuter instance.
        - If data is already an ControllerResponseVrfsSwitchesMultisiteConnOuter instance, return as-is.
        """
        if isinstance(data, str):
            if data in ["", "{}"]:
                return ControllerResponseVrfsSwitchesMultisiteConnOuter().model_construct()
            return ControllerResponseVrfsSwitchesMultisiteConnOuter(**json.loads(data))
        if isinstance(data, dict):
            data = ControllerResponseVrfsSwitchesMultisiteConnOuter(**data)
        return data

    @field_validator("vrf_lite_conn", mode="before")
    @classmethod
    def preprocess_vrf_lite_conn(cls, data: Any) -> ControllerResponseVrfsSwitchesVrfLiteConnOuter:
        """
        Convert incoming data

        - If data is a JSON string, use json.loads() to convert to a dict.
        - If data is a dict, convert it to an ControllerResponseVrfsSwitchesVrfLiteConnOuter instance.
        - If data is already an ControllerResponseVrfsSwitchesVrfLiteConnOuter instance, return as-is.
        """
        if isinstance(data, str):
            if data in ["", "{}"]:
                return ControllerResponseVrfsSwitchesVrfLiteConnOuter().model_construct()
            return ControllerResponseVrfsSwitchesVrfLiteConnOuter(**json.loads(data))
        if isinstance(data, dict):
            data = ControllerResponseVrfsSwitchesVrfLiteConnOuter(**data)
        return data

    @classmethod
    def model_construct(cls, *args, **kwargs):  # pylint: disable=signature-differs
        """For ansible-sanity import tests. Construct model instance, with fallback for when pydantic is not available."""
        if HAS_PYDANTIC:
            return super().model_construct(*args, **kwargs)
        # Fallback: return self when pydantic is not available
        return cls()


class ControllerResponseVrfsSwitchesSwitchDetails(BaseModel):
    error_message: Union[str, None] = Field(alias="errorMessage")
    extension_prototype_values: Optional[List[ControllerResponseVrfsSwitchesExtensionPrototypeValue]] = Field(
        default=[ControllerResponseVrfsSwitchesExtensionPrototypeValue().model_construct()], alias="extensionPrototypeValues"
    )
    extension_values: Optional[ControllerResponseVrfsSwitchesExtensionValuesOuter] = Field(
        default=ControllerResponseVrfsSwitchesExtensionValuesOuter().model_construct(), alias="extensionValues"
    )
    freeform_config: Union[str, None] = Field(alias="freeformConfig")
    instance_values: Optional[ControllerResponseVrfsSwitchesInstanceValues] = Field(
        default=ControllerResponseVrfsSwitchesInstanceValues().model_construct(), alias="instanceValues"
    )
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
    def preprocess_extension_prototype_values(cls, data: Any) -> ControllerResponseVrfsSwitchesExtensionPrototypeValue:
        """
        Convert incoming data

        - If data is a JSON string, use json.loads() to convert to a dict.
        - If data is a list, convert it to a list of ControllerResponseVrfsSwitchesExtensionPrototypeValue instance.
        - If data is already an ControllerResponseVrfsSwitchesExtensionPrototypeValue model, return as-is.
        """
        if isinstance(data, str):
            if data == "":
                return ControllerResponseVrfsSwitchesExtensionPrototypeValue().model_construct()
        if isinstance(data, list):
            for instance in data:
                if isinstance(instance, dict):
                    instance = ControllerResponseVrfsSwitchesExtensionPrototypeValue(**instance)
        return data

    @field_validator("extension_values", mode="before")
    @classmethod
    def preprocess_extension_values(cls, data: Any) -> Union[ControllerResponseVrfsSwitchesExtensionValuesOuter, str]:
        """
        Convert incoming data

        - If data is a JSON string, use json.loads() to convert to a dict.
        - If data is a dict, convert it to an ControllerResponseVrfsSwitchesExtensionValuesOuter instance.
        - If data is already an ControllerResponseVrfsSwitchesExtensionValuesOuter instance, return as-is.
        """
        if isinstance(data, str):
            if data in ["", "{}"]:
                return ControllerResponseVrfsSwitchesExtensionValuesOuter().model_construct()
            return ControllerResponseVrfsSwitchesExtensionValuesOuter(**json.loads(data))
        if isinstance(data, dict):
            data = ControllerResponseVrfsSwitchesExtensionValuesOuter(**data)
        return data

    @field_validator("instance_values", mode="before")
    @classmethod
    def preprocess_instance_values(cls, data: Any) -> ControllerResponseVrfsSwitchesInstanceValues:
        """
        Convert incoming data

        - If data is a JSON string, use json.loads() to convert to a dict.
        - If data is a dict, convert it to an ControllerResponseVrfsSwitchesInstanceValues instance.
        - If data is already an ControllerResponseVrfsSwitchesInstanceValues instance, return as-is.
        """
        if isinstance(data, str):
            if data in ["", "{}"]:
                return ControllerResponseVrfsSwitchesInstanceValues().model_construct()
            return ControllerResponseVrfsSwitchesInstanceValues(**json.loads(data))
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
