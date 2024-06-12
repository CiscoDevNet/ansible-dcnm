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
# pylint: disable=protected-access

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

from typing import Any, Dict

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_dcnm import \
    Sender
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import (
    responses_sender_dcnm, sender_dcnm_fixture)


def test_sender_dcnm_00000() -> None:
    """
    ### Classes and Methods
    -   Sender()
            -   __init__()

    ### Summary
    -   Class properties are initialized to expected values
    """
    instance = Sender()
    assert instance.params is None
    assert instance._ansible_module is None
    assert instance._path is None
    assert instance.payload is None
    assert instance._response is None
    assert instance._valid_verbs == {"GET", "POST", "PUT", "DELETE"}
    assert instance._verb is None


def test_sender_dcnm_00100() -> None:
    """
    ### Classes and Methods
    -   Sender()
            -   _verify_commit_parameters()
            -   commit()

    ### Summary
    Verify ``commit()`` re-raises ``ValueError`` when
    ``_verify_commit_parameters()`` raises ``ValueError``
    due to ``ansible_module`` not being set.

    ### Setup - Code
    -   Sender() is initialized.
    -   Sender().path is set.
    -   Sender().verb is set.
    -   Sender().ansible_module is NOT set.

    ### Setup - Data
    None

    ### Trigger
    -   Sender().commit() is called.

    ### Expected Result
    -   Sender().commit() re-raises ``ValueError``.


    """
    instance = Sender()
    instance.path = "/foo/path"
    instance.verb = "GET"

    match = r"Sender\.commit:\s+"
    match += r"Not all mandatory parameters are set\.\s+"
    match += r"Error detail:\s+"
    match += r"Sender\._verify_commit_parameters:\s+"
    match += r"ansible_module must be set before calling commit\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_sender_dcnm_00110(sender_dcnm) -> None:
    """
    ### Classes and Methods
    -   Sender()
            -   _verify_commit_parameters()
            -   commit()

    ### Summary
    Verify ``commit()`` re-raises ``ValueError`` when
    ``_verify_commit_parameters()`` raises ``ValueError``
    due to ``path`` not being set.

    ### Setup - Code
    -   Sender() is initialized.
    -   Sender().ansible_module is set.
    -   Sender().verb is set.
    -   Sender().path is NOT set.

    ### Setup - Data
    None

    ### Trigger
    -   Sender().commit() is called.

    ### Expected Result
    -   Sender().commit() re-raises ``ValueError``.


    """
    instance = sender_dcnm
    instance.verb = "GET"

    match = r"Sender\.commit:\s+"
    match += r"Not all mandatory parameters are set\.\s+"
    match += r"Error detail:\s+"
    match += r"Sender\._verify_commit_parameters:\s+"
    match += r"path must be set before calling commit\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_sender_dcnm_00120(sender_dcnm) -> None:
    """
    ### Classes and Methods
    -   Sender()
            -   _verify_commit_parameters()
            -   commit()

    ### Summary
    Verify ``commit()`` re-raises ``ValueError`` when
    ``_verify_commit_parameters()`` raises ``ValueError``
    due to ``verb`` not being set.

    ### Setup - Code
    -   Sender() is initialized.
    -   Sender().ansible_module is set.
    -   Sender().path is set.
    -   Sender().verb is NOT set.

    ### Setup - Data
    None

    ### Trigger
    -   Sender().commit() is called.

    ### Expected Result
    -   Sender().commit() re-raises ``ValueError``.
    """
    instance = sender_dcnm
    instance.path = "/foo/path"

    match = r"Sender\.commit:\s+"
    match += r"Not all mandatory parameters are set\.\s+"
    match += r"Error detail:\s+"
    match += r"Sender\._verify_commit_parameters:\s+"
    match += r"verb must be set before calling commit\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.commit()
