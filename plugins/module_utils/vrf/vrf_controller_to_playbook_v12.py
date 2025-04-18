#!/usr/bin/env python
# -*- coding: utf-8 -*-
# mypy: disable-error-code="import-untyped"
"""
VrfControllerToPlaybookV12Model

Serialize controller field names to names used in a dcnm_vrf playbook.
"""
import json
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class VrfControllerToPlaybookV12Model(BaseModel):
    """
    # Summary

    Serialize controller field names to names used in a dcnm_vrf playbook.
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


def main():
    """
    test the model
    """
    # pylint: disable=line-too-long
    json_string = '{"vrfSegmentId": 9008011, "vrfName": "test_vrf_1", "vrfVlanId": "202", "vrfVlanName": "", "vrfIntfDescription": "", "vrfDescription": "", "mtu": "9216", "tag": "12345", "vrfRouteMap": "FABRIC-RMAP-REDIST-SUBNET", "maxBgpPaths": "1", "maxIbgpPaths": "2", "ipv6LinkLocalFlag": "true", "trmEnabled": "false", "isRPExternal": "false", "rpAddress": "", "loopbackNumber": "", "L3VniMcastGroup": "", "multicastGroup": "", "trmBGWMSiteEnabled": "false", "advertiseHostRouteFlag": "false", "advertiseDefaultRouteFlag": "true", "configureStaticDefaultRouteFlag": "true", "bgpPassword": "", "bgpPasswordKeyType": "3", "isRPAbsent": "false", "ENABLE_NETFLOW": "false", "NETFLOW_MONITOR": "", "disableRtAuto": "false", "routeTargetImport": "", "routeTargetExport": "", "routeTargetImportEvpn": "", "routeTargetExportEvpn": "", "routeTargetImportMvpn": "", "routeTargetExportMvpn": ""}'
    # pylint: enable=line-too-long
    json_data = json.loads(json_string)
    model = VrfControllerToPlaybookV12Model(**json_data)
    print(model.model_dump(by_alias=True))
    print()
    print(model.model_dump(by_alias=False))


if __name__ == "__main__":
    main()
