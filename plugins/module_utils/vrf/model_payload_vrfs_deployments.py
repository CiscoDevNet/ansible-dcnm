# -*- coding: utf-8 -*-
"""
Validation for payloads sent to the following controller endpoint:

- Path:  /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs/deployments
- Verb: POST
"""
from pydantic import BaseModel, ConfigDict, Field, field_serializer


class PayloadfVrfsDeployments(BaseModel):
    """
    # Summary

    Represents a payload suitable for sending to the following controller endpoint:

    ## Endpoint

    ### Verb

    POST

    ### Path

    /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs/deployments

    ## Structure

    - `vrf_names`: list[str] - A list of VRF names to be deployed.  alias "vrfNames", default_factory=list

    ## Example pre-serialization

    vrf_names=['vrf2', 'vrf1', 'vrf3']

    ## Example post-serialization, model_dump(by_alias=True)

    ```json
    {
        "vrfNames": "vrf1,vrf2,vrf3"
    }
    ```
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        validate_by_alias=True,
        validate_by_name=True,
    )

    vrf_names: list[str] = Field(alias="vrfNames", default_factory=list)

    @field_serializer("vrf_names")
    def serialize_vrf_names(self, vrf_names: list[str]) -> str:
        """
        Serialize vrf_names to a comma-separated string of unique sorted vrf names.
        """
        return ",".join(set(sorted(list(vrf_names))))
