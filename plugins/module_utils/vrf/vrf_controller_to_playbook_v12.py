#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Allen Robel
# @file: plugins/module_utils/vrf/vrf_controller_to_playbook_v12.py
"""
Serialize NDFC version 12 controller payload fields to fie;ds used in a dcnm_vrf playbook.
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class VrfControllerToPlaybookV12Model(BaseModel):
    """
    # Summary

    Serialize NDFC version 12 controller payload fields to fie;ds used in a dcnm_vrf playbook.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )
    disable_rt_auto: Optional[bool] = Field(alias="disableRtAuto")

    export_evpn_rt: Optional[str] = Field(alias="routeTargetExportEvpn")
    export_mvpn_rt: Optional[str] = Field(alias="routeTargetExportMvpn")
    export_vpn_rt: Optional[str] = Field(alias="routeTargetExport")

    netflow_enable: Optional[bool] = Field(alias="ENABLE_NETFLOW")
    nf_monitor: Optional[str] = Field(alias="NETFLOW_MONITOR")
    no_rp: Optional[bool] = Field(alias="isRPAbsent")

    import_evpn_rt: Optional[str] = Field(alias="routeTargetImportEvpn")
    import_mvpn_rt: Optional[str] = Field(alias="routeTargetImportMvpn")
    import_vpn_rt: Optional[str] = Field(alias="routeTargetImport")
