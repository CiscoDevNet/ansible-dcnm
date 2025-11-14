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


from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.imagemanagement.rest.imageupgrade.imageupgrade import (
    EpInstallOptions, EpUpgradeImage)
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    does_not_raise

PATH_PREFIX = "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/imageupgrade"


def test_ep_install_options_00010():
    """
    ### Class
    -   EpInstallOptions

    ### Summary
    -   Verify path and verb
    """
    with does_not_raise():
        instance = EpInstallOptions()
    assert instance.path == f"{PATH_PREFIX}/install-options"
    assert instance.verb == "POST"


def test_ep_upgrade_image_00010():
    """
    ### Class
    -   EpUpgradeImage

    ### Summary
    -   Verify path and verb
    """
    with does_not_raise():
        instance = EpUpgradeImage()
    assert instance.path == f"{PATH_PREFIX}/upgrade-image"
    assert instance.verb == "POST"
