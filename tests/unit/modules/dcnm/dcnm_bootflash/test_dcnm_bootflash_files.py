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

# See the following regarding *_fixture imports
# https://pylint.pycqa.org/en/latest/user_guide/messages/warning/redefined-outer-name.html
# Due to the above, we also need to disable unused-import
# Also, fixtures need to use *args to match the signature of the function they are mocking
# pylint: disable=unused-import, protected-access

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

from ansible_collections.cisco.dcnm.plugins.module_utils.bootflash.bootflash_files import \
    BootflashFiles
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_maintenance_mode.utils import \
    does_not_raise


def test_bootflash_files_00000() -> None:
    """
    ### Classes and Methods
    - BootflashFiles()
        - __init__()

    ### Summary
    - Verify class attributes are initialized to expected values.

    ### Test
    -   Class attributes are initialized to expected values.
    -   Exceptions are not not raised.
    """
    with does_not_raise():
        instance = BootflashFiles()
    assert instance.action == "bootflash_delete"
    assert instance.class_name == "BootflashFiles"
    assert instance.conversion.class_name == "ConversionUtils"
    assert instance.diff == {}  # pylint: disable=use-implicit-booleaness-not-comparison
    assert instance.ep_bootflash_files.class_name == "EpBootflashFiles"
    assert instance.ok_to_delete_files_reason is None
    assert instance.payload == {"deleteFiles": []}
    assert instance.filename is None
    assert instance.filepath is None
    assert instance.filesize is None
    assert instance.ip_address is None
    assert instance.partition is None
    assert instance._rest_send is None
    assert instance._results is None
    assert instance.supervisor is None
    assert instance.switch_details is None
    assert instance.target is None
