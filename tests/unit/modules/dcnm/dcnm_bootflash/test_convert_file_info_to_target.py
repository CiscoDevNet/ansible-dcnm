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
# pylint: disable=unused-import, protected-access, use-implicit-booleaness-not-comparison

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

from ansible_collections.cisco.dcnm.plugins.module_utils.bootflash.convert_file_info_to_target import \
    ConvertFileInfoToTarget
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_maintenance_mode.utils import \
    does_not_raise


def test_convert_file_info_to_target_00000() -> None:
    """
    ### Classes and Methods
    - ConvertFileInfoToTarget()
        - __init__()

    ### Summary
    - Verify class attributes are initialized to expected values.

    ### Test
    -   Class attributes are initialized to expected values.
    -   Exceptions are not not raised.
    """
    with does_not_raise():
        instance = ConvertFileInfoToTarget()
    assert instance.action == "convert_file_info_to_target"
    assert instance.class_name == "ConvertFileInfoToTarget"

    assert instance._file_info is None
    assert instance._filename is None
    assert instance._filepath is None
    assert instance._ip_address is None
    assert instance._serial_number is None
    assert instance._supervisor is None
    assert instance._target is None
    assert instance.timestamp_format == "%b %d %H:%M:%S %Y"
