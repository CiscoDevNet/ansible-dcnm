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

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_file import \
    Sender
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import (
    ResponseGenerator, does_not_raise, responses_sender_file,
    sender_file_fixture)


def responses():
    """
    ### Summary
    Co-routine for any unit tests below using ResponseGenerator() class.
    """
    yield {}


def test_sender_file_00000() -> None:
    """
    ### Classes and Methods
    -   Sender()
            -   __init__()

    ### Summary
    -   Class properties are initialized to expected values
    """
    with does_not_raise():
        instance = Sender()
    assert instance._ansible_module is None
    assert instance._gen is None
    assert instance._path is None
    assert instance._payload is None
    assert instance._response is None
    assert instance._verb is None


def test_sender_file_00100() -> None:
    """
    ### Classes and Methods
    -   Sender()
            -   _verify_commit_parameters()
            -   commit()

    ### Summary
    Verify ``commit()`` re-raises ``ValueError`` when
    ``_verify_commit_parameters()`` raises ``ValueError``
    due to ``gen`` not being set.

    ### Setup - Code
    -   Sender() is initialized.
    -   Sender().gen is NOT set.

    ### Setup - Data
    None

    ### Trigger
    -   Sender().commit() is called.

    ### Expected Result
    -   Sender().commit() re-raises ``ValueError``.


    """
    with does_not_raise():
        instance = Sender()

    match = r"Sender\.commit:\s+"
    match += r"Not all mandatory parameters are set\.\s+"
    match += r"Error detail: Sender\._verify_commit_parameters:\s+"
    match += r"gen must be set before calling commit\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_sender_file_00200() -> None:
    """
    ### Classes and Methods
    -   Sender()
            -   ansible_module.setter

    ### Summary
    Verify ``ansible_module.setter`` does not raise exceptions
    and that ``ansible_module.getter`` returns whatever is passed
    to ``ansible_module.setter``.

    ### NOTES
    ``ansible_module`` property is basically a noop, included only to satisfy
    the external interface.
    """
    with does_not_raise():
        instance = Sender()
        instance.ansible_module = 10
    assert instance.ansible_module == 10


def test_sender_file_00210() -> None:
    """
    ### Classes and Methods
    -   Sender()
            -   path.setter

    ### Summary
    Verify ``path.setter`` does not raise exceptions
    and that ``path.getter`` returns whatever is passed
    to ``path.setter``.

    ### NOTES
    ``path`` property is basically a noop, included only to satisfy
    the external interface.
    """
    with does_not_raise():
        instance = Sender()
        instance.path = 10
    assert instance.path == 10


def test_sender_file_00220() -> None:
    """
    ### Classes and Methods
    -   Sender()
            -   payload.setter

    ### Summary
    Verify ``payload.setter`` does not raise exceptions
    and that ``payload.getter`` returns whatever is passed
    to ``payload.setter``.

    ### NOTES
    ``payload`` property is basically a noop, included only to satisfy
    the external interface.
    """
    with does_not_raise():
        instance = Sender()
        instance.payload = 10
    assert instance.payload == 10


def test_sender_file_00230() -> None:
    """
    ### Classes and Methods
    -   Sender()
            -   response.setter

    ### Summary
    Verify ``response.getter`` returns whatever is yielded
    by the coroutine passed to ResponseGenerator()

    ### NOTES
    ``response`` has no setter.
    """
    with does_not_raise():
        instance = Sender()
        instance.gen = ResponseGenerator(responses())
    assert instance.response == {}


def test_sender_file_00240() -> None:
    """
    ### Classes and Methods
    -   Sender()
            -   verb.setter

    ### Summary
    Verify ``verb.setter`` does not raise exceptions
    and that ``verb.getter`` returns whatever is passed
    to ``verb.setter``.

    ### NOTES
    ``verb`` property is basically a noop, included only to satisfy
    the external interface.
    """
    with does_not_raise():
        instance = Sender()
        instance.verb = 10
    assert instance.verb == 10


MATCH_00300 = r"Sender.gen:\s+"
MATCH_00300 += r"Expected a class implementing the response_generator\s+"
MATCH_00300 += r"interface\. Got.*"


@pytest.mark.parametrize(
    "value, does_raise, expected",
    [
        (10, True, pytest.raises(TypeError, match=MATCH_00300)),
        ("FOO", True, pytest.raises(TypeError, match=MATCH_00300)),
        (ResponseGenerator(responses()), False, does_not_raise()),
    ],
)
def test_sender_file_00300(value, does_raise, expected) -> None:
    """
    ### Classes and Methods
    -   Sender()
            -   gen.setter

    ### Summary
    Verify ``gen.setter`` raises ``TypeError`` if the value
    passed to it does not implement expected response_generator
    interface.
    """
    with expected:
        instance = Sender()
        instance.gen = value
    if not does_raise:
        assert isinstance(instance.gen, ResponseGenerator)


def test_sender_file_00310() -> None:
    """
    ### Classes and Methods
    -   Sender()
            -   gen.setter

    ### Summary
    Verify ``gen.setter`` raises ``TypeError`` if the value
    passed to it is a class that exposes an ``implements``
    property, but that does not implement expected
    response_generator interface.
    """

    class ResponseGenerator2:  # pylint: disable=too-few-public-methods
        """
        A class that does not implement the response_generator interface.
        """

        @property
        def implements(self):
            """
            Return unexpected value.
            """
            return "not_response_generator"

    with does_not_raise():
        instance = Sender()
    match = r"Sender\.gen:\s+"
    match += r"Expected a class implementing the\s+"
    match += r"response_generator interface\. Got.*"
    with pytest.raises(TypeError, match=match):
        instance.gen = ResponseGenerator2()
