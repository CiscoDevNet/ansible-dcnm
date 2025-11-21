"""
Validation model for payloads conforming the expectations of the
following endpoint:

Path: /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs
Verb: POST
"""
from __future__ import annotations

import traceback
import warnings
from typing import Optional

try:
    from pydantic import BaseModel, ConfigDict, Field, PydanticExperimentalWarning, field_serializer, field_validator, model_validator
except ImportError:
    from ..common.third_party.pydantic import BaseModel, ConfigDict, Field, PydanticExperimentalWarning, field_serializer, field_validator, model_validator
    HAS_PYDANTIC = False
    PYDANTIC_IMPORT_ERROR = traceback.format_exc()
else:
    HAS_PYDANTIC = True
    PYDANTIC_IMPORT_ERROR = None


from .vrf_template_config_v12 import VrfTemplateConfigV12

warnings.filterwarnings("ignore", category=PydanticExperimentalWarning)
warnings.filterwarnings("ignore", category=UserWarning)

base_vrf_model_config = ConfigDict(
    str_strip_whitespace=True,
    use_enum_values=True,
    validate_assignment=True,
    populate_by_name=True,
    populate_by_alias=True,
)


class VrfPayloadV12(BaseModel):
    """
    # Summary

    Validation model for payloads conforming the expectations of the
    following endpoint:

    On model_dump, the model will convert the vrfTemplateConfig
    parameter into a JSON string, which is the expected format for
    the controller.

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
        "hierarchicalKey": "fabric_1"
        "serviceVrfTemplate": "",
        "tenantName": "",
        "vrfExtensionTemplate": "Default_VRF_Extension_Universal",
        "vrfId": 50011,
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
        }
    }
    ```
    """

    model_config = base_vrf_model_config

    fabric: str = Field(..., alias="fabric", max_length=64, description="Fabric name in which the VRF resides.")
    hierarchical_key: str = Field(alias="hierarchicalKey", default="", max_length=64)
    service_vrf_template: str = Field(alias="serviceVrfTemplate", default="")
    source: Optional[str] = Field(default=None)
    tenant_name: str = Field(alias="tenantName", default="")
    vrf_extension_template: str = Field(alias="vrfExtensionTemplate", default="Default_VRF_Extension_Universal")
    vrf_id: int = Field(..., alias="vrfId", ge=1, le=16777214)
    vrf_name: str = Field(..., alias="vrfName", min_length=1, max_length=32, description="Name of the VRF, 1-32 characters.")
    vrf_template: str = Field(alias="vrfTemplate", default="Default_VRF_Universal")
    vrf_template_config: VrfTemplateConfigV12 = Field(alias="vrfTemplateConfig")

    @field_serializer("vrf_template_config")
    def serialize_vrf_template_config(self, vrf_template_config: VrfTemplateConfigV12) -> str:
        """
        Serialize the vrfTemplateConfig field to a JSON string required by the controller.
        """
        return vrf_template_config.model_dump_json(exclude_none=True, by_alias=True)

    @field_validator("service_vrf_template", mode="before")
    @classmethod
    def validate_service_vrf_template(cls, value: Optional[str]) -> str:
        """
        Validate serviceVrfTemplate.  If it is not empty, it must be a valid
        service VRF template.
        """
        if value is None:
            return ""
        return value

    @model_validator(mode="after")
    def validate_hierarchical_key(self) -> "VrfPayloadV12":
        """
        If hierarchicalKey is "", set it to the fabric name.
        """
        if self.hierarchical_key == "":
            self.hierarchical_key = self.fabric
        return self
