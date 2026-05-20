# Copyright (c) 2026 Cisco and/or its affiliates.
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

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

from ansible_collections.cisco.dcnm.plugins.module_utils.common.action_error_handler import ActionErrorHandler
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    obtain_federated_fabric_associations,
)


class MockLogger:
    def debug(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass

    def info(self, *args, **kwargs):
        pass


class MockActionModule:
    def __init__(self, response, ndfc_version=12.2):
        self.error_handler = ActionErrorHandler(MockLogger())
        self.logger = MockLogger()
        self.ndfc_version = ndfc_version
        self.response = response

    def _execute_module(self, **kwargs):
        return self.response


def test_obtain_federated_fabric_associations_handles_stringified_failure_msg():
    """
    Verify Ansible Core versions that return failed module msg as a stringified
    dict do not trigger AttributeError during fabric discovery.
    """
    response = {
        "failed": True,
        "msg": (
            "{'RETURN_CODE': 503, 'METHOD': 'GET', "
            "'REQUEST_PATH': 'https://controller/appcenter/cisco/ndfc/api/v1/onemanage/fabrics', "
            "'MESSAGE': 'Service Unavailable', "
            "'DATA': 'Invalid JSON response: this API is allowed only for remote user'}"
        ),
    }
    action_module = MockActionModule(response)

    result = obtain_federated_fabric_associations(action_module, {}, None)

    assert result == "A federation manager does not exist"


def test_obtain_federated_fabric_associations_handles_json_string_response():
    """
    Verify string JSON responses are normalized before API response validation.
    """
    response = json.dumps(
        {
            "response": {
                "RETURN_CODE": 200,
                "MESSAGE": "OK",
                "DATA": [
                    {
                        "fabricName": "parent",
                        "fabricType": "Federated",
                        "fabricState": "parent",
                        "members": [
                            {
                                "fabricName": "child",
                                "clusterName": "cluster-1",
                                "fabricType": "VXLAN",
                                "fabricState": "member",
                            }
                        ],
                    }
                ],
            }
        }
    )
    action_module = MockActionModule(response)

    result = obtain_federated_fabric_associations(action_module, {}, None)

    assert result["parent"]["fabricType"] == "Federated"
    assert result["child"]["clusterName"] == "cluster-1"
