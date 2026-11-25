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

"""
Unit tests for dcnm_get_switch_policies() and the dcnm_policy policy-group filter.

ND 4.2+ returns HTTP 500 for GET .../policies/switches?serialNumber=<list> when a
switch has a policy group attached (policy ID "POLICY-GROUP-<id>~<serial>").
The helper must then read the switches one by one.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_get_switch_policies,
)

MULTI = "/policies/switches?serialNumber={}"
SINGLE = "/policies/switches/{}"

POLICY_SW1 = {"policyId": "POLICY-100", "serialNumber": "SW1", "templateName": "switch_freeform"}
POLICY_SW2 = {"policyId": "POLICY-200", "serialNumber": "SW2", "templateName": "banner"}
GROUP_SW2 = {"policyId": "POLICY-GROUP-300~SW2", "serialNumber": "SW2", "templateName": "banner"}


class FakeSend:
    """Records requests and answers from a path -> response map."""

    def __init__(self, responses):
        self.responses = responses
        self.paths = []

    def __call__(self, module, method, path, data=None):
        self.paths.append(path)
        return self.responses[path]


def ok(data):
    return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": data}


def test_multi_switch_request_used_when_it_works():
    send = FakeSend({MULTI.format("SW1,SW2"): ok([POLICY_SW1, POLICY_SW2])})
    assert dcnm_get_switch_policies(None, "SW1,SW2", MULTI, SINGLE, send=send) == [POLICY_SW1, POLICY_SW2]
    assert send.paths == [MULTI.format("SW1,SW2")]


def test_falls_back_per_switch_on_http_500():
    send = FakeSend(
        {
            MULTI.format("SW1,SW2"): {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": 'For input string: "300~SW2"'},
            SINGLE.format("SW1"): ok([POLICY_SW1]),
            SINGLE.format("SW2"): ok([POLICY_SW2, GROUP_SW2]),
        }
    )
    result = dcnm_get_switch_policies(None, ["SW1", "SW2"], MULTI, SINGLE, send=send)
    assert result == [POLICY_SW1, POLICY_SW2, GROUP_SW2]
    assert send.paths == [MULTI.format("SW1,SW2"), SINGLE.format("SW1"), SINGLE.format("SW2")]


def test_no_fallback_when_answer_is_not_an_http_error():
    # Previous behaviour: anything that is not a 200 list means "no policies".
    send = FakeSend({MULTI.format("SW1"): []})
    assert dcnm_get_switch_policies(None, "SW1", MULTI, SINGLE, send=send) == []
    assert send.paths == [MULTI.format("SW1")]


def test_empty_serial_list_sends_nothing():
    send = FakeSend({})
    assert dcnm_get_switch_policies(None, "", MULTI, SINGLE, send=send) == []
    assert send.paths == []


def test_dcnm_policy_drops_policy_group_entries(monkeypatch):
    from ansible_collections.cisco.dcnm.plugins.modules import dcnm_policy

    monkeypatch.setattr(
        dcnm_policy,
        "dcnm_get_switch_policies",
        lambda module, snos, multi, single, send=None: [POLICY_SW2, GROUP_SW2],
    )
    obj = dcnm_policy.DcnmPolicy.__new__(dcnm_policy.DcnmPolicy)
    obj.module = None
    obj.paths = {"POLICY_GET_SWITCHES": MULTI, "POLICY_GET_SWITCH": SINGLE}
    assert obj.dcnm_policy_get_all_policies("SW2") == [POLICY_SW2]


@pytest.mark.parametrize("resp", [None, {}, {"RETURN_CODE": 200, "DATA": "not a list"}, {"RETURN_CODE": 401}, {"RETURN_CODE": 404}])
def test_no_fallback_unless_http_500(resp):
    send = FakeSend({MULTI.format("SW1"): resp})
    assert dcnm_get_switch_policies(None, "SW1", MULTI, SINGLE, send=send) == []
    assert send.paths == [MULTI.format("SW1")]


def test_fallback_skips_switch_that_fails():
    send = FakeSend(
        {
            MULTI.format("SW1,SW2"): {"RETURN_CODE": 500, "DATA": "error"},
            SINGLE.format("SW1"): {"RETURN_CODE": 500, "DATA": "error"},
            SINGLE.format("SW2"): ok([POLICY_SW2]),
        }
    )
    assert dcnm_get_switch_policies(None, ["SW1", "SW2"], MULTI, SINGLE, send=send) == [POLICY_SW2]


def test_trailing_comma_in_serial_string_is_ignored():
    send = FakeSend({MULTI.format("SW1,SW2"): ok([POLICY_SW1, POLICY_SW2])})
    assert dcnm_get_switch_policies(None, "SW1,SW2,", MULTI, SINGLE, send=send) == [POLICY_SW1, POLICY_SW2]
    assert send.paths == [MULTI.format("SW1,SW2")]


def test_dcnm_policy_keeps_regular_policies_unchanged(monkeypatch):
    from ansible_collections.cisco.dcnm.plugins.modules import dcnm_policy

    monkeypatch.setattr(
        dcnm_policy,
        "dcnm_get_switch_policies",
        lambda module, snos, multi, single, send=None: [POLICY_SW1, POLICY_SW2],
    )
    obj = dcnm_policy.DcnmPolicy.__new__(dcnm_policy.DcnmPolicy)
    obj.module = None
    obj.paths = {"POLICY_GET_SWITCHES": MULTI, "POLICY_GET_SWITCH": SINGLE}
    assert obj.dcnm_policy_get_all_policies("SW1,SW2") == [POLICY_SW1, POLICY_SW2]


def test_dcnm_template_policy_list_without_fabric_name(monkeypatch):
    # The single-switch request does not return fabricName.
    from ansible_collections.cisco.dcnm.plugins.modules import dcnm_template

    monkeypatch.setattr(
        dcnm_template,
        "dcnm_get_switch_policies",
        lambda module, snos, multi, single, send=None: [POLICY_SW2, POLICY_SW1],
    )
    obj = dcnm_template.DcnmTemplate.__new__(dcnm_template.DcnmTemplate)
    obj.module = None
    obj.paths = {"TEMP_GET_SWITCHES": MULTI, "TEMP_GET_SWITCH": SINGLE}
    assert obj.dcnm_template_get_policy_list("SW1,SW2", ["banner"]) == {
        "banner": {"POLICY-200": {"fabricName": "", "serialNumber": "SW2"}},
    }


def test_dcnm_template_policy_list_uses_both_paths(monkeypatch):
    from ansible_collections.cisco.dcnm.plugins.modules import dcnm_template

    seen = {}

    def fake(module, snos, multi, single, send=None):
        seen.update(snos=snos, multi=multi, single=single, send=send)
        return []

    monkeypatch.setattr(dcnm_template, "dcnm_get_switch_policies", fake)
    obj = dcnm_template.DcnmTemplate.__new__(dcnm_template.DcnmTemplate)
    obj.module = None
    obj.paths = {"TEMP_GET_SWITCHES": MULTI, "TEMP_GET_SWITCH": SINGLE}
    assert obj.dcnm_template_get_policy_list("SW1,", ["banner"]) == {}
    assert (seen["snos"], seen["multi"], seen["single"], seen["send"]) == ("SW1,", MULTI, SINGLE, dcnm_template.dcnm_send)


def test_policy_and_template_paths_have_single_switch_request():
    from ansible_collections.cisco.dcnm.plugins.modules import dcnm_policy, dcnm_template

    for version in (11, 12):
        policy_paths = dcnm_policy.DcnmPolicy.dcnm_policy_paths[version]
        template_paths = dcnm_template.DcnmTemplate.dcnm_template_paths[version]
        assert policy_paths["POLICY_GET_SWITCH"] == policy_paths["POLICY_GET_SWITCHES"].replace("?serialNumber={}", "/{}")
        assert template_paths["TEMP_GET_SWITCH"] == template_paths["TEMP_GET_SWITCHES"].replace("?serialNumber={}", "/{}")


def test_dcnm_network_reads_policies_per_switch():
    from ansible_collections.cisco.dcnm.plugins.modules import dcnm_network

    for paths in dcnm_network.DcnmNetwork.dcnm_network_paths.values():
        assert paths["GET_SWITCH_POLICIES"].endswith("/rest/control/policies/switches/{}")
