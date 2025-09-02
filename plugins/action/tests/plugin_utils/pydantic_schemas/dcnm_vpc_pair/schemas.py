from __future__ import absolute_import, division, print_function
from typing import List, Optional, Annotated
from ansible.module_utils.six import raise_from
from ansible.errors import AnsibleError

try:
    from pydantic import BaseModel, model_validator, BeforeValidator
except ImportError as imp_exc:
    PYDANTIC_IMPORT_ERROR = imp_exc
else:
    PYDANTIC_IMPORT_ERROR = None

if PYDANTIC_IMPORT_ERROR:
    raise_from(
        AnsibleError('Pydantic must be installed to use this plugin. Use pip or install test-requirements.'),
        PYDANTIC_IMPORT_ERROR)

# Top level schema
# Format: ModuleMethodSchema
# 1. DcnmVpcPairQuerySchema

# replace None with default value if it throws an error
# this can happen if fields are unevenly defined across different vpc pairs
# eg: in one vpc pair, some fields are defined, in others they are not


def coerce_int_to_str(data):
    """Transform input int to str, return other types as is"""
    if isinstance(data, int):
        return str(data)
    return data


def coerce_bool_to_str(data):
    """Transform input bool to str, return other types as is"""
    if isinstance(data, bool):
        return str(data).lower()
    return data


CoercedStr = Annotated[str, BeforeValidator(coerce_int_to_str)]
CoercedBoolStr = Annotated[str, BeforeValidator(coerce_bool_to_str)]


class DcnmVpcPairQuerySchema(BaseModel):

    class NvPairs(BaseModel):
        ADMIN_STATE: Optional[CoercedBoolStr] = None
        ALLOWED_VLANS: Optional[str] = None
        DOMAIN_ID: Optional[CoercedStr] = None
        FABRIC_NAME: Optional[str] = None
        KEEP_ALIVE_HOLD_TIMEOUT: Optional[CoercedStr] = None
        KEEP_ALIVE_VRF: Optional[str] = None
        LOOPBACK_SECONDARY_IP: Optional[str] = None
        NVE_INTERFACE: Optional[CoercedStr] = None
        PC_MODE: Optional[str] = None
        PEER1_DOMAIN_CONF: Optional[str] = None
        PEER1_KEEP_ALIVE_LOCAL_IP: Optional[str] = None
        PEER1_MEMBER_INTERFACES: Optional[str] = None
        PEER1_PCID: Optional[CoercedStr] = None
        PEER1_PO_CONF: Optional[str] = None
        PEER1_PO_DESC: Optional[str] = None
        PEER1_PRIMARY_IP: Optional[str] = None
        PEER1_SOURCE_LOOPBACK: Optional[str] = None
        PEER2_DOMAIN_CONF: Optional[str] = None
        PEER2_KEEP_ALIVE_LOCAL_IP: Optional[str] = None
        PEER2_MEMBER_INTERFACES: Optional[str] = None
        PEER2_PCID: Optional[CoercedStr] = None
        PEER2_PO_CONF: Optional[str] = None
        PEER2_PO_DESC: Optional[str] = None
        PEER2_PRIMARY_IP: Optional[str] = None
        PEER2_SOURCE_LOOPBACK: Optional[str] = None
        POLICY_DESC: Optional[str] = None
        POLICY_ID: Optional[str] = None
        PRIORITY: Optional[CoercedStr] = None
        PTP: Optional[CoercedBoolStr] = None
        clear_policy: Optional[CoercedBoolStr] = None
        fabricPath_switch_id: Optional[str] = None
        isVTEPS: Optional[CoercedBoolStr] = None
        isVpcPlus: Optional[CoercedBoolStr] = None

        @model_validator(mode="after")
        @classmethod
        def sort_member_interfaces(cls, values):
            # Sort member interfaces for consistent comparison
            for peer_field in ['PEER1_MEMBER_INTERFACES', 'PEER2_MEMBER_INTERFACES']:
                interfaces = getattr(values, peer_field, None)
                if interfaces is not None and interfaces != "":
                    # Split by comma, sort, and rejoin
                    interface_list = [iface.strip() for iface in interfaces.split(',')]
                    sorted_interfaces = sorted(interface_list)
                    setattr(values, peer_field, ','.join(sorted_interfaces))
            return values

    class VpcPair(BaseModel):
        nvPairs: Optional["DcnmVpcPairQuerySchema.NvPairs"] = None
        peerOneDbId: Optional[int] = None
        peerOneId: Optional[str] = None
        peerTwoDbId: Optional[int] = None
        peerTwoId: Optional[str] = None
        templateName: Optional[str] = None
        useVirtualPeerlink: Optional[bool] = None

    failed: Optional[bool] = None
    response: Optional[List[VpcPair]] = None

    @classmethod
    def yaml_config_to_dict(cls, expected_config_data, test_fabric):
        """
        Convert YAML config to the format expected by DCNM API response
        Maps the YAML structure to the API response structure
        """
        
        # Mapping of fields in the yaml config to the fields in the DCNM API response
        # Format: {yaml_field: api_field}
        # All fields are included in the model - validation logic handles what to compare
        # ignore_extra_fields=True in validator ignores fields present in actual but not expected
        
        # response.nvPairs mapping
        profile_to_nvpairs_fields = {
            "ADMIN_STATE": "ADMIN_STATE",
            "ALLOWED_VLANS": "ALLOWED_VLANS", 
            "DOMAIN_ID": "DOMAIN_ID",
            "FABRIC_NAME": "FABRIC_NAME",
            "KEEP_ALIVE_HOLD_TIMEOUT": "KEEP_ALIVE_HOLD_TIMEOUT",
            "KEEP_ALIVE_VRF": "KEEP_ALIVE_VRF",
            "LOOPBACK_SECONDARY_IP": "LOOPBACK_SECONDARY_IP",
            "NVE_INTERFACE": "NVE_INTERFACE",
            "PC_MODE": "PC_MODE",
            "PEER1_DOMAIN_CONF": "PEER1_DOMAIN_CONF",
            "PEER1_KEEP_ALIVE_LOCAL_IP": "PEER1_KEEP_ALIVE_LOCAL_IP",
            "PEER1_MEMBER_INTERFACES": "PEER1_MEMBER_INTERFACES",
            "PEER1_PCID": "PEER1_PCID",
            "PEER1_PO_CONF": "PEER1_PO_CONF",
            "PEER1_PO_DESC": "PEER1_PO_DESC",
            "PEER1_PRIMARY_IP": "PEER1_PRIMARY_IP",
            "PEER1_SOURCE_LOOPBACK": "PEER1_SOURCE_LOOPBACK",
            "PEER2_DOMAIN_CONF": "PEER2_DOMAIN_CONF",
            "PEER2_KEEP_ALIVE_LOCAL_IP": "PEER2_KEEP_ALIVE_LOCAL_IP",
            "PEER2_MEMBER_INTERFACES": "PEER2_MEMBER_INTERFACES",
            "PEER2_PCID": "PEER2_PCID",
            "PEER2_PO_CONF": "PEER2_PO_CONF",
            "PEER2_PO_DESC": "PEER2_PO_DESC",
            "PEER2_PRIMARY_IP": "PEER2_PRIMARY_IP",
            "PEER2_SOURCE_LOOPBACK": "PEER2_SOURCE_LOOPBACK",
            "POLICY_DESC": "POLICY_DESC",
            "POLICY_ID": "POLICY_ID",
            "PRIORITY": "PRIORITY",
            "PTP": "PTP",
            "clear_policy": "clear_policy",
            "fabricPath_switch_id": "fabricPath_switch_id",
            "isVTEPS": "isVTEPS",
            "isVpcPlus": "isVpcPlus"
        }

        # Top level vpc pair fields
        vpc_pair_fields = {
            "peerOneId": "peerOneId",
            "peerTwoId": "peerTwoId", 
            "templateName": "templateName",
            # Note: deploy field doesn't map directly to API response
        }

        expected_data = {}
        expected_data["failed"] = False
        expected_data["response"] = []

        for vpc_pair in expected_config_data:
            vpc_pair_dict = {}
            
            # Map top-level VPC pair fields
            for yaml_field, api_field in vpc_pair_fields.items():
                if yaml_field in vpc_pair:
                    vpc_pair_dict[api_field] = vpc_pair[yaml_field]

            # Map profile fields to nvPairs
            vpc_pair_dict["nvPairs"] = {}
            if "profile" in vpc_pair:
                for yaml_field, api_field in profile_to_nvpairs_fields.items():
                    if yaml_field in vpc_pair["profile"]:
                        vpc_pair_dict["nvPairs"][api_field] = vpc_pair["profile"][yaml_field]

            expected_data["response"].append(vpc_pair_dict)

        return expected_data
