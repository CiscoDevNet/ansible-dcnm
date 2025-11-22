# -*- coding: utf-8 -*-
# @author: Allen Robel
# @file: plugins/module_utils/vrf/vrf_controller_to_playbook_v12.py
# Copyright (c) 2020-2025 Cisco and/or its affiliates.
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
Serialize NDFC version 12 controller payload fields to fields used in a dcnm_vrf playbook.
"""
from __future__ import annotations

import traceback
from typing import Optional

try:
    from pydantic import BaseModel, ConfigDict, Field
except ImportError:
    from ..common.third_party.pydantic import BaseModel, ConfigDict, Field
    HAS_PYDANTIC = False
    PYDANTIC_IMPORT_ERROR = traceback.format_exc()
else:
    HAS_PYDANTIC = True
    PYDANTIC_IMPORT_ERROR = None


class VrfControllerToPlaybookV12Model(BaseModel):
    """
    # Summary

    Serialize NDFC version 12 controller payload fields to fields used in a dcnm_vrf playbook.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )
    adv_default_routes: Optional[bool] = Field(alias="advertiseDefaultRouteFlag")
    adv_host_routes: Optional[bool] = Field(alias="advertiseHostRouteFlag")

    bgp_password: Optional[str] = Field(alias="bgpPassword")
    bgp_passwd_encrypt: Optional[int] = Field(alias="bgpPasswordKeyType")

    disable_rt_auto: Optional[bool] = Field(alias="disableRtAuto")

    export_evpn_rt: Optional[str] = Field(alias="routeTargetExportEvpn")
    export_mvpn_rt: Optional[str] = Field(alias="routeTargetExportMvpn")
    export_vpn_rt: Optional[str] = Field(alias="routeTargetExport")

    import_evpn_rt: Optional[str] = Field(alias="routeTargetImportEvpn")
    import_mvpn_rt: Optional[str] = Field(alias="routeTargetImportMvpn")
    import_vpn_rt: Optional[str] = Field(alias="routeTargetImport")
    ipv6_linklocal_enable: Optional[bool] = Field(alias="ipv6LinkLocalFlag")

    loopback_route_tag: Optional[int] = Field(alias="tag")

    max_bgp_paths: Optional[int] = Field(alias="maxBgpPaths")
    max_ibgp_paths: Optional[int] = Field(alias="maxIbgpPaths")

    netflow_enable: Optional[bool] = Field(alias="ENABLE_NETFLOW")
    nf_monitor: Optional[str] = Field(alias="NETFLOW_MONITOR")
    no_rp: Optional[bool] = Field(alias="isRPAbsent")

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
