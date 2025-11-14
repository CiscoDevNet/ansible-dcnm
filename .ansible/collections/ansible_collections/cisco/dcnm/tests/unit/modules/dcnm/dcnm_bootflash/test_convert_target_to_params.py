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

import inspect

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.bootflash.convert_target_to_params import \
    ConvertTargetToParams
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_bootflash.utils import (
    does_not_raise, targets)


def test_convert_target_to_params_00000() -> None:
    """
    ### Classes and Methods
    - ConvertTargetToParams()
        - __init__()

    ### Summary
    - Verify class attributes are initialized to expected values.

    ### Test
    -   Class attributes are initialized to expected values.
    -   Exceptions are not not raised.
    """
    with does_not_raise():
        instance = ConvertTargetToParams()
    assert instance.action == "convert_target_to_params"
    assert instance.class_name == "ConvertTargetToParams"

    assert instance._filename is None
    assert instance._filepath is None
    assert instance._target is None
    assert instance._partition is None
    assert instance._supervisor is None
    assert instance.committed is False


def test_convert_target_to_params_00100() -> None:
    """
    ### Classes and Methods
    - ConvertTargetToParams()
        - commit()

    ### Summary
    - Verify commit() happy path.
    - File located in top-level (root) of bootflash.

    ### Test
    -   Given a property-constructed target dict, getter properties are set
        to expected values.
    -   Exceptions are not not raised.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = ConvertTargetToParams()
        instance.target = targets(f"{key}")
        instance.commit()

    assert instance.target == targets(f"{key}")
    assert instance.filename == "air.txt"
    assert instance.filepath == "bootflash:"
    assert instance.partition == "bootflash:"
    assert instance.supervisor == "active"


def test_convert_target_to_params_00110() -> None:
    """
    ### Classes and Methods
    - ConvertTargetToParams()
        - commit()

    ### Summary
    - Verify commit() happy path.
    - File located in directory on bootflash.

    ### Test
    -   Given a property-constructed target dict, getter properties are set
        to expected values.
    -   Exceptions are not not raised.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = ConvertTargetToParams()
        instance.target = targets(f"{key}")
        instance.commit()

    assert instance.target == targets(f"{key}")
    assert instance.filename == "air.txt"
    assert instance.filepath == "bootflash:/foo/"
    assert instance.partition == "bootflash:"
    assert instance.supervisor == "active"


def test_convert_target_to_params_00120() -> None:
    """
    ### Classes and Methods
    - ConvertTargetToParams()
        - commit()

    ### Summary
    Verify ``ValueError`` is raised when commit() is called prior to setting
    ``target``.

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectation.
    """
    with does_not_raise():
        instance = ConvertTargetToParams()

    match = r"ConvertTargetToParams\.commit:\s+"
    match += r"target must be set before calling commit\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_convert_target_to_params_00200() -> None:
    """
    ### Classes and Methods
    - ConvertTargetToParams()
        - commit()
        - parse_target()

    ### Summary
    Verify ``parse_target()`` raises ``ValueError`` if ``target`` is missing
    ``filepath`` key.

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = ConvertTargetToParams()
        instance.target = targets(f"{key}")

    match = r"ConvertTargetToParams\.parse_target:\s+"
    match += r"Expected filepath in target dict. Got.*\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_convert_target_to_params_00210() -> None:
    """
    ### Classes and Methods
    - ConvertTargetToParams()
        - commit()
        - parse_target()

    ### Summary
    Verify ``parse_target()`` raises ``ValueError`` if ``target`` is missing
    ``supervisor`` key.

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = ConvertTargetToParams()
        instance.target = targets(f"{key}")

    match = r"ConvertTargetToParams\.parse_target:\s+"
    match += r"Expected supervisor in target dict. Got.*\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_convert_target_to_params_00300() -> None:
    """
    ### Classes and Methods
    - ConvertTargetToParams()
        - filename

    ### Summary
    Verify ``filename`` raises ``ValueError`` if accessed before ``commit()``
    is called.

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectation.
    """
    with does_not_raise():
        instance = ConvertTargetToParams()

    match = r"ConvertTargetToParams.filename:\s+"
    match += r"commit\(\) must be called before accessing filename\."
    with pytest.raises(ValueError, match=match):
        instance.filename  # pylint: disable=pointless-statement


def test_convert_target_to_params_00400() -> None:
    """
    ### Classes and Methods
    - ConvertTargetToParams()
        - filepath

    ### Summary
    Verify ``filepath`` raises ``ValueError`` if accessed before ``commit()``
    is called.

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectation.
    """
    with does_not_raise():
        instance = ConvertTargetToParams()

    match = r"ConvertTargetToParams.filepath:\s+"
    match += r"commit\(\) must be called before accessing filepath\."
    with pytest.raises(ValueError, match=match):
        instance.filepath  # pylint: disable=pointless-statement


def test_convert_target_to_params_00500() -> None:
    """
    ### Classes and Methods
    - ConvertTargetToParams()
        - partition

    ### Summary
    Verify ``partition`` raises ``ValueError`` if accessed before ``commit()``
    is called.

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectation.
    """
    with does_not_raise():
        instance = ConvertTargetToParams()

    match = r"ConvertTargetToParams.partition:\s+"
    match += r"commit\(\) must be called before accessing partition\."
    with pytest.raises(ValueError, match=match):
        instance.partition  # pylint: disable=pointless-statement


def test_convert_target_to_params_00510() -> None:
    """
    ### Classes and Methods
    - ConvertTargetToParams()
        - partition

    ### Summary
    Verify ``partition`` raises ``ValueError`` passed a value not ending in ":".

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = ConvertTargetToParams()
        instance.target = targets(f"{key}")

    match = r"ConvertTargetToParams\.partition:\s+"
    match += r"Invalid partition: bootflash\.\s+"
    match += r"Expected partition to end with a colon."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_convert_target_to_params_00600() -> None:
    """
    ### Classes and Methods
    - ConvertTargetToParams()
        - supervisor

    ### Summary
    Verify ``supervisor`` raises ``ValueError`` if accessed before ``commit()``
    is called.

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectation.
    """
    with does_not_raise():
        instance = ConvertTargetToParams()

    match = r"ConvertTargetToParams.supervisor:\s+"
    match += r"commit\(\) must be called before accessing supervisor\."
    with pytest.raises(ValueError, match=match):
        instance.supervisor  # pylint: disable=pointless-statement


def test_convert_target_to_params_00610() -> None:
    """
    ### Classes and Methods
    - ConvertTargetToParams()
        - supervisor

    ### Summary
    Verify ``supervisor`` raises ``ValueError`` if not valid (i.e. not one of
    "active" or "standby").

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = ConvertTargetToParams()
        instance.target = targets(f"{key}")

    match = r"ConvertTargetToParams\.supervisor:\s+"
    match += r"Invalid supervisor: bad_supervisor_value\.\s+"
    match += r"Expected one of: active,standby\."
    with pytest.raises(ValueError, match=match):
        instance.commit()
