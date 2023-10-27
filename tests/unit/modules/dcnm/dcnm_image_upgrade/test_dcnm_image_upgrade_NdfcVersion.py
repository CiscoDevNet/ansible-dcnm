"""
ndfc_version: 12
description: Verify functionality of NdfcVersion
"""

from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_image_upgrade import NdfcVersion
from .fixture import load_fixture

dcnm_send_patch = "ansible_collections.cisco.dcnm.plugins.modules.dcnm_image_upgrade.dcnm_send"

def response_data_ndfc_version(key: str) -> Dict[str, str]:
    response_file = f"dcnm_image_upgrade_responses_NdfcVersion"
    response = load_fixture(response_file).get(key)
    print(f"response_data_ndfc_version: {key} : {response}")
    return response


class MockAnsibleModule:
    params = {}

    def fail_json(msg) -> AnsibleFailJson:
        raise AnsibleFailJson(msg)


@pytest.fixture
def module():
    return NdfcVersion(MockAnsibleModule)


@pytest.fixture
def mock_ndfc_version() -> NdfcVersion:
    return NdfcVersion(MockAnsibleModule)


def test_init_properties(module) -> None:
    """
    Properties are initialized to expected values
    """
    module._init_properties()
    assert isinstance(module.properties, dict)
    assert module.properties.get("ndfc_data") == None
    assert module.properties.get("ndfc_response") == None
    assert module.properties.get("ndfc_result") == None


@pytest.mark.parametrize(
    "key, expected",
    [
        ("NdfcVersion_dev_false", False),
        ("NdfcVersion_dev_true", True),
        ("NdfcVersion_dev_none", None),
    ],
)
def test_dev(monkeypatch, module, key, expected) -> None:
    """
    Function description:

    NdfcVersion.dev returns:
        - True if NDFC is a development version
        - False if NDFC is not a development version
        - None otherwise

    Expectations:

    1. NdfcVersion.dev returns above values given corresponding responses

    Expected results:

    1. NdfcVersion_dev_false == False
    2. NdfcVersion_dev_true == True
    3. NdfcVersion_dev_none == None
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        return response_data_ndfc_version(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    module.refresh()
    assert module.dev == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("NdfcVersion_install_EASYFABRIC", "EASYFABRIC"),
        ("NdfcVersion_install_none", None),
    ],
)
def test_install(monkeypatch, module, key, expected) -> None:
    """
    Description:

    NdfcVersion.install returns:
        - Value of NDFC response "install" key, if present
        - None, if NDFC response "install" key is missing

    Expectations:

    1.  NdfcVersion.install returns above values given
        corresponding responses

    Expected results:

    1. NdfcVersion_install_EASYFABRIC == "EASYFABRIC"
    2. NdfcVersion_install_none == None
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        return response_data_ndfc_version(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    module.refresh()
    assert module.install == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("NdfcVersion_is_ha_enabled_true", True),
        ("NdfcVersion_is_ha_enabled_false", False),
        ("NdfcVersion_is_ha_enabled_none", None),
    ],
)
def test_is_ha_enabled(monkeypatch, module, key, expected) -> None:
    """
    Function description:

    NdfcVersion.is_ha_enabled returns:
        - True, if NDFC response "isHaEnabled" key == "true"
        - False, if NDFC response "isHaEnabled" key == "false"
        - None, if NDFC response "isHaEnabled" key is missing

    Expectations:

    1. install returns above values given corresponding responses

    Expected results:

    1. NdfcVersion_is_ha_enabled_true == True
    2. NdfcVersion_is_ha_enabled_false == False
    3. NdfcVersion_is_ha_enabled_none == None
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        return response_data_ndfc_version(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    module.refresh()
    assert module.is_ha_enabled == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("NdfcVersion_is_media_controller_true", True),
        ("NdfcVersion_is_media_controller_false", False),
        ("NdfcVersion_is_media_controller_none", None),
    ],
)
def test_is_media_controller(monkeypatch, module, key, expected) -> None:
    """
    Function description:

    NdfcVersion.is_media_controller returns:
        - True, if NDFC response "isMediaController" key == "true"
        - False, if NDFC response "isMediaController" key == "false"
        - None, if NDFC response "isMediaController" key is missing

    Expectations:

    1.  NdfcVersion.is_media_controller returns above values
        given corresponding responses

    Expected results:

    1. NdfcVersion_is_media_controller_true == True
    2. NdfcVersion_is_media_controller_false == False
    3. NdfcVersion_is_media_controller_none == None
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        return response_data_ndfc_version(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    module.refresh()
    assert module.is_media_controller == expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("NdfcVersion_is_upgrade_inprogress_true", True),
        ("NdfcVersion_is_upgrade_inprogress_false", False),
        ("NdfcVersion_is_upgrade_inprogress_none", None),
    ],
)
def test_is_upgrade_inprogress(monkeypatch, module, key, expected) -> None:
    """
    Function description:

    NdfcVersion.is_ha_enabled returns:
        - True, if NDFC response "is_upgrade_inprogress" key == "true"
        - False, if NDFC response "is_upgrade_inprogress" key == "false"
        - None, if NDFC response "is_upgrade_inprogress" key is missing

    Expectations:

    1.  NdfcVersion.is_upgrade_inprogress returns above values
        given corresponding responses

    Expected results:

    1. NdfcVersion_is_upgrade_inprogress_true == True
    2. NdfcVersion_is_upgrade_inprogress_false == False
    3. NdfcVersion_is_upgrade_inprogress_none == None
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        return response_data_ndfc_version(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    module.refresh()
    assert module.is_upgrade_inprogress == expected


def test_ndfc_data_present(monkeypatch, module) -> None:
    """
    Function description:

    NdfcVersion.ndfc_data returns the "DATA" key in the
    NDFC response, which is a dictionary of key-value pairs.
    If the "DATA" key is absent, fail_json is called.

    Expectations:

    1.  NdfcVersion.ndfc_data will return a dictionary of key-value
        pairs

    Expected results:

    1. NdfcVersion_DATA_present, NdfcVersion.ndfc_data == type(dict)
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        key = "NdfcVersion_DATA_present"
        return response_data_ndfc_version(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    module.refresh()
    assert isinstance(module.ndfc_data, dict)


def test_ndfc_data_not_present(monkeypatch, module) -> None:
    """
    Function description:

    See: test_ndfc_data_present

    Expectations:

    1.  fail_json is called if the "DATA" key is absent

    Expected results:

    1. fail_json is called
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        key = "NdfcVersion_DATA_not_present"
        return response_data_ndfc_version(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    with pytest.raises(AnsibleFailJson):
        module.refresh()


def test_ndfc_result_200(monkeypatch, module) -> None:
    """
    Function description:

    NdfcVersion.ndfc_result returns the result of its superclass
    method NdfcAnsibleImageUpgradeCommon._handle_response()

    Expectations:

    1.  For a 200 response with "message" key == "OK",
        NdfcVersion.ndfc_result == {'found': True, 'success': True}

    Expected results:

    1. NdfcVersion_result_200 == {'found': True, 'success': True}
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        key = "NdfcVersion_get_return_code_200"
        return response_data_ndfc_version(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    module.refresh()
    assert module.ndfc_result == {"found": True, "success": True}


def test_ndfc_result_404(monkeypatch, module) -> None:
    """
    Function description:

    See: test_ndfc_result_200

    Expectations:

    1.  For a 404 response with "message" key == "Not Found",
        NdfcVersion.ndfc_result == {'found': False, 'success': True}
        and NdfcVersion.refresh() calls fail_json

    Expected results:

    1. fail_json is called
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        key = "NdfcVersion_get_return_code_404"
        return response_data_ndfc_version(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    with pytest.raises(AnsibleFailJson):
        module.refresh()


def test_ndfc_result_500(monkeypatch, module) -> None:
    """
    Function description:

    See: test_ndfc_result_200

    Expectations:

    1.  For a 500 response with any "message" key value,
        NdfcVersion.ndfc_result == {'found': False, 'success': False}
        and NdfcVersion.refresh() calls fail_json

    Expected results:

    1. fail_json is called
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        key = "NdfcVersion_get_return_code_500"
        return response_data_ndfc_version(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    with pytest.raises(AnsibleFailJson):
        module.refresh()


@pytest.mark.parametrize(
    "key, expected", [("NdfcVersion_mode_LAN", "LAN"), ("NdfcVersion_mode_none", None)]
)
def test_mode(monkeypatch, module, key, expected) -> None:
    """
    Function description:

    NdfcVersion.mode returns:
        - If NDFC response "mode" key is present, its value
        - If NDFC response "mode" key is not present, None

    Expectations:

    1.  NdfcVersion.mode returns above values
        given corresponding responses

    Expected results:

    1. NdfcVersion_mode_LAN == "LAN"
    2. NdfcVersion_mode_none == None
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        return response_data_ndfc_version(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    module.refresh()
    assert module.mode == expected


@pytest.mark.parametrize(
    "key, expected",
    [("NdfcVersion_uuid_UUID", "foo-uuid"), ("NdfcVersion_uuid_none", None)],
)
def test_uuid(monkeypatch, module, key, expected) -> None:
    """
    Function description:

    NdfcVersion.uuid returns:
        - If NDFC response "uuid" key is present, its value
        - If NDFC response "uuid" key is not present, None

    Expectations:

    1.  NdfcVersion.uuid returns above values
        given corresponding responses

    Expected results:

    1. NdfcVersion_uuid_UUID == "foo-uuid"
    2. NdfcVersion_uuid_none == None
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        return response_data_ndfc_version(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    module.refresh()
    assert module.uuid == expected


@pytest.mark.parametrize(
    "key, expected",
    [("NdfcVersion_version_12.1.3b", "12.1.3b"), ("NdfcVersion_version_none", None)],
)
def test_version(monkeypatch, module, key, expected) -> None:
    """
    Function description:

    NdfcVersion.version returns:
        - If NDFC response "version" key is present, its value
        - If NDFC response "version" key is not present, None

    Expectations:

    1.  NdfcVersion.version returns above values
        given corresponding responses

    Expected results:

    1. NdfcVersion_version_12.1.3b == "12.1.3b"
    2. NdfcVersion_version_none == None
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        return response_data_ndfc_version(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    module.refresh()
    assert module.version == expected


@pytest.mark.parametrize(
    "key, expected",
    [("NdfcVersion_version_12.1.3b", "12"), ("NdfcVersion_version_none", None)],
)
def test_version_major(monkeypatch, module, key, expected) -> None:
    """
    Function description:

    version_major returns the major version of NDFC
    It derives this from the "version" key in the NDFC response
    by splitting the string on "." and returning the first element

    NdfcVersion.version_major returns:
        - If NDFC response "version" key is present, the major version
        - If NDFC response "version" key is not present, None

    Expectations:

    1.  NdfcVersion.version_major returns above values
        given corresponding responses

    Expected results:

    1. NdfcVersion_version_12.1.3b == "12"
    2. NdfcVersion_version_none == None
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        return response_data_ndfc_version(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    module.refresh()
    assert module.version_major == expected


@pytest.mark.parametrize(
    "key, expected",
    [("NdfcVersion_version_12.1.3b", "1"), ("NdfcVersion_version_none", None)],
)
def test_version_minor(monkeypatch, module, key, expected) -> None:
    """
    Function description:

    version_minor returns the minor version of NDFC
    It derives this from the "version" key in the NDFC response
    by splitting the string on "." and returning the second element

    NdfcVersion.version_minor returns:
        - If NDFC response "version" key is present, the minor version
        - If NDFC response "version" key is not present, None

    Expectations:

    1.  NdfcVersion.version_minor returns above values
        given corresponding responses

    Expected results:

    1. NdfcVersion_version_12.1.3b == "1"
    2. NdfcVersion_version_none == None
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        return response_data_ndfc_version(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    module.refresh()
    assert module.version_minor == expected


@pytest.mark.parametrize(
    "key, expected",
    [("NdfcVersion_version_12.1.3b", "3b"), ("NdfcVersion_version_none", None)],
)
def test_version_patch(monkeypatch, module, key, expected) -> None:
    """
    Function description:

    version_patch returns the patch version of NDFC
    It derives this from the "version" key in the NDFC response
    by splitting the string on "." and returning the third element

    NdfcVersion.version_patch returns:
        - If NDFC response "version" key is present, the patch version
        - If NDFC response "version" key is not present, None

    Expectations:

    1.  NdfcVersion.version_patch returns above values
        given corresponding responses

    Expected results:

    1. NdfcVersion_version_12.1.3b == "3b"
    2. NdfcVersion_version_none == None
    """

    def mock_dcnm_send(*args, **kwargs) -> Dict[str, Any]:
        return response_data_ndfc_version(key)

    monkeypatch.setattr(dcnm_send_patch, mock_dcnm_send)

    module.refresh()
    assert module.version_patch == expected
