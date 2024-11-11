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

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import inspect

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.common.exceptions import \
    ControllerResponseError
from ansible_collections.cisco.dcnm.plugins.module_utils.common.response_handler import \
    ResponseHandler
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_file import \
    Sender
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    ResponseGenerator

from .utils import (MockAnsibleModule, does_not_raise,
                    image_install_options_fixture, params,
                    responses_ep_install_options)

PATCH_MODULE_UTILS = "ansible_collections.cisco.dcnm.plugins.module_utils."
PATCH_IMAGE_UPGRADE = PATCH_MODULE_UTILS + "image_upgrade."
DCNM_SEND_INSTALL_OPTIONS = PATCH_IMAGE_UPGRADE + "install_options.dcnm_send"


def test_image_install_options_00000(image_install_options) -> None:
    """
    ### Classes and Methods

    -   ``ImageInstallOptions``
            -   ``__init__``

    Test
    - Exceptions are not raised.
    - Class attributes are initialized to expected values
    """
    with does_not_raise():
        instance = image_install_options

    assert instance.class_name == "ImageInstallOptions"
    assert instance.conversion.class_name == "ConversionUtils"
    assert instance.ep_install_options.class_name == "EpInstallOptions"
    path = "/appcenter/cisco/ndfc/api/v1/imagemanagement"
    path += "/rest/imageupgrade/install-options"
    assert instance.ep_install_options.path == path
    assert instance.ep_install_options.verb == "POST"
    assert instance.compatibility_status == {}
    assert instance.payload == {}


def test_image_install_options_00010(image_install_options) -> None:
    """
    ### Classes and Methods

    -   ``ImageInstallOptions``
            - ``_init_properties``

    ### Test

    - Class properties are initialized to expected values.
    """
    with does_not_raise():
        instance = image_install_options

    assert instance.epld is False
    assert instance.issu is True
    assert instance.package_install is False
    assert instance.policy_name is None
    assert instance.response_data is None
    assert instance.rest_send is None
    assert instance.results is None
    assert instance.serial_number is None


def test_image_install_options_00100(image_install_options) -> None:
    """
    ### Classes and Methods

    -   ``ImageInstallOptions``
            -   ``refresh``

    ### Test
    -   ``ValueError`` is raised because ``serial_number`` is not set before
        ``refresh`` is called.
    -   Error message matches expectation.
    """

    def responses():
        # ImageStage()._populate_controller_version
        yield None

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_install_options
        instance.results = Results()
        instance.rest_send = rest_send
        instance.policy_name = "FOO"

    match = r"ImageInstallOptions\._validate_refresh_parameters:\s+"
    match += r"serial_number must be set before calling refresh\(\)\."

    with pytest.raises(ValueError, match=match):
        image_install_options.refresh()


def test_image_install_options_00110(image_install_options) -> None:
    """
    ### Classes and Methods

    -   ``ImageInstallOptions``
            -   ``refresh``

    ### Test

    -   Request is successful.
    -   No exceptions are raised.
    -   Properties are updated with expected values.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_install_options(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_install_options
        instance.results = Results()
        instance.rest_send = rest_send
        instance.policy_name = "KRM5"
        instance.serial_number = "BAR"
        instance.refresh()

    assert isinstance(instance.results.response, list)
    assert isinstance(instance.results.response_current, dict)
    assert instance.rest_send.result_current.get("success") is True

    assert instance.device_name == "cvd-1314-leaf"
    assert instance.err_message is None
    assert instance.epld_modules is None
    assert instance.install_option == "disruptive"
    assert instance.install_packages is None
    assert instance.ip_address == "172.22.150.105"
    assert instance.os_type == "64bit"
    assert instance.platform == "N9K/N3K"
    assert instance.pre_issu_link == "Not Applicable"
    assert isinstance(instance.raw_data, dict)
    assert isinstance(instance.raw_response, dict)
    assert "compatibilityStatusList" in instance.raw_data
    assert instance.rep_status == "skipped"
    assert instance.serial_number == "BAR"
    assert instance.status == "Success"
    assert instance.timestamp == "NA"
    assert instance.version == "10.2.5"
    comp_disp = "show install all impact nxos bootflash:nxos64-cs.10.2.5.M.bin"
    assert instance.comp_disp == comp_disp


def test_image_install_options_00120(image_install_options) -> None:
    """
    ### Classes and Methods

    -   ``ImageInstallOptions``
            -   ``refresh``

    ### Test

    -   ``ControllerResponseError`` is raised because response RETURN_CODE != 200.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_install_options(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_install_options
        instance.results = Results()
        instance.rest_send = rest_send
        instance.policy_name = "KRM5"
        instance.serial_number = "BAR"

    match = r"ImageInstallOptions\.refresh:\s+"
    match += r"Bad result when retrieving install-options from\s+"
    match += r"the controller\. Controller response:.*"

    with pytest.raises(ControllerResponseError, match=match):
        instance.refresh()


def test_image_install_options_00130(image_install_options) -> None:
    """
    ### Classes and Methods

    -   ``ImageInstallOptions``
            -   ``refresh``

    ### Setup

    -   Device has no policy attached.
    -   POST REQUEST
            -   epld is False.
            -   issu is True.
            -   package_install is False.

    ### Test
    -   Request is successful.
    -   No exceptions are raised.
    -   Response contains expected values.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_install_options(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_install_options
        instance.results = Results()
        instance.rest_send = rest_send

        instance.epld = False
        instance.issu = True
        instance.package_install = False

        instance.policy_name = "KRM5"
        instance.serial_number = "FDO21120U5D"
        instance.refresh()

    assert isinstance(instance.rest_send.response_current, dict)
    assert isinstance(instance.rest_send.response, list)
    assert isinstance(instance.rest_send.result_current, dict)
    assert isinstance(instance.rest_send.result, list)
    assert instance.rest_send.result_current.get("success") is True

    assert instance.device_name == "leaf1"
    assert instance.err_message is None
    assert instance.epld_modules is None
    assert instance.install_option == "NA"
    assert instance.install_packages is None
    assert instance.ip_address == "172.22.150.102"
    assert instance.os_type == "64bit"
    assert instance.platform == "N9K/N3K"
    assert instance.pre_issu_link == "Not Applicable"
    assert isinstance(instance.raw_data, dict)
    assert isinstance(instance.raw_response, dict)
    assert "compatibilityStatusList" in image_install_options.raw_data
    assert instance.rep_status == "skipped"
    assert instance.serial_number == "FDO21120U5D"
    assert instance.status == "Skipped"
    assert instance.timestamp == "NA"
    assert instance.version == "10.2.5"
    assert instance.version_check == "Compatibility status skipped."
    assert instance.comp_disp == "Compatibility status skipped."


def test_image_install_options_00140(image_install_options) -> None:
    """
    ### Classes and Methods

    -   ``ImageInstallOptions``
            -   ``refresh``

    ### Setup

    -  Device has no policy attached.
    -   POST REQUEST
            -   epld is True.
            -   issu is True.
            -   package_install is False.

    ### Test
    -   Request is successful.
    -   No exceptions are raised.
    -   Response contains expected values.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_install_options(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_install_options
        instance.results = Results()
        instance.rest_send = rest_send
        instance.rest_send.timeout = 1

        instance.epld = True
        instance.issu = True
        instance.package_install = False

        instance.policy_name = "KRM5"
        instance.serial_number = "FDO21120U5D"
        instance.refresh()

    assert isinstance(instance.rest_send.response_current, dict)
    assert isinstance(instance.rest_send.response, list)
    assert isinstance(instance.rest_send.result_current, dict)
    assert isinstance(instance.rest_send.result, list)
    assert instance.rest_send.result_current.get("success") is True

    assert instance.device_name == "leaf1"
    assert instance.err_message is None
    assert isinstance(instance.epld_modules, dict)
    assert len(instance.epld_modules.get("moduleList")) == 2
    assert instance.install_option == "NA"
    assert instance.install_packages is None
    assert instance.ip_address == "172.22.150.102"
    assert instance.os_type == "64bit"
    assert instance.platform == "N9K/N3K"
    assert instance.pre_issu_link == "Not Applicable"
    assert isinstance(instance.raw_data, dict)
    assert isinstance(instance.raw_response, dict)
    assert "compatibilityStatusList" in instance.raw_data
    assert instance.rep_status == "skipped"
    assert instance.serial_number == "FDO21120U5D"
    assert instance.status == "Skipped"
    assert instance.timestamp == "NA"
    assert instance.version == "10.2.5"
    assert instance.version_check == "Compatibility status skipped."
    assert instance.comp_disp == "Compatibility status skipped."


def test_image_install_options_00150(image_install_options) -> None:
    """
    ### Classes and Methods
    -   ``ImageInstallOptions``
            -   ``refresh``

    ### Setup

    -  Device has no policy attached.
    -   POST REQUEST
            -   epld is True.
            -   issu is False.
            -   package_install is False.

    ### Test

    -   Request is successful.
    -   No exceptions are raised.
    -   Response contains expected values.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_install_options(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_install_options
        instance.results = Results()
        instance.rest_send = rest_send
        instance.rest_send.timeout = 1

        instance.epld = True
        instance.issu = False
        instance.package_install = False

        instance.policy_name = "KRM5"
        instance.serial_number = "FDO21120U5D"
        instance.refresh()

    assert isinstance(instance.rest_send.response_current, dict)
    assert isinstance(instance.rest_send.response, list)
    assert isinstance(instance.rest_send.result_current, dict)
    assert isinstance(instance.rest_send.result, list)
    assert instance.rest_send.result_current.get("success") is True

    assert instance.device_name is None
    assert instance.err_message is None
    assert isinstance(instance.epld_modules, dict)
    assert len(instance.epld_modules.get("moduleList")) == 2
    assert instance.install_option is None
    assert instance.install_packages is None
    assert instance.ip_address is None
    assert instance.os_type is None
    assert instance.platform is None
    assert instance.pre_issu_link is None
    assert isinstance(instance.raw_data, dict)
    assert isinstance(instance.raw_response, dict)
    assert "compatibilityStatusList" in instance.raw_data
    assert instance.rep_status is None
    assert instance.serial_number == "FDO21120U5D"
    assert instance.status is None
    assert instance.timestamp is None
    assert instance.version is None
    assert instance.version_check is None
    assert instance.comp_disp is None


def test_image_install_options_00160(monkeypatch, image_install_options) -> None:
    """
    ### Classes and Methods

    -   ``ImageInstallOptions``
            -   ``refresh``

    ### Setup

    -  Device has no policy attached.
    -   POST REQUEST
        - issu is False.
        - epld is True.
        - package_install is True.
            -   Causes expected error.

    ### Test

    -   500 response from endpoint because
            - KR5M policy has no packages defined and,
            - package_install set to True.
    -   Response contains expected values.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_install_options(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_install_options
        instance.results = Results()
        instance.rest_send = rest_send
        instance.rest_send.timeout = 1

        instance.epld = True
        instance.issu = True
        instance.package_install = True

        instance.policy_name = "KRM5"
        instance.serial_number = "FDO21120U5D"

    match = r"ImageInstallOptions\.refresh:\s+"
    match += r"Bad result when retrieving install-options from the\s+"
    match += r"controller\.\s+"
    match += r"Controller response:.*\.\s+"
    match += r"Possible cause:\s+"
    match += r"Image policy KRM5 does not have a package defined,\s+"
    match += r"and package_install is set to True in the playbook for\s+"
    match += r"device FDO21120U5D\."

    with pytest.raises(ControllerResponseError, match=match):
        instance.refresh()


def test_image_install_options_00170(image_install_options) -> None:
    """
    ### Classes and Methods
    -   ``ImageInstallOptions``
            -   ``refresh``

    ### Setup

    -   POST REQUEST
        - epld is False
        - issu is False
        - package_install is False

    ### Test

    -   ``ImageInstallOptions`` returns a mocked response when all of
        issu, epld, and package_install are False.
    -   Mocked response contains expected values.

    ### NOTES
    ``ResponseGenerator()`` is set to return None since ``ImageInstallOptions``
    never sends a request to the controller in this case.
    """

    def responses():
        yield None

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_install_options
        instance.results = Results()
        instance.rest_send = rest_send

        instance.epld = False
        instance.issu = False
        instance.package_install = False

        instance.policy_name = "KRM5"
        instance.serial_number = "FDO21120U5D"
        instance.refresh()

    # response_data
    # {
    #     'compatibilityStatusList': [],
    #     'epldModules': {},
    #     'installPacakges': None,
    #     'errMessage': ''
    # }
    assert isinstance(instance.response_data, dict)
    assert instance.response_data.get("compatibilityStatusList") == []
    assert instance.response_data.get("epldModules") == {}
    # yes, installPackages is intentionally misspelled below since
    # this is what the controller returns in a real response
    assert instance.response_data.get("installPacakges") is None
    assert instance.response_data.get("errMessage") == ""


def test_image_install_options_00180(image_install_options) -> None:
    """
    ### Classes and Methods
    -   ``ImageInstallOptions``
            -   ``refresh``

    ### Test

    -   ``refresh()`` raises ValueError because ``policy_name`` is not set.
    -   Error message matches expectation.
    """

    def responses():
        yield None

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_install_options
        instance.results = Results()
        instance.rest_send = rest_send
        instance.serial_number = "FOO"

    match = r"ImageInstallOptions\._validate_refresh_parameters:\s+"
    match += r"policy_name must be set before calling refresh\(\)\."

    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_image_install_options_00200(image_install_options) -> None:
    """
    ### Classes and Methods
    -   ``ImageInstallOptions``
            -   ``build_payload``

    ### Setup

    -   Defaults are not specified by the user.

    ### Test

    -   Default values for issu, epld, and package_install are applied.
    """
    with does_not_raise():
        instance = image_install_options
        instance.policy_name = "KRM5"
        instance.serial_number = "BAR"
        instance._build_payload()  # pylint: disable=protected-access

    assert instance.payload.get("epld") is False
    assert instance.payload.get("issu") is True
    assert instance.payload.get("packageInstall") is False
    assert instance.payload.get("devices")[0].get("policyName") == "KRM5"
    assert instance.payload.get("devices")[0].get("serialNumber") == "BAR"


def test_image_install_options_00210(image_install_options) -> None:
    """
    ### Classes and Methods
    -   ``ImageInstallOptions``
            -   ``build_payload``

    ### Setup

    -   Values are specified by the user.

    ### Test

    -   Payload contains user-specified values if the user sets them.
    -   Defaults for issu, epld, and package_install are overridden by
        user values.
    """
    with does_not_raise():
        instance = image_install_options
        instance.epld = True
        instance.issu = False
        instance.package_install = True
        instance.policy_name = "KRM5"
        instance.serial_number = "BAR"

        instance._build_payload()  # pylint: disable=protected-access

    assert instance.payload.get("epld") is True
    assert instance.payload.get("issu") is False
    assert instance.payload.get("packageInstall") is True
    assert instance.payload.get("devices")[0].get("policyName") == "KRM5"
    assert instance.payload.get("devices")[0].get("serialNumber") == "BAR"


def test_image_install_options_00300(image_install_options) -> None:
    """
    ### Classes and Methods
    -   ``ImageInstallOptions``
            -   ``issu.setter``

    ### Test

    -   ``TypeError`` is raised because issu is not a boolean.
    """
    match = r"ImageInstallOptions\.issu:\s+"
    match += r"issu must be a boolean value\."

    with does_not_raise():
        instance = image_install_options
    with pytest.raises(TypeError, match=match):
        instance.issu = "FOO"


def test_image_install_options_00400(image_install_options) -> None:
    """
    ### Classes and Methods

    -   ``ImageInstallOptions``
            -   ``epld.setter``

    ### Test

    -   ``TypeError`` is raised because epld is not a boolean.
    """
    match = r"ImageInstallOptions\.epld:\s+"
    match += r"epld must be a boolean value\."

    with does_not_raise():
        instance = image_install_options
    with pytest.raises(TypeError, match=match):
        instance.epld = "FOO"


def test_image_install_options_00500(image_install_options) -> None:
    """
    ### Classes and Methods

    -   ``ImageInstallOptions``
            -   ``package_install.setter``

    ### Test

    -   ``TypeError`` is raised because package_install is not a boolean.
    """
    match = r"ImageInstallOptions\.package_install:\s+"
    match += r"package_install must be a boolean value\."

    with does_not_raise():
        instance = image_install_options
    with pytest.raises(TypeError, match=match):
        instance.package_install = "FOO"


MATCH_00600 = r"ImageInstallOptions\.policy_name: "
MATCH_00600 += r"instance\.policy_name must be a string. Got"


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        ("NR3F", does_not_raise(), False),
        (1, pytest.raises(TypeError, match=MATCH_00600), True),
        (False, pytest.raises(TypeError, match=MATCH_00600), True),
        ({"foo": "bar"}, pytest.raises(TypeError, match=MATCH_00600), True),
        ([1, 2], pytest.raises(TypeError, match=MATCH_00600), True),
    ],
)
def test_image_install_options_00600(
    image_install_options, value, expected, raise_flag
) -> None:
    """
    ### Classes and Methods

    -   ``ImageInstallOptions``
            -   ``policy_name.setter``

    ### Test

    -   ``TypeError`` is raised when ``property_name`` is not a string.
    -   ``TypeError`` is not raised when ``property_name`` is a string.
    """
    with does_not_raise():
        instance = image_install_options
    with expected:
        instance.policy_name = value
    if raise_flag is False:
        assert instance.policy_name == value
