# -*- coding: utf-8 -*-
# @author: Allen Robel
# @file: plugins/module_utils/vrf/vrf_playbook_model.py
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
Validation model for VRF attachment payload.
"""
import json
from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from ..common.models.ipv4_cidr_host import IPv4CidrHostModel
from ..common.models.ipv4_host import IPv4HostModel
from ..common.models.ipv6_cidr_host import IPv6CidrHostModel


class PayloadVrfsAttachmentsLanAttachListExtensionValuesMultisiteConn(BaseModel):
    """
    # Summary

    Represents the multisite connection values for a single lan attach item within VrfAttachPayload.lan_attach_list.

    # Structure

    - MULTISITE_CONN: list, alias: MULTISITE_CONN

    ## Example

    ```json
    {
        "MULTISITE_CONN": []
    }
    }
    ```
    """

    MULTISITE_CONN: list = Field(alias="MULTISITE_CONN", default_factory=list)


class PayloadVrfsAttachmentsLanAttachListExtensionValuesVrfLiteConnItem(BaseModel):
    """
    # Summary

    Represents a single VRF Lite connection item within VrfAttachPayload.lan_attach_list.

    # Structure

    - AUTO_VRF_LITE_FLAG: bool, alias: AUTO_VRF_LITE_FLAG
    - DOT1Q_ID: str, alias: DOT1Q_ID
    - IF_NAME: str, alias: IF_NAME
    - IP_MASK: str, alias: IP_MASK
    - IPV6_MASK: str, alias: IPV6_MASK
    - IPV6_NEIGHBOR: str, alias: IPV6_NEIGHBOR
    - NEIGHBOR_ASN: str, alias: NEIGHBOR_ASN
    - NEIGHBOR_IP: str, alias: NEIGHBOR_IP
    - PEER_VRF_NAME: str, alias: PEER_VRF_NAME
    - VRF_LITE_JYTHON_TEMPLATE: str, alias: VRF_LITE_JYTHON_TEMPLATE

    ## Example

    ```json
    {
        "AUTO_VRF_LITE_FLAG": "true",
        "DOT1Q_ID": "2",
        "IF_NAME": "Ethernet2/10",
        "IP_MASK": "10.33.0.2/30",
        "IPV6_MASK": "2010::10:34:0:7/64",
        "IPV6_NEIGHBOR": "2010::10:34:0:3",
        "NEIGHBOR_ASN": "65001",
        "NEIGHBOR_IP": "10.33.0.1",
        "PEER_VRF_NAME": "ansible-vrf-int1",
        "VRF_LITE_JYTHON_TEMPLATE": "Ext_VRF_Lite_Jython"
    }
    ```
    """

    AUTO_VRF_LITE_FLAG: bool = Field(alias="AUTO_VRF_LITE_FLAG", default=True)
    DOT1Q_ID: str = Field(alias="DOT1Q_ID")
    IF_NAME: str = Field(alias="IF_NAME")
    IP_MASK: str = Field(alias="IP_MASK", default="")
    IPV6_MASK: str = Field(alias="IPV6_MASK", default="")
    IPV6_NEIGHBOR: str = Field(alias="IPV6_NEIGHBOR", default="")
    NEIGHBOR_ASN: str = Field(alias="NEIGHBOR_ASN", default="")
    NEIGHBOR_IP: str = Field(alias="NEIGHBOR_IP", default="")
    PEER_VRF_NAME: str = Field(alias="PEER_VRF_NAME", default="")
    VRF_LITE_JYTHON_TEMPLATE: str = Field(alias="VRF_LITE_JYTHON_TEMPLATE")

    @field_validator("IP_MASK", mode="before")
    @classmethod
    def validate_ip_mask(cls, value: str) -> str:
        """
        Validate IP_MASK to ensure it is a valid IPv4 CIDR host address.
        """
        if value == "":
            return value
        try:
            return IPv4CidrHostModel(ipv4_cidr_host=value).ipv4_cidr_host
        except ValueError as error:
            msg = f"Invalid IP_MASK: {value}. detail: {error}"
            raise ValueError(msg) from error

    @field_validator("IPV6_MASK", mode="before")
    @classmethod
    def validate_ipv6_mask(cls, value: str) -> str:
        """
        Validate IPV6_MASK to ensure it is a valid IPv6 CIDR host address.
        """
        if value == "":
            return value
        try:
            return IPv6CidrHostModel(ipv6_cidr_host=value).ipv6_cidr_host
        except ValueError as error:
            msg = f"Invalid IPV6_MASK: {value}. detail: {error}"
            raise ValueError(msg) from error

    @field_validator("NEIGHBOR_IP", mode="before")
    @classmethod
    def validate_neighbor_ip(cls, value: str) -> str:
        """
        Validate NEIGHBOR_IP to ensure it is a valid IPv4 host address without prefix length.
        """
        if value == "":
            return value
        try:
            return IPv4HostModel(ipv4_host=value).ipv4_host
        except ValueError as error:
            msg = f"Invalid neighbor IP address (NEIGHBOR_IP): {value}. detail: {error}"
            raise ValueError(msg) from error

    @field_serializer("AUTO_VRF_LITE_FLAG")
    def serialize_auto_vrf_lite_flag(self, value) -> str:
        """
        Serialize AUTO_VRF_LITE_FLAG to a string representation.
        """
        return str(value).lower()


class PayloadVrfsAttachmentsLanAttachListExtensionValuesVrfLiteConn(BaseModel):
    """
    # Summary

    Represents a list of PayloadVrfsAttachmentsLanAttachListExtensionValuesVrfLiteConnItem.

    # Structure

    - VRF_LITE_CONN: list[PayloadVrfsAttachmentsLanAttachListExtensionValuesVrfLiteConnItem], alias: VRF_LITE_CONN

    ## Example

    ```json
    {
        "VRF_LITE_CONN": [
            {
                "AUTO_VRF_LITE_FLAG": "true",
                "DOT1Q_ID": "2",
                "IF_NAME": "Ethernet2/10",
                "IP_MASK": "10.33.0.2/30",
                "IPV6_MASK": "2010::10:34:0:7/64",
                "IPV6_NEIGHBOR": "2010::10:34:0:3",
                "NEIGHBOR_ASN": "65001",
                "NEIGHBOR_IP": "10.33.0.1",
                "PEER_VRF_NAME": "ansible-vrf-int1",
                "VRF_LITE_JYTHON_TEMPLATE": "Ext_VRF_Lite_Jython"
            }
        ]
    }
    ```
    """

    VRF_LITE_CONN: list[PayloadVrfsAttachmentsLanAttachListExtensionValuesVrfLiteConnItem] = Field(alias="VRF_LITE_CONN", default_factory=list)


class PayloadVrfsAttachmentsLanAttachListExtensionValues(BaseModel):
    """
    # Summary

    Represents the extension values for a single lan attach item within VrfAttachPayload.lan_attach_list.

    # Structure

    # Example

    ```json
    {
        'MULTISITE_CONN': {'MULTISITE_CONN': []},
        'VRF_LITE_CONN': {
            'VRF_LITE_CONN': [
                {
                    'AUTO_VRF_LITE_FLAG': 'true',
                    'DOT1Q_ID': '2',
                    'IF_NAME': 'Ethernet2/10',
                    'IP_MASK': '10.33.0.2/30',
                    'IPV6_MASK': '2010::10:34:0:7/64',
                    'IPV6_NEIGHBOR': '2010::10:34:0:3',
                    'NEIGHBOR_ASN': '65001',
                    'NEIGHBOR_IP': '10.33.0.1',
                    'PEER_VRF_NAME': 'ansible-vrf-int1',
                    'VRF_LITE_JYTHON_TEMPLATE': 'Ext_VRF_Lite_Jython'
                }
            ]
        }
    }
    ```
    """

    MULTISITE_CONN: PayloadVrfsAttachmentsLanAttachListExtensionValuesMultisiteConn = Field(
        alias="MULTISITE_CONN",
        default_factory=PayloadVrfsAttachmentsLanAttachListExtensionValuesMultisiteConn,
    )
    VRF_LITE_CONN: PayloadVrfsAttachmentsLanAttachListExtensionValuesVrfLiteConn = Field(
        alias="VRF_LITE_CONN",
        default_factory=PayloadVrfsAttachmentsLanAttachListExtensionValuesVrfLiteConn,
    )

    @field_serializer("MULTISITE_CONN")
    def serialize_multisite_conn(self, value: PayloadVrfsAttachmentsLanAttachListExtensionValuesMultisiteConn) -> str:
        """
        Serialize MULTISITE_CONN to a JSON string.
        """
        return value.model_dump_json(by_alias=True)

    @field_serializer("VRF_LITE_CONN")
    def serialize_vrf_lite_conn(self, value: PayloadVrfsAttachmentsLanAttachListExtensionValuesVrfLiteConn) -> str:
        """
        Serialize VRF_LITE_CONN to a JSON string.
        """
        return value.model_dump_json(by_alias=True)

    @field_validator("MULTISITE_CONN", mode="before")
    @classmethod
    def preprocess_multisite_conn(cls, value: Union[str, dict]) -> Optional[PayloadVrfsAttachmentsLanAttachListExtensionValuesMultisiteConn]:
        """
        Convert incoming data

        - If data is a JSON string, use json.loads() to convert to a dict.
        - If data is a dict, return it as is.
        """
        if isinstance(value, str):
            if value == "":
                return ""
            return json.loads(value)
        return value

    @field_validator("VRF_LITE_CONN", mode="before")
    @classmethod
    def preprocess_vrf_lite_conn(cls, value: dict) -> Optional[PayloadVrfsAttachmentsLanAttachListExtensionValuesVrfLiteConn]:
        """
        Convert incoming data

        - If data is a JSON string, use json.loads() to convert to a dict.
        - If data is a dict, return it as is.
        """
        if isinstance(value, str):
            if value == "":
                return ""
            return json.loads(value)
        return value


class PayloadVrfsAttachmentsLanAttachListInstanceValues(BaseModel):
    """
    # Summary

    Represents the instance values for a single lan attach item within VrfAttachPayload.lan_attach_list.

    # Structure

    - loopback_id: str, alias: loopbackId
    - loopback_ip_address: str, alias: loopbackIpAddress
    - loopback_ip_v6_address: str, alias: loopbackIpV6Address
    - switch_route_target_import_evpn: str, alias: switchRouteTargetImportEvpn
    - switch_route_target_export_evpn: str, alias: switchRouteTargetExportEvpn

    ## Example

    ```json
        {
            "loopbackId": "1",
            "loopbackIpAddress": "10.1.1.1",
            "loopbackIpV6Address": "f16c:f7ec:cfa2:e1c5:9a3c:cb08:801f:36b8",
            "switchRouteTargetImportEvpn": "5000:100",
            "switchRouteTargetExportEvpn": "5000:100"
        }
    ```
    """

    loopback_id: str = Field(alias="loopbackId", default="")
    loopback_ip_address: str = Field(alias="loopbackIpAddress", default="")
    loopback_ipv6_address: str = Field(alias="loopbackIpV6Address", default="")
    switch_route_target_import_evpn: str = Field(alias="switchRouteTargetImportEvpn", default="")
    switch_route_target_export_evpn: str = Field(alias="switchRouteTargetExportEvpn", default="")

    @field_validator("loopback_ip_address", mode="before")
    @classmethod
    def validate_loopback_ip_address(cls, value: str) -> str:
        """
        Validate loopback_ip_address to ensure it is a valid IPv4 CIDR host.
        """
        if value == "":
            return value
        try:
            return IPv4CidrHostModel(ipv4_cidr_host=value).ipv4_cidr_host
        except ValueError as error:
            msg = f"Invalid loopback IP address (loopback_ip_address): {value}. detail: {error}"
            raise ValueError(msg) from error

    @field_validator("loopback_ipv6_address", mode="before")
    @classmethod
    def validate_loopback_ipv6_address(cls, value: str) -> str:
        """
        Validate loopback_ipv6_address to ensure it is a valid IPv6 CIDR host.
        """
        if value == "":
            return value
        try:
            return IPv6CidrHostModel(ipv6_cidr_host=value).ipv6_cidr_host
        except ValueError as error:
            msg = f"Invalid loopback IPv6 address (loopback_ipv6_address): {value}. detail: {error}"
            raise ValueError(msg) from error


class PayloadVrfsAttachmentsLanAttachListItem(BaseModel):
    """
    # Summary

    A single lan attach item within VrfAttachPayload.lan_attach_list.

    # Structure

    - deployment: bool, alias: deployment, default=False
    - extension_values: Optional[str], alias: extensionValues, default=""
    - fabric: str (min_length=1, max_length=64), alias: fabric
    - freeform_config: Optional[str], alias: freeformConfig, default=""
    - instance_values: Optional[str], alias: instanceValues, default=""
    - serial_number: str, alias: serialNumber
    - vlan_id: int, alias: vlanId
    - vrf_name: str (min_length=1, max_length=32), alias: vrfName

    ## Notes

    1. extensionValues in the example is shortened for brevity.  It is a JSON string with the following structure::

    ```json
    {
        'MULTISITE_CONN': {'MULTISITE_CONN': []},
        'VRF_LITE_CONN': {
            'VRF_LITE_CONN': [
                {
                    'AUTO_VRF_LITE_FLAG': 'true',
                    'DOT1Q_ID': '2',
                    'IF_NAME': 'Ethernet2/10',
                    'IP_MASK': '10.33.0.2/30',
                    'IPV6_MASK': '2010::10:34:0:7/64',
                    'IPV6_NEIGHBOR': '2010::10:34:0:3',
                    'NEIGHBOR_ASN': '65001',
                    'NEIGHBOR_IP': '10.33.0.1',
                    'PEER_VRF_NAME': 'ansible-vrf-int1',
                    'VRF_LITE_JYTHON_TEMPLATE': 'Ext_VRF_Lite_Jython'
                }
            ]
        }
    }
    ```

    2. instanceValues in the example is shortened for brevity. It is a JSON string with the following fields:

    - It has the following structure:


    - instanceValues in the example is shortened for brevity. It is a JSON string with the following fields:
    - loopbackId: str
    - loopbackIpAddress: str
    - loopbackIpV6Address: str
    - switchRouteTargetImportEvpn: str
    - switchRouteTargetExportEvpn: str
    ## Example

    ```json
        {
            "deployment": true,
            "extensionValues": "{\"field1\":\"field1_value\",\"field2\":\"field2_value\"}",
            "fabric": "f1",
            "freeformConfig": "",
            "instanceValues": "{\"field1\":\"field1_value\",\"field2\":\"field2_value\"}",
            "serialNumber": "FOX2109PGD0",
            "vlan": 0,
            "vrfName": "ansible-vrf-int1"
        }
    ```
    """

    deployment: bool = Field(alias="deployment")
    extension_values: Optional[PayloadVrfsAttachmentsLanAttachListExtensionValues] = Field(
        alias="extensionValues",
        default=PayloadVrfsAttachmentsLanAttachListExtensionValues.model_construct(),
    )
    fabric: str = Field(alias="fabric", min_length=1, max_length=64)
    freeform_config: Optional[str] = Field(alias="freeformConfig", default="")
    instance_values: Optional[PayloadVrfsAttachmentsLanAttachListInstanceValues] = Field(alias="instanceValues", default="")
    serial_number: str = Field(alias="serialNumber")
    vlan: int = Field(alias="vlan")
    vrf_name: str = Field(alias="vrfName", min_length=1, max_length=32)

    @field_validator("extension_values", mode="before")
    @classmethod
    def preprocess_extension_values(cls, value: Union[dict, str]) -> PayloadVrfsAttachmentsLanAttachListExtensionValues:
        """
        # Summary

        - If data is a JSON string, use json.loads() to convert to a dict and pipe it to the model.
        - If data is an empty string, return an empty PayloadVrfsAttachmentsLanAttachListExtensionValues instance.
        - If data is a dict, pipe it to the model.
        - If data is already a PayloadVrfsAttachmentsLanAttachListExtensionValues instance, return it as is.

        # Raises
        - ValueError: If the value is not a valid type (not dict, str, or PayloadVrfsAttachmentsLanAttachListExtensionValues).
        - ValueError: If the JSON string cannot be parsed into a dictionary.
        """
        if isinstance(value, str):
            if value == "":
                return PayloadVrfsAttachmentsLanAttachListExtensionValues.model_construct()
            try:
                value = json.loads(value)
                return PayloadVrfsAttachmentsLanAttachListExtensionValues(**value)
            except json.JSONDecodeError as error:
                msg = f"Invalid JSON string for extension_values: {value}. detail: {error}"
                raise ValueError(msg) from error
        if isinstance(value, dict):
            return PayloadVrfsAttachmentsLanAttachListExtensionValues(**value)
        if isinstance(value, PayloadVrfsAttachmentsLanAttachListExtensionValues):
            return value
        msg = f"Invalid type for extension_values: {type(value)}. "
        msg += "Expected dict, str, or PayloadVrfsAttachmentsLanAttachListExtensionValues."
        raise ValueError(msg)

    @field_serializer("extension_values")
    def serialize_extension_values(self, value: PayloadVrfsAttachmentsLanAttachListExtensionValues) -> str:
        """
        Serialize extension_values to a JSON string.
        """
        if value == "":
            return json.dumps({})
        if len(value.MULTISITE_CONN.MULTISITE_CONN) == 0 and len(value.VRF_LITE_CONN.VRF_LITE_CONN) == 0:
            return json.dumps({})
        result = {}
        if len(value.MULTISITE_CONN.MULTISITE_CONN) == 0 and len(value.VRF_LITE_CONN.VRF_LITE_CONN) == 0:
            return json.dumps(result)
        result["MULTISITE_CONN"] = value.MULTISITE_CONN.model_dump_json(by_alias=True)
        result["VRF_LITE_CONN"] = value.VRF_LITE_CONN.model_dump_json(by_alias=True)
        return json.dumps(result)

    @field_serializer("instance_values")
    def serialize_instance_values(self, value: PayloadVrfsAttachmentsLanAttachListInstanceValues) -> str:
        """
        Serialize instance_values to a JSON string.
        """
        if value == "":
            return json.dumps({})
        return value.model_dump_json(by_alias=True)


class PayloadVrfsAttachments(BaseModel):
    """
    # Summary

    Represents a POST payload for the following endpoint:

    api.v1.lan_fabric.rest.top_down.fabrics.vrfs.Vrfs.EpVrfPost

    /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/test_fabric/vrfs/attachments

    See NdfcVrf12.push_diff_attach

    ## Structure

    - lan_attach_list: list[PayloadVrfsAttachmentsLanAttachListItem]
    - vrf_name: str

    ## Example payload

    ```json
    {
        "lanAttachList": [
            {
                "deployment": true,
                "extensionValues": "",
                "fabric": "test_fabric",
                "freeformConfig": "",
                "instanceValues": "{\"loopbackId\":\"\"}", # content removed for brevity
                "serialNumber": "XYZKSJHSMK1",
                "vlan": 0,
                "vrfName": "test_vrf_1"
            },
       ],
        "vrfName": "test_vrf"
    }
    ```
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        validate_by_alias=True,
        validate_by_name=True,
    )

    lan_attach_list: list[PayloadVrfsAttachmentsLanAttachListItem] = Field(alias="lanAttachList")
    vrf_name: str = Field(alias="vrfName", min_length=1, max_length=32)
