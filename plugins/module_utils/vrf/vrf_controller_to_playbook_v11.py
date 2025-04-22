#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Allen Robel
# @file: plugins/module_utils/vrf/vrf_controller_to_playbook_v11.py
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
Serialize NDFC v11 payload fields to fields used in a dcnm_vrf playbook.
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class VrfControllerToPlaybookV11Model(BaseModel):
    """
    # Summary

    Serialize NDFC v11 payload fields to fields used in a dcnm_vrf playbook.
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
