"""
DCNM VRF Action Plugin Test Fixtures
Generic test data for MSD (Multisite Domain) action plugin testing
"""

import json
from typing import Dict, Any, List

class DCNMVRFActionPluginFixtures:
    """Comprehensive fixtures for DCNM VRF Action Plugin testing with generic names."""
    
    # Generic fabric and configuration names
    PARENT_FABRIC = "PARENT_MSD_FABRIC"
    CHILD_FABRIC = "CHILD_FABRIC_01"
    SWITCH_IP = "10.1.1.100"
    CONTROLLER_IP = "10.10.10.1"
    SWITCH_SERIAL = "ABC123DEF456"
    SWITCH_NAME = "Switch01"
    
    @staticmethod
    def get_fabric_associations_query_response() -> Dict[str, Any]:
        """Returns fabric associations query response (success scenario)."""
        return {
            "changed": False,
            "failed": False,
            "diff": [],
            "response": [
                {
                    "attach": [
                        {
                            "switchDetailsList": [
                                {
                                    "errorMessage": None,
                                    "extensionPrototypeValues": [],
                                    "extensionValues": "",
                                    "freeformConfig": "",
                                    "instanceValues": '{"loopbackIpV6Address":"","loopbackId":"","deviceSupportL3VniNoVlan":"false","switchRouteTargetImportEvpn":"","loopbackIpAddress":"","switchRouteTargetExportEvpn":""}',
                                    "islanAttached": True,
                                    "lanAttachedState": "PENDING",
                                    "peerSerialNumber": None,
                                    "role": "leaf",
                                    "serialNumber": DCNMVRFActionPluginFixtures.SWITCH_SERIAL,
                                    "showVlan": True,
                                    "switchName": DCNMVRFActionPluginFixtures.SWITCH_NAME,
                                    "vlan": 2001,
                                    "vlanModifiable": True
                                }
                            ],
                            "templateName": "Default_VRF_Universal",
                            "vrfName": "TestVRF_Query"
                        }
                    ],
                    "parent": {
                        "defaultSGTag": None,
                        "enforce": None,
                        "fabric": DCNMVRFActionPluginFixtures.PARENT_FABRIC,
                        "hierarchicalKey": DCNMVRFActionPluginFixtures.PARENT_FABRIC,
                        "id": 12345,
                        "serviceVrfTemplate": None,
                        "source": None,
                        "tenantName": None,
                        "vrfExtensionTemplate": "Default_VRF_Extension_Universal",
                        "vrfId": 50001,
                        "vrfName": "TestVRF_Query",
                        "vrfStatus": "PENDING",
                        "vrfTemplate": "Default_VRF_Universal",
                        "vrfTemplateConfig": '{"routeTargetExportEvpn":"","routeTargetImport":"","vrfVlanId":"2001","vrfDescription":"","disableRtAuto":"false","v6VrfRouteMap":"FABRIC-RMAP-REDIST-SUBNET","vrfSegmentId":"50001","maxBgpPaths":"1","maxIbgpPaths":"2","routeTargetExport":"","ipv6LinkLocalFlag":"true","mtu":"9216","vrfRouteMap":"FABRIC-RMAP-REDIST-SUBNET","vrfVlanName":"","tag":"12345","nveId":"1","vrfIntfDescription":"","vrfName":"TestVRF_Query","routeTargetImportEvpn":""}'
                    }
                }
            ],
            "workflow": "Multisite Parent without Child Fabric Processing"
        }
    
    @staticmethod
    def get_merged_parent_with_child_failure() -> Dict[str, Any]:
        """Returns merged operation with child fabric failure."""
        return {
            "changed": True,
            "child_fabrics": [
                {
                    "changed": False,
                    "diff": [],
                    "fabric": DCNMVRFActionPluginFixtures.CHILD_FABRIC,
                    "failed": True,
                    "invocation": {
                        "module_args": {
                            "_fabric_type": "multisite_child",
                            "config": [
                                {
                                    "adv_default_routes": True,
                                    "adv_host_routes": True,
                                    "deploy": False,
                                    "l3vni_wo_vlan": False,
                                    "vrf_name": "TestVRF_Success"
                                }
                            ],
                            "fabric": DCNMVRFActionPluginFixtures.CHILD_FABRIC,
                            "state": "merged"
                        }
                    },
                    "response": []
                }
            ],
            "fabric_type": "multisite_parent",
            "msg": f"Child fabric task failed for {DCNMVRFActionPluginFixtures.CHILD_FABRIC}: MODULE FAILURE\nSee stdout/stderr for the exact error",
            "parent_fabric": {
                "changed": True,
                "diff": [
                    {
                        "attach": [
                            {
                                "deploy": True,
                                "ip_address": DCNMVRFActionPluginFixtures.SWITCH_IP,
                                "vlan_id": 2101
                            }
                        ],
                        "disable_rt_auto": False,
                        "export_evpn_rt": "",
                        "export_vpn_rt": "",
                        "import_evpn_rt": "",
                        "import_vpn_rt": "",
                        "ipv6_linklocal_enable": True,
                        "loopback_route_tag": 12345,
                        "max_bgp_paths": 1,
                        "max_ibgp_paths": 2,
                        "redist_direct_rmap": "FABRIC-RMAP-REDIST-SUBNET",
                        "service_vrf_template": None,
                        "source": None,
                        "v6_redist_direct_rmap": "FABRIC-RMAP-REDIST-SUBNET",
                        "vlan_id": 2101,
                        "vrf_description": "",
                        "vrf_extension_template": "Default_VRF_Extension_Universal",
                        "vrf_id": 50101,
                        "vrf_int_mtu": 9216,
                        "vrf_intf_desc": "",
                        "vrf_name": "TestVRF_Success",
                        "vrf_template": "Default_VRF_Universal",
                        "vrf_vlan_name": ""
                    }
                ],
                "fabric": DCNMVRFActionPluginFixtures.PARENT_FABRIC,
                "response": [
                    {
                        "DATA": {
                            "VRF Id": 50101,
                            "VRF Name": "TestVRF_Success"
                        },
                        "MESSAGE": "OK",
                        "METHOD": "POST",
                        "REQUEST_PATH": f"https://{DCNMVRFActionPluginFixtures.CONTROLLER_IP}:443/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{DCNMVRFActionPluginFixtures.PARENT_FABRIC}/vrfs",
                        "RETURN_CODE": 200
                    },
                    {
                        "DATA": {
                            f"TestVRF_Success-[{DCNMVRFActionPluginFixtures.SWITCH_SERIAL}/{DCNMVRFActionPluginFixtures.SWITCH_NAME}]": "SUCCESS"
                        },
                        "MESSAGE": "OK",
                        "METHOD": "POST",
                        "REQUEST_PATH": f"https://{DCNMVRFActionPluginFixtures.CONTROLLER_IP}:443/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{DCNMVRFActionPluginFixtures.PARENT_FABRIC}/vrfs/attachments",
                        "RETURN_CODE": 200
                    }
                ]
            },
            "workflow": "Multisite Parent with Child Fabric Processing"
        }
    
    @staticmethod
    def get_configuration_validation_failures() -> Dict[str, Dict[str, Any]]:
        """Returns all configuration validation failure scenarios."""
        return {
            "invalid_vrf_id": {
                "changed": False,
                "failed": True,
                "msg": "DcnmVrf.validate_input: Invalid parameters in playbook: vrf_id:99999999 : The item exceeds the allowed range of max 16777214",
                "workflow": "Multisite Parent without Child Fabric Processing"
            },
            "empty_vrf_name": {
                "changed": False,
                "failed": True,
                "msg": f"DcnmVrf.get_want: vrf missing mandatory key vrf_name: {{'vrf_name': '', 'attach': [{{'deploy': False, 'ip_address': '{DCNMVRFActionPluginFixtures.SWITCH_IP}', 'import_evpn_rt': '', 'export_evpn_rt': '', 'vrf_lite': None}}], 'deploy': False, 'vrf_id': 50103, 'vlan_id': 2103, 'vrf_template': 'Default_VRF_Universal', 'vrf_extension_template': 'Default_VRF_Extension_Universal'}}",
                "workflow": "Multisite Parent without Child Fabric Processing"
            },
            "invalid_vlan_id": {
                "changed": False,
                "failed": True,
                "msg": "DcnmVrf.validate_input: Invalid parameters in playbook: vlan_id:99999 : The item exceeds the allowed range of max 4094",
                "workflow": "Multisite Parent without Child Fabric Processing"
            },
            "duplicate_vrf_id": {
                "changed": False,
                "failed": True,
                "msg": {
                    "DATA": {
                        "Error": "Bad Request Error",
                        "message": "VRF ID\t50101\talready exists",
                        "path": f"/rest/top-down/fabrics/{DCNMVRFActionPluginFixtures.PARENT_FABRIC}/vrfs",
                        "status": "400",
                        "timestamp": "2025-10-17 17:01:13.534"
                    },
                    "MESSAGE": "Bad Request",
                    "METHOD": "POST",
                    "REQUEST_PATH": f"https://{DCNMVRFActionPluginFixtures.CONTROLLER_IP}:443/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{DCNMVRFActionPluginFixtures.PARENT_FABRIC}/vrfs",
                    "RETURN_CODE": 400
                },
                "workflow": "Multisite Parent without Child Fabric Processing"
            }
        }
    
    @staticmethod
    def get_fabric_related_failures() -> Dict[str, Dict[str, Any]]:
        """Returns fabric-related failure scenarios."""
        return {
            "nonexistent_fabric": {
                "failed": True,
                "msg": "{'failed': True, 'msg': \"Fabric 'NONEXISTENT_FABRIC' not found in NDFC. Available fabrics: ['FABRIC_1', 'FABRIC_2', 'PARENT_MSD_FABRIC', 'CHILD_FABRIC_01', 'STANDALONE_FABRIC']\", 'error_type': 'AnsibleError', 'operation': 'main_execution'}"
            },
            "child_direct_merged": {
                "changed": False,
                "fabric_type": "multisite_child",
                "failed": True,
                "msg": f"Task not permitted on Child Multisite fabric '{DCNMVRFActionPluginFixtures.CHILD_FABRIC}'. Please perform operations through the Parent fabric.",
                "workflow": "Child Multisite Workflow"
            },
            "child_direct_deleted": {
                "changed": False,
                "fabric_type": "multisite_child",
                "failed": True,
                "msg": f"Task not permitted on Child Multisite fabric '{DCNMVRFActionPluginFixtures.CHILD_FABRIC}'. Please perform operations through the Parent fabric.",
                "workflow": "Child Multisite Workflow"
            }
        }
    
    @staticmethod
    def get_template_attachment_failures() -> Dict[str, Dict[str, Any]]:
        """Returns template and attachment failure scenarios."""
        return {
            "invalid_template": {
                "changed": False,
                "failed": True,
                "msg": {
                    "DATA": {
                        "Error": "Bad Request Error",
                        "message": "Invalid VRF Template : NONEXISTENT_TEMPLATE",
                        "path": f"/rest/top-down/fabrics/{DCNMVRFActionPluginFixtures.PARENT_FABRIC}/vrfs",
                        "status": "400",
                        "timestamp": "2025-10-17 17:01:20.171"
                    },
                    "MESSAGE": "Bad Request",
                    "METHOD": "POST",
                    "REQUEST_PATH": f"https://{DCNMVRFActionPluginFixtures.CONTROLLER_IP}:443/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{DCNMVRFActionPluginFixtures.PARENT_FABRIC}/vrfs",
                    "RETURN_CODE": 400
                },
                "workflow": "Multisite Parent without Child Fabric Processing"
            },
            "invalid_switch_ip": {
                "changed": False,
                "failed": True,
                "msg": '{"Error": "Given switch elem = \\"10.255.255.255\\" cannot be validated, provide a valid ip_sn object\\n"}',
                "workflow": "Multisite Parent without Child Fabric Processing"
            },
            "nonexistent_switch": {
                "changed": False,
                "failed": True,
                "msg": f"DcnmVrf.update_attach_params: caller: get_want. Fabric {DCNMVRFActionPluginFixtures.PARENT_FABRIC} does not contain switch 10.9.9.9",
                "workflow": "Multisite Parent without Child Fabric Processing"
            }
        }
    
    @staticmethod
    def get_fabric_associations_data() -> List[Dict[str, Any]]:
        """Returns mock fabric associations data."""
        return [
            {
                "fabricName": DCNMVRFActionPluginFixtures.PARENT_FABRIC,
                "fabricType": "MSD",
                "fabricState": "msd",
                "fabricId": 12345
            },
            {
                "fabricName": DCNMVRFActionPluginFixtures.CHILD_FABRIC,
                "fabricType": "Switch_Fabric", 
                "fabricState": "member",
                "fabricId": 12346,
                "parentFabricName": DCNMVRFActionPluginFixtures.PARENT_FABRIC,
                "fabricParent": DCNMVRFActionPluginFixtures.PARENT_FABRIC
            },
            {
                "fabricName": "STANDALONE_FABRIC",
                "fabricType": "Switch_Fabric",
                "fabricState": "standalone",
                "fabricId": 12347
            }
        ]
    
    @staticmethod
    def get_module_args_successful_merged() -> Dict[str, Any]:
        """Returns module args for successful merged operation."""
        return {
            "fabric": DCNMVRFActionPluginFixtures.PARENT_FABRIC,
            "state": "merged",
            "config": [
                {
                    "vrf_name": "TestVRF_Success",
                    "vrf_id": 50101,
                    "vlan_id": 2101,
                    "vrf_template": "Default_VRF_Universal",
                    "vrf_extension_template": "Default_VRF_Extension_Universal",
                    "attach": [
                        {
                            "ip_address": DCNMVRFActionPluginFixtures.SWITCH_IP,
                            "deploy": False
                        }
                    ],
                    "deploy": False
                }
            ]
        }
    
    @staticmethod
    def get_module_args_query() -> Dict[str, Any]:
        """Returns module args for query operation."""
        return {
            "fabric": DCNMVRFActionPluginFixtures.PARENT_FABRIC,
            "state": "query",
            "config": []
        }
    
    @staticmethod
    def get_module_args_invalid_vrf_id() -> Dict[str, Any]:
        """Returns module args with invalid VRF ID."""
        return {
            "fabric": DCNMVRFActionPluginFixtures.PARENT_FABRIC,
            "state": "merged",
            "config": [
                {
                    "vrf_name": "TestVRF_InvalidID",
                    "vrf_id": 99999999,  # Invalid - exceeds max
                    "vlan_id": 2102,
                    "vrf_template": "Default_VRF_Universal",
                    "attach": [
                        {
                            "ip_address": DCNMVRFActionPluginFixtures.SWITCH_IP
                        }
                    ],
                    "deploy": False
                }
            ]
        }
    
    @staticmethod
    def get_module_args_child_fabric_direct() -> Dict[str, Any]:
        """Returns module args for direct child fabric access (should fail)."""
        return {
            "fabric": DCNMVRFActionPluginFixtures.CHILD_FABRIC,
            "state": "merged",
            "config": [
                {
                    "vrf_name": "TestVRF_Child",
                    "vrf_id": 50201,
                    "vlan_id": 2201,
                    "vrf_template": "Default_VRF_Universal"
                }
            ]
        }
    
    @staticmethod
    def get_all_fixtures() -> Dict[str, Any]:
        """Returns complete fixture data structure."""
        return {
            "metadata": {
                "generated_date": "2025-10-17T16:33:54Z",
                "parent_fabric": DCNMVRFActionPluginFixtures.PARENT_FABRIC,
                "child_fabric": DCNMVRFActionPluginFixtures.CHILD_FABRIC,
                "switch_ip": DCNMVRFActionPluginFixtures.SWITCH_IP,
                "controller": DCNMVRFActionPluginFixtures.CONTROLLER_IP,
                "action_plugin_version": "enhanced_multisite_support_with_comprehensive_failures"
            },
            "success_responses": {
                "fabric_associations": DCNMVRFActionPluginFixtures.get_fabric_associations_query_response(),
                "merged_parent": DCNMVRFActionPluginFixtures.get_merged_parent_with_child_failure()
            },
            "failure_responses": {
                "configuration_validation": DCNMVRFActionPluginFixtures.get_configuration_validation_failures(),
                "fabric_related": DCNMVRFActionPluginFixtures.get_fabric_related_failures(),
                "template_attachment": DCNMVRFActionPluginFixtures.get_template_attachment_failures()
            },
            "fabric_associations": DCNMVRFActionPluginFixtures.get_fabric_associations_data(),
            "module_args": {
                "successful_merged": DCNMVRFActionPluginFixtures.get_module_args_successful_merged(),
                "query": DCNMVRFActionPluginFixtures.get_module_args_query(),
                "invalid_vrf_id": DCNMVRFActionPluginFixtures.get_module_args_invalid_vrf_id(),
                "child_fabric_direct": DCNMVRFActionPluginFixtures.get_module_args_child_fabric_direct()
            }
        }

# Usage example:
if __name__ == "__main__":
    fixtures = DCNMVRFActionPluginFixtures()
    
    # Get specific failure type
    config_failures = fixtures.get_configuration_validation_failures()
    print("Configuration validation failures:")
    for failure_type, failure_data in config_failures.items():
        print(f"  {failure_type}: {failure_data.get('msg', 'No message')}")
    
    # Get all fixtures
    all_fixtures = fixtures.get_all_fixtures()
    print(f"\nTotal fixture categories: {len(all_fixtures['failure_responses'])}")