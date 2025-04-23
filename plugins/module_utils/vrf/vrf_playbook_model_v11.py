# -*- coding: utf-8 -*-
# @author: Allen Robel
# @file: plugins/module_utils/vrf/vrf_playbook_model.py
# Copyright (c) 2020-2023 Cisco and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# pylint: disable=wrong-import-position
"""
Validation model for dcnm_vrf playbooks.
"""
from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing_extensions import Self

from ..common.enums.bgp import BgpPasswordEncrypt
from ..common.models.ipv4_cidr_host import IPv4CidrHostModel
from ..common.models.ipv4_host import IPv4HostModel
from ..common.models.ipv6_cidr_host import IPv6CidrHostModel
from ..common.models.ipv6_host import IPv6HostModel


class VrfLiteModel(BaseModel):
    """
    # Summary

    Model for VRF Lite configuration.

    ## Raises

    - ValueError if:
      - dot1q is not within the range 0-4094
      - ipv4_addr is not valid
      - ipv6_addr is not valid
      - interface is not provided
      - neighbor_ipv4 is not valid
      - neighbor_ipv6 is not valid

    ## Attributes:

    - dot1q (int): VLAN ID for the interface.
    - interface (str): Interface name.
    - ipv4_addr (str): IPv4 address in CIDR format.
    - ipv6_addr (str): IPv6 address in CIDR format.
    - neighbor_ipv4 (str): IPv4 address without prefix.
    - neighbor_ipv6 (str): IPv6 address without prefix.
    - peer_vrf (str): Peer VRF name.

    ## Example usage:

    ```python
    from pydantic import ValidationError
    from vrf_lite_module import VrfLiteModel
    try:
        vrf_lite = VrfLiteModel(
            dot1q=100,
            interface="Ethernet1/1",
            ipv4_addr="10.1.1.1/24"
        )
    except ValidationError as e:
        handle_error
    ```

    """

    dot1q: int = Field(default=0, ge=0, le=4094)
    interface: str
    ipv4_addr: Optional[str] = Field(default="")
    ipv6_addr: Optional[str] = Field(default="")
    neighbor_ipv4: Optional[str] = Field(default="")
    neighbor_ipv6: Optional[str] = Field(default="")
    peer_vrf: Optional[str] = Field(default="")

    @model_validator(mode="after")
    def validate_ipv4_host(self) -> Self:
        """
        Validate neighbor_ipv4 is an IPv4 host address without prefix.
        """
        if self.neighbor_ipv4 != "":
            IPv4HostModel(ipv4_host=str(self.neighbor_ipv4))
        return self

    @model_validator(mode="after")
    def validate_ipv6_host(self) -> Self:
        """
        Validate neighbor_ipv6 is an IPv6 host address without prefix.
        """
        if self.neighbor_ipv6 != "":
            IPv6HostModel(ipv6_host=str(self.neighbor_ipv6))
        return self

    @model_validator(mode="after")
    def validate_ipv4_cidr_host(self) -> Self:
        """
        Validate ipv4_addr is a CIDR-format IPv4 host address.
        """
        if self.ipv4_addr != "":
            IPv4CidrHostModel(ipv4_cidr_host=str(self.ipv4_addr))
        return self

    @model_validator(mode="after")
    def validate_ipv6_cidr_host(self) -> Self:
        """
        Validate ipv6_addr is a CIDR-format IPv6 host address.
        """
        if self.ipv6_addr != "":
            IPv6CidrHostModel(ipv6_cidr_host=str(self.ipv6_addr))
        return self


class VrfAttachModel(BaseModel):
    """
    # Summary

    Model for VRF attachment configuration.

    ## Raises

    - ValueError if:
        - deploy is not a boolean
        - ip_address is not a valid IPv4 host address
        - ip_address is not provided
        - vrf_lite (if provided) is not a list of VrfLiteModel instances

    ## Attributes:

    - deploy (bool): Flag to indicate if the VRF should be deployed.
    - ip_address (str): IP address of the interface.
    - vrf_lite (list[VrfLiteModel]): List of VRF Lite configurations.
    - vrf_lite (None): If not provided, defaults to None.

    ## Example usage:

    ```python
    from pydantic import ValidationError
    from vrf_attach_module import VrfAttachModel
    try:
        vrf_attach = VrfAttachModel(
            deploy=True,
            ip_address="10.1.1.1",
            vrf_lite=[
                VrfLiteModel(
                    dot1q=100,
                    interface="Ethernet1/1",
                    ipv4_addr="10.1.1.1/24"
                )
            ]
        )
    except ValidationError as e:
        handle_error
    ```
    """

    deploy: bool = Field(default=True)
    ip_address: str
    vrf_lite: Union[list[VrfLiteModel], None] = Field(default=None)

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


class VrfPlaybookModelV11(BaseModel):
    """
    # Summary


    Model to validate a playbook VRF configuration.

    All fields can take an alias, which is the name of the field in the
    original payload. The alias is used to map the field to the
    corresponding field in the playbook.

    ## Raises

    - ValueError if:
        - adv_default_routes is not a boolean
        - adv_host_routes is not a boolean
        - attach (if provided) is not a list of VrfAttachModel instances
        - bgp_passwd_encrypt is not a valid BgpPasswordEncrypt enum value
        - bgp_password is not a string
        - deploy is not a boolean
        - ipv6_linklocal_enable is not a boolean
        - loopback_route_tag is not an integer between 0 and 4294967295
        - max_bgp_paths is not an integer between 1 and 64
        - max_ibgp_paths is not an integer between 1 and 64
        - overlay_mcast_group is not a string
        - redist_direct_rmap is not a string
        - rp_address is not a valid IPv4 host address
        - rp_external is not a boolean
        - rp_loopback_id is not an integer between 0 and 1023
        - service_vrf_template is not a string
        - static_default_route is not a boolean
        - trm_bgw_msite is not a boolean
        - trm_enable is not a boolean
        - underlay_mcast_ip is not a string
        - vlan_id is not an integer between 0 and 4094
        - vrf_description is not a string
        - vrf_extension_template is not a string
        - vrf_id is not an integer between 0 and 16777214
        - vrf_int_mtu is not an integer between 68 and 9216
        - vrf_intf_desc is not a string
        - vrf_name is not a string
        - vrf_template is not a string
        - vrf_vlan_name is not a string
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
    ipv6_linklocal_enable: bool = Field(default=True, alias="ipv6LinkLocalFlag")
    loopback_route_tag: int = Field(default=12345, ge=0, le=4294967295, alias="tag")
    max_bgp_paths: int = Field(default=1, ge=1, le=64, alias="maxBgpPaths")
    max_ibgp_paths: int = Field(default=2, ge=1, le=64, alias="maxIbgpPaths")
    overlay_mcast_group: str = Field(default="", alias="multicastGroup")
    redist_direct_rmap: str = Field(default="FABRIC-RMAP-REDIST-SUBNET", alias="vrfRouteMap")
    rp_address: str = Field(default="", alias="rpAddress")
    rp_external: bool = Field(default=False, alias="isRPExternal")
    rp_loopback_id: Optional[Union[int, str]] = Field(default="", ge=0, le=1023, alias="loopbackNumber")
    service_vrf_template: Optional[str] = Field(default=None, alias="serviceVrfTemplate")
    source: Optional[str] = None
    static_default_route: bool = Field(default=True, alias="configureStaticDefaultRouteFlag")
    trm_bgw_msite: bool = Field(default=False, alias="trmBGWMSiteEnabled")
    trm_enable: bool = Field(default=False, alias="trmEnabled")
    underlay_mcast_ip: str = Field(default="", alias="L3VniMcastGroup")
    vlan_id: Optional[int] = Field(default=None, le=4094)
    vrf_description: str = Field(default="", alias="vrfDescription")
    vrf_extension_template: str = Field(default="Default_VRF_Extension_Universal", alias="vrfExtensionTemplate")
    vrf_id: Optional[int] = Field(default=None, le=16777214)
    vrf_int_mtu: int = Field(default=9216, ge=68, le=9216, alias="mtu")
    vrf_intf_desc: str = Field(default="", alias="vrfIntfDescription")
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


class VrfPlaybookConfigModelV11(BaseModel):
    """
    Model for VRF playbook configuration.
    """

    config: list[VrfPlaybookModelV11] = Field(default_factory=list[VrfPlaybookModelV11])
