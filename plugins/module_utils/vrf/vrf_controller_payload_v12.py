"""
Validation model for payloads conforming the expectations of the
following endpoint:

Path: /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs
Verb: POST
"""

from typing import Union
import warnings

from pydantic import BaseModel, ConfigDict, Field, PydanticExperimentalWarning, field_validator, model_validator
from typing_extensions import Self

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

    fabric: str = Field(..., alias="fabric", max_length=64, description="Fabric name in which the VRF resides.")
    hierarchical_key: str = Field(alias="hierarchicalKey", default="", max_length=64)
    service_vrf_template: str = Field(alias="serviceVrfTemplate", default="")
    tenant_name: str = Field(alias="tenantName", default="")
    vrf_id: int = Field(..., alias="vrfId", ge=1, le=16777214)
    vrf_name: str = Field(..., alias="vrfName", min_length=1, max_length=32, description="Name of the VRF, 1-32 characters.")
    vrf_template: str = Field(alias="vrfTemplate", default="Default_VRF_Universal")
    vrf_template_config: VrfTemplateConfigV12 = Field(alias="vrfTemplateConfig")

    @field_validator("service_vrf_template", mode="before")
    @classmethod
    def validate_service_vrf_template(cls, value: Union[str, None]) -> str:
        """
        Validate serviceVrfTemplate.  If it is not empty, it must be a valid
        service VRF template.
        """
        if value is None:
            return ""
        return value

    @model_validator(mode="after")
    def validate_hierarchical_key(self) -> Self:
        """
        If hierarchicalKey is "", set it to the fabric name.
        """
        if self.hierarchical_key == "":
            self.hierarchical_key = self.fabric
        return self
