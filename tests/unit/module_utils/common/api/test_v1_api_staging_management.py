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


from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.imagemanagement.rest.stagingmanagement.stagingmanagement import (
    EpImageStage, EpImageValidate, EpStageInfo)
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    does_not_raise

PATH_PREFIX = "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/stagingmanagement"


def test_ep_staging_management_00010():
    """
    ### Class
    -   EpImageStage

    ### Summary
    -   Verify path and verb
    """
    with does_not_raise():
        instance = EpImageStage()
    assert instance.path == f"{PATH_PREFIX}/stage-image"
    assert instance.verb == "POST"


def test_ep_staging_management_00020():
    """
    ### Class
    -   EpImageValidate

    ### Summary
    -   Verify path and verb
    """
    with does_not_raise():
        instance = EpImageValidate()
    assert instance.path == f"{PATH_PREFIX}/validate-image"
    assert instance.verb == "POST"


def test_ep_staging_management_00030():
    """
    ### Class
    -   EpStageInfo

    ### Summary
    -   Verify path and verb
    """
    with does_not_raise():
        instance = EpStageInfo()
    assert instance.path == f"{PATH_PREFIX}/stage-info"
    assert instance.verb == "GET"
