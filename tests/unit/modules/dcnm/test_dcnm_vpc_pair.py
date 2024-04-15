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
__author__ = "Mallik Mudigonda"

from unittest.mock import patch
from _pytest.monkeypatch import MonkeyPatch

from .dcnm_module import TestDcnmModule, set_module_args, loadPlaybookData

# from typing import Any, Dict

import os
import copy
import json
import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm import dcnm_vpc_pair_utils
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm import dcnm
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_vpc_pair
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm_vpc_pair_utils import (
    dcnm_vpc_pair_paths as vpc_pair_paths,
)
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_vpc_pair import DcnmVpcPair

# Importing Fixtures
from .fixtures.dcnm_vpc_pair.dcnm_vpc_pair_common import dcnm_vpc_pair_fixture

from unittest.mock import Mock

# Fixtures path
fixture_path = os.path.join(os.path.dirname(__file__), "fixtures")
module_data_path = fixture_path + "/dcnm_vpc_pair/"

# UNIT TEST CASES


def load_data(module_name):
    path = os.path.join(module_data_path, "{0}.json".format(module_name))

    with open(path) as f:
        data = f.read()

    try:
        j_data = json.loads(data)
    except Exception as e:
        pass

    return j_data


def test_dcnm_vpc_pair_log_msg(monkeypatch, dcnm_vpc_pair_fixture):

    # Testing Function log_msg()

    vpc_pair = dcnm_vpc_pair_fixture
    vpc_pair.log_msg("This is a test message to test logging function\n")

    try:
        os.remove("dcnm_vpc_pair.log")
    except Exception as e:
        print(str(e))


@pytest.mark.parametrize(
    "tc_id, filename, wkey, hkey",
    [(1, "dcnm_vpc_pair_data", "vpc_pair_want", "vpc_pair_have_00001")],
)
def test_dcnm_vpc_pair_00001(
    tc_id, monkeypatch, dcnm_vpc_pair_fixture, filename, wkey, hkey
):

    # Testing Function dcnm_vpc_pair_merge_want_and_have_objects()

    vpc_pair = dcnm_vpc_pair_fixture

    data = load_data("dcnm_vpc_pair_data")
    want = data.get(wkey)
    have = data.get(hkey)

    vpc_pair.dcnm_vpc_pair_merge_want_and_have_objects(want, have)

    # Remove a key from have.
    have["nvPairs"].pop("PEER1_MEMBER_INTERFACES")

    vpc_pair.dcnm_vpc_pair_merge_want_and_have_objects(
        want["nvPairs"], have["nvPairs"]
    )


@pytest.mark.parametrize(
    "tc_id, filename, wkey, hkey",
    [
        (1, "dcnm_vpc_pair_data", "vpc_pair_want", "vpc_pair_have_00001"),
        (
            2,
            "dcnm_vpc_pair_data",
            "vpc_pair_want_00002",
            "vpc_pair_have_00002",
        ),
    ],
)
def test_dcnm_vpc_pair_00002(
    tc_id, monkeypatch, dcnm_vpc_pair_fixture, filename, wkey, hkey
):

    # Testing Function dcnm_vpc_pair_merge_want_and_have()

    vpc_pair = dcnm_vpc_pair_fixture

    data = load_data("dcnm_vpc_pair_data")
    want = data.get(wkey)
    have = data.get(hkey)

    vpc_pair.dcnm_vpc_pair_merge_want_and_have(want, have)

    if tc_id == 1:
        assert want["nvPairs"]["PEER1_MEMBER_INTERFACES"] == "e1/21,e1/20"
        assert want["nvPairs"]["PEER2_MEMBER_INTERFACES"] == "e1/21,e1/20"
        assert (
            want["nvPairs"]["PEER1_PO_CONF"] == "test command2\ntest command1"
        )
        assert (
            want["nvPairs"]["PEER2_PO_CONF"] == "test command2\ntest command1"
        )


@pytest.mark.parametrize(
    "tc_id, filename, vpc_info_key",
    [
        (1, "dcnm_vpc_pair_data", "vpc_pair_null_vpc_info"),
        (2, "dcnm_vpc_pair_data", "vpc_pair_query_cfg_00003_11"),
        (3, "dcnm_vpc_pair_data", "vpc_pair_query_cfg_00003_12"),
        (4, "dcnm_vpc_pair_data", "vpc_pair_query_cfg_00003_2"),
        (5, "dcnm_vpc_pair_data", "vpc_pair_query_cfg_00003_3"),
        (6, "dcnm_vpc_pair_data", "vpc_pair_query_cfg_00003_3"),
        (7, "dcnm_vpc_pair_data", "vpc_pair_query_cfg_00003_3"),
        (8, "dcnm_vpc_pair_data", "vpc_pair_query_cfg_00003_3"),
        (9, "dcnm_vpc_pair_data", "vpc_pair_query_invalid_cfg_00003"),
    ],
)
def test_dcnm_vpc_pair_00003(
    tc_id, monkeypatch, dcnm_vpc_pair_fixture, filename, vpc_info_key
):

    # MALLS: Non Null filters case ==> Testing Function dcnm_vpc_pair_get_diff_query()

    vpc_pair = dcnm_vpc_pair_fixture

    # Mock Functions
    data = load_data("dcnm_vpc_pair_data")
    vpc_pair.vpc_pair_info = data.get(vpc_info_key)
    vpc_pair.sn_swid = data.get("vpc_pair_sn_swids_00003")
    vpc_pair.ip_sn = data.get("vpc_pair_ip_sn")
    vpc_pair.paths = vpc_pair_paths[12]

    dcnm_send_side_effect = []

    resp = load_data("dcnm_vpc_pair_response")

    if tc_id < 7:
        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_00003"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_00003"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_00003"))
        dcnm_send_side_effect.append(
            copy.deepcopy(resp.get("vpc_pair_policy_resp_00003"))
        )
    elif tc_id == 7:
        dcnm_send_side_effect.append(resp.get("vpc_pair_null_vpc_info_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_null_policy_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_null_vpc_info_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_null_policy_resp"))
    elif tc_id == 8:
        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_00003"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_null_policy_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_00003"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_null_policy_resp"))

    mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
    monkeypatch.setattr(dcnm_vpc_pair_utils, "dcnm_send", mock_dcnm_send)

    vpc_pair.dcnm_vpc_pair_get_diff_query()

    # Asserts

    if tc_id < 7:
        assert len(vpc_pair.result["response"]) == 1


@pytest.mark.parametrize(
    "tc_id, filename, cfg_key, want_key",
    [
        (1, "dcnm_vpc_pair_data", "vpc_pair_null_cfg", "vpc_pair_null_want"),
        (2, "dcnm_vpc_pair_data", "vpc_pair_cfg_00004_1", "vpc_pair_want"),
    ],
)
def test_dcnm_vpc_pair_00004(
    tc_id, monkeypatch, dcnm_vpc_pair_fixture, filename, cfg_key, want_key
):

    # Testing Function dcnm_vpc_pair_get_diff_overridden()

    vpc_pair = dcnm_vpc_pair_fixture

    # Mock Functions
    data = load_data("dcnm_vpc_pair_data")
    vpc_pair.sn_swid = data.get("vpc_pair_sn_swids")
    vpc_pair.config = []
    vpc_pair.want = []

    config = data.get(cfg_key)
    if config:
        vpc_pair.config.append(config)

    want = data.get(want_key)
    if want:
        vpc_pair.want.append(want)

    vpc_pair.paths = vpc_pair_paths[12]

    dcnm_send_side_effect = []
    update_delete_payloads_side_effect = []
    get_diff_merge_side_effect = []

    resp = load_data("dcnm_vpc_pair_response")

    dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_1"))
    dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_1"))
    dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_1"))
    dcnm_send_side_effect.append(
        copy.deepcopy(resp.get("vpc_pair_policy_resp_1"))
    )

    dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_2"))
    dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_2"))
    dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_2"))
    dcnm_send_side_effect.append(
        copy.deepcopy(resp.get("vpc_pair_policy_resp_2"))
    )

    dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_3"))
    dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_3"))
    dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_3"))
    dcnm_send_side_effect.append(
        copy.deepcopy(resp.get("vpc_pair_policy_resp_3"))
    )

    update_delete_payloads_side_effect.append(
        "update_delete_payloads_mock_ret1"
    )
    update_delete_payloads_side_effect.append(
        "update_delete_payloads_mock_ret2"
    )
    update_delete_payloads_side_effect.append(
        "update_delete_payloads_mock_ret3"
    )

    get_diff_merge_side_effect.append("get_diff_merge_mock_ret1")

    mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
    monkeypatch.setattr(dcnm_vpc_pair_utils, "dcnm_send", mock_dcnm_send)

    mock_update_delete_payloads = Mock(
        side_effect=update_delete_payloads_side_effect
    )
    monkeypatch.setattr(
        DcnmVpcPair,
        "dcnm_vpc_pair_update_delete_payloads",
        mock_update_delete_payloads,
    )

    mock_get_diff_merge = Mock(side_effect=get_diff_merge_side_effect)
    monkeypatch.setattr(
        DcnmVpcPair,
        "dcnm_vpc_pair_get_diff_merge",
        mock_get_diff_merge,
    )

    vpc_pair.dcnm_vpc_pair_get_diff_overridden(vpc_pair.config)

    # Asserts


@pytest.mark.parametrize(
    "tc_id, filename, vpc_info_key, ip_sn_key",
    [
        (1, "dcnm_vpc_pair_data", "vpc_pair_null_vpc_info", "vpc_pair_ip_sn"),
        (2, "dcnm_vpc_pair_data", "vpc_pair_vpc_info_00005", "vpc_pair_ip_sn"),
        (3, "dcnm_vpc_pair_data", "vpc_pair_vpc_info_00005", "vpc_pair_ip_sn"),
        (4, "dcnm_vpc_pair_data", "vpc_pair_vpc_info_00005", "vpc_pair_ip_sn"),
        (5, "dcnm_vpc_pair_data", "vpc_pair_vpc_info_00005", "vpc_pair_ip_sn"),
    ],
)
def test_dcnm_vpc_pair_00005(
    tc_id, monkeypatch, dcnm_vpc_pair_fixture, filename, vpc_info_key, ip_sn_key
):

    # Testing Function dcnm_vpc_pair_get_diff_deleted()

    vpc_pair = dcnm_vpc_pair_fixture

    # Mock Functions
    data = load_data("dcnm_vpc_pair_data")

    vpc_pair.vpc_pair_info = data.get(vpc_info_key)
    vpc_pair.paths = vpc_pair_paths[12]
    vpc_pair.ip_sn = data.get(ip_sn_key)

    dcnm_send_side_effect = []
    update_delete_payloads_side_effect = []
    get_diff_overridden_side_effect = []

    resp = load_data("dcnm_vpc_pair_response")

    vpc_pair.sn_swid = data.get("vpc_pair_sn_swids")

    if tc_id < 3:
        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_1"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_1"))

        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_2"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_2"))

        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_3"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_3"))
    elif tc_id == 3:
        dcnm_send_side_effect.append([])
        dcnm_send_side_effect.append([])
        dcnm_send_side_effect.append([])
    elif tc_id == 4:
        vpc_pair.vpc_pair_info[0]["peerOneId"] = "10.122.84.190"

        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_1"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_1"))

        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_2"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_2"))

        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_3"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_3"))
    elif tc_id == 5:
        vpc_pair.vpc_pair_info[0]["peerTwoId"] = "10.122.84.190"

        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_1"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_1"))

        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_2"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_2"))

        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_3"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_3"))

    update_delete_payloads_side_effect.append(
        "update_delete_payloads_mock_ret_00005_1"
    )
    update_delete_payloads_side_effect.append(
        "update_delete_payloads_mock_r_00005_2"
    )
    update_delete_payloads_side_effect.append(
        "update_delete_payloads_mock_r_00005_3"
    )

    get_diff_overridden_side_effect.append("get_diff_overridden_mock_00005_1")

    mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
    monkeypatch.setattr(dcnm_vpc_pair_utils, "dcnm_send", mock_dcnm_send)

    mock_update_delete_payloads = Mock(
        side_effect=update_delete_payloads_side_effect
    )
    monkeypatch.setattr(
        DcnmVpcPair,
        "dcnm_vpc_pair_update_delete_payloads",
        mock_update_delete_payloads,
    )

    mock_get_diff_overridden = Mock(
        side_effect=get_diff_overridden_side_effect
    )
    monkeypatch.setattr(
        DcnmVpcPair,
        "dcnm_vpc_pair_get_diff_overridden",
        mock_get_diff_overridden,
    )

    vpc_pair.dcnm_vpc_pair_get_diff_deleted()


@pytest.mark.parametrize(
    "tc_id, filename, have_key, deploy",
    [
        (1, "dcnm_vpc_pair_data", "vpc_pair_have_00006", True),
        (2, "dcnm_vpc_pair_data", "vpc_pair_have_00006", False),
    ],
)
def test_dcnm_vpc_pair_00006(
    tc_id, monkeypatch, dcnm_vpc_pair_fixture, filename, have_key, deploy
):

    # Testing Function dcnm_vpc_pair_update_delete_payloads()

    vpc_pair = dcnm_vpc_pair_fixture

    vpc_pair.fabric = "mmudigon-svi"
    vpc_pair.deploy = deploy

    # Mock Functions
    data = load_data("dcnm_vpc_pair_data")
    have = data.get(have_key)

    vpc_pair.dcnm_vpc_pair_update_delete_payloads(have)

    # Asserts

    if tc_id == 1:
        assert len(vpc_pair.diff_delete) == 1
        assert len(vpc_pair.diff_delete_deploy) == 1
    elif tc_id == 2:
        assert len(vpc_pair.diff_delete) == 1
        assert len(vpc_pair.diff_delete_deploy) == 0


@pytest.mark.parametrize(
    "tc_id, filename, want_key, have_key, deploy",
    [
        (
            1,
            "dcnm_vpc_pair_data",
            "vpc_pair_null_want",
            "vpc_pair_null_have",
            True,
        ),
        (2, "dcnm_vpc_pair_data", "vpc_pair_want", "vpc_pair_null_have", True),
        (
            3,
            "dcnm_vpc_pair_data",
            "vpc_pair_want",
            "vpc_pair_null_have",
            False,
        ),
        (4, "dcnm_vpc_pair_data", "vpc_pair_want", "vpc_pair_have", True),
        (5, "dcnm_vpc_pair_data", "vpc_pair_want", "vpc_pair_have", False),
        (
            6,
            "dcnm_vpc_pair_data",
            "vpc_pair_want",
            "vpc_pair_have_00001",
            True,
        ),
        (
            7,
            "dcnm_vpc_pair_data",
            "vpc_pair_want",
            "vpc_pair_have_00001",
            False,
        ),
        (8, "dcnm_vpc_pair_data", "vpc_pair_want", "vpc_pair_have", True),
        (9, "dcnm_vpc_pair_data", "vpc_pair_want", "vpc_pair_have", True),
    ],
)
def test_dcnm_vpc_pair_00007(
    tc_id, monkeypatch, dcnm_vpc_pair_fixture, filename, want_key, have_key, deploy
):

    # Testing Function dcnm_vpc_pair_get_diff_merge()

    vpc_pair = dcnm_vpc_pair_fixture

    data = load_data("dcnm_vpc_pair_data")
    want = data.get(want_key)
    have = data.get(have_key)

    vpc_pair.ip_sn = data.get("vpc_pair_ip_sn")
    vpc_pair.sn_ip = data.get("vpc_pair_sn_ip")
    vpc_pair.fabric = "mmudigon-svi"
    vpc_pair.deploy = deploy
    vpc_pair.paths = vpc_pair_paths[12]
    vpc_pair.module.params["state"] = "merged"

    if want:
        vpc_pair.want = [want]
        want["PEER1_MEMBER_INTERFACES_defaulted"] = False
        want["PEER2_MEMBER_INTERFACES_defaulted"] = False
    if have:
        vpc_pair.have = [have]

    dcnm_send_side_effect = []

    resp = load_data("dcnm_vpc_pair_response")

    if tc_id < 9:
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))
    else:
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_sync_status_not_in_sync")
        )

    mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
    monkeypatch.setattr(dcnm_vpc_pair_utils, "dcnm_send", mock_dcnm_send)

    vpc_pair.dcnm_vpc_pair_get_diff_merge()

    # Asserts

    if tc_id == 1:
        assert len(vpc_pair.diff_create) == 0
        assert len(vpc_pair.diff_delete) == 0
        assert len(vpc_pair.diff_modify) == 0
        assert len(vpc_pair.diff_deploy) == 0
    elif tc_id == 2:
        assert len(vpc_pair.diff_create) == 1
        assert len(vpc_pair.diff_delete) == 0
        assert len(vpc_pair.diff_modify) == 0
        assert len(vpc_pair.diff_deploy) == 1
    elif tc_id == 3:
        assert len(vpc_pair.diff_create) == 1
        assert len(vpc_pair.diff_delete) == 0
        assert len(vpc_pair.diff_modify) == 0
        assert len(vpc_pair.diff_deploy) == 0
    elif tc_id == 4:
        assert len(vpc_pair.diff_create) == 0
        assert len(vpc_pair.diff_delete) == 0
        assert len(vpc_pair.diff_modify) == 0
        assert len(vpc_pair.diff_deploy) == 0
    elif tc_id == 5:
        assert len(vpc_pair.diff_create) == 0
        assert len(vpc_pair.diff_delete) == 0
        assert len(vpc_pair.diff_modify) == 0
        assert len(vpc_pair.diff_deploy) == 0
    elif tc_id == 6:
        assert len(vpc_pair.diff_create) == 0
        assert len(vpc_pair.diff_delete) == 0
        assert len(vpc_pair.diff_modify) == 1
        assert len(vpc_pair.diff_deploy) == 1
    elif tc_id == 7:
        assert len(vpc_pair.diff_create) == 0
        assert len(vpc_pair.diff_delete) == 0
        assert len(vpc_pair.diff_modify) == 1
        assert len(vpc_pair.diff_deploy) == 0
    elif tc_id == 8:
        assert len(vpc_pair.diff_create) == 0
        assert len(vpc_pair.diff_delete) == 0
        assert len(vpc_pair.diff_modify) == 0
        assert len(vpc_pair.diff_deploy) == 0
    elif tc_id == 9:
        assert len(vpc_pair.diff_create) == 0
        assert len(vpc_pair.diff_delete) == 0
        assert len(vpc_pair.diff_modify) == 0
        assert len(vpc_pair.diff_deploy) == 1


@pytest.mark.parametrize(
    "tc_id, filename, state, want_key, have_key, cfg_key",
    [
        (
            1,
            "dcnm_vpc_pair_data",
            "replaced",
            "vpc_pair_want",
            "vpc_pair_have",
            "vpc_pair_null_cfg",
        ),
        (
            2,
            "dcnm_vpc_pair_data",
            "merged",
            "vpc_pair_want",
            "vpc_pair_have",
            "vpc_pair_null_cfg",
        ),
        (
            3,
            "dcnm_vpc_pair_data",
            "merged",
            "vpc_pair_want",
            "vpc_pair_have_00008",
            "vpc_pair_cfg_00008",
        ),
        (
            4,
            "dcnm_vpc_pair_data",
            "merged",
            "vpc_pair_want",
            "vpc_pair_have",
            "vpc_pair_cfg_00008",
        ),
    ],
)
def test_dcnm_vpc_pair_00008(
    tc_id,
    monkeypatch,
    dcnm_vpc_pair_fixture,
    filename,
    state,
    want_key,
    have_key,
    cfg_key,
):

    # Testing Function  dcnm_vpc_pair_update_want()

    vpc_pair = dcnm_vpc_pair_fixture

    data = load_data("dcnm_vpc_pair_data")
    want = data.get(want_key)
    have = data.get(have_key)
    cfg = data.get(cfg_key)

    vpc_pair.want = [want]
    vpc_pair.have = [have]
    vpc_pair.config = cfg
    vpc_pair.module.params["state"] = state
    vpc_pair.ip_sn = data.get("vpc_pair_ip_sn")

    vpc_pair.dcnm_vpc_pair_update_want()


@pytest.mark.parametrize(
    "tc_id, filename, vpc_info_key, cfg_key",
    [
        (
            1,
            "dcnm_vpc_pair_data",
            "vpc_pair_null_vpc_info",
            "vpc_pair_null_cfg",
        ),
        (
            2,
            "dcnm_vpc_pair_data",
            "vpc_pair_null_vpc_info",
            "vpc_pair_00004_1",
        ),
        (
            3,
            "dcnm_vpc_pair_data",
            "vpc_pair_vpc_info_00005",
            "vpc_pair_null_cfg",
        ),
        (
            4,
            "dcnm_vpc_pair_data",
            "vpc_pair_vpc_info_00005",
            "vpc_pair_cfg_00004_1",
        ),
    ],
)
def test_dcnm_vpc_pair_00009(
    tc_id, monkeypatch, dcnm_vpc_pair_fixture, filename, vpc_info_key, cfg_key
):

    # Testing Function dcnm_vpc_pair_get_want()

    vpc_pair = dcnm_vpc_pair_fixture

    data = load_data("dcnm_vpc_pair_data")
    vpc_info = data.get(vpc_info_key)
    cfg = data.get(cfg_key)

    vpc_pair.config = cfg
    vpc_pair.vpc_pair_info = vpc_info
    vpc_pair.ip_sn = data.get("vpc_pair_ip_sn")

    vpc_pair.dcnm_vpc_pair_get_want()

    # Asserts

    if tc_id == 4:
        assert len(vpc_pair.want) == 3


@pytest.mark.parametrize(
    "tc_id, filename, want_key",
    [
        (1, "dcnm_vpc_pair_data", "vpc_pair_null_want"),
        (2, "dcnm_vpc_pair_data", "vpc_pair_want_00010"),
    ],
)
def test_dcnm_vpc_pair_00010(
    tc_id, monkeypatch, dcnm_vpc_pair_fixture, filename, want_key
):

    # Testing Function dcnm_vpc_pair_get_have()

    vpc_pair = dcnm_vpc_pair_fixture

    data = load_data("dcnm_vpc_pair_data")
    want = data.get(want_key)

    vpc_pair.ip_sn = data.get("vpc_pair_ip_sn")
    vpc_pair.sn_swid = data.get("vpc_pair_sn_swids")
    vpc_pair.paths = vpc_pair_paths[12]

    vpc_pair.want = want

    dcnm_send_side_effect = []

    resp = load_data("dcnm_vpc_pair_response")

    dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_1"))
    dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_1"))
    dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_1"))
    dcnm_send_side_effect.append(
        copy.deepcopy(resp.get("vpc_pair_policy_resp_1"))
    )
    dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_2"))
    dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_2"))
    dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_3"))
    dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_3"))

    mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
    monkeypatch.setattr(dcnm_vpc_pair_utils, "dcnm_send", mock_dcnm_send)

    vpc_pair.dcnm_vpc_pair_get_have()

    # Asserts

    if tc_id == 2:
        assert len(vpc_pair.want) == 4
        assert len(vpc_pair.have) == 3


@pytest.mark.parametrize(
    "tc_id, filename, want_key",
    [(2, "dcnm_vpc_pair_data", "vpc_pair_want_00010")],
)
def test_dcnm_vpc_pair_00010_2(
    tc_id, monkeypatch, dcnm_vpc_pair_fixture, filename, want_key
):

    # Testing Function dcnm_vpc_pair_get_have()
    # Checking if peerOneId does not match existing

    vpc_pair = dcnm_vpc_pair_fixture

    data = load_data("dcnm_vpc_pair_data")
    want = data.get(want_key)

    vpc_pair.ip_sn = data.get("vpc_pair_ip_sn")
    vpc_pair.sn_swid = data.get("vpc_pair_sn_swids")
    vpc_pair.paths = vpc_pair_paths[12]

    vpc_pair.want = want
    want.pop()
    want.pop()
    want.pop()

    # Modify peerOneId in want and check

    want[0]["peerOneId"] = "TEST820SDPR"

    dcnm_send_side_effect = []

    resp = load_data("dcnm_vpc_pair_response")

    dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_1"))
    dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_1"))

    mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
    monkeypatch.setattr(dcnm_vpc_pair_utils, "dcnm_send", mock_dcnm_send)

    try:
        vpc_pair.dcnm_vpc_pair_get_have()
    except Exception as e:
        assert "Cannot create peering" in str(e)


@pytest.mark.parametrize(
    "tc_id, filename, want_key",
    [(2, "dcnm_vpc_pair_data", "vpc_pair_want_00010")],
)
def test_dcnm_vpc_pair_00010_3(
    tc_id, monkeypatch, dcnm_vpc_pair_fixture, filename, want_key
):

    # Testing Function dcnm_vpc_pair_get_have()
    # Checking if peerOneId does not match existing

    vpc_pair = dcnm_vpc_pair_fixture

    data = load_data("dcnm_vpc_pair_data")
    want = data.get(want_key)

    vpc_pair.ip_sn = data.get("vpc_pair_ip_sn")
    vpc_pair.sn_swid = data.get("vpc_pair_sn_swids")
    vpc_pair.paths = vpc_pair_paths[12]

    vpc_pair.want = want
    want.pop()
    want.pop()
    want.pop()

    # Modify peerOneId in want and check

    want[0]["peerTwoId"] = "TEST820SDPR"

    dcnm_send_side_effect = []

    resp = load_data("dcnm_vpc_pair_response")

    dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_1"))
    dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_1"))

    mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
    monkeypatch.setattr(dcnm_vpc_pair_utils, "dcnm_send", mock_dcnm_send)

    try:
        vpc_pair.dcnm_vpc_pair_get_have()
    except Exception as e:
        assert "Cannot create peering" in str(e)


@pytest.mark.parametrize(
    "tc_id, filename, cfg_key",
    [
        (1, "dcnm_vpc_pair_data", "vpc_pair_cfg_00011_1"),
        (2, "dcnm_vpc_pair_data", "vpc_pair_cfg_00011_2"),
        (3, "dcnm_vpc_pair_data", "vpc_pair_cfg_00011_3"),
    ],
)
def test_dcnm_vpc_pair_00011(
    tc_id, monkeypatch, dcnm_vpc_pair_fixture, filename, cfg_key
):

    # Testing Function dcnm_vpc_pair_validate_deleted_state_input()

    vpc_pair = dcnm_vpc_pair_fixture

    data = load_data("dcnm_vpc_pair_data")
    cfg = data.get(cfg_key)

    try:
        vpc_pair.dcnm_vpc_pair_validate_deleted_state_input([cfg])
    except Exception as e:
        if tc_id == 1:
            assert "Invalid IPv4 address syntax" in str(e)
            assert "Invalid parameters in playbook" in str(e)
        elif tc_id == 2:
            assert "Invalid parameters in playbook" in str(e)
            assert "Required parameter not found" in str(e)


@pytest.mark.parametrize(
    "tc_id, filename, cfg_key",
    [
        (1, "dcnm_vpc_pair_data", "vpc_pair_cfg_00012_1"),
        (2, "dcnm_vpc_pair_data", "vpc_pair_cfg_00012_2"),
        (3, "dcnm_vpc_pair_data", "vpc_pair_cfg_00012_3"),
    ],
)
def test_dcnm_vpc_pair_00012(
    tc_id, monkeypatch, dcnm_vpc_pair_fixture, filename, cfg_key
):

    # Testing Function dcnm_vpc_pair_validate_query_state_input()

    vpc_pair = dcnm_vpc_pair_fixture

    data = load_data("dcnm_vpc_pair_data")
    cfg = data.get(cfg_key)

    vpc_pair.ip_sn = data.get("vpc_pair_ip_sn")
    vpc_pair.sn_swid = data.get("vpc_pair_sn_swids")
    vpc_pair.paths = vpc_pair_paths[12]

    try:
        vpc_pair.dcnm_vpc_pair_validate_query_state_input([cfg])
    except Exception as e:
        if tc_id == 1:
            assert "Invalid IPv4 address syntax" in str(e)
            assert "Invalid parameters in playbook" in str(e)


@pytest.mark.parametrize(
    "tc_id, filename, fabric_type, cfg_key, temp_resp_key",
    [
        (
            1,
            "dcnm_vpc_pair_data",
            "LANClassic",
            "vpc_pair_cfg_00013_1",
            "vpc_pair_null_template_resp",
        ),
        (
            2,
            "dcnm_vpc_pair_data",
            "VXLAN",
            "vpc_pair_cfg_00013_2",
            "vpc_pair_null_template_resp",
        ),
        (
            3,
            "dcnm_vpc_pair_data",
            "LANClassic",
            "vpc_pair_cfg_00013_3",
            "vpc_pair_template_resp",
        ),
        (
            4,
            "dcnm_vpc_pair_data",
            "LANClassic",
            "vpc_pair_cfg_00013_4",
            "vpc_pair_template_resp",
        ),
    ],
)
def test_dcnm_vpc_pair_00013(
    tc_id,
    monkeypatch,
    dcnm_vpc_pair_fixture,
    filename,
    fabric_type,
    cfg_key,
    temp_resp_key,
):

    # Testing Function dcnm_vpc_pair_validate_input()

    vpc_pair = dcnm_vpc_pair_fixture

    data = load_data("dcnm_vpc_pair_data")
    resp = load_data("dcnm_vpc_pair_response")

    cfg = data.get(cfg_key)

    vpc_pair.src_fabric_info = {}
    vpc_pair.src_fabric_info["fabricTechnology"] = fabric_type
    vpc_pair.dcnm_version = 12

    dcnm_send_side_effect = []

    dcnm_send_side_effect.append(resp.get(temp_resp_key))

    mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
    monkeypatch.setattr(dcnm, "dcnm_send", mock_dcnm_send)

    try:
        vpc_pair.dcnm_vpc_pair_validate_input([cfg])
    except Exception as e:
        if tc_id == 1:
            assert "Invalid IPv4 address syntax" in str(e)
            assert "Invalid parameters in playbook" in str(e)
        elif tc_id == 4:
            assert "Invalid parameters in playbook" in str(e)
            assert "Invalid choice" in str(e)
            assert "PC_MODE" in str(e)
    if tc_id == 3:
        assert len(vpc_pair.vpc_pair_info) == 1


@pytest.mark.parametrize(
    "tc_id, filename, fabric_type, cfg_key, temp_resp_key, state",
    [
        (
            1,
            "dcnm_vpc_pair_data",
            "LANClassic",
            "vpc_pair_null_cfg",
            "vpc_pair_template_resp",
            "merged",
        ),
        (
            2,
            "dcnm_vpc_pair_data",
            "LANClassic",
            "vpc_pair_cfg_00014_1",
            "vpc_pair_template_resp",
            "merged",
        ),
        (
            3,
            "dcnm_vpc_pair_data",
            "VXLAN",
            "vpc_pair_cfg_00014_1",
            "vpc_pair_template_resp",
            "merged",
        ),
        (
            4,
            "dcnm_vpc_pair_data",
            "LANClassic",
            "vpc_pair_cfg_00014_2",
            "vpc_pair_template_resp",
            "query",
        ),
        (
            5,
            "dcnm_vpc_pair_data",
            "LANClassic",
            "vpc_pair_cfg_00014_2",
            "vpc_pair_template_resp",
            "deleted",
        ),
    ],
)
def test_dcnm_vpc_pair_00014(
    tc_id,
    monkeypatch,
    dcnm_vpc_pair_fixture,
    filename,
    fabric_type,
    cfg_key,
    temp_resp_key,
    state,
):

    # Testing Function dcnm_vpc_pair_validate_all_input()

    vpc_pair = dcnm_vpc_pair_fixture

    data = load_data("dcnm_vpc_pair_data")
    resp = load_data("dcnm_vpc_pair_response")

    cfg = data.get(cfg_key)

    vpc_pair.config = cfg
    vpc_pair.src_fabric_info = {}
    vpc_pair.src_fabric_info["fabricTechnology"] = fabric_type
    vpc_pair.dcnm_version = 12

    vpc_pair.module.params["state"] = state

    dcnm_send_side_effect = []

    dcnm_send_side_effect.append(resp.get(temp_resp_key))
    dcnm_send_side_effect.append(resp.get(temp_resp_key))
    dcnm_send_side_effect.append(resp.get(temp_resp_key))

    mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
    monkeypatch.setattr(dcnm, "dcnm_send", mock_dcnm_send)

    try:
        vpc_pair.dcnm_vpc_pair_validate_all_input()
    except Exception as e:
        pass

    if tc_id >= 2:
        assert len(vpc_pair.vpc_pair_info) == 3


@pytest.mark.parametrize(
    "tc_id, filename1, filename2, inv_info_key, access_info_key",
    [
        (
            1,
            "dcnm_vpc_pair_data",
            "dcnm_vpc_pair_response",
            "vpc_pair_inv_info",
            "vpc_pair_access_info_1",
        ),
        (
            2,
            "dcnm_vpc_pair_data",
            "dcnm_vpc_pair_response",
            "vpc_pair_inv_info",
            "vpc_pair_access_info_2",
        ),
    ],
)
def test_dcnm_vpc_pair_00016(
    tc_id,
    monkeypatch,
    dcnm_vpc_pair_fixture,
    filename1,
    filename2,
    inv_info_key,
    access_info_key,
):

    # Testing Function dcnm_vpc_pair_update_inventory_data()

    vpc_pair = dcnm_vpc_pair_fixture

    data = load_data("dcnm_vpc_pair_data")
    resp = load_data("dcnm_vpc_pair_response")

    vpc_pair.fabric = "mmudigon-svi"
    vpc_pair.dcnm_version = 12
    vpc_pair.paths = vpc_pair_paths[12]
    vpc_pair.inventory_data = data.get(inv_info_key)

    dcnm_send_side_effect = []

    dcnm_send_side_effect.append(resp.get(access_info_key))

    mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
    monkeypatch.setattr(dcnm_vpc_pair, "dcnm_send", mock_dcnm_send)

    try:
        vpc_pair.dcnm_vpc_pair_update_inventory_data()
    except Exception as e:
        assert "Monitoring mode" in str(e)
        assert "No changes are allowed on the fabric" in str(e)

    assert len(vpc_pair.inventory_data) == 8
    assert len(vpc_pair.ip_sn) == 8
    assert len(vpc_pair.hn_sn) == 8
    assert len(vpc_pair.sn_ip) == 8
    assert len(vpc_pair.managable) == 12
    assert len(vpc_pair.meta_switches) == 2

    if tc_id == 1:
        assert len(vpc_pair.monitoring) == 0
    if tc_id == 2:
        assert len(vpc_pair.monitoring) == 1


@pytest.mark.parametrize(
    "tc_id, filename, cfg_key, managable_key, meta_key",
    [
        (
            1,
            "dcnm_vpc_pair_data",
            "vpc_pair_null_cfg",
            "vpc_pair_managable_1",
            "vpc_pair_meta_1",
        ),
        (
            2,
            "dcnm_vpc_pair_data",
            "vpc_pair_cfg_00017_1",
            "vpc_pair_managable_1",
            "vpc_pair_meta_1",
        ),
        (
            3,
            "dcnm_vpc_pair_data",
            "vpc_pair_cfg_00017_1",
            "vpc_pair_managable_2",
            "vpc_pair_meta_2",
        ),
        (
            4,
            "dcnm_vpc_pair_data",
            "vpc_pair_cfg_00017_1",
            "vpc_pair_managable",
            "vpc_pair_meta_1",
        ),
        (
            5,
            "dcnm_vpc_pair_data",
            "vpc_pair_cfg_00017_1",
            "vpc_pair_managable",
            "vpc_pair_meta_2",
        ),
        (
            6,
            "dcnm_vpc_pair_data",
            "vpc_pair_cfg_00017_1",
            "vpc_pair_managable",
            "vpc_pair_null_meta",
        ),
    ],
)
def test_dcnm_vpc_pair_00017(
    tc_id,
    monkeypatch,
    dcnm_vpc_pair_fixture,
    filename,
    cfg_key,
    managable_key,
    meta_key,
):

    # Testing Function dcnm_vpc_pair_translate_playbook_info()

    vpc_pair = dcnm_vpc_pair_fixture

    data = load_data("dcnm_vpc_pair_data")
    resp = load_data("dcnm_vpc_pair_response")

    vpc_pair.managable = data.get(managable_key)
    vpc_pair.meta_switches = data.get(meta_key)
    cfg = data.get(cfg_key)
    if cfg != []:
        cfg = [cfg]
    vpc_pair.ip_sn = data.get("vpc_pair_ip_sn")
    vpc_pair.hn_sn = data.get("vpc_pair_hn_sn")

    try:
        vpc_pair.dcnm_vpc_pair_translate_playbook_info(
            cfg, vpc_pair.ip_sn, vpc_pair.hn_sn
        )
    except Exception as e:
        if tc_id == 2:
            assert "Switch 10.122.84.175 is not Manageable" in str(e)
        if tc_id == 3:
            assert "Switch 10.122.84.174 is not Manageable" in str(e)
        if tc_id == 4:
            assert "Switch 10.122.84.175 is not Manageable" in str(e)
        if tc_id == 5:
            assert "Switch 10.122.84.174 is not Manageable" in str(e)


@pytest.mark.parametrize(
    "tc_id, template_info, temp_resp_key",
    [
        (1, ["vpc_pair"], "vpc_pair_template_resp"),
        (2, ["vpc_pair", "vpc_pair"], "vpc_pair_template_resp"),
        (3, ["vpc_pair", "vpc_pair_2"], "vpc_pair_template_resp"),
    ],
)
def test_dcnm_vpc_pair_00018(
    tc_id, monkeypatch, dcnm_vpc_pair_fixture, template_info, temp_resp_key
):

    # Testing Function dcnm_vpc_pair_fetch_template_details()

    vpc_pair = dcnm_vpc_pair_fixture

    vpc_pair.dcnm_version = 12

    resp = load_data("dcnm_vpc_pair_response")

    dcnm_send_side_effect = []

    dcnm_send_side_effect.append(resp.get(temp_resp_key))
    if tc_id == 3:
        dcnm_send_side_effect.append(resp.get(temp_resp_key + "_2"))
    else:
        dcnm_send_side_effect.append(resp.get(temp_resp_key))

    mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
    monkeypatch.setattr(dcnm, "dcnm_send", mock_dcnm_send)

    template_list = vpc_pair.dcnm_vpc_pair_fetch_template_details(
        template_info
    )

    if tc_id <= 2:
        assert len(template_list) == 1
    elif tc_id == 3:
        assert len(template_list) == 2


@pytest.mark.parametrize(
    "tc_id, del_list_key, del_resp_key, deploy_list_key, deploy_resp_key",
    [
        (
            1,
            "vpc_pair_del_list_1",
            "vpc_pair_delete_succ_resp",
            "vpc_pair_null_deploy_list",
            "vpc_pair_null_deploy_resp",
        ),
        (
            2,
            "vpc_pair_del_list_2",
            "vpc_pair_delete_fail_resp",
            "vpc_pair_null_deploy_list",
            "vpc_pair_null_deploy_resp",
        ),
        (
            3,
            "vpc_pair_del_list_2",
            "vpc_pair_delete_succ_resp_2",
            "vpc_pair_deploy_list",
            "vpc_pair_null_deploy_resp",
        ),
        (
            4,
            "vpc_pair_del_list_2",
            "vpc_pair_delete_succ_resp_2",
            "vpc_pair_null_deploy_list",
            "vpc_pair_null_deploy_resp",
        ),
    ],
)
def test_dcnm_vpc_pair_00019(
    tc_id,
    monkeypatch,
    dcnm_vpc_pair_fixture,
    del_list_key,
    deploy_list_key,
    del_resp_key,
    deploy_resp_key,
):

    # Testing Function dcnm_vpc_pair_send_message_to_dcnm() ==> dcnm_vpc_pair_utils_process_delete_payloads()

    vpc_pair = dcnm_vpc_pair_fixture

    data = load_data("dcnm_vpc_pair_data")
    resp = load_data("dcnm_vpc_pair_response")

    vpc_pair.diff_delete = data.get(del_list_key)
    vpc_pair.diff_delete_deploy = data.get(deploy_list_key)
    vpc_pair.dcnm_version = 12
    vpc_pair.paths = vpc_pair_paths[12]
    vpc_pair.sn_ip = data.get("vpc_pair_sn_ip")

    dcnm_send_side_effect = []
    process_deploy_payloads_side_effect = [True, True]

    if tc_id == 1:
        dcnm_send_side_effect.append(resp.get(del_resp_key))
        dcnm_send_side_effect.append(resp.get(del_resp_key))
    elif tc_id == 2:
        dcnm_send_side_effect.append(resp.get(del_resp_key))
    elif tc_id == 3:
        dcnm_send_side_effect.append(resp.get(del_resp_key))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))
    elif tc_id == 4:
        dcnm_send_side_effect.append(resp.get(del_resp_key))
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_sync_status_not_in_sync")
        )

    mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
    monkeypatch.setattr(dcnm_vpc_pair_utils, "dcnm_send", mock_dcnm_send)

    mock_process_deploy_payloads = Mock(
        side_effect=process_deploy_payloads_side_effect
    )
    monkeypatch.setattr(
        dcnm_vpc_pair_utils,
        "dcnm_vpc_pair_utils_process_deploy_payloads",
        mock_process_deploy_payloads,
    )

    try:
        vpc_pair.dcnm_vpc_pair_send_message_to_dcnm()
    except Exception as e:
        if tc_id == 2:
            d = eval(str(e))
            assert d[0]["RETURN_CODE"] == 500

    if tc_id == 1:
        assert len(vpc_pair.diff_delete) == 2
        assert vpc_pair.result["changed"] is True
    elif tc_id == 3:
        assert (
            "VPC Pair could not be deleted"
            in vpc_pair.result["response"][0]["DATA"]
        )


@pytest.mark.parametrize(
    "tc_id, create_list_key, create_succ_resp_key, create_fail_resp_key",
    [
        (
            1,
            "vpc_pair_create_list",
            "vpc_pair_create_succ_resp",
            "vpc_pair_create_fail_resp",
        ),
        (
            2,
            "vpc_pair_create_list",
            "vpc_pair_create_succ_resp",
            "vpc_pair_create_fail_resp",
        ),
    ],
)
def test_dcnm_vpc_pair_00020(
    tc_id,
    monkeypatch,
    dcnm_vpc_pair_fixture,
    create_list_key,
    create_succ_resp_key,
    create_fail_resp_key,
):

    # Testing Function dcnm_vpc_pair_send_message_to_dcnm() ==> dcnm_vpc_pair_utils_process_create_payloads()

    vpc_pair = dcnm_vpc_pair_fixture

    data = load_data("dcnm_vpc_pair_data")
    resp = load_data("dcnm_vpc_pair_response")

    vpc_pair.diff_create = data.get(create_list_key)
    vpc_pair.dcnm_version = 12
    vpc_pair.paths = vpc_pair_paths[12]

    dcnm_send_side_effect = []

    if tc_id == 1:
        dcnm_send_side_effect.append(resp.get(create_succ_resp_key))
        dcnm_send_side_effect.append(resp.get(create_succ_resp_key))
        dcnm_send_side_effect.append(resp.get(create_succ_resp_key))
    elif tc_id == 2:
        dcnm_send_side_effect.append(resp.get(create_succ_resp_key))
        dcnm_send_side_effect.append(resp.get(create_succ_resp_key))
        dcnm_send_side_effect.append(resp.get(create_fail_resp_key))

    mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
    monkeypatch.setattr(dcnm_vpc_pair_utils, "dcnm_send", mock_dcnm_send)

    try:
        vpc_pair.dcnm_vpc_pair_send_message_to_dcnm()
    except Exception as e:
        if tc_id == 2:
            d = eval(str(e))
            assert d[0]["RETURN_CODE"] == 500

    assert len(vpc_pair.result["response"]) == 3


@pytest.mark.parametrize(
    "tc_id, modify_list_key, modify_succ_resp_key, modify_fail_resp_key",
    [
        (
            1,
            "vpc_pair_modify_list",
            "vpc_pair_modify_succ_resp",
            "vpc_pair_modify_fail_resp",
        ),
        (
            2,
            "vpc_pair_modify_list",
            "vpc_pair_modify_succ_resp",
            "vpc_pair_modify_fail_resp",
        ),
    ],
)
def test_dcnm_vpc_pair_00021(
    tc_id,
    monkeypatch,
    dcnm_vpc_pair_fixture,
    modify_list_key,
    modify_succ_resp_key,
    modify_fail_resp_key,
):

    # Testing Function dcnm_vpc_pair_send_message_to_dcnm() ==> dcnm_vpc_pair_utils_process_modify_payloads()

    vpc_pair = dcnm_vpc_pair_fixture

    data = load_data("dcnm_vpc_pair_data")
    resp = load_data("dcnm_vpc_pair_response")

    vpc_pair.diff_modify = data.get(modify_list_key)
    vpc_pair.dcnm_version = 12
    vpc_pair.paths = vpc_pair_paths[12]

    dcnm_send_side_effect = []

    if tc_id == 1:
        dcnm_send_side_effect.append(resp.get(modify_succ_resp_key))
        dcnm_send_side_effect.append(resp.get(modify_succ_resp_key))
        dcnm_send_side_effect.append(resp.get(modify_succ_resp_key))
    elif tc_id == 2:
        dcnm_send_side_effect.append(resp.get(modify_succ_resp_key))
        dcnm_send_side_effect.append(resp.get(modify_succ_resp_key))
        dcnm_send_side_effect.append(resp.get(modify_fail_resp_key))

    mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
    monkeypatch.setattr(dcnm_vpc_pair_utils, "dcnm_send", mock_dcnm_send)

    try:
        vpc_pair.dcnm_vpc_pair_send_message_to_dcnm()
    except Exception as e:
        if tc_id == 2:
            d = eval(str(e))
            assert d[0]["RETURN_CODE"] == 500

    assert len(vpc_pair.result["response"]) == 3


@pytest.mark.parametrize(
    "tc_id, deploy_list_key",
    [
        (1, "vpc_pair_null_deploy_list"),
        (2, "vpc_pair_deploy_list"),
        (3, "vpc_pair_deploy_list"),
        (4, "vpc_pair_deploy_list"),
        (5, "vpc_pair_deploy_list"),
        (6, "vpc_pair_deploy_list"),
        (7, "vpc_pair_deploy_list"),
    ],
)
def test_dcnm_vpc_pair_00022(
    tc_id, monkeypatch, dcnm_vpc_pair_fixture, deploy_list_key
):

    # Testing Function dcnm_vpc_pair_send_message_to_dcnm() ==> dcnm_vpc_pair_utils_process_modify_payloads()

    vpc_pair = dcnm_vpc_pair_fixture

    data = load_data("dcnm_vpc_pair_data")
    resp = load_data("dcnm_vpc_pair_response")

    vpc_pair.diff_deploy = data.get(deploy_list_key)
    vpc_pair.dcnm_version = 12
    vpc_pair.paths = vpc_pair_paths[12]
    vpc_pair.sn_ip = data.get("vpc_pair_sn_ip")
    vpc_pair.changed_dict = [{}]

    dcnm_send_side_effect = []
    if tc_id == 2:
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_config_save_succ_resp")
        )
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_fail_resp"))
    elif tc_id == 3:
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_config_save_succ_resp")
        )
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))
    elif tc_id == 4:
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_config_save_succ_resp")
        )
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_sync_status_not_in_sync")
        )
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))
    elif tc_id == 5:
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_config_save_succ_resp")
        )
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_sync_status_not_in_sync")
        )
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_sync_status_not_in_sync")
        )
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_sync_status_not_in_sync")
        )
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_sync_status_not_in_sync")
        )
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_sync_status_not_in_sync")
        )
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_sync_status_not_in_sync")
        )
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_sync_status_not_in_sync")
        )
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_sync_status_not_in_sync")
        )
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_sync_status_not_in_sync")
        )
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_sync_status_not_in_sync")
        )
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_sync_status_not_in_sync")
        )
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_sync_status_not_in_sync")
        )
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_sync_status_not_in_sync")
        )
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_sync_status_not_in_sync")
        )
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_sync_status_not_in_sync")
        )
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_sync_status_not_in_sync")
        )
    elif tc_id == 6:
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_config_save_fail_resp")
        )
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
    elif tc_id == 7:
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_config_save_succ_resp")
        )
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_sync_status_not_in_sync")
        )
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_sync_status_not_in_sync")
        )
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_sync_status_not_in_sync")
        )
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_sync_status_not_in_sync")
        )
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))

    mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
    monkeypatch.setattr(dcnm_vpc_pair_utils, "dcnm_send", mock_dcnm_send)

    try:
        vpc_pair.dcnm_vpc_pair_send_message_to_dcnm()
    except Exception as e:
        if tc_id == 5:
            "did not reach 'In-Sync' state after deploy" in str(e)


def test_dcnm_vpc_pair_00023(monkeypatch, dcnm_vpc_pair_fixture):

    # Testing Function dcnm_vpc_pair_update_module_info()

    vpc_pair = dcnm_vpc_pair_fixture

    resp = load_data("dcnm_vpc_pair_response")

    vpc_pair.fabric = "mmudigon"

    dcnm_version_supported_side_effect = []
    get_fabric_inventory_details_side_effect = []
    get_fabric_details_side_effect = []

    dcnm_version_supported_side_effect.append(12)
    get_fabric_inventory_details_side_effect.append(
        resp.get("vpc_pair_inv_details_resp")
    )
    get_fabric_details_side_effect.append(
        resp.get("vpc_pair_fab_details_resp")
    )

    mock_dcnm_version_supported = Mock(
        side_effect=dcnm_version_supported_side_effect
    )
    monkeypatch.setattr(
        dcnm_vpc_pair, "dcnm_version_supported", mock_dcnm_version_supported
    )

    mock_get_fabric_inventory_details = Mock(
        side_effect=get_fabric_inventory_details_side_effect
    )
    monkeypatch.setattr(
        dcnm_vpc_pair,
        "get_fabric_inventory_details",
        mock_get_fabric_inventory_details,
    )

    mock_get_fabric_details = Mock(side_effect=get_fabric_details_side_effect)
    monkeypatch.setattr(
        dcnm_vpc_pair, "get_fabric_details", mock_get_fabric_details
    )

    vpc_pair.dcnm_vpc_pair_update_module_info()

    assert vpc_pair.inventory_data != []
    assert vpc_pair.src_fabric_info != []
    assert vpc_pair.dcnm_version == 12
    assert vpc_pair.paths != {}


# From here on the test cases will do a black box testing. Complete module will be executed based on the given config and state.


class TestDcnmVpcPairModule(TestDcnmModule):

    module = dcnm_vpc_pair

    fd = None

    def setUp(self):
        super(TestDcnmVpcPairModule, self).setUp()
        self.monkeypatch = MonkeyPatch()

    def test_dcnm_vpc_pair_merged_new(self):

        data = load_data("dcnm_vpc_pair_data")
        resp = load_data("dcnm_vpc_pair_response")

        dcnm_version_supported_side_effect = []
        get_fabric_inventory_details_side_effect = []
        get_fabric_details_side_effect = []
        dcnm_send_side_effect = []
        dcnm_send_side_effect_2 = []
        dcnm_send_side_effect_3 = []

        # dcnm_send() invoked from module_utils/dcnm_vpc_pair_utils.py
        dcnm_send_side_effect.append(data.get("vpc_pair_null_have"))
        dcnm_send_side_effect.append(data.get("vpc_pair_null_have"))
        dcnm_send_side_effect.append(data.get("vpc_pair_null_have"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_create_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_create_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_create_succ_resp"))
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_config_save_succ_resp")
        )
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))

        # dcnm_send() invoked from modules/dcnm_vpc_pair.py
        dcnm_send_side_effect_2.append(resp.get("vpc_pair_access_info_1"))

        # dcnm_send() invoked from module_utils/dcnm.py
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))

        dcnm_version_supported_side_effect.append(12)
        get_fabric_inventory_details_side_effect.append(
            data.get("vpc_pair_inv_info")
        )
        get_fabric_details_side_effect.append(data.get("vpc_pair_fab_details"))

        mock_dcnm_version_supported = Mock(
            side_effect=dcnm_version_supported_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair, "dcnm_version_supported", mock_dcnm_version_supported
        )

        mock_get_fabric_inventory_details = Mock(
            side_effect=get_fabric_inventory_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair,
            "get_fabric_inventory_details",
            mock_get_fabric_inventory_details,
        )

        mock_get_fabric_details = Mock(
            side_effect=get_fabric_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair, "get_fabric_details", mock_get_fabric_details
        )

        mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
        self.monkeypatch.setattr(
            dcnm_vpc_pair_utils, "dcnm_send", mock_dcnm_send
        )

        mock_dcnm_send_2 = Mock(side_effect=dcnm_send_side_effect_2)
        self.monkeypatch.setattr(dcnm_vpc_pair, "dcnm_send", mock_dcnm_send_2)

        mock_dcnm_send_3 = Mock(side_effect=dcnm_send_side_effect_3)
        self.monkeypatch.setattr(dcnm, "dcnm_send", mock_dcnm_send_3)

        # load required config data
        playbook_config = data.get("vpc_pair_merge_new_cfg")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-svi",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 3)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 3)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_vpc_pair_merged_new_check_mode(self):

        data = load_data("dcnm_vpc_pair_data")
        resp = load_data("dcnm_vpc_pair_response")

        dcnm_version_supported_side_effect = []
        get_fabric_inventory_details_side_effect = []
        get_fabric_details_side_effect = []
        dcnm_send_side_effect = []
        dcnm_send_side_effect_2 = []
        dcnm_send_side_effect_3 = []

        # dcnm_send() invoked from module_utils/dcnm_vpc_pair_utils.py
        dcnm_send_side_effect.append(data.get("vpc_pair_null_have"))
        dcnm_send_side_effect.append(data.get("vpc_pair_null_have"))
        dcnm_send_side_effect.append(data.get("vpc_pair_null_have"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))

        # dcnm_send() invoked from modules/dcnm_vpc_pair.py
        dcnm_send_side_effect_2.append(resp.get("vpc_pair_access_info_1"))

        # dcnm_send() invoked from module_utils/dcnm.py
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))

        dcnm_version_supported_side_effect.append(12)
        get_fabric_inventory_details_side_effect.append(
            data.get("vpc_pair_inv_info")
        )
        get_fabric_details_side_effect.append(data.get("vpc_pair_fab_details"))

        mock_dcnm_version_supported = Mock(
            side_effect=dcnm_version_supported_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair, "dcnm_version_supported", mock_dcnm_version_supported
        )

        mock_get_fabric_inventory_details = Mock(
            side_effect=get_fabric_inventory_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair,
            "get_fabric_inventory_details",
            mock_get_fabric_inventory_details,
        )

        mock_get_fabric_details = Mock(
            side_effect=get_fabric_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair, "get_fabric_details", mock_get_fabric_details
        )

        mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
        self.monkeypatch.setattr(
            dcnm_vpc_pair_utils, "dcnm_send", mock_dcnm_send
        )

        mock_dcnm_send_2 = Mock(side_effect=dcnm_send_side_effect_2)
        self.monkeypatch.setattr(dcnm_vpc_pair, "dcnm_send", mock_dcnm_send_2)

        mock_dcnm_send_3 = Mock(side_effect=dcnm_send_side_effect_3)
        self.monkeypatch.setattr(dcnm, "dcnm_send", mock_dcnm_send_3)

        # load required config data
        playbook_config = data.get("vpc_pair_merge_new_cfg")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-svi",
                config=playbook_config,
                _ansible_check_mode=True,
            )
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 3)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 3)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_vpc_pair_merged_existing(self):

        data = load_data("dcnm_vpc_pair_data")
        resp = load_data("dcnm_vpc_pair_response")

        dcnm_version_supported_side_effect = []
        get_fabric_inventory_details_side_effect = []
        get_fabric_details_side_effect = []
        dcnm_send_side_effect = []
        dcnm_send_side_effect_2 = []
        dcnm_send_side_effect_3 = []

        # dcnm_send() invoked from module_utils/dcnm_vpc_pair_utils.py
        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_84"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_84"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_85"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_85"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_86"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_86"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_create_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_create_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_create_succ_resp"))
        dcnm_send_side_effect.append(
            resp.get("vpc_pair_config_save_succ_resp")
        )
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))

        # dcnm_send() invoked from modules/dcnm_vpc_pair.py
        dcnm_send_side_effect_2.append(resp.get("vpc_pair_access_info_1"))

        # dcnm_send() invoked from module_utils/dcnm.py
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))

        dcnm_version_supported_side_effect.append(12)
        get_fabric_inventory_details_side_effect.append(
            data.get("vpc_pair_inv_info")
        )
        get_fabric_details_side_effect.append(data.get("vpc_pair_fab_details"))

        mock_dcnm_version_supported = Mock(
            side_effect=dcnm_version_supported_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair, "dcnm_version_supported", mock_dcnm_version_supported
        )

        mock_get_fabric_inventory_details = Mock(
            side_effect=get_fabric_inventory_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair,
            "get_fabric_inventory_details",
            mock_get_fabric_inventory_details,
        )

        mock_get_fabric_details = Mock(
            side_effect=get_fabric_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair, "get_fabric_details", mock_get_fabric_details
        )

        mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
        self.monkeypatch.setattr(
            dcnm_vpc_pair_utils, "dcnm_send", mock_dcnm_send
        )

        mock_dcnm_send_2 = Mock(side_effect=dcnm_send_side_effect_2)
        self.monkeypatch.setattr(dcnm_vpc_pair, "dcnm_send", mock_dcnm_send_2)

        mock_dcnm_send_3 = Mock(side_effect=dcnm_send_side_effect_3)
        self.monkeypatch.setattr(dcnm, "dcnm_send", mock_dcnm_send_3)

        # load required config data
        playbook_config = data.get("vpc_pair_merge_new_cfg")

        set_module_args(
            dict(
                state="merged",
                src_fabric="mmudigon-svi",
                config=playbook_config,
            )
        )

        result = None
        try:
            result = self.execute_module(changed=False, failed=False)
        except SystemExit as err:
            pass
        except Exception as e:
            pass

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_vpc_pair_merged_cfg_null(self):

        data = load_data("dcnm_vpc_pair_data")
        resp = load_data("dcnm_vpc_pair_response")

        set_module_args(
            dict(state="merged", src_fabric="mmudigon-svi", config=[])
        )

        result = None
        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception as e:
            assert "'config' element is mandatory for state" in str(e)

    def test_dcnm_vpc_pair_delete_existing(self):

        data = load_data("dcnm_vpc_pair_data")
        resp = load_data("dcnm_vpc_pair_response")

        dcnm_version_supported_side_effect = []
        get_fabric_inventory_details_side_effect = []
        get_fabric_details_side_effect = []
        dcnm_send_side_effect = []
        dcnm_send_side_effect_2 = []
        dcnm_send_side_effect_3 = []

        # dcnm_send() invoked from module_utils/dcnm_vpc_pair_utils.py
        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_84"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_84"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_85"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_85"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_86"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_86"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_delete_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_delete_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_delete_succ_resp"))

        dcnm_send_side_effect.append(
            resp.get("vpc_pair_config_save_succ_resp")
        )

        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))

        # dcnm_send() invoked from modules/dcnm_vpc_pair.py
        dcnm_send_side_effect_2.append(resp.get("vpc_pair_access_info_1"))

        # dcnm_send() invoked from module_utils/dcnm.py
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))

        dcnm_version_supported_side_effect.append(12)
        get_fabric_inventory_details_side_effect.append(
            data.get("vpc_pair_inv_info")
        )
        get_fabric_details_side_effect.append(data.get("vpc_pair_fab_details"))

        mock_dcnm_version_supported = Mock(
            side_effect=dcnm_version_supported_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair, "dcnm_version_supported", mock_dcnm_version_supported
        )

        mock_get_fabric_inventory_details = Mock(
            side_effect=get_fabric_inventory_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair,
            "get_fabric_inventory_details",
            mock_get_fabric_inventory_details,
        )

        mock_get_fabric_details = Mock(
            side_effect=get_fabric_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair, "get_fabric_details", mock_get_fabric_details
        )

        mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
        self.monkeypatch.setattr(
            dcnm_vpc_pair_utils, "dcnm_send", mock_dcnm_send
        )

        mock_dcnm_send_2 = Mock(side_effect=dcnm_send_side_effect_2)
        self.monkeypatch.setattr(dcnm_vpc_pair, "dcnm_send", mock_dcnm_send_2)

        mock_dcnm_send_3 = Mock(side_effect=dcnm_send_side_effect_3)
        self.monkeypatch.setattr(dcnm, "dcnm_send", mock_dcnm_send_3)

        # load required config data
        playbook_config = data.get("vpc_pair_delete_existing")

        set_module_args(
            dict(
                state="deleted",
                src_fabric="mmudigon-svi",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

    def test_dcnm_vpc_pair_override_new_cfg(self):

        data = load_data("dcnm_vpc_pair_data")
        resp = load_data("dcnm_vpc_pair_response")

        dcnm_version_supported_side_effect = []
        get_fabric_inventory_details_side_effect = []
        get_fabric_details_side_effect = []
        dcnm_send_side_effect = []
        dcnm_send_side_effect_2 = []
        dcnm_send_side_effect_3 = []

        # dcnm_send() invoked from module_utils/dcnm_vpc_pair_utils.py
        dcnm_send_side_effect.append(resp.get("vpc_pair_null_have"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_null_have"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_null_have"))

        dcnm_send_side_effect.append(resp.get("vpc_pair_null_have"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_null_have"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_null_have"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_null_have"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_null_have"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_null_have"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_null_have"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_null_have"))

        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))

        dcnm_send_side_effect.append(resp.get("vpc_pair_create_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_create_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_create_succ_resp"))

        dcnm_send_side_effect.append(
            resp.get("vpc_pair_config_save_succ_resp")
        )

        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))

        # dcnm_send() invoked from modules/dcnm_vpc_pair.py
        dcnm_send_side_effect_2.append(resp.get("vpc_pair_access_info_1"))

        # dcnm_send() invoked from module_utils/dcnm.py
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))

        dcnm_version_supported_side_effect.append(12)
        get_fabric_inventory_details_side_effect.append(
            data.get("vpc_pair_inv_info")
        )
        get_fabric_details_side_effect.append(data.get("vpc_pair_fab_details"))

        mock_dcnm_version_supported = Mock(
            side_effect=dcnm_version_supported_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair, "dcnm_version_supported", mock_dcnm_version_supported
        )

        mock_get_fabric_inventory_details = Mock(
            side_effect=get_fabric_inventory_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair,
            "get_fabric_inventory_details",
            mock_get_fabric_inventory_details,
        )

        mock_get_fabric_details = Mock(
            side_effect=get_fabric_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair, "get_fabric_details", mock_get_fabric_details
        )

        mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
        self.monkeypatch.setattr(
            dcnm_vpc_pair_utils, "dcnm_send", mock_dcnm_send
        )

        mock_dcnm_send_2 = Mock(side_effect=dcnm_send_side_effect_2)
        self.monkeypatch.setattr(dcnm_vpc_pair, "dcnm_send", mock_dcnm_send_2)

        mock_dcnm_send_3 = Mock(side_effect=dcnm_send_side_effect_3)
        self.monkeypatch.setattr(dcnm, "dcnm_send", mock_dcnm_send_3)

        # load required config data
        playbook_config = data.get("vpc_pair_override_new")

        set_module_args(
            dict(
                state="overridden",
                src_fabric="mmudigon-svi",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 3)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 3)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_vpc_pair_override_existing_cfg(self):

        data = load_data("dcnm_vpc_pair_data")
        resp = load_data("dcnm_vpc_pair_response")

        dcnm_version_supported_side_effect = []
        get_fabric_inventory_details_side_effect = []
        get_fabric_details_side_effect = []
        dcnm_send_side_effect = []
        dcnm_send_side_effect_2 = []
        dcnm_send_side_effect_3 = []

        # dcnm_send() invoked from module_utils/dcnm_vpc_pair_utils.py
        dcnm_send_side_effect.append(resp.get("vpc_pair_null_have"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_85"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_85"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_86"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_86"))

        dcnm_send_side_effect.append(resp.get("vpc_pair_null_have"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_null_have"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_85"))
        dcnm_send_side_effect.append(
            copy.deepcopy(resp.get("vpc_pair_policy_resp_85"))
        )
        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_86"))
        dcnm_send_side_effect.append(
            copy.deepcopy(resp.get("vpc_pair_policy_resp_86"))
        )
        dcnm_send_side_effect.append(resp.get("vpc_pair_null_have"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_null_have"))

        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))

        dcnm_send_side_effect.append(resp.get("vpc_pair_delete_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_delete_succ_resp"))

        dcnm_send_side_effect.append(
            resp.get("vpc_pair_config_save_succ_resp")
        )

        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))

        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))

        dcnm_send_side_effect.append(resp.get("vpc_pair_create_succ_resp"))

        dcnm_send_side_effect.append(
            resp.get("vpc_pair_config_save_succ_resp")
        )

        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))

        # dcnm_send() invoked from modules/dcnm_vpc_pair.py
        dcnm_send_side_effect_2.append(resp.get("vpc_pair_access_info_1"))

        # dcnm_send() invoked from module_utils/dcnm.py
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))

        dcnm_version_supported_side_effect.append(12)
        get_fabric_inventory_details_side_effect.append(
            data.get("vpc_pair_inv_info")
        )
        get_fabric_details_side_effect.append(data.get("vpc_pair_fab_details"))

        mock_dcnm_version_supported = Mock(
            side_effect=dcnm_version_supported_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair, "dcnm_version_supported", mock_dcnm_version_supported
        )

        mock_get_fabric_inventory_details = Mock(
            side_effect=get_fabric_inventory_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair,
            "get_fabric_inventory_details",
            mock_get_fabric_inventory_details,
        )

        mock_get_fabric_details = Mock(
            side_effect=get_fabric_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair, "get_fabric_details", mock_get_fabric_details
        )

        mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
        self.monkeypatch.setattr(
            dcnm_vpc_pair_utils, "dcnm_send", mock_dcnm_send
        )

        mock_dcnm_send_2 = Mock(side_effect=dcnm_send_side_effect_2)
        self.monkeypatch.setattr(dcnm_vpc_pair, "dcnm_send", mock_dcnm_send_2)

        mock_dcnm_send_3 = Mock(side_effect=dcnm_send_side_effect_3)
        self.monkeypatch.setattr(dcnm, "dcnm_send", mock_dcnm_send_3)

        # load required config data
        playbook_config = data.get("vpc_pair_override_one_pair")

        set_module_args(
            dict(
                state="overridden",
                src_fabric="mmudigon-svi",
                config=playbook_config,
            )
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 2)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 1)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_vpc_pair_override_existing_no_new_cfg(self):

        data = load_data("dcnm_vpc_pair_data")
        resp = load_data("dcnm_vpc_pair_response")

        dcnm_version_supported_side_effect = []
        get_fabric_inventory_details_side_effect = []
        get_fabric_details_side_effect = []
        dcnm_send_side_effect = []
        dcnm_send_side_effect_2 = []
        dcnm_send_side_effect_3 = []

        # dcnm_send() invoked from module_utils/dcnm_vpc_pair_utils.py
        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_84"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_84"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_85"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_85"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_86"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_86"))

        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_84"))
        dcnm_send_side_effect.append(
            copy.deepcopy(resp.get("vpc_pair_policy_resp_84"))
        )
        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_85"))
        dcnm_send_side_effect.append(
            copy.deepcopy(resp.get("vpc_pair_policy_resp_85"))
        )
        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_86"))
        dcnm_send_side_effect.append(
            copy.deepcopy(resp.get("vpc_pair_policy_resp_86"))
        )
        dcnm_send_side_effect.append(resp.get("vpc_pair_null_have"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_null_have"))

        dcnm_send_side_effect.append(resp.get("vpc_pair_delete_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_delete_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_delete_succ_resp"))

        dcnm_send_side_effect.append(
            resp.get("vpc_pair_config_save_succ_resp")
        )

        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_deploy_succ_resp"))

        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_sync_status_in_sync"))

        # dcnm_send() invoked from modules/dcnm_vpc_pair.py
        dcnm_send_side_effect_2.append(resp.get("vpc_pair_access_info_1"))

        # dcnm_send() invoked from module_utils/dcnm.py
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))

        dcnm_version_supported_side_effect.append(12)
        get_fabric_inventory_details_side_effect.append(
            data.get("vpc_pair_inv_info")
        )
        get_fabric_details_side_effect.append(data.get("vpc_pair_fab_details"))

        mock_dcnm_version_supported = Mock(
            side_effect=dcnm_version_supported_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair, "dcnm_version_supported", mock_dcnm_version_supported
        )

        mock_get_fabric_inventory_details = Mock(
            side_effect=get_fabric_inventory_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair,
            "get_fabric_inventory_details",
            mock_get_fabric_inventory_details,
        )

        mock_get_fabric_details = Mock(
            side_effect=get_fabric_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair, "get_fabric_details", mock_get_fabric_details
        )

        mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
        self.monkeypatch.setattr(
            dcnm_vpc_pair_utils, "dcnm_send", mock_dcnm_send
        )

        mock_dcnm_send_2 = Mock(side_effect=dcnm_send_side_effect_2)
        self.monkeypatch.setattr(dcnm_vpc_pair, "dcnm_send", mock_dcnm_send_2)

        mock_dcnm_send_3 = Mock(side_effect=dcnm_send_side_effect_3)
        self.monkeypatch.setattr(dcnm, "dcnm_send", mock_dcnm_send_3)

        set_module_args(
            dict(state="overridden", src_fabric="mmudigon-svi", config=[])
        )

        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 3)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_vpc_pair_query(self):

        data = load_data("dcnm_vpc_pair_data")
        resp = load_data("dcnm_vpc_pair_response")

        dcnm_version_supported_side_effect = []
        get_fabric_inventory_details_side_effect = []
        get_fabric_details_side_effect = []
        dcnm_send_side_effect = []
        dcnm_send_side_effect_2 = []
        dcnm_send_side_effect_3 = []

        # dcnm_send() invoked from module_utils/dcnm_vpc_pair_utils.py
        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_84"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_84"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_85"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_85"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_86"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_policy_resp_86"))

        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_84"))
        dcnm_send_side_effect.append(
            copy.deepcopy(resp.get("vpc_pair_policy_resp_84"))
        )
        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_85"))
        dcnm_send_side_effect.append(
            copy.deepcopy(resp.get("vpc_pair_policy_resp_85"))
        )
        dcnm_send_side_effect.append(resp.get("vpc_pair_info_resp_86"))
        dcnm_send_side_effect.append(
            copy.deepcopy(resp.get("vpc_pair_policy_resp_86"))
        )
        dcnm_send_side_effect.append(resp.get("vpc_pair_null_have"))
        dcnm_send_side_effect.append(resp.get("vpc_pair_null_have"))

        # dcnm_send() invoked from modules/dcnm_vpc_pair.py
        dcnm_send_side_effect_2.append(resp.get("vpc_pair_access_info_1"))

        # dcnm_send() invoked from module_utils/dcnm.py
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))

        dcnm_version_supported_side_effect.append(12)
        get_fabric_inventory_details_side_effect.append(
            data.get("vpc_pair_inv_info")
        )
        get_fabric_details_side_effect.append(data.get("vpc_pair_fab_details"))

        mock_dcnm_version_supported = Mock(
            side_effect=dcnm_version_supported_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair, "dcnm_version_supported", mock_dcnm_version_supported
        )

        mock_get_fabric_inventory_details = Mock(
            side_effect=get_fabric_inventory_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair,
            "get_fabric_inventory_details",
            mock_get_fabric_inventory_details,
        )

        mock_get_fabric_details = Mock(
            side_effect=get_fabric_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair, "get_fabric_details", mock_get_fabric_details
        )

        mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
        self.monkeypatch.setattr(
            dcnm_vpc_pair_utils, "dcnm_send", mock_dcnm_send
        )

        mock_dcnm_send_2 = Mock(side_effect=dcnm_send_side_effect_2)
        self.monkeypatch.setattr(dcnm_vpc_pair, "dcnm_send", mock_dcnm_send_2)

        mock_dcnm_send_3 = Mock(side_effect=dcnm_send_side_effect_3)
        self.monkeypatch.setattr(dcnm, "dcnm_send", mock_dcnm_send_3)

        set_module_args(
            dict(state="query", src_fabric="mmudigon-svi", config=[])
        )

        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["modified"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        assert len(result["response"]) == 3

        self.assertEqual(len(result["diff"][0]["deploy"]), 0)

    def test_dcnm_vpc_pair_fetch(self):

        data = load_data("dcnm_vpc_pair_data")
        resp = load_data("dcnm_vpc_pair_response")

        dcnm_version_supported_side_effect = []
        get_fabric_inventory_details_side_effect = []
        get_fabric_details_side_effect = []
        dcnm_send_side_effect_2 = []
        dcnm_send_side_effect_3 = []

        # dcnm_send() invoked from modules/dcnm_vpc_pair.py
        dcnm_send_side_effect_2.append(resp.get("vpc_pair_access_info_1"))

        # dcnm_send() invoked from module_utils/dcnm.py
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))
        dcnm_send_side_effect_3.append(resp.get("vpc_pair_template_resp"))

        dcnm_version_supported_side_effect.append(12)
        get_fabric_inventory_details_side_effect.append(
            data.get("vpc_pair_inv_info")
        )
        get_fabric_details_side_effect.append(data.get("vpc_pair_fab_details"))

        mock_dcnm_version_supported = Mock(
            side_effect=dcnm_version_supported_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair, "dcnm_version_supported", mock_dcnm_version_supported
        )

        mock_get_fabric_inventory_details = Mock(
            side_effect=get_fabric_inventory_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair,
            "get_fabric_inventory_details",
            mock_get_fabric_inventory_details,
        )

        mock_get_fabric_details = Mock(
            side_effect=get_fabric_details_side_effect
        )
        self.monkeypatch.setattr(
            dcnm_vpc_pair, "get_fabric_details", mock_get_fabric_details
        )

        mock_dcnm_send_2 = Mock(side_effect=dcnm_send_side_effect_2)
        self.monkeypatch.setattr(dcnm_vpc_pair, "dcnm_send", mock_dcnm_send_2)

        mock_dcnm_send_3 = Mock(side_effect=dcnm_send_side_effect_3)
        self.monkeypatch.setattr(dcnm, "dcnm_send", mock_dcnm_send_3)

        set_module_args(
            dict(
                state="fetch",
                src_fabric="mmudigon-svi",
                config=[],
                templates=["vpc_pair"],
            )
        )

        result = self.execute_module(changed=False, failed=False)

        assert result["templates"] != []
