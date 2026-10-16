# Copyright (c) 2026 Cisco and/or its affiliates.
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

import inspect
from unittest.mock import Mock, patch

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm import (
    dcnm,
)


def version_response(version):
    return {
        "RETURN_CODE": 200,
        "DATA": {
            "version": version,
        },
    }


def action_version_response(version):
    return {
        "failed": False,
        "response": version_response(version),
    }


def test_dcnm_version_supported_returns_major_by_default():
    module = Mock()

    with patch.object(
        dcnm,
        "dcnm_send",
        return_value=version_response("12.4.1.245"),
    ) as dcnm_send:
        assert dcnm.dcnm_version_supported(module) == 12

    dcnm_send.assert_called_once()


def test_dcnm_version_supported_reuses_response_for_full_version():
    module = Mock()

    with patch.object(
        dcnm,
        "dcnm_send",
        return_value=version_response("12.4.1.245"),
    ) as dcnm_send:
        assert dcnm.dcnm_version_supported(
            module, return_full_version=True
        ) == (12, "12.4.1.245")

    dcnm_send.assert_called_once()


def test_dcnm_version_supported_normalizes_alpha_suffix():
    module = Mock()

    with patch.object(
        dcnm,
        "dcnm_send",
        return_value=version_response("12.1.2e"),
    ):
        assert dcnm.dcnm_version_supported(
            module, return_full_version=True
        ) == (12, "12.1.2")


def test_dcnm_version_supported_normalizes_parenthesized_version():
    module = Mock()

    with patch.object(
        dcnm,
        "dcnm_send",
        return_value=version_response("11.5(1)"),
    ):
        assert dcnm.dcnm_version_supported(
            module, return_full_version=True
        ) == (11, "11.5.1")


def test_dcnm_version_supported_reports_malformed_response():
    module = Mock()
    module.fail_json.side_effect = RuntimeError("fail_json")
    response = {
        "RETURN_CODE": 200,
        "DATA": {
            "unexpected": "value",
        },
    }

    with patch.object(dcnm, "dcnm_send", return_value=response):
        with pytest.raises(RuntimeError, match="fail_json"):
            dcnm.dcnm_version_supported(
                module, return_full_version=True
            )

    message = module.fail_json.call_args.kwargs["msg"]
    assert "Unable to determine the DCNM/NDFC Software Version" in message
    assert str(response) in message


def test_dcnm_version_supported_reports_failed_http_responses():
    module = Mock()
    module.fail_json.side_effect = RuntimeError("fail_json")
    responses = [
        {
            "RETURN_CODE": 401,
            "MESSAGE": "Unauthorized",
        },
        {
            "RETURN_CODE": 503,
            "MESSAGE": "Service unavailable",
        },
    ]

    with patch.object(dcnm, "dcnm_send", side_effect=responses):
        with pytest.raises(RuntimeError, match="fail_json"):
            dcnm.dcnm_version_supported(
                module, return_full_version=True
            )

    message = module.fail_json.call_args.kwargs["msg"]
    assert "Unauthorized" in message
    assert "Service unavailable" in message


def test_dcnm_version_supported_reports_non_mapping_responses():
    module = Mock()
    module.fail_json.side_effect = RuntimeError("fail_json")

    with patch.object(dcnm, "dcnm_send", side_effect=[None, []]):
        with pytest.raises(RuntimeError, match="fail_json"):
            dcnm.dcnm_version_supported(
                module, return_full_version=True
            )

    message = module.fail_json.call_args.kwargs["msg"]
    assert "None" in message
    assert "[]" in message


def test_get_nd_version_returns_major_minor_and_full_version():
    action = Mock()
    action._execute_module.return_value = action_version_response(
        "12.4.1.245"
    )

    assert dcnm.get_nd_version(
        action, {}, None, return_full_version=True
    ) == (12.4, "12.4.1.245")

    action._execute_module.assert_called_once()


def test_get_nd_version_normalizes_full_version_from_fallback_endpoint():
    action = Mock()
    action._execute_module.side_effect = [
        {
            "failed": False,
            "response": {
                "RETURN_CODE": 503,
                "MESSAGE": "Service unavailable",
            },
        },
        action_version_response("12.4.1a"),
    ]

    assert dcnm.get_nd_version(
        action, {}, None, return_full_version=True
    ) == (12.4, "12.4.1")

    assert action._execute_module.call_count == 2


def test_get_nd_version_preserves_actionable_lookup_failures():
    action = Mock()
    action._execute_module.side_effect = [
        {
            "failed": True,
            "msg": "Authentication failed",
        },
        {
            "failed": False,
            "response": {
                "RETURN_CODE": 503,
                "MESSAGE": "Service unavailable",
            },
        },
    ]
    action.error_handler.handle_failure.side_effect = (
        lambda msg: {"failed": True, "changed": False, "msg": msg}
    )

    result = dcnm.get_nd_version(
        action, {}, None, return_full_version=True
    )

    assert result["failed"] is True
    assert "Authentication failed" in result["msg"]
    assert "HTTP 503: Service unavailable" in result["msg"]


def test_get_nd_version_reports_malformed_success_responses():
    action = Mock()
    action._execute_module.side_effect = [
        {
            "failed": False,
            "response": {
                "RETURN_CODE": 200,
                "DATA": {"unexpected": "value"},
            },
        },
        action_version_response("not-a-version"),
    ]
    action.error_handler.handle_failure.side_effect = (
        lambda msg: {"failed": True, "changed": False, "msg": msg}
    )

    result = dcnm.get_nd_version(
        action, {}, None, return_full_version=True
    )

    assert result["failed"] is True
    assert "did not contain DATA.version" in result["msg"]
    assert "malformed version 'not-a-version'" in result["msg"]


# DCNM715-SECONDARYGWS-001 / G7: one authoritative normalized full-version
# value crosses the helper/action/module boundary. The helper's public
# full-version contract is always an exact two-tuple; there is no opt-in third
# value. Normalization remains the existing digit-run behavior, including the
# explicitly accepted tradeoff that punctuation inside a version may collapse
# into a canonical dotted value.


def test_get_nd_version_g7_has_no_third_version_opt_in():
    signature = inspect.signature(dcnm.get_nd_version)

    assert tuple(signature.parameters) == (
        "action_module",
        "task_vars",
        "tmp",
        "return_full_version",
    )


@pytest.mark.parametrize(
    ("controller_version", "expected"),
    (
        ("12.4.1.245", (12.4, "12.4.1.245")),
        ("11.5(1)", (11.0, "11.5.1")),
        ("12.1.2e", (12.1, "12.1.2")),
        ("12.4.1a", (12.4, "12.4.1")),
        ("DEVEL", (11.0, "11.5.1")),
        ("12.2.3.+70", (12.2, "12.2.3.70")),
    ),
)
def test_get_nd_version_g7_returns_exact_normalized_pair(controller_version, expected):
    action = Mock()
    action._execute_module.return_value = action_version_response(controller_version)

    result = dcnm.get_nd_version(action, {}, None, return_full_version=True)

    assert result.__class__ is tuple
    assert len(result) == 2
    assert result[0].__class__ is float
    assert result[1].__class__ is str
    assert result == expected
    action._execute_module.assert_called_once()


def test_get_nd_version_g7_fallback_returns_exact_normalized_pair():
    action = Mock()
    action._execute_module.side_effect = [
        {
            "failed": False,
            "response": {
                "RETURN_CODE": 503,
                "MESSAGE": "Service unavailable",
            },
        },
        action_version_response("12.4.1a"),
    ]

    result = dcnm.get_nd_version(action, {}, None, return_full_version=True)

    assert result.__class__ is tuple
    assert len(result) == 2
    assert result == (12.4, "12.4.1")
    assert action._execute_module.call_count == 2


def test_get_nd_version_g7_default_scalar_contract_for_vrf_caller():
    """dcnm_vrf continues to use the unchanged default scalar contract."""
    action = Mock()
    action._execute_module.return_value = action_version_response("12.4.1a")

    result = dcnm.get_nd_version(action, {}, None)

    assert result.__class__ is float
    assert result == 12.4
