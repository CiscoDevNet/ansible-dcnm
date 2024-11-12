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
# pylint: disable=unused-import
# Some fixtures need to use *args to match the signature of the function they are mocking
# pylint: disable=unused-argument
# Some tests require calling protected methods
# pylint: disable=protected-access

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.common.merge_dicts import \
    MergeDicts
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import (
    does_not_raise, merge_dicts_data, merge_dicts_fixture)


def test_merge_dicts_00001(merge_dicts) -> None:
    """
    Function
    - __init__

    Test
    - Class attributes are initialized to expected values
    """
    with does_not_raise():
        instance = merge_dicts
    assert isinstance(instance, MergeDicts)
    assert isinstance(instance.properties, dict)
    assert instance.class_name == "MergeDicts"
    assert instance.properties.get("dict1", "foo") is None
    assert instance.properties.get("dict2", "foo") is None
    assert instance.properties.get("dict_merged", "foo") is None


MATCH_00020 = "MergeDicts.dict1: Invalid value. Expected type dict. Got type "


@pytest.mark.parametrize(
    "value, expected",
    [
        ({}, does_not_raise()),
        ([], pytest.raises(AnsibleFailJson, match=MATCH_00020)),
        ((), pytest.raises(AnsibleFailJson, match=MATCH_00020)),
        (None, pytest.raises(AnsibleFailJson, match=MATCH_00020)),
        (1, pytest.raises(AnsibleFailJson, match=MATCH_00020)),
        (1.1, pytest.raises(AnsibleFailJson, match=MATCH_00020)),
        ("foo", pytest.raises(AnsibleFailJson, match=MATCH_00020)),
        (True, pytest.raises(AnsibleFailJson, match=MATCH_00020)),
        (False, pytest.raises(AnsibleFailJson, match=MATCH_00020)),
    ],
)
def test_merge_dicts_00020(merge_dicts, value, expected) -> None:
    """
    Function
    - dict1

    Test
    - dict1 accepts only a dict
    """
    with does_not_raise():
        instance = merge_dicts
    with expected:
        instance.dict1 = value


MATCH_00021 = "MergeDicts.dict2: Invalid value. Expected type dict. Got type "


@pytest.mark.parametrize(
    "value, expected",
    [
        ({}, does_not_raise()),
        ([], pytest.raises(AnsibleFailJson, match=MATCH_00021)),
        ((), pytest.raises(AnsibleFailJson, match=MATCH_00021)),
        (None, pytest.raises(AnsibleFailJson, match=MATCH_00021)),
        (1, pytest.raises(AnsibleFailJson, match=MATCH_00021)),
        (1.1, pytest.raises(AnsibleFailJson, match=MATCH_00021)),
        ("foo", pytest.raises(AnsibleFailJson, match=MATCH_00021)),
        (True, pytest.raises(AnsibleFailJson, match=MATCH_00021)),
        (False, pytest.raises(AnsibleFailJson, match=MATCH_00021)),
    ],
)
def test_merge_dicts_00021(merge_dicts, value, expected) -> None:
    """
    Function
    - dict2

    Test
    - dict2 accepts only a dict
    """
    with does_not_raise():
        instance = merge_dicts
    with expected:
        instance.dict2 = value


MATCH_00030 = "MergeDicts.commit: "
MATCH_00030 += "dict1 and dict2 must be set "
MATCH_00030 += r"before calling commit\(\)"


@pytest.mark.parametrize(
    "dict1, dict2, expected",
    [
        ({}, {}, does_not_raise()),
        (None, {}, pytest.raises(AnsibleFailJson, match=MATCH_00030)),
        ({}, None, pytest.raises(AnsibleFailJson, match=MATCH_00030)),
    ],
)
def test_merge_dicts_00030(merge_dicts, dict1, dict2, expected) -> None:
    """
    Function
    - commit

    Test
    - commit calls fail_json when dict1 or dict2 is None
    """
    with does_not_raise():
        instance = merge_dicts
        if dict1 is not None:
            instance.dict1 = dict1
        if dict2 is not None:
            instance.dict2 = dict2
    with expected:
        instance.commit()


def test_merge_dicts_00041(merge_dicts) -> None:
    """
    Function
    - dict_merged

    Test
    - dict_merged calls fail_json when called before calling commit
    """
    with does_not_raise():
        instance = merge_dicts

    match = "MergeDicts.dict_merged: "
    match += r"Call instance\.commit\(\) before "
    match += r"calling instance\.dict_merged\."

    with pytest.raises(AnsibleFailJson, match=match):
        value = instance.dict_merged  # pylint: disable=unused-variable


# The remaining tests verify various combinations of dict1 and dict2
# using the following merge rules:
# 1.  non-dict keys in dict1 are overwritten by dict2
#     if they exist in dict2
# 2.  non-dict keys in dict1 are not overwritten by dict2
#     if they do not exist in dict2
# 3.  if a key exists in both dict1 and dict2 and that key's value
#     is a dict in both dict1 and dict2, the function recurses into
#     the dict and applies the first two rules to the nested dict
# 4.  in all other cases, dict2 overwrites dict1.  For example, if
#     a key exists in both dict1 and dict2 and that key's value
#     is a dict in dict1 but not in dict2, the key is overwritten
#     by dict2 (similar to rule 1)
def test_merge_dicts_00050(merge_dicts) -> None:
    """
    Function
    - dict1
    - dict2
    - commit
    - dict_merged

    Test
    -  dict1 contains one top-level key foo with non-dict value
    -  dict2 contains one top-level key bar with non-dict value
    -  dict_merged contains both top-level keys with unchanged values
    """
    key = "test_merge_dicts_00050"
    data = merge_dicts_data(key)

    with does_not_raise():
        instance = merge_dicts
        instance.dict1 = data.get("dict1")
        instance.dict2 = data.get("dict2")
        instance.commit()
    assert instance.dict_merged == data.get("dict_merged")


def test_merge_dicts_00051(merge_dicts) -> None:
    """
    Function
    - dict1
    - dict2
    - commit
    - dict_merged

    Test
    -  dict1 contains one top-level key foo with non-dict value
    -  dict2 contains one top-level key foo with non-dict value
    -  dict_merged contains one top-level key foo with value from dict2
    """
    key = "test_merge_dicts_00051"
    data = merge_dicts_data(key)

    with does_not_raise():
        instance = merge_dicts
        instance.dict1 = data.get("dict1")
        instance.dict2 = data.get("dict2")
        instance.commit()
    assert instance.dict_merged == data.get("dict_merged")


def test_merge_dicts_00052(merge_dicts) -> None:
    """
    Function
    - dict1
    - dict2
    - commit
    - dict_merged

    Test
    -  dict1 contains one top-level key foo with dict value
    -  dict2 contains one top-level key foo with non-dict value
    -  dict_merged contains one top-level key foo with value from dict2
    """
    key = "test_merge_dicts_00052"
    data = merge_dicts_data(key)

    with does_not_raise():
        instance = merge_dicts
        instance.dict1 = data.get("dict1")
        instance.dict2 = data.get("dict2")
        instance.commit()
    assert instance.dict_merged == data.get("dict_merged")


def test_merge_dicts_00053(merge_dicts) -> None:
    """
    Function
    - dict1
    - dict2
    - commit
    - dict_merged

    Test
    -   dict1 contains one top-level key foo that is a dict
    -   dict2 contains one top-level key foo that is a dict
    -   the keys in both nested dicts are the same
    -   dict_merged contains one top-level key foo
        that is a dict containing key/values from dict2
    """
    key = "test_merge_dicts_00053"
    data = merge_dicts_data(key)

    with does_not_raise():
        instance = merge_dicts
        instance.dict1 = data.get("dict1")
        instance.dict2 = data.get("dict2")
        instance.commit()
    assert instance.dict_merged == data.get("dict_merged")


def test_merge_dicts_00054(merge_dicts) -> None:
    """
    Function
    - dict1
    - dict2
    - commit
    - dict_merged

    Test
    -   dict1 contains one top-level key foo that is a dict
    -   dict2 contains one top-level key foo that is a dict
    -   the keys in dict1/dict2 nested dicts are different
    -   dict_merged contains one top-level key foo
        that is a dict containing keys from both dict1
        and dict2, with values unchanged.
    """
    key = "test_merge_dicts_00054"
    data = merge_dicts_data(key)

    with does_not_raise():
        instance = merge_dicts
        instance.dict1 = data.get("dict1")
        instance.dict2 = data.get("dict2")
        instance.commit()
    assert instance.dict_merged == data.get("dict_merged")


def test_merge_dicts_00055(merge_dicts) -> None:
    """
    Function
    - dict1
    - dict2
    - commit
    - dict_merged

    Test
    -   dict1 is empty
    -   dict2 contains several keys with a combination of
        dict and non-dict values
    -   dict_merged contains the contents of dict2
    """
    key = "test_merge_dicts_00055"
    data = merge_dicts_data(key)

    with does_not_raise():
        instance = merge_dicts
        instance.dict1 = data.get("dict1")
        instance.dict2 = data.get("dict2")
        instance.commit()
    assert instance.dict_merged == data.get("dict_merged")


def test_merge_dicts_00056(merge_dicts) -> None:
    """
    Function
    - dict1
    - dict2
    - commit
    - dict_merged

    Test
    -   dict2 is empty
    -   dict1 contains several keys with a combination of
        dict and non-dict values
    -   dict_merged contains the contents of dict1
    """
    key = "test_merge_dicts_00056"
    data = merge_dicts_data(key)

    with does_not_raise():
        instance = merge_dicts
        instance.dict1 = data.get("dict1")
        instance.dict2 = data.get("dict2")
        instance.commit()
    assert instance.dict_merged == data.get("dict_merged")
