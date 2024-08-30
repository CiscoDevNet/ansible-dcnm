# Copyright (c) 2024 Cisco and/or its affiliates.
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

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import (
    AnsibleFailJson,
)

from ansible_collections.cisco.dcnm.plugins.modules.dcnm_sgrp_association import (
    DcnmSgrpAssociation,
)


class MockAnsibleModule:
    """
    Mock the AnsibleModule class
    """

    params = {
        "config": [],
        "state": "merged",
        "fabric": "mmudigon",
        "deploy": True,
    }
    supports_check_mode = True

    @staticmethod
    def fail_json(msg, **kwargs) -> AnsibleFailJson:
        """
        mock the fail_json method
        """
        raise AnsibleFailJson(msg, kwargs)


@pytest.fixture(name="dcnm_sgrp_association_fixture")
def dcnm_sgrp_association_fixture(monkeypatch):
    """
    mock DcnmSgrpAssociation
    """

    return DcnmSgrpAssociation(MockAnsibleModule)