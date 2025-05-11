"""
Validation model for the vrfTemplateConfig field contents in the controller response
to the following endpoint:

Path: /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs
Verb: GET
"""

import warnings
from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, PydanticExperimentalWarning, field_validator

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
    # asn: str = Field(..., alias="asn", description="BGP Autonomous System Number")
    bgp_password: str = Field(default="", alias="bgpPassword", description="BGP password")
    bgp_passwd_encrypt: int = Field(default=BgpPasswordEncrypt.MD5.value, alias="bgpPasswordKeyType", description="BGP password key type")
    static_default_route: bool = Field(default=True, alias="configureStaticDefaultRouteFlag", description="Configure static default route flag")
    disable_rt_auto: bool = Field(default=False, alias="disableRtAuto", description="Disable RT auto")
    netflow_enable: bool = Field(default=False, alias="ENABLE_NETFLOW", description="Enable NetFlow")
    ipv6_linklocal_enable: bool = Field(
        default=True,
        alias="ipv6LinkLocalFlag",
        description="Enables IPv6 link-local Option under VRF SVI. Not applicable to L3VNI w/o VLAN config.",
    )
    no_rp: bool = Field(default=False, alias="isRPAbsent", description="There is no RP in TRMv4 as only SSM is used")
    rp_external: bool = Field(default=False, alias="isRPExternal", description="Is TRMv4 RP external to the fabric?")
    rp_loopback_id: Optional[Union[int, str]] = Field(default="", alias="loopbackNumber", description="Loopback number")
    underlay_mcast_ip: str = Field(default="", alias="L3VniMcastGroup", description="L3 VNI multicast group")
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
    vrf_int_mtu: Union[int, str] = Field(default=9216, ge=68, le=9216, alias="mtu", description="VRF interface MTU")
    overlay_mcast_group: str = Field(default="", alias="multicastGroup", description="Overlay Multicast group")
    nf_monitor: str = Field(default="", alias="NETFLOW_MONITOR", description="NetFlow monitor")
    # nve_id: int = Field(default=1, ge=1, le=1, alias="nveId", description="NVE ID")
    export_vpn_rt: str = Field(default="", alias="routeTargetExport", description="Route target export")
    export_evpn_rt: str = Field(default="", alias="routeTargetExportEvpn", description="Route target export EVPN")
    export_mvpn_rt: str = Field(default="", alias="routeTargetExportMvpn", description="Route target export MVPN")
    import_vpn_rt: str = Field(default="", alias="routeTargetImport", description="Route target import")
    import_evpn_rt: str = Field(default="", alias="routeTargetImportEvpn", description="Route target import EVPN")
    import_mvpn_rt: str = Field(default="", alias="routeTargetImportMvpn", description="Route target import MVPN")
    rp_address: str = Field(
        default="",
        alias="rpAddress",
        description="IPv4 Address. Applicable when trmEnabled is True and isRPAbsent is False",
    )
    loopback_route_tag: int = Field(default=12345, ge=0, le=4294967295, alias="tag", description="Loopback routing tag")
    trm_bgw_msite: bool = Field(
        default=False,
        alias="trmBGWMSiteEnabled",
        description="Tenent routed multicast border-gateway multi-site enabled",
    )
    trm_enable: bool = Field(default=False, alias="trmEnabled", description="Enable IPv4 Tenant Routed Multicast (TRMv4)")
    vrf_description: str = Field(default="", alias="vrfDescription", description="VRF description")
    vrf_intf_desc: str = Field(default="", alias="vrfIntfDescription", description="VRF interface description")
    vrf_name: str = Field(..., alias="vrfName", description="VRF name")
    redist_direct_rmap: str = Field(default="FABRIC-RMAP-REDIST-SUBNET", alias="vrfRouteMap", description="VRF route map")
    vrf_id: int = Field(..., ge=1, le=16777214, alias="vrfSegmentId", description="VRF segment ID")
    vlan_id: int = Field(default=0, ge=0, le=4094, alias="vrfVlanId", description="VRF VLAN ID")
    vrf_vlan_name: str = Field(
        default="",
        alias="vrfVlanName",
        description="If > 32 chars, enable 'system vlan long-name' for NX-OS. Not applicable to L3VNI w/o VLAN config",
    )

    @field_validator("vlan_id", mode="before")
    @classmethod
    def preprocess_vlan_id(cls, data: Any) -> int:
        """
        Preprocess the vlan_id field to ensure it is an integer.
        """
        if data is None:
            return 0
        if isinstance(data, int):
            return data
        if isinstance(data, str):
            try:
                return int(data)
            except ValueError:
                return 0
