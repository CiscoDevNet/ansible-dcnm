from typing import Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_image_upgrade import (
    NdfcAnsibleImageUpgradeCommon, NdfcEndpoints)

from .fixture import load_fixture

"""
ndfc_version: 12
description: Verify functionality of class NdfcAnsibleImageUpgradeCommon
"""


class MockAnsibleModule:
    params = {}

    def fail_json(msg) -> dict:
        raise AnsibleFailJson(msg)


@pytest.fixture
def module():
    return NdfcAnsibleImageUpgradeCommon(MockAnsibleModule)


def responses_ndfc_ansible_image_upgrade_common(key: str) -> Dict[str, str]:
    response_file = f"dcnm_image_upgrade_responses_NdfcAnsibleImageUpgradeCommon"
    response = load_fixture(response_file).get(key)
    verb = response.get("METHOD")
    print(f"{key} : {verb} : {response}")
    return {"response": response, "verb": verb}


def test_init_(module) -> None:
    """
    __init__ sets expected values
    """
    module.__init__(MockAnsibleModule)
    assert module.params == {}
    assert module.debug == True
    assert module.fd == None
    assert module.logfile == "/tmp/dcnm_image_upgrade.log"
    assert isinstance(module.endpoints, NdfcEndpoints)


@pytest.mark.parametrize(
    "key, expected",
    [
        ("mock_post_return_code_200_MESSAGE_OK", {"success": True, "changed": True}),
        (
            "mock_post_return_code_400_MESSAGE_NOT_OK",
            {"success": False, "changed": False},
        ),
        (
            "mock_post_return_code_200_ERROR_key_present",
            {"success": False, "changed": False},
        ),
    ],
)
def test_handle_response_post(module, key, expected) -> None:
    """
    verify _handle_reponse() return values for 200/OK response
    to POST request
    """
    data = responses_ndfc_ansible_image_upgrade_common(key)
    result = module._handle_response(data.get("response"), data.get("verb"))
    assert result.get("success") == expected.get("success")
    assert result.get("changed") == expected.get("changed")


@pytest.mark.parametrize(
    "key, expected",
    [
        ("mock_get_return_code_200_MESSAGE_OK", {"success": True, "found": True}),
        ("mock_get_return_code_200_MESSAGE_not_OK", {"success": False, "found": False}),
        (
            "mock_get_return_code_404_MESSAGE_not_found",
            {"success": True, "found": False},
        ),
        ("mock_get_return_code_500_MESSAGE_OK", {"success": False, "found": False}),
    ],
)
def test_handle_response_get(module, key, expected) -> None:
    """
    verify _handle_reponse() return values for GET requests
    """
    data = responses_ndfc_ansible_image_upgrade_common(key)
    result = module._handle_response(data.get("response"), data.get("verb"))
    # TODO: We could assert on the dictionary, with a less granular error message
    # assert result == expected
    assert result.get("success") == expected.get("success")
    assert result.get("changed") == expected.get("changed")


def test_handle_response_unknown_response_verb(module) -> None:
    """
    verify that fail_json() is called if a unknown request verb is provided
    """
    data = responses_ndfc_ansible_image_upgrade_common("mock_unknown_response_verb")
    with pytest.raises(AnsibleFailJson, match=r"Unknown request verb \(FOO\)"):
        module._handle_response(data.get("response"), data.get("verb"))


@pytest.mark.parametrize(
    "key, expected",
    [
        ("mock_get_return_code_200_MESSAGE_OK", {"success": True, "found": True}),
        ("mock_get_return_code_200_MESSAGE_not_OK", {"success": False, "found": False}),
        (
            "mock_get_return_code_404_MESSAGE_not_found",
            {"success": True, "found": False},
        ),
        ("mock_get_return_code_500_MESSAGE_OK", {"success": False, "found": False}),
    ],
)
def test_handle_get_response(module, key, expected) -> None:
    """
    verify _handle_get_reponse() return values for GET requests

    NOTE: Adding this test increases coverage by 2% according to pytest-cov
    """
    data = responses_ndfc_ansible_image_upgrade_common(key)
    result = module._handle_get_response(data.get("response"))

    assert result.get("success") == expected.get("success")
    assert result.get("changed") == expected.get("changed")


@pytest.mark.parametrize(
    "key, expected",
    [
        ("mock_post_return_code_200_MESSAGE_OK", {"success": True, "changed": True}),
        (
            "mock_post_return_code_400_MESSAGE_NOT_OK",
            {"success": False, "changed": False},
        ),
        (
            "mock_post_return_code_200_ERROR_key_present",
            {"success": False, "changed": False},
        ),
    ],
)
def test_handle_post_put_delete_response(module, key, expected) -> None:
    """
    _handle_post_put_delete_response() return expected values for POST requests
    NOTE: This method is covered in test_handle_response_post() above, but...
    NOTE: Adding this test increases coverage by 2% according to pytest-cov
    """
    data = responses_ndfc_ansible_image_upgrade_common(key)
    result = module._handle_post_put_delete_response(data.get("response"))
    assert result.get("success") == expected.get("success")
    assert result.get("changed") == expected.get("changed")


@pytest.mark.parametrize(
    "key, expected",
    [
        ("True", True),
        ("true", True),
        ("TRUE", True),
        ("True", True),
        ("False", False),
        ("false", False),
        ("FALSE", False),
        ("False", False),
        ("foo", "foo"),
        (0, 0),
        (1, 1),
        (None, None),
        (None, None),
        ({"foo": 10}, {"foo": 10}),
        ([1, 2, "3"], [1, 2, "3"]),
    ],
)
def test_make_boolean(module, key, expected) -> None:
    """
    verify that make_boolean() returns expected values for all cases
    """
    assert module.make_boolean(key) == expected


# def test_dcnm_image_upgrade_common_make_boolean(module) -> None:
#     """
#     NOTE: The above parameterized testcase results in 7% greater coverage according to pytest-cov versus for loops (below)
#     verify that make_boolean() returns expected values for all cases
#     """
#     for value in ["True", "true", "TRUE", True]:
#         assert module.make_boolean(value) == True
#     for value in ["False", "false", "FALSE", False]:
#         assert module.make_boolean(value) == False
#     for value in ["foo", 1, 0, None, {"foo": 10}, [1, 2, "3"]]:
#         assert module.make_boolean(value) == value


@pytest.mark.parametrize(
    "key, expected",
    [
        ("", None),
        ("none", None),
        ("None", None),
        ("NONE", None),
        ("null", None),
        ("Null", None),
        ("NULL", None),
        ("None", None),
        ("foo", "foo"),
        (0, 0),
        (1, 1),
        (True, True),
        (False, False),
        ({"foo": 10}, {"foo": 10}),
        ([1, 2, "3"], [1, 2, "3"]),
    ],
)
def test_make_none(module, key, expected) -> None:
    """
    verify that make_none() returns expected values for all cases
    """
    assert module.make_none(key) == expected


# def test_dcnm_image_upgrade_common_make_none(module) -> None:
#     """
#     NOTE: The above parameterized testcase results in 7% greater coverage according to pytest-cov versus for loops (below)
#     verify that make_none() returns expected values for all cases
#     """
#     for value in ["", "none", "None", "NONE", "null", "Null", "NULL", None]:
#         assert module.make_none(value) == None
#     for value in ["foo", 1, 0, True, False, {"foo": 10}, [1, 2, "3"]]:
#         assert module.make_none(value) == value


def test_log_msg_disabled(module) -> None:
    """
    verify that make_none() returns expected values for all cases
    """
    ERROR_MESSAGE = "This is an error message"
    module.debug = False
    assert module.log_msg(ERROR_MESSAGE) == None


def test_log_msg_enabled(tmp_path, module) -> None:
    """
    verify that make_none() returns expected values for all cases
    """
    directory = tmp_path / "test_log_msg"
    directory.mkdir()
    filename = directory / f"test_log_msg.txt"

    ERROR_MESSAGE = "This is an error message"
    module.debug = True
    module.logfile = filename
    module.log_msg(ERROR_MESSAGE)

    assert filename.read_text(encoding="UTF-8") == ERROR_MESSAGE + "\n"
    assert len(list(tmp_path.iterdir())) == 1


def test_log_msg_enabled_fail_json(tmp_path, module) -> None:
    """
    log_msg() calls fail_json() if the logfile cannot be opened
    """
    directory = tmp_path / "test_log_msg"
    directory.mkdir()
    filename = directory / f"test_{'a' * 2000}_log_msg.txt"

    ERROR_MESSAGE = "This is an error message"
    module.debug = True
    module.logfile = filename
    with pytest.raises(AnsibleFailJson, match=r"error opening logfile"):
        module.log_msg(ERROR_MESSAGE)
