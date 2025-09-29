"""
Validation model for the vrfTemplateConfig field contents in the controller response
to the following endpoint:

Path: /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs
Verb: GET
"""

import json
import warnings
from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, PydanticExperimentalWarning, field_validator, model_validator

from ..common.enums.bgp import BgpPasswordEncrypt

warnings.filterwarnings("ignore", category=PydanticExperimentalWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Base configuration for the Vrf* models
base_vrf_model_config = ConfigDict(
    str_strip_whitespace=True,
    use_enum_values=True,
    validate_assignment=True,
    populate_by_name=True,
    populate_by_alias=True,
)


class VrfTemplateConfigV12(BaseModel):
    """
    vrfTempateConfig field contents in VrfPayloadV12
    """

    model_config = base_vrf_model_config

    adv_default_routes: bool = Field(default=True, alias="advertiseDefaultRouteFlag", description="Advertise default route flag")
    adv_host_routes: bool = Field(default=False, alias="advertiseHostRouteFlag", description="Advertise host route flag")
    bgp_password: str = Field(default="", alias="bgpPassword", description="BGP password")
    bgp_passwd_encrypt: int = Field(default=BgpPasswordEncrypt.MD5.value, alias="bgpPasswordKeyType", description="BGP password key type")
    disable_rt_auto: bool = Field(default=False, alias="disableRtAuto", description="Disable RT auto")
    export_evpn_rt: str = Field(default="", alias="routeTargetExportEvpn", description="Route target export EVPN")
    export_mvpn_rt: str = Field(default="", alias="routeTargetExportMvpn", description="Route target export MVPN")
    export_vpn_rt: str = Field(default="", alias="routeTargetExport", description="Route target export")
    import_evpn_rt: str = Field(default="", alias="routeTargetImportEvpn", description="Route target import EVPN")
    import_mvpn_rt: str = Field(default="", alias="routeTargetImportMvpn", description="Route target import MVPN")
    import_vpn_rt: str = Field(default="", alias="routeTargetImport", description="Route target import")
    ipv6_linklocal_enable: bool = Field(
        default=True,
        alias="ipv6LinkLocalFlag",
        description="Enables IPv6 link-local Option under VRF SVI. Not applicable to L3VNI w/o VLAN config.",
    )
    l3vni_wo_vlan: bool = Field(default=False, alias="enableL3VniNoVlan", description="Enable L3 VNI without VLAN configuration")
    loopback_route_tag: int = Field(default=12345, ge=0, le=4294967295, alias="tag", description="Loopback routing tag")
    max_bgp_paths: int = Field(
        default=1,
        ge=1,
        le=64,
        alias="maxBgpPaths",
        description="Max BGP paths, 1-64 for NX-OS, 1-32 for IOS XE",
    )
    max_ibgp_paths: int = Field(
        default=2,
        ge=1,
        le=64,
        alias="maxIbgpPaths",
        description="Max IBGP paths, 1-64 for NX-OS, 1-32 for IOS XE",
    )
    netflow_enable: bool = Field(default=False, alias="ENABLE_NETFLOW", description="Enable NetFlow")
    nf_monitor: str = Field(default="", alias="NETFLOW_MONITOR", description="NetFlow monitor")
    no_rp: bool = Field(default=False, alias="isRPAbsent", description="There is no RP in TRMv4 as only SSM is used")
    overlay_mcast_group: str = Field(default="", alias="multicastGroup", description="Overlay Multicast group")
    redist_direct_rmap: str = Field(default="FABRIC-RMAP-REDIST-SUBNET", alias="vrfRouteMap", description="VRF route map")
    v6_redist_direct_rmap: str = Field(default="FABRIC-RMAP-REDIST-SUBNET", alias="v6VrfRouteMap", description="VRF v6 route map")
    rp_address: str = Field(
        default="",
        alias="rpAddress",
        description="IPv4 Address. Applicable when trmEnabled is True and isRPAbsent is False",
    )
    rp_external: bool = Field(default=False, alias="isRPExternal", description="Is TRMv4 RP external to the fabric?")
    rp_loopback_id: Optional[Union[int, str]] = Field(default="", alias="loopbackNumber", description="Loopback number")
    static_default_route: bool = Field(default=True, alias="configureStaticDefaultRouteFlag", description="Configure static default route flag")
    trm_bgw_msite: bool = Field(
        default=False,
        alias="trmBGWMSiteEnabled",
        description="Tenent routed multicast border-gateway multi-site enabled",
    )
    trm_enable: bool = Field(default=False, alias="trmEnabled", description="Enable IPv4 Tenant Routed Multicast (TRMv4)")
    underlay_mcast_ip: str = Field(default="", alias="L3VniMcastGroup", description="L3 VNI multicast group")
    vlan_id: int = Field(default=0, ge=0, le=4094, alias="vrfVlanId", description="VRF VLAN ID")
    vrf_description: str = Field(default="", alias="vrfDescription", description="VRF description")
    vrf_id: int = Field(..., ge=1, le=16777214, alias="vrfSegmentId", description="VRF segment ID")
    vrf_int_mtu: int = Field(default=9216, ge=68, le=9216, alias="mtu", description="VRF interface MTU")
    vrf_intf_desc: str = Field(default="", alias="vrfIntfDescription", description="VRF interface description")
    vrf_name: str = Field(..., alias="vrfName", description="VRF name")
    vrf_vlan_name: str = Field(
        default="",
        alias="vrfVlanName",
        description="If > 32 chars, enable 'system vlan long-name' for NX-OS. Not applicable to L3VNI w/o VLAN config",
    )

    @field_validator("rp_loopback_id", mode="before")
    @classmethod
    def validate_rp_loopback_id(cls, data: Any) -> Union[int, str]:
        """
        If rp_loopback_id is None, return ""
        If rp_loopback_id is an empty string, return ""
        If rp_loopback_id is an integer, verify it is within range 0-1023
        If rp_loopback_id is a non-empty string, try to convert to int and verify it is within range 0-1023

        ## Raises

        - ValueError: If rp_loopback_id is not an integer or string representing an integer
        - ValueError: If rp_loopback_id is not in range 0-1023

        ## Notes

        - Replace this validator with the one using match-case when python 3.10 is the minimum version supported
        """
        if data is None:
            return ""
        if data == "":
            return ""
        if isinstance(data, str):
            try:
                data = int(data)
            except ValueError as error:
                msg = "rp_loopback_id (loopbackNumber) must be an integer "
                msg += "or string representing an integer. "
                msg += f"Got: {data} of type {type(data)}. "
                msg += f"Error detail: {error}"
                raise ValueError(msg) from error
        if isinstance(data, int):
            if data in range(0, 1024):
                return data
            msg = "rp_loopback_id (loopbackNumber) must be between 0 and 1023. "
            msg += f"Got: {data}"
            raise ValueError(msg)
        # Return invalid data as-is.  Type checking is done in the model_validator
        return data

    @field_validator("vlan_id", mode="before")
    @classmethod
    def preprocess_vlan_id(cls, data: Any) -> int:
        """
        Preprocess the vlan_id field to ensure it is an integer.

        ## Raises

        - ValueError: If vlan_id is not an integer or string representing an integer
        - ValueError: If vlan_id is 1
        """
        if data is None:
            return 0
        if isinstance(data, str):
            try:
                data = int(data)
            except ValueError as error:
                msg = "vlan_id (vrfVlanId) must be an integer "
                msg += "or string representing an integer. "
                msg += f"Got: {data} of type {type(data)}. "
                msg += f"Error detail: {error}"
                raise ValueError(msg) from error
        if data == 1:
            msg = "vlan_id (vrfVlanId) must not be 1. "
            msg += f"Got: {data}"
            raise ValueError(msg)
        # Further validation is done in the model_validator
        return data

    @model_validator(mode="before")
    @classmethod
    def preprocess_data(cls, data: Any) -> Any:
        """
        Convert incoming data

        - If data is a JSON string, use json.loads() to convert to a dict.
        - If data is a dict, convert to int all fields that should be int.
        - If data is already a VrfTemplateConfig model, return as-is.
        """

        if isinstance(data, str):
            data = json.loads(data)
        if isinstance(data, dict):
            pass
        if isinstance(data, VrfTemplateConfigV12):
            pass
        return data

    @model_validator(mode="after")
    def validate_l3vni_without_vlan_config(self) -> "VrfTemplateConfigV12":
        """
        Handle L3VNI without VLAN configuration
        """
        if self.l3vni_wo_vlan:
            # For L3VNI without VLAN, these fields should be cleared
            self.vlan_id = ""
        return self

    # Replace rp_loopback_id validator with this one when python 3.10 is the minimum version supported
    '''
    @field_validator("rp_loopback_id", mode="before")
    @classmethod
    def validate_rp_loopback_id(cls, data: Any) -> Union[int, str]:
        """
        If rp_loopback_id is None, return ""
        If rp_loopback_id is an empty string, return ""
        If rp_loopback_id is an integer, verify it is within range 0-1023
        If rp_loopback_id is a non-empty string, try to convert to int and verify it is within range 0-1023

        ## Raises

        - ValueError: If rp_loopback_id is not an integer or string representing an integer
        - ValueError: If rp_loopback_id is not in range 0-1023
        """
        match data:
            case None:
                return ""
            case "":
                return ""
            case int():
                pass
            case str():
                try:
                    data = int(data)
                except ValueError as error:
                    msg = "rp_loopback_id (loopbackNumber) must be an integer "
                    msg += "or string representing an integer. "
                    msg += f"Got: {data} of type {type(data)}. "
                    msg += f"Error detail: {error}"
                    raise ValueError(msg) from error
        if data in range(0, 1024):
            return data
        msg = "rp_loopback_id (loopbackNumber) must be between 0 and 1023. "
        msg += f"Got: {data}"
        raise ValueError(msg)
    '''

    # Replace vlan_id validator with this one when python 3.10 is the minimum version supported
    '''
    @field_validator("vlan_id", mode="before")
    @classmethod
    def preprocess_vlan_id(cls, data: Any) -> int:
        """
        Preprocess the vlan_id field to ensure it is an integer.

        ## Raises

        - ValueError: If vlan_id is not an integer or string representing an integer
        - ValueError: If vlan_id is 1
        """
        match data:
            case None:
                return 0
            case "":
                return 0
            case 1 | "1":
                msg = "vlan_id (vrfVlanId) must not be 1. "
                msg += f"Got: {data}"
                raise ValueError(msg)
            case str():
                try:
                    data = int(data)
                except ValueError as error:
                    msg = "vlan_id (vrfVlanId) must be an integer "
                    msg += "or string representing an integer. "
                    msg += f"Got: {data} of type {type(data)}. "
                    msg += f"Error detail: {error}"
                    raise ValueError(msg) from error
    '''
