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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.merge_dicts_v2 import \
    MergeDicts
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import (
    does_not_raise, merge_dicts_v2_data, merge_dicts_v2_fixture)


def test_merge_dicts_v2_00000(merge_dicts_v2) -> None:
    """
    ### Method
    -   ``__init__``

    ### Test
    -   Verify Class attributes are initialized to expected values.
    """
    with does_not_raise():
        instance = merge_dicts_v2
    assert isinstance(instance, MergeDicts)
    assert isinstance(instance.properties, dict)
    assert instance.class_name == "MergeDicts"
    assert instance.properties.get("dict1", "foo") is None
    assert instance.properties.get("dict2", "foo") is None
    assert instance.properties.get("dict_merged", "foo") is None


MATCH_00100 = "MergeDicts.dict1: Invalid value. Expected type dict. Got type "


@pytest.mark.parametrize(
    "value, expected",
    [
        ({}, does_not_raise()),
        ([], pytest.raises(TypeError, match=MATCH_00100)),
        ((), pytest.raises(TypeError, match=MATCH_00100)),
        (None, pytest.raises(TypeError, match=MATCH_00100)),
        (1, pytest.raises(TypeError, match=MATCH_00100)),
        (1.1, pytest.raises(TypeError, match=MATCH_00100)),
        ("foo", pytest.raises(TypeError, match=MATCH_00100)),
        (True, pytest.raises(TypeError, match=MATCH_00100)),
        (False, pytest.raises(TypeError, match=MATCH_00100)),
    ],
)
def test_merge_dicts_v2_00100(merge_dicts_v2, value, expected) -> None:
    """
    ### Property
    -   ``dict1``

    ### Test
    -   Verify ``dict1`` raises ``TypeError`` if passed anything other
        than a dict.
    """
    with does_not_raise():
        instance = merge_dicts_v2
    with expected:
        instance.dict1 = value


MATCH_00200 = "MergeDicts.dict2: Invalid value. Expected type dict. Got type "


@pytest.mark.parametrize(
    "value, expected",
    [
        ({}, does_not_raise()),
        ([], pytest.raises(TypeError, match=MATCH_00200)),
        ((), pytest.raises(TypeError, match=MATCH_00200)),
        (None, pytest.raises(TypeError, match=MATCH_00200)),
        (1, pytest.raises(TypeError, match=MATCH_00200)),
        (1.1, pytest.raises(TypeError, match=MATCH_00200)),
        ("foo", pytest.raises(TypeError, match=MATCH_00200)),
        (True, pytest.raises(TypeError, match=MATCH_00200)),
        (False, pytest.raises(TypeError, match=MATCH_00200)),
    ],
)
def test_merge_dicts_v2_00200(merge_dicts_v2, value, expected) -> None:
    """
    ### Property
    -   ``dict2``

    ### Test
    -   Verify ``dict2`` raises ``TypeError`` if passed anything other
        than a dict.
    """
    with does_not_raise():
        instance = merge_dicts_v2
    with expected:
        instance.dict2 = value


MATCH_00300 = "MergeDicts.commit: "
MATCH_00300 += "dict1 and dict2 must be set "
MATCH_00300 += r"before calling commit\(\)"


@pytest.mark.parametrize(
    "dict1, dict2, expected",
    [
        ({}, {}, does_not_raise()),
        (None, {}, pytest.raises(ValueError, match=MATCH_00300)),
        ({}, None, pytest.raises(ValueError, match=MATCH_00300)),
    ],
)
def test_merge_dicts_v2_00300(merge_dicts_v2, dict1, dict2, expected) -> None:
    """
    ### Method
    -   ``commit``

    ### Test
    -   Verify ``commit`` raises ``ValueError`` when dict1 or dict2 have not
        been set.
    """
    with does_not_raise():
        instance = merge_dicts_v2
        if dict1 is not None:
            instance.dict1 = dict1
        if dict2 is not None:
            instance.dict2 = dict2
    with expected:
        instance.commit()


def test_merge_dicts_v2_00400(merge_dicts_v2) -> None:
    """
    ### Property
    -   ``dict_merged``

    ### Test
    -   Verify that ``dict_merged`` raises ``ValueError`` when accessed before
        calling ``commit``.
    """
    with does_not_raise():
        instance = merge_dicts_v2

    match = "MergeDicts.dict_merged: "
    match += r"Call instance\.commit\(\) before "
    match += r"calling instance\.dict_merged\."

    with pytest.raises(ValueError, match=match):
        instance.dict_merged  # pylint: disable=pointless-statement


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
def test_merge_dicts_v2_00500(merge_dicts_v2) -> None:
    """
    ### Property
    -   ``dict1`
    -   ``dict2``
    -   ``dict_merged``

    ### Method
    -   ``commit``

    ### Test
    -  ``dict1`` contains one top-level key foo with non-dict value.
    -  ``dict2`` contains one top-level key bar with non-dict value.
    -  ``dict_merged`` contains both top-level keys with unchanged values.
    """
    key = "test_merge_dicts_v2_00500"
    data = merge_dicts_v2_data(key)

    with does_not_raise():
        instance = merge_dicts_v2
        instance.dict1 = data.get("dict1")
        instance.dict2 = data.get("dict2")
        instance.commit()
    assert instance.dict_merged == data.get("dict_merged")


def test_merge_dicts_v2_00510(merge_dicts_v2) -> None:
    """
    ### Property
    -   ``dict1`
    -   ``dict2``
    -   ``dict_merged``

    ### Method
    -   ``commit``

    ### Test
    -   ``dict1`` contains one top-level key foo with non-dict value.
    -   ``dict2`` contains one top-level key foo with non-dict value.
    -   ``dict_merged`` contains one top-level key foo with value
        from ``dict2``.
    """
    key = "test_merge_dicts_v2_00510"
    data = merge_dicts_v2_data(key)

    with does_not_raise():
        instance = merge_dicts_v2
        instance.dict1 = data.get("dict1")
        instance.dict2 = data.get("dict2")
        instance.commit()
    assert instance.dict_merged == data.get("dict_merged")


def test_merge_dicts_v2_00520(merge_dicts_v2) -> None:
    """
    ### Property
    -   ``dict1`
    -   ``dict2``
    -   ``dict_merged``

    ### Method
    -   ``commit``

    ### Test
    -   ``dict1`` contains one top-level key foo with dict value.
    -   ``dict2`` contains one top-level key foo with non-dict value.
    -   ``dict_merged`` contains one top-level key foo with value
        from ``dict2``.
    """
    key = "test_merge_dicts_v2_00520"
    data = merge_dicts_v2_data(key)

    with does_not_raise():
        instance = merge_dicts_v2
        instance.dict1 = data.get("dict1")
        instance.dict2 = data.get("dict2")
        instance.commit()
    assert instance.dict_merged == data.get("dict_merged")


def test_merge_dicts_v2_00530(merge_dicts_v2) -> None:
    """
    ### Property
    -   ``dict1`
    -   ``dict2``
    -   ``dict_merged``

    ### Method
    -   ``commit``

    ### Test
    -   ``dict1`` contains one top-level key foo that is a dict.
    -   ``dict2`` contains one top-level key foo that is a dict.
    -   the keys in both nested dicts are the same.
    -   ``dict_merged`` contains one top-level key foo
        that is a dict containing key/values from ``dict2``.
    """
    key = "test_merge_dicts_v2_00530"
    data = merge_dicts_v2_data(key)

    with does_not_raise():
        instance = merge_dicts_v2
        instance.dict1 = data.get("dict1")
        instance.dict2 = data.get("dict2")
        instance.commit()
    assert instance.dict_merged == data.get("dict_merged")


def test_merge_dicts_v2_00540(merge_dicts_v2) -> None:
    """
    ### Property
    -   ``dict1`
    -   ``dict2``
    -   ``dict_merged``

    ### Method
    -   ``commit``

    ### Test
    -   ``dict1`` contains one top-level key foo that is a dict.
    -   ``dict2`` contains one top-level key foo that is a dict.
    -   The keys in ``dict1``/``dict2`` nested dicts differ.
    -   ``dict_merged`` contains one top-level key foo
        that is a dict containing keys from both ``dict1``
        and ``dict2``, with values unchanged.
    """
    key = "test_merge_dicts_v2_00540"
    data = merge_dicts_v2_data(key)

    with does_not_raise():
        instance = merge_dicts_v2
        instance.dict1 = data.get("dict1")
        instance.dict2 = data.get("dict2")
        instance.commit()
    assert instance.dict_merged == data.get("dict_merged")


def test_merge_dicts_v2_00550(merge_dicts_v2) -> None:
    """
    ### Property
    -   ``dict1`
    -   ``dict2``
    -   ``dict_merged``

    ### Method
    -   ``commit``

    ### Test
    -   ``dict1`` is empty.
    -   ``dict2`` contains several keys with a combination of
        dict and non-dict values.
    -   ``dict_merged`` contains the contents of dict2.
    """
    key = "test_merge_dicts_v2_00550"
    data = merge_dicts_v2_data(key)

    with does_not_raise():
        instance = merge_dicts_v2
        instance.dict1 = data.get("dict1")
        instance.dict2 = data.get("dict2")
        instance.commit()
    assert instance.dict_merged == data.get("dict_merged")


def test_merge_dicts_v2_00560(merge_dicts_v2) -> None:
    """
    ### Property
    -   ``dict1`
    -   ``dict2``
    -   ``dict_merged``

    ### Method
    -   ``commit``

    ### Test
    -   ``dict2`` is empty.
    -   ``dict1`` contains several keys with a combination of
        dict and non-dict values.
    -   ``dict_merged`` contains the contents of dict1.
    """
    key = "test_merge_dicts_v2_00560"
    data = merge_dicts_v2_data(key)

    with does_not_raise():
        instance = merge_dicts_v2
        instance.dict1 = data.get("dict1")
        instance.dict2 = data.get("dict2")
        instance.commit()
    assert instance.dict_merged == data.get("dict_merged")
