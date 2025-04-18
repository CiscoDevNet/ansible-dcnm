#!/usr/bin/env python
# -*- coding: utf-8 -*-
# mypy: disable-error-code="import-untyped"
"""
VrfPlaybookModel

Validation models for dcnm_vrf playbooks.
"""
import traceback
from typing import Optional, Union

from ansible.module_utils.basic import missing_required_lib # pylint: disable=unused-import

PYDANTIC_IMPORT_ERROR: str | None = None
HAS_PYDANTIC: bool = True
HAS_TYPING_EXTENSIONS: bool = True

try:
    from pydantic import BaseModel, ConfigDict, Field, model_validator
except ImportError:
    HAS_PYDANTIC = False
    PYDANTIC_IMPORT_ERROR = traceback.format_exc()

try:
    from typing_extensions import Self
except ImportError:
    HAS_TYPING_EXTENSIONS = False
    TYPING_EXTENSIONS_IMPORT_ERROR = traceback.format_exc()

from ..common.enums.bgp import BgpPasswordEncrypt
from ..common.models.ipv4_cidr_host import IPv4CidrHostModel
from ..common.models.ipv4_host import IPv4HostModel
from ..common.models.ipv6_cidr_host import IPv6CidrHostModel
from ..common.models.ipv6_host import IPv6HostModel


class VrfLiteModel(BaseModel):
    """
    Model for VRF Lite configuration."
    """

    dot1q: int = Field(default=0, ge=0, le=4094)
    interface: str
    ipv4_addr: str = Field(default="")
    ipv6_addr: str = Field(default="")
    neighbor_ipv4: str = Field(default="")
    neighbor_ipv6: str = Field(default="")
    peer_vrf: str

    @model_validator(mode="after")
    def validate_ipv4_host(self) -> Self:
        """
        Validate neighbor_ipv4 is an IPv4 host address without prefix.
        """
        if self.neighbor_ipv4 != "":
            IPv4HostModel(ipv4_host=self.neighbor_ipv4)
        return self

    @model_validator(mode="after")
    def validate_ipv6_host(self) -> Self:
        """
        Validate neighbor_ipv6 is an IPv6 host address without prefix.
        """
        if self.neighbor_ipv6 != "":
            IPv6HostModel(ipv6_host=self.neighbor_ipv6)
        return self

    @model_validator(mode="after")
    def validate_ipv4_cidr_host(self) -> Self:
        """
        Validate ipv4_addr is a CIDR-format IPv4 host address.
        """
        if self.ipv4_addr != "":
            IPv4CidrHostModel(ipv4_cidr_host=self.ipv4_addr)
        return self

    @model_validator(mode="after")
    def validate_ipv6_cidr_host(self) -> Self:
        """
        Validate ipv6_addr is a CIDR-format IPv6 host address.
        """
        if self.ipv6_addr != "":
            IPv6CidrHostModel(ipv6_cidr_host=self.ipv6_addr)
        return self


class VrfAttachModel(BaseModel):
    """
    Model for VRF attachment configuration.
    """

    deploy: bool = Field(default=True)
    export_evpn_rt: str = Field(default="")
    import_evpn_rt: str = Field(default="")
    ip_address: str
    vrf_lite: list[VrfLiteModel] | None = Field(default=None)

    @model_validator(mode="after")
    def validate_ipv4_host(self) -> Self:
        """
        Validate ip_address is an IPv4 host address without prefix.
        """
        if self.ip_address != "":
            IPv4HostModel(ipv4_host=self.ip_address)
        return self

    @model_validator(mode="after")
    def vrf_lite_set_to_none_if_empty_list(self) -> Self:
        """
        Set vrf_lite to None if it is an empty list.
        This mimics the behavior of the original code.
        """
        if not self.vrf_lite:
            self.vrf_lite = None
        return self


class VrfPlaybookModel(BaseModel):
    """
    Model for VRF configuration.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True,
        validate_assignment=True,
    )
    adv_default_routes: bool = Field(default=True, alias="advertiseDefaultRouteFlag")
    adv_host_routes: bool = Field(default=False, alias="advertiseHostRouteFlag")
    attach: Optional[list[VrfAttachModel]] = None
    bgp_passwd_encrypt: Union[BgpPasswordEncrypt, int] = Field(default=BgpPasswordEncrypt.MD5.value, alias="bgpPasswordKeyType")
    bgp_password: str = Field(default="", alias="bgpPassword")
    deploy: bool = Field(default=True)
    disable_rt_auto: bool = Field(default=False, alias="disableRtAuto")
    export_evpn_rt: str = Field(default="", alias="routeTargetExportEvpn")
    export_mvpn_rt: str = Field(default="", alias="routeTargetExportMvpn")
    export_vpn_rt: str = Field(default="", alias="routeTargetExport")
    import_evpn_rt: str = Field(default="", alias="routeTargetImportEvpn")
    import_mvpn_rt: str = Field(default="", alias="routeTargetImportMvpn")
    import_vpn_rt: str = Field(default="", alias="routeTargetImport")
    ipv6_linklocal_enable: bool = Field(default=True, alias="ipv6LinkLocalFlag")
    loopback_route_tag: int = Field(default=12345, ge=0, le=4294967295, alias="tag")
    max_bgp_paths: int = Field(default=1, ge=1, le=64, alias="maxBgpPaths")
    max_ibgp_paths: int = Field(default=2, ge=1, le=64, alias="maxIbgpPaths")
    netflow_enable: bool = Field(default=False, alias="ENABLE_NETFLOW")
    nf_monitor: str = Field(default="", alias="NETFLOW_MONITOR")
    no_rp: bool = Field(default=False, alias="isRPAbsent")
    overlay_mcast_group: str = Field(default="", alias="multicastGroup")
    redist_direct_rmap: str = Field(default="FABRIC-RMAP-REDIST-SUBNET", alias="vrfRouteMap")
    rp_address: str = Field(default="", alias="rpAddress")
    rp_external: bool = Field(default=False, alias="isRPExternal")
    rp_loopback_id: Optional[int] = Field(default=None, ge=0, le=1023, alias="loopbackNumber")
    service_vrf_template: Optional[str] = Field(default=None, alias="serviceVrfTemplate")
    source: Optional[str] = None
    static_default_route: bool = Field(default=True, alias="configureStaticDefaultRouteFlag")
    trm_bgw_msite: bool = Field(default=False, alias="trmBGWMSiteEnabled")
    trm_enable: bool = Field(default=False, alias="trmEnabled")
    underlay_mcast_ip: str = Field(default="", alias="L3VniMcastGroup")
    vlan_id: Optional[int] = Field(default=None, le=4094)
    vrf_description: str = Field(default="", alias="vrfDescription")
    vrf_extension_template: str = Field(default="Default_VRF_Extension_Universal", alias="vrfExtensionTemplate")
    # vrf_id: Optional[int] = Field(default=None, le=16777214, alias="vrfId")
    vrf_id: Optional[int] = Field(default=None, le=16777214)
    vrf_int_mtu: int = Field(default=9216, ge=68, le=9216, alias="mtu")
    vrf_intf_desc: str = Field(default="", alias="vrfIntfDescription")
    #vrf_name: str = Field(..., max_length=32, alias="vrfName")
    vrf_name: str = Field(..., max_length=32)
    vrf_template: str = Field(default="Default_VRF_Universal")
    vrf_vlan_name: str = Field(default="", alias="vrfVlanName")

    @model_validator(mode="after")
    def hardcode_source_to_none(self) -> Self:
        """
        To mimic original code, hardcode source to None.
        """
        if self.source is not None:
            self.source = None
        return self

    @model_validator(mode="after")
    def validate_rp_address(self) -> Self:
        """
        Validate rp_address is an IPv4 host address without prefix.
        """
        if self.rp_address != "":
            IPv4HostModel(ipv4_host=self.rp_address)
        return self


class VrfPlaybookConfigModel(BaseModel):
    """
    Model for VRF playbook configuration.
    """

    config: list[VrfPlaybookModel] = Field(default_factory=list[VrfPlaybookModel])


if __name__ == "__main__":
    pass
