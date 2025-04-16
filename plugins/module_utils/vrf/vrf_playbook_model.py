#!/usr/bin/env python
"""
VrfPlaybookModel

Validation models for dcnm_vrf playbooks.
"""

from typing import Optional, Union
from typing_extensions import Self

from pydantic import BaseModel, Field, model_validator
from ..common.models.ipv4_cidr_host import IPv4CidrHostModel
from ..common.models.ipv6_cidr_host import IPv6CidrHostModel
from ..common.models.ipv4_host import IPv4HostModel
from ..common.models.ipv6_host import IPv6HostModel
from ..common.enums.bgp import BgpPasswordEncrypt


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
    model_config = {
        "str_strip_whitespace": True,
        "str_to_lower": True,
        "use_enum_values": True,
        "validate_assignment": True,
        "arbitrary_types_allowed": True,
    }
    adv_default_routes: bool = Field(default=True)
    adv_host_routes: bool = Field(default=False)
    attach: Optional[list[VrfAttachModel]] = None
    bgp_passwd_encrypt: Union[BgpPasswordEncrypt, int] = Field(default=BgpPasswordEncrypt.MD5.value)
    bgp_password: str = Field(default="")
    deploy: bool = Field(default=True)
    disable_rt_auto: bool = Field(default=False)
    export_evpn_rt: str = Field(default="")
    export_mvpn_rt: str = Field(default="")
    export_vpn_rt: str = Field(default="")
    import_evpn_rt: str = Field(default="")
    import_mvpn_rt: str = Field(default="")
    import_vpn_rt: str = Field(default="")
    ipv6_linklocal_enable: bool = Field(default=True)
    loopback_route_tag: int = Field(default=12345, ge=0, le=4294967295)
    max_bgp_paths: int = Field(default=1, ge=1, le=64)
    max_ibgp_paths: int = Field(default=2, ge=1, le=64)
    netflow_enable: bool = Field(default=False)
    nf_monitor: str = Field(default="")
    no_rp: bool = Field(default=False)
    overlay_mcast_group: str = Field(default="")
    redist_direct_rmap: str = Field(default="FABRIC-RMAP-REDIST-SUBNET")
    rp_address: str = Field(default="")
    rp_external: bool = Field(default=False)
    rp_loopback_id: Optional[int] = Field(default=None, ge=0, le=1023)
    service_vrf_template: Optional[str] = None
    source: Optional[str] = None
    static_default_route: bool = Field(default=True)
    trm_bgw_msite: bool = Field(default=False)
    trm_enable: bool = Field(default=False)
    underlay_mcast_ip: str = Field(default="")
    vlan_id: Optional[int] = Field(default=None, le=4094)
    vrf_description: str = Field(default="")
    vrf_extension_template: str = Field(default="Default_VRF_Extension_Universal")
    vrf_id: Optional[int] = Field(default=None, le=16777214)
    vrf_int_mtu: int = Field(default=9216, ge=68, le=9216)
    vrf_intf_desc: str = Field(default="")
    vrf_name: str = Field(..., max_length=32)
    vrf_template: str = Field(default="Default_VRF_Universal")
    vrf_vlan_name: str = Field(default="")

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
