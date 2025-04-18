#!/usr/bin/env python
# -*- coding: utf-8 -*-
# mypy: disable-error-code="import-untyped"
"""
vrfTemplateConfigToDiffModel

Serialize vrfTemplateConfig formatted as a dcnm_vrf diff.
"""

import json
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class VrfControllerToPlaybookModel(BaseModel):
    """
    # Summary

    Serialize vrfTemplateConfig formatted as a dcnm_vrf diff.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )
    adv_default_routes: Optional[bool] = Field(alias="advertiseDefaultRouteFlag")
    adv_host_routes: Optional[bool] = Field(alias="advertiseHostRouteFlag")
    bgp_password: Optional[str] = Field(alias="bgpPassword")
    bgp_passwd_encrypt: Optional[int] = Field(alias="bgpPasswordKeyType")
    ipv6_linklocal_enable: Optional[bool] = Field(alias="ipv6LinkLocalFlag")
    loopback_route_tag: Optional[int] = Field(alias="tag")
    max_bgp_paths: Optional[int] = Field(alias="maxBgpPaths")
    max_ibgp_paths: Optional[int] = Field(alias="maxIbgpPaths")
    overlay_mcast_group: Optional[str] = Field(alias="multicastGroup")
    redist_direct_rmap: Optional[str] = Field(alias="vrfRouteMap")
    rp_address: Optional[str] = Field(alias="rpAddress")
    rp_external: Optional[bool] = Field(alias="isRPExternal")
    rp_loopback_id: Optional[int | str] = Field(alias="loopbackNumber")
    static_default_route: Optional[bool] = Field(alias="configureStaticDefaultRouteFlag")
    trm_bgw_msite: Optional[bool] = Field(alias="trmBGWMSiteEnabled")
    trm_enable: Optional[bool] = Field(alias="trmEnabled")
    underlay_mcast_ip: Optional[str] = Field(alias="L3VniMcastGroup")
    vrf_description: Optional[str] = Field(alias="vrfDescription")
    vrf_int_mtu: Optional[int] = Field(alias="mtu")
    vrf_intf_desc: Optional[str] = Field(alias="vrfIntfDescription")
    vrf_vlan_name: Optional[str] = Field(alias="vrfVlanName")
