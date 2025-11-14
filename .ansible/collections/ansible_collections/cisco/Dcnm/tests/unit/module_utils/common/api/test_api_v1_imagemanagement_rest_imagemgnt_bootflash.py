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


from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.imagemanagement.rest.imagemgnt.bootflash.bootflash import \
    EpBootflashInfo
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    does_not_raise

PATH_PREFIX = "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/imagemgnt"


def test_ep_image_mgnt_00010():
    """
    ### Class
    -   EpBootflashInfo

    ### Summary
    -   Verify path and verb
    """
    with does_not_raise():
        instance = EpBootflashInfo()
        instance.serial_number = "1234567890"
    assert instance.path == f"{PATH_PREFIX}/bootFlash/bootflash-info?serialNumber=1234567890"
    assert instance.verb == "GET"
