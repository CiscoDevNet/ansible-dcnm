"""
Validation model for payloads conforming the expectations of the
following endpoint:

Path: /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs
Verb: POST
"""

# import json
import warnings
# from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, PydanticExperimentalWarning, model_validator
from typing_extensions import Self

# from ..common.enums.bgp import BgpPasswordEncrypt
from .vrf_template_config_v12 import VrfTemplateConfigV12

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


# class VrfTemplateConfig(BaseModel):
#     """
#     vrfTempateConfig field contents in VrfPayloadV12
#     """

#     model_config = base_vrf_model_config

#     advertiseDefaultRouteFlag: bool = Field(default=True, description="Advertise default route flag")
#     advertiseHostRouteFlag: bool = Field(default=False, description="Advertise host route flag")
#     asn: str = Field(..., description="BGP Autonomous System Number")
#     bgpPassword: str = Field(default="", description="BGP password")
#     bgpPasswordKeyType: int = Field(default=BgpPasswordEncrypt.MD5.value, description="BGP password key type")
#     configureStaticDefaultRouteFlag: bool = Field(default=True, description="Configure static default route flag")
#     disableRtAuto: bool = Field(default=False, description="Disable RT auto")
#     ENABLE_NETFLOW: bool = Field(default=False, description="Enable NetFlow")
#     ipv6LinkLocalFlag: bool = Field(default=True, description="Enables IPv6 link-local Option under VRF SVI. Not applicable to L3VNI w/o VLAN config.")
#     isRPAbsent: bool = Field(default=False, description="There is no RP in TRMv4 as only SSM is used")
#     isRPExternal: bool = Field(default=False, description="Is TRMv4 RP external to the fabric?")
#     loopbackNumber: Optional[Union[int, str]] = Field(default="", ge=-1, le=1023, description="Loopback number")
#     L3VniMcastGroup: str = Field(default="", description="L3 VNI multicast group")
#     maxBgpPaths: int = Field(default=1, ge=1, le=64, description="Max BGP paths, 1-64 for NX-OS, 1-32 for IOS XE")
#     maxIbgpPaths: int = Field(default=2, ge=1, le=64, description="Max IBGP paths, 1-64 for NX-OS, 1-32 for IOS XE")
#     multicastGroup: str = Field(default="", description="Overlay Multicast group")
#     mtu: Union[int, str] = Field(default=9216, ge=68, le=9216, description="VRF interface MTU")
#     NETFLOW_MONITOR: str = Field(default="", description="NetFlow monitor")
#     nveId: int = Field(default=1, ge=1, le=1, description="NVE ID")
#     routeTargetExport: str = Field(default="", description="Route target export")
#     routeTargetExportEvpn: str = Field(default="", description="Route target export EVPN")
#     routeTargetExportMvpn: str = Field(default="", description="Route target export MVPN")
#     routeTargetImport: str = Field(default="", description="Route target import")
#     routeTargetImportEvpn: str = Field(default="", description="Route target import EVPN")
#     routeTargetImportMvpn: str = Field(default="", description="Route target import MVPN")
#     rpAddress: str = Field(default="", description="IPv4 Address. Applicable when trmEnabled is True and isRPAbsent is False")
#     tag: int = Field(default=12345, ge=0, le=4294967295, description="Loopback routing tag")
#     trmBGWMSiteEnabled: bool = Field(default=False, description="Tenent routed multicast border-gateway multi-site enabled")
#     trmEnabled: bool = Field(default=False, description="Enable IPv4 Tenant Routed Multicast (TRMv4)")
#     vrfDescription: str = Field(default="", description="VRF description")
#     vrfIntfDescription: str = Field(default="", description="VRF interface description")
#     vrfName: str = Field(..., description="VRF name")
#     vrfRouteMap: str = Field(default="FABRIC-RMAP-REDIST-SUBNET", description="VRF route map")
#     vrfSegmentId: int = Field(..., ge=1, le=16777214, description="VRF segment ID")
#     vrfVlanId: int = Field(..., ge=2, le=4094, description="VRF VLAN ID")
#     vrfVlanName: str = Field(..., description="If > 32 chars, enable 'system vlan long-name' for NX-OS. Not applicable to L3VNI w/o VLAN config")

#     @model_validator(mode="before")
#     @classmethod
#     def preprocess_data(cls, data: Any) -> Any:
#         """
#         Convert incoming data

#         - If data is a JSON string, use json.loads() to convert to a dict.
#         - If data is a dict, convert to int all fields that should be int.
#         - If data is already a VrfTemplateConfig model, return as-is.
#         """

#         def convert_to_integer(key: str, dictionary: dict) -> int:
#             """
#             # Summary

#             Given a key and a dictionary, try to convert dictionary[key]
#             to an integer.

#             ## Raises

#             None

#             ## Returns

#             - A positive integer, if successful
#             - A negative integer (-1) if unsuccessful (KeyError or ValueError)

#             ## Notes

#             1.  It is expected that the Field() validation will fail for a parameter
#                 if the returned value (e.g. -1) is out of range.
#             2.  If you want to post-process a parameter (with an "after" validator)
#                 Then set the allowed range to include -1, e.g. ge=-1.  See
#                 the handling for `loopbackNumber` for an example.
#             """
#             result: int
#             try:
#                 result = int(dictionary[key])
#             except KeyError:
#                 msg = f"Key {key} not found. "
#                 msg += "Returning -1."
#                 result = -1
#             except ValueError:
#                 msg = "Unable to convert to integer. "
#                 msg += f"key: {key}, value: {dictionary[key]}. "
#                 msg += "Returning -1."
#                 result = -1
#             return result

#         vrf_template_config_params_with_integer_values: list[str] = [
#             "bgpPasswordKeyType",
#             "loopbackNumber",
#             "maxBgpPaths",
#             "maxIbgpPaths",
#             "mtu",
#             "nveId",
#             "tag",
#             "vrfId",
#             "vrfSegmentId",
#             "vrfVlanId",
#         ]

#         if isinstance(data, str):
#             data = json.loads(data)
#         if isinstance(data, dict):
#             for key in vrf_template_config_params_with_integer_values:
#                 data[key] = convert_to_integer(key, data)
#         if isinstance(data, VrfTemplateConfig):
#             pass
#         return data

#     @model_validator(mode="after")
#     def delete_loopback_number_if_negative(self) -> Self:
#         """
#         If loopbackNumber is negative, delete it from vrfTemplateConfig
#         """
#         if isinstance(self.loopbackNumber, int):
#             if self.loopbackNumber < 0:
#                 del self.loopbackNumber
#         return self
#
# @field_validator("loopbackNumber", mode="after")
# @classmethod
# def delete_loopback_number_if_negative(cls, data: Any) -> int:
#     """
#     If loopbackNumber is negative, delete it from vrfTemplateConfig
#     """
#     if isinstance(data, int):
#         if data < 0:
#             del data


class VrfPayloadV12(BaseModel):
    """
    # Summary

    Validation model for payloads conforming the expectations of the
    following endpoint:

    Verb: POST
    Path: /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs

    ## Raises

    ValueError if validation fails

    ## Structure

    Note, vrfTemplateConfig is received as a JSON string and converted by the model
    into a dictionary so that its parameters can be validated.  It should be
    converted back into a JSON string before sending to the controller.

    ```json
    {
        "fabric": "fabric_1",
        "vrfName": "vrf_1",
        "vrfTemplate": "Default_VRF_Universal",
        "vrfTemplateConfig": {
            "advertiseDefaultRouteFlag": true,
            "advertiseHostRouteFlag": false,
            "asn": "65002",
            "bgpPassword": "",
            "bgpPasswordKeyType": 3,
            "configureStaticDefaultRouteFlag": true,
            "disableRtAuto": false,
            "ENABLE_NETFLOW": false,
            "ipv6LinkLocalFlag": true,
            "isRPAbsent": false,
            "isRPExternal": false,
            "L3VniMcastGroup": "",
            "maxBgpPaths": 1,
            "maxIbgpPaths": 2,
            "multicastGroup": "",
            "mtu": 9216,
            "NETFLOW_MONITOR": "",
            "nveId": 1,
            "routeTargetExport": "",
            "routeTargetExportEvpn": "",
            "routeTargetExportMvpn": "",
            "routeTargetImport": "",
            "routeTargetImportEvpn": "",
            "routeTargetImportMvpn": "",
            "rpAddress": "",
            "tag": 12345,
            "trmBGWMSiteEnabled": false,
            "trmEnabled": false,
            "vrfDescription": "",
            "vrfIntfDescription": "",
            "vrfName": "my_vrf",
            "vrfRouteMap": "FABRIC-RMAP-REDIST-SUBNET",
            "vrfSegmentId": 50022,
            "vrfVlanId": 10,
            "vrfVlanName": "vlan10"
        },
        "tenantName": "",
        "vrfId": 50011,
        "serviceVrfTemplate": "",
        "hierarchicalKey": "fabric_1"
    }
    ```
    """

    model_config = base_vrf_model_config

    fabric: str = Field(..., max_length=64, description="Fabric name in which the VRF resides.")
    vrfName: str = Field(..., min_length=1, max_length=32, description="Name of the VRF, 1-32 characters.")
    vrfTemplate: str = Field(default="Default_VRF_Universal")
    # vrfTemplateConfig: VrfTemplateConfig
    vrfTemplateConfig: VrfTemplateConfigV12
    tenantName: str = Field(default="")
    vrfId: int = Field(..., ge=1, le=16777214)
    serviceVrfTemplate: str = Field(default="")
    hierarchicalKey: str = Field(default="", max_length=64)

    @model_validator(mode="after")
    def validate_hierarchical_key(self) -> Self:
        """
        If hierarchicalKey is "", set it to the fabric name.
        """
        if self.hierarchicalKey == "":
            self.hierarchicalKey = self.fabric
        return self
