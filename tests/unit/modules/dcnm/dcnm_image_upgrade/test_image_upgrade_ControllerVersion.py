"""
controller_version: 12
description: Verify functionality of ControllerVersion
"""

from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.common.controller_version import \
    ControllerVersion

from .fixture import load_fixture

patch_module_utils = "ansible_collections.cisco.dcnm.plugins.module_utils."
patch_common = patch_module_utils + "common."

dcnm_send_version = patch_common + "controller_version.dcnm_send"


def responses_controller_version(key: str) -> Dict[str, str]:
    response_file = f"image_upgrade_responses_ControllerVersion"
    response = load_fixture(response_file).get(key)
    print(f"responses_controller_version: {key} : {response}")
    return response


class MockAnsibleModule:
    params = {}

    def fail_json(msg) -> AnsibleFailJson:
        raise AnsibleFailJson(msg)


@pytest.fixture
def module():
    return ControllerVersion(MockAnsibleModule)


@pytest.fixture
def mock_controller_version() -> ControllerVersion:
    return ControllerVersion(MockAnsibleModule)


def test_init_properties(module) -> None:
    """
    Properties are initialized to expected values
    """
    module._init_properties()
    assert isinstance(module.properties, dict)
    assert module.properties.get("response_data") == None
    assert module.properties.get("response") == None
    assert module.properties.get("result") == None


@pytest.mark.parametrize(
    "key, expected",
    [
        ("ControllerVersion_dev_false", False),
        ("ControllerVersion_dev_true", True),
        ("ControllerVersion_dev_none", None),
    ],
)
def test_dev(monkeypatch, module, key, expected) -> None:
    """
    Function description:

    ControllerVersion.dev returns:
        - True if NDFC is a development version
        - False if NDFC is not a development version
        - None otherwise

    Expectations:

    1. ControllerVersion.dev returns above values given corresponding responses

    Expected results:

    1. ControllerVersion_dev_false == False
    2. ControllerVersion_dev_true == True
    3. ControllerVersion_dev_none == None
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    module.refresh()
    assert module.dev == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("ControllerVersion_install_EASYFABRIC", "EASYFABRIC"),
        ("ControllerVersion_install_none", None),
    ],
)
def test_install(monkeypatch, module, key, expected) -> None:
    """
    Description:

    ControllerVersion.install returns:
        - Value of NDFC response "install" key, if present
        - None, if NDFC response "install" key is missing

    Expectations:

    1.  ControllerVersion.install returns above values given
        corresponding responses

    Expected results:

    1. ControllerVersion_install_EASYFABRIC == "EASYFABRIC"
    2. ControllerVersion_install_none == None
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    module.refresh()
    assert module.install == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("ControllerVersion_is_ha_enabled_true", True),
        ("ControllerVersion_is_ha_enabled_false", False),
        ("ControllerVersion_is_ha_enabled_none", None),
    ],
)
def test_is_ha_enabled(monkeypatch, module, key, expected) -> None:
    """
    Function description:

    ControllerVersion.is_ha_enabled returns:
        - True, if NDFC response "isHaEnabled" key == "true"
        - False, if NDFC response "isHaEnabled" key == "false"
        - None, if NDFC response "isHaEnabled" key is missing

    Expectations:

    1. install returns above values given corresponding responses

    Expected results:

    1. ControllerVersion_is_ha_enabled_true == True
    2. ControllerVersion_is_ha_enabled_false == False
    3. ControllerVersion_is_ha_enabled_none == None
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    module.refresh()
    assert module.is_ha_enabled == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("ControllerVersion_is_media_controller_true", True),
        ("ControllerVersion_is_media_controller_false", False),
        ("ControllerVersion_is_media_controller_none", None),
    ],
)
def test_is_media_controller(monkeypatch, module, key, expected) -> None:
    """
    Function description:

    ControllerVersion.is_media_controller returns:
        - True, if NDFC response "isMediaController" key == "true"
        - False, if NDFC response "isMediaController" key == "false"
        - None, if NDFC response "isMediaController" key is missing

    Expectations:

    1.  ControllerVersion.is_media_controller returns above values
        given corresponding responses

    Expected results:

    1. ControllerVersion_is_media_controller_true == True
    2. ControllerVersion_is_media_controller_false == False
    3. ControllerVersion_is_media_controller_none == None
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    module.refresh()
    assert module.is_media_controller == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("ControllerVersion_is_upgrade_inprogress_true", True),
        ("ControllerVersion_is_upgrade_inprogress_false", False),
        ("ControllerVersion_is_upgrade_inprogress_none", None),
    ],
)
def test_is_upgrade_inprogress(monkeypatch, module, key, expected) -> None:
    """
    Function description:

    ControllerVersion.is_ha_enabled returns:
        - True, if NDFC response "is_upgrade_inprogress" key == "true"
        - False, if NDFC response "is_upgrade_inprogress" key == "false"
        - None, if NDFC response "is_upgrade_inprogress" key is missing

    Expectations:

    1.  ControllerVersion.is_upgrade_inprogress returns above values
        given corresponding responses

    Expected results:

    1. ControllerVersion_is_upgrade_inprogress_true == True
    2. ControllerVersion_is_upgrade_inprogress_false == False
    3. ControllerVersion_is_upgrade_inprogress_none == None
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    module.refresh()
    assert module.is_upgrade_inprogress == expected


def test_response_data_present(monkeypatch, module) -> None:
    """
    Function description:

    ControllerVersion.response_data returns the "DATA" key in the
    NDFC response, which is a dictionary of key-value pairs.
    If the "DATA" key is absent, fail_json is called.

    Expectations:

    1.  ControllerVersion.response_data will return a dictionary of key-value
        pairs

    Expected results:

    1. ControllerVersion_DATA_present, ControllerVersion.response_data == type(dict)
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        key = "ControllerVersion_DATA_present"
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    module.refresh()
    assert isinstance(module.response_data, dict)


def test_response_data_not_present(monkeypatch, module) -> None:
    """
    Function description:

    See: test_response_data_present

    Expectations:

    1.  fail_json is called if the "DATA" key is absent

    Expected results:

    1. fail_json is called
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        key = "ControllerVersion_DATA_not_present"
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    with pytest.raises(AnsibleFailJson):
        module.refresh()


def test_result_200(monkeypatch, module) -> None:
    """
    Function description:

    ControllerVersion.result returns the result of its superclass
    method ImageUpgradeCommon._handle_response()

    Expectations:

    1.  For a 200 response with "message" key == "OK",
        ControllerVersion.result == {'found': True, 'success': True}

    Expected results:

    1. ControllerVersion_result_200 == {'found': True, 'success': True}
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        key = "ControllerVersion_get_return_code_200"
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    module.refresh()
    assert module.result == {"found": True, "success": True}


def test_result_404(monkeypatch, module) -> None:
    """
    Function description:

    See: test_result_200

    Expectations:

    1.  For a 404 response with "message" key == "Not Found",
        ControllerVersion.result == {'found': False, 'success': True}
        and ControllerVersion.refresh() calls fail_json

    Expected results:

    1. fail_json is called
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        key = "ControllerVersion_get_return_code_404"
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    with pytest.raises(AnsibleFailJson):
        module.refresh()


def test_result_500(monkeypatch, module) -> None:
    """
    Function description:

    See: test_result_200

    Expectations:

    1.  For a 500 response with any "message" key value,
        ControllerVersion.result == {'found': False, 'success': False}
        and ControllerVersion.refresh() calls fail_json

    Expected results:

    1. fail_json is called
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        key = "ControllerVersion_get_return_code_500"
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    with pytest.raises(AnsibleFailJson):
        module.refresh()


@pytest.mark.parametrize(
    "key, expected",
    [("ControllerVersion_mode_LAN", "LAN"), ("ControllerVersion_mode_none", None)],
)
def test_mode(monkeypatch, module, key, expected) -> None:
    """
    Function description:

    ControllerVersion.mode returns:
        - If NDFC response "mode" key is present, its value
        - If NDFC response "mode" key is not present, None

    Expectations:

    1.  ControllerVersion.mode returns above values
        given corresponding responses

    Expected results:

    1. ControllerVersion_mode_LAN == "LAN"
    2. ControllerVersion_mode_none == None
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    module.refresh()
    assert module.mode == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("ControllerVersion_uuid_UUID", "foo-uuid"),
        ("ControllerVersion_uuid_none", None),
    ],
)
def test_uuid(monkeypatch, module, key, expected) -> None:
    """
    Function description:

    ControllerVersion.uuid returns:
        - If NDFC response "uuid" key is present, its value
        - If NDFC response "uuid" key is not present, None

    Expectations:

    1.  ControllerVersion.uuid returns above values
        given corresponding responses

    Expected results:

    1. ControllerVersion_uuid_UUID == "foo-uuid"
    2. ControllerVersion_uuid_none == None
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    module.refresh()
    assert module.uuid == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("ControllerVersion_version_12.1.3b", "12.1.3b"),
        ("ControllerVersion_version_none", None),
    ],
)
def test_version(monkeypatch, module, key, expected) -> None:
    """
    Function description:

    ControllerVersion.version returns:
        - If NDFC response "version" key is present, its value
        - If NDFC response "version" key is not present, None

    Expectations:

    1.  ControllerVersion.version returns above values
        given corresponding responses

    Expected results:

    1. ControllerVersion_version_12.1.3b == "12.1.3b"
    2. ControllerVersion_version_none == None
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    module.refresh()
    assert module.version == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("ControllerVersion_version_12.1.3b", "12"),
        ("ControllerVersion_version_none", None),
    ],
)
def test_version_major(monkeypatch, module, key, expected) -> None:
    """
    Function description:

    version_major returns the major version of NDFC
    It derives this from the "version" key in the NDFC response
    by splitting the string on "." and returning the first element

    ControllerVersion.version_major returns:
        - If NDFC response "version" key is present, the major version
        - If NDFC response "version" key is not present, None

    Expectations:

    1.  ControllerVersion.version_major returns above values
        given corresponding responses

    Expected results:

    1. ControllerVersion_version_12.1.3b == "12"
    2. ControllerVersion_version_none == None
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    module.refresh()
    assert module.version_major == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("ControllerVersion_version_12.1.3b", "1"),
        ("ControllerVersion_version_none", None),
    ],
)
def test_version_minor(monkeypatch, module, key, expected) -> None:
    """
    Function description:

    version_minor returns the minor version of NDFC
    It derives this from the "version" key in the NDFC response
    by splitting the string on "." and returning the second element

    ControllerVersion.version_minor returns:
        - If NDFC response "version" key is present, the minor version
        - If NDFC response "version" key is not present, None

    Expectations:

    1.  ControllerVersion.version_minor returns above values
        given corresponding responses

    Expected results:

    1. ControllerVersion_version_12.1.3b == "1"
    2. ControllerVersion_version_none == None
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    module.refresh()
    assert module.version_minor == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("ControllerVersion_version_12.1.3b", "3b"),
        ("ControllerVersion_version_none", None),
    ],
)
def test_version_patch(monkeypatch, module, key, expected) -> None:
    """
    Function description:

    version_patch returns the patch version of NDFC
    It derives this from the "version" key in the NDFC response
    by splitting the string on "." and returning the third element

    ControllerVersion.version_patch returns:
        - If NDFC response "version" key is present, the patch version
        - If NDFC response "version" key is not present, None

    Expectations:

    1.  ControllerVersion.version_patch returns above values
        given corresponding responses

    Expected results:

    1. ControllerVersion_version_12.1.3b == "3b"
    2. ControllerVersion_version_none == None
    """

    def mock_dcnm_send_version(*args, **kwargs) -> Dict[str, Any]:
        return responses_controller_version(key)

    monkeypatch.setattr(dcnm_send_version, mock_dcnm_send_version)

    module.refresh()
    assert module.version_patch == expected
