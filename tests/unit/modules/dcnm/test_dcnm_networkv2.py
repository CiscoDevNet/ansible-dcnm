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
__author__ = "Praveen Ramoorthy"

from unittest.mock import patch
from _pytest.monkeypatch import MonkeyPatch

from .dcnm_module import TestDcnmModule, set_module_args, loadPlaybookData

# from typing import Any, Dict

import os
import copy
import json
import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm import dcnm
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_networkv2
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_networkv2 import DcnmNetworkv2

# Importing Fixtures
from .fixtures.dcnm_networkv2.dcnm_networkv2_common import dcnm_networkv2_fixture

from unittest.mock import Mock

import datetime
import inspect


def log(msg):
    with open('netv2.log', 'a') as of:
        callerframerecord = inspect.stack()[1]
        frame = callerframerecord[0]
        info = inspect.getframeinfo(frame)
        d = datetime.datetime.now().replace(microsecond=0).isoformat()
        of.write("---- %s ---- %s@%s ---- %s \n" % (d, info.lineno, info.function, msg))

# Fixtures path
fixture_path = os.path.join(os.path.dirname(__file__), "fixtures")
module_data_path = fixture_path + "/dcnm_networkv2/"

# UNIT TEST CASES

def load_data(module_name):
    path = os.path.join(module_data_path, "{0}.json".format(module_name))
    log("path: {0}".format(path))

    with open(path) as f:
        data = f.read()

    try:
        j_data = json.loads(data)
    except Exception as e:
        pass

    return j_data


def test_dcnm_networkv2_log_msg(monkeypatch, dcnm_networkv2_fixture):

    # Logging test
    networkv2 = dcnm_networkv2_fixture
    networkv2.log("This is a test message to test logging function\n")

    try:
        os.remove("netv2.log")
    except Exception as e:
        print(str(e))


@pytest.mark.parametrize(
    "tc_id, filename, wkey, hkey, cfg",
    [(1, "dcnm_networkv2_data", "networkv2_want", "networkv2_have_00001", "networkv2_cfg_00001")],
)
def test_dcnm_networkv2_00001(
    tc_id, monkeypatch, dcnm_networkv2_fixture, filename, wkey, hkey, cfg
):

    # Testing Function dcnm_update_network_information()

    networkv2 = dcnm_networkv2_fixture

    data = load_data(filename)
    want = data.get(wkey)
    have = data.get(hkey)
    conf = data.get(cfg)

    networkv2.dcnm_update_network_information(want, have, conf)
    assert want["networkTemplateConfig"]["mtu"] == '1800'


@pytest.mark.parametrize(
    "tc_id, filename, wkey, hkey, hkey1, cfg",
    [(1, "dcnm_networkv2_data", "networkv2_want", "networkv2_have_00001", "networkv2_have_00002", "networkv2_cfg_00001"),
     (2, "dcnm_networkv2_data", "networkv2_want", "networkv2_have_00001", "networkv2_have_00002", "networkv2_cfg_00001"),
     (3, "dcnm_networkv2_data", "networkv2_want", "networkv2_have_00001", "networkv2_have_00002", "networkv2_cfg_00001"),
     (4, "dcnm_networkv2_data", "networkv2_want", "networkv2_have_00001", "networkv2_have_00002", "networkv2_cfg_00001")],
)
def test_dcnm_networkv2_00002(
    tc_id, monkeypatch, dcnm_networkv2_fixture, filename, wkey, hkey, hkey1, cfg
):
    
    # Testing Function update_want()

    networkv2 = dcnm_networkv2_fixture

    data = load_data(filename)
    want = data.get(wkey)
    have = data.get(hkey)
    have1 = data.get(hkey1)
    conf = data.get(cfg)

    if tc_id == 1:
        networkv2.want_create = []
    elif tc_id == 2:
        networkv2.want_create.append(want)
        networkv2.have_create.append(have1)
        networkv2.have_create.append(have)
        networkv2.config.append(conf)
    elif tc_id == 3:
        networkv2.want_create.append(want)
        networkv2.have_create.append(have1)
        networkv2.config.append(conf)
    elif tc_id == 4:
        networkv2.want_create.append(want)
        networkv2.have_create.append(have)
        conf1 = copy.deepcopy(conf)
        conf1["net_name"] = "netv2"
        networkv2.config.append(conf1)

    networkv2.update_want()
    if tc_id == 2:
        assert networkv2.want_create[0]["networkTemplateConfig"]["mtu"] == '1800'
    elif tc_id == 3:
        assert networkv2.want_create[0]["networkTemplateConfig"]["mtu"] == '1500'
    elif tc_id == 4:
        assert networkv2.want_create[0]["networkTemplateConfig"]["mtu"] == '1500'

@pytest.mark.parametrize("tc_id", [(1), (2)],)
def test_dcnm_networkv2_00003(tc_id, monkeypatch, dcnm_networkv2_fixture):

    # Testing Function update_module_info()

    networkv2 = dcnm_networkv2_fixture

    resp = load_data("dcnm_networkv2_response")

    networkv2.fabric = "test_netv2"

    dcnm_version_supported_side_effect = []
    get_fabric_inventory_details_side_effect = []
    get_fabric_details_side_effect = []

    if tc_id == 1:
        dcnm_version_supported_side_effect.append(12)
    elif tc_id == 2:
        dcnm_version_supported_side_effect.append(11)

    get_fabric_inventory_details_side_effect.append(
        resp.get("networkv2_inv_details")
    )
    get_fabric_details_side_effect.append(
        resp.get("networkv2_fab_details")
    )

    mock_dcnm_version_supported = Mock(
        side_effect=dcnm_version_supported_side_effect
    )
    monkeypatch.setattr(
        dcnm_networkv2, "dcnm_version_supported", mock_dcnm_version_supported
    )

    mock_get_fabric_inventory_details = Mock(
        side_effect=get_fabric_inventory_details_side_effect
    )
    monkeypatch.setattr(
        dcnm_networkv2,
        "get_fabric_inventory_details",
        mock_get_fabric_inventory_details,
    )

    mock_get_fabric_details = Mock(side_effect=get_fabric_details_side_effect)
    monkeypatch.setattr(
        dcnm_networkv2, "get_fabric_details", mock_get_fabric_details
    )

    try:
        networkv2.update_module_info()
    except Exception as e:
        assert "dcnm_networkv2 module is only supported on NDFC. It is not support on DCN" in str(e)

    if tc_id == 1:
        assert networkv2.inventory_data != []
        assert networkv2.fabric_det != []
        assert networkv2.dcnm_version == 12
        assert networkv2.paths != {}

@pytest.mark.parametrize(
    "tc_id, filename, create, create_update, attach, detach, deploy, undeploy",
    [(1, "dcnm_networkv2_data", "networkv2_diff_create_00001", "networkv2_diff_create_update_00001",
      "networkv2_diff_attach_00001", "networkv2_diff_detach_00001", "networkv2_diff_deploy_00001",
      "networkv2_diff_undeploy_00001"),
     (2, "dcnm_networkv2_data", "networkv2_diff_create_00001", "networkv2_diff_create_update_00001",
      "networkv2_diff_attach_00002", "networkv2_diff_detach_00001", "networkv2_diff_deploy_00001",
      "networkv2_diff_undeploy_00001"),],
)
def test_dcnm_networkv2_00004(
    tc_id, monkeypatch, dcnm_networkv2_fixture, filename, create, create_update,
    attach, detach, deploy, undeploy
):
    
    # Testing Function format_diff()

    networkv2 = dcnm_networkv2_fixture

    data = load_data(filename)
    networkv2.diff_create = data.get(create)
    networkv2.diff_create_update = data.get(create_update)
    if tc_id == 1:
        networkv2.diff_attach = data.get(attach)
    elif tc_id == 2:
        networkv2.diff_attach = []
    networkv2.diff_detach = data.get(detach)
    networkv2.diff_deploy = data.get(deploy)
    networkv2.diff_undeploy = data.get(undeploy)

    networkv2.format_diff()
    assert networkv2.diff_input_format != []
    assert networkv2.diff_input_format[0]["net_name"] == "net1"
    assert networkv2.diff_input_format[0]["networkTemplateConfig"] != {}
    assert networkv2.diff_input_format[0]["networkTemplateConfig"]["mtu"] == 1800
    assert networkv2.diff_input_format[0]["networkTemplateConfig"]["vlanId"] == 1001
    assert networkv2.diff_input_format[0]["networkTemplateConfig"]["secondaryGW1"] == '3.1.1.1/24'
    if tc_id == 1:
        assert networkv2.diff_input_format[0]["attach"]!= []
        assert networkv2.diff_input_format[0]["attach"][0]["ipAddress"] == "192.168.2.1"
        assert networkv2.diff_input_format[0]["attach"][0]["deploy"] == True
    elif tc_id == 2:
        assert networkv2.diff_input_format[0]["attach"] == []

@pytest.mark.parametrize(
    "tc_id, cfg",
    [(1, "networkv2_cfg_00001"),
     (2, "networkv2_cfg_00001"),
     (3, "networkv2_cfg_00001"),
     (4, "networkv2_cfg_00002"),
     (5, "networkv2_cfg_00002"),
     (6, "networkv2_cfg_00002"),],
)
def test_dcnm_networkv2_00005(
    tc_id,
    monkeypatch,
    dcnm_networkv2_fixture,
    cfg,
    ):

    # Testing Function validate_input()

    networkv2 = dcnm_networkv2_fixture

    data = load_data("dcnm_networkv2_data")
    resp = load_data("dcnm_networkv2_response")
    config = data.get(cfg)

    networkv2.paths = DcnmNetworkv2.dcnm_network_paths[12]

    if tc_id == 2:
        conf = copy.deepcopy(config)
        conf.pop("net_name")
    elif tc_id == 5:
        conf = copy.deepcopy(config)
        conf["network_template_config"]["attach"][0]["switchPorts"] = []
        conf["network_template_config"]["attach"][0]["torPorts"] = []
    else:
        conf = config
    networkv2.config.append(conf)

    networkv2.fabric = "test_netv2"

    if tc_id == 1:
        networkv2.params["state"] = "deleted"
    else:
        networkv2.params["state"] = "merged"

    if tc_id == 3 or tc_id == 4 or tc_id == 5:
        dcnm_send_side_effect = []
        dcnm_send_side_effect.append(resp.get("resp_net_template"))
        dcnm_send_side_effect.append(resp.get("resp_net_ext_template"))
        mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
        monkeypatch.setattr(dcnm, "dcnm_send", mock_dcnm_send)

    if tc_id == 6:
        networkv2.dyn_arg_spec = data.get("dyn_arg_spec")

    try:
        networkv2.validate_input()
    except Exception as e:
        if tc_id == 2:
            assert "Invalid parameters in playbook:" in str(e)

    if tc_id != 2:
        assert len(networkv2.validated) == 1

@pytest.mark.parametrize(
    "tc_id, validated_cfg, cfg",
    [(1, "networkv2_validated_00001", "networkv2_cfg_00002"),
     (2, "networkv2_validated_00001", "networkv2_cfg_00002"),
     (3, "networkv2_validated_00001", "networkv2_cfg_00002"),
     (4, "networkv2_validated_00001", "networkv2_cfg_00002"),
     (5, "networkv2_validated_00001", "networkv2_cfg_00002"),
     (6, "networkv2_validated_00001", "networkv2_cfg_00002"),
     (7, "networkv2_validated_00001", "networkv2_cfg_00002"),
     (8, "networkv2_validated_00001", "networkv2_cfg_00002"),],
)
def test_dcnm_networkv2_00006(
    tc_id,
    monkeypatch,
    dcnm_networkv2_fixture,
    validated_cfg,
    cfg
    ):

    # Testing Function get_want()

    networkv2 = dcnm_networkv2_fixture

    data = load_data("dcnm_networkv2_data")
    validated_config = data.get(validated_cfg)
    config = data.get(cfg)
    networkv2.ip_sn = data.get("networkv2_ip_sn")
    have_create = data.get("networkv2_have_create_00001")
    have_attach = data.get("networkv2_have_attach_00001")

    if tc_id != 2:
        networkv2.config.append(config)

    networkv2.validated = validated_config
    if tc_id == 1:
        networkv2.params["state"] = "deleted"
    else:
        networkv2.params["state"] = "merged"

    if tc_id == 3:
        networkv2.have_create = have_create
        networkv2.have_attach = have_attach
    elif tc_id == 4:
        networkv2.have_create = have_create
        networkv2.have_attach = have_attach
        validated = copy.deepcopy(validated_config)
        validated[0]["attach"][0]["switchPorts"].remove("Ethernet1/12")
        validated[0]["attach"][0]["torPorts"][0]["ports"].remove("Ethernet1/12")
        networkv2.validated = validated
    elif tc_id == 5:
        networkv2.have_create = have_create
        networkv2.have_attach = have_attach
        validated = copy.deepcopy(validated_config)
        validated[0]["attach"][0]["switchPorts"] = []
        validated[0]["attach"][0]["torPorts"] = []
        networkv2.validated = validated
    elif tc_id == 6:
        networkv2.have_create = have_create
        attach = copy.deepcopy(have_attach)
        attach[0]["lanAttachList"][0]["switchPorts"] = []
        attach[0]["lanAttachList"][0]["torPorts"] = []
        networkv2.have_attach = attach
        validated = copy.deepcopy(validated_config)
        validated[0]["attach"][0]["switchPorts"] = []
        validated[0]["attach"][0]["torPorts"] = []
        networkv2.validated = validated
    elif tc_id == 7:
        networkv2.have_create = have_create
        networkv2.have_attach = have_attach
        validated = copy.deepcopy(validated_config)
        validated[0]["attach"][0]["detachSwitchPorts"].append("Ethernet1/12")
        validated[0]["attach"][0]["attached"] = False
        networkv2.validated = validated
    elif tc_id == 8:
        networkv2.have_create = have_create
        networkv2.have_attach = have_attach
        validated = copy.deepcopy(validated_config)
        validated[0]["attach"][0]["ipAddress"] = "192.168.2.4"
        networkv2.validated = validated

    try:
        networkv2.get_want()
    except Exception as e:
        if tc_id == 8:
            assert "does not have the switch" in str(e)
        
    if tc_id != 8 and tc_id != 1 and tc_id != 2:
        assert len(networkv2.want_create) == 1
        assert len(networkv2.want_attach) == 1
        assert networkv2.want_deploy != {}

@pytest.mark.parametrize(
    "tc_id, get_network, get_netattach",
    [(1, "networkv2_net_objects_00001", "networkv2_net_attach_objects_00001"),
     (2, "networkv2_net_objects_00001", "networkv2_net_attach_objects_00001"),
     (3, "networkv2_net_objects_00001", "networkv2_net_attach_objects_00001"),
     (4, "networkv2_net_objects_00001", "networkv2_net_attach_objects_00001"),
     (5, "networkv2_net_objects_00001", "networkv2_net_attach_objects_00001"),
     (6, "networkv2_net_objects_00001", "networkv2_net_attach_objects_00001"),
     (7, "networkv2_net_objects_00001", "networkv2_net_attach_objects_00001"),],
)
def test_dcnm_networkv2_00007(
    tc_id,
    monkeypatch,
    dcnm_networkv2_fixture,
    get_network,
    get_netattach,
    ):

    # Testing Function get_have()

    networkv2 = dcnm_networkv2_fixture

    resp = load_data("dcnm_networkv2_response")
    get_net = copy.deepcopy(resp.get(get_network))
    get_attach = copy.deepcopy(resp.get(get_netattach))
    
    networkv2.paths = DcnmNetworkv2.dcnm_network_paths[12]
    networkv2.fabric = "test_netv2"
    networkv2.params["state"] = "merged"

    if tc_id == 4:
        get_net["DATA"] = []
    elif tc_id == 5:
        del get_net["DATA"]
        del get_net["MESSAGE"]
        get_net.update({"ERROR": "Not Found"})
        get_net["RETURN_CODE"] = 404
    elif tc_id == 6:
        del get_net["DATA"]
        get_net["RETURN_CODE"] = 400
        get_net["MESSAGE"] = "Bad Request"
    elif tc_id == 7:
        networkv2.params["state"] = "deleted"
        get_attach["DATA"][0]["lanAttachList"][0]["lanAttachState"] = "PENDING"

    dcnm_send_side_effect = []
    dcnm_send_side_effect.append(get_net)
    mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
    monkeypatch.setattr(dcnm_networkv2, "dcnm_send", mock_dcnm_send)

    if tc_id == 2:
        get_attach["DATA"][0]["lanAttachList"][0]["portNames"] = "leaf1(Ethernet1/10,Ethernet1/11) tor(Ethernet1/10,Ethernet1/11)"
    elif tc_id == 3:
        get_attach["DATA"] = []
    
    dcnm_get_url_side_effect = []
    dcnm_get_url_side_effect.append(get_attach)
    mock_dcnm_get_url = Mock(side_effect=dcnm_get_url_side_effect)
    monkeypatch.setattr(dcnm_networkv2, "dcnm_get_url", mock_dcnm_get_url)

    try:
        networkv2.get_have()
    except Exception as e:
        if tc_id == 5:
            assert "Fabric test_netv2 not present on NDFC" in str(e)
        elif tc_id == 56:
            assert "Unable to find Networks under fabric" in str(e)

    if tc_id == 1 or tc_id == 2:
        assert len(networkv2.have_create) == 1
        assert len(networkv2.have_attach) == 1
        assert networkv2.have_deploy != {}

@pytest.mark.parametrize(
    "tc_id, cfg, have, want, get_network, get_netattach",
    [(1, "networkv2_cfg_00001", "networkv2_have_00001", "networkv2_want","networkv2_net_objects_00002", "networkv2_net_attach_objects_00001"),
     (2, "networkv2_cfg_00001", "networkv2_have_00001", "networkv2_want","networkv2_net_objects_00001", "networkv2_net_attach_objects_00001"),],
)
def test_dcnm_networkv2_00008(
    tc_id,
    monkeypatch,
    dcnm_networkv2_fixture,
    cfg,
    have,
    want,
    get_network,
    get_netattach,
    ):

    # Testing Function get_diff_query()

    networkv2 = dcnm_networkv2_fixture

    data = load_data("dcnm_networkv2_data")
    resp = load_data("dcnm_networkv2_response")

    config = data.get(cfg)
    have_create = data.get(have)
    want_create = data.get(want)
    get_net = copy.deepcopy(resp.get(get_network))
    get_attach = copy.deepcopy(resp.get(get_netattach))

    networkv2.paths = DcnmNetworkv2.dcnm_network_paths[12]
    networkv2.fabric = "test_netv2"
    networkv2.params["state"] = "query"
    if tc_id == 1:
        networkv2.config.append(config)
    networkv2.have_create.append(have_create)
    networkv2.want_create.append(want_create)

    dcnm_send_side_effect = []
    dcnm_send_side_effect.append(get_net)
    dcnm_send_side_effect.append(get_attach)
    mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
    monkeypatch.setattr(dcnm_networkv2, "dcnm_send", mock_dcnm_send)

    networkv2.get_diff_query()

    assert len(networkv2.query) == 1

@pytest.mark.parametrize(
    "tc_id, cfg, have, want, have_netattach",
    [(1, "networkv2_cfg_00001", "networkv2_have_00001", "networkv2_want", "networkv2_have_attach_00001"),
     (2, "networkv2_cfg_00001", "networkv2_have_00001", "networkv2_want", "networkv2_have_attach_00001"),
     (3, "networkv2_cfg_00001", "networkv2_have_00001", "networkv2_want", "networkv2_have_attach_00001"),
     (4, "networkv2_cfg_00001", "networkv2_have_00001", "networkv2_want", "networkv2_have_attach_00001")],
)
def test_dcnm_networkv2_00009(
    tc_id,
    monkeypatch,
    dcnm_networkv2_fixture,
    cfg,
    have,
    want,
    have_netattach,
    ):

    # Testing Function get_diff_delete()

    networkv2 = dcnm_networkv2_fixture

    data = load_data("dcnm_networkv2_data")

    config = data.get(cfg)
    have_create = data.get(have)
    want_create = data.get(want)
    have_attach = data.get(have_netattach)

    networkv2.paths = DcnmNetworkv2.dcnm_network_paths[12]
    networkv2.fabric = "test_netv2"
    networkv2.params["state"] = "deleted"

    if tc_id == 1 or tc_id == 2:
        networkv2.config.append(config)
    if tc_id == 2 or tc_id == 4:
        networkv2.have_attach = have_attach
    networkv2.have_create.append(have_create)
    networkv2.want_create.append(want_create)
            
    networkv2.get_diff_delete()

    assert len(networkv2.diff_delete) == 1

@pytest.mark.parametrize(
    "tc_id, cfg, have, want, have_netattach",
    [(1, "networkv2_cfg_00001", "networkv2_have_00001", "networkv2_want", "networkv2_have_attach_00001"),
     (2, "networkv2_cfg_00001", "networkv2_have_00002", "networkv2_want", "networkv2_have_attach_00002"),],
)
def test_dcnm_networkv2_00010(
    tc_id,
    monkeypatch,
    dcnm_networkv2_fixture,
    cfg,
    have,
    want,
    have_netattach,
    ):

    # Testing Function get_diff_override() with get_diff_override() and get_diff_merge()

    networkv2 = dcnm_networkv2_fixture

    data = load_data("dcnm_networkv2_data")

    config = data.get(cfg)
    have_create = data.get(have)
    want_create = data.get(want)
    have_attach = data.get(have_netattach)

    networkv2.paths = DcnmNetworkv2.dcnm_network_paths[12]
    networkv2.fabric = "test_netv2"
    networkv2.params["state"] = "overridden"

    networkv2.config.append(config)
    networkv2.have_create.append(have_create)
    networkv2.have_attach = have_attach
    networkv2.want_create.append(want_create)

    networkv2.get_diff_override()

    if tc_id == 1:
        assert len(networkv2.diff_create) == 0
        assert len(networkv2.diff_attach) == 1
    elif tc_id == 2:
        assert len(networkv2.diff_create) == 1
        assert len(networkv2.diff_attach) == 0

@pytest.mark.parametrize(
    "tc_id, cfg, have, want, have_netattach, want_netattach",
    [(1, "networkv2_cfg_00001", "networkv2_have_00001", "networkv2_want", "networkv2_have_attach_00001", "networkv2_want_attach_00001"),
     (2, "networkv2_cfg_00001", "networkv2_have_00001", "networkv2_want", "networkv2_have_attach_00001", "networkv2_want_attach_00001"),],
)
def test_dcnm_networkv2_00011(
    tc_id,
    monkeypatch,
    dcnm_networkv2_fixture,
    cfg,
    have,
    want,
    have_netattach,
    want_netattach
    ):

    # Testing Fuction get_diff_replace()

    networkv2 = dcnm_networkv2_fixture

    data = load_data("dcnm_networkv2_data")

    config = data.get(cfg)
    have_create = data.get(have)
    want_create = data.get(want)
    have_attach = copy.deepcopy(data.get(have_netattach))
    want_attach = copy.deepcopy(data.get(want_netattach))

    if tc_id == 2:
        del want_attach[0]["lanAttachList"][0]

    networkv2.paths = DcnmNetworkv2.dcnm_network_paths[12]
    networkv2.fabric = "test_netv2"
    networkv2.params["state"] = "replaced"

    networkv2.config.append(config)
    networkv2.have_create.append(have_create)
    networkv2.have_attach = have_attach
    networkv2.want_create.append(want_create)
    networkv2.want_attach = want_attach

    networkv2.get_diff_replace()

    assert len(networkv2.diff_create) == 0
    assert len(networkv2.diff_attach) == 1

@pytest.mark.parametrize(
    "tc_id, cfg, have, want, have_netattach, want_netattach",
    [(1, "networkv2_cfg_00001", "networkv2_have_00001", "networkv2_want", "networkv2_have_attach_00001", "networkv2_want_attach_00001"),
     (2, "networkv2_cfg_00001", "networkv2_have_00001", "networkv2_want", "networkv2_have_attach_00001", "networkv2_want_attach_00002"),
     (3, "networkv2_cfg_00001", "networkv2_have_00001", "networkv2_want", "networkv2_have_attach_00001", "networkv2_want_attach_00003"),
     (4, "networkv2_cfg_00001", "networkv2_have_00001", "networkv2_want", "networkv2_have_attach_00001", "networkv2_want_attach_00001"),],
)
def test_dcnm_networkv2_00012(
    tc_id,
    monkeypatch,
    dcnm_networkv2_fixture,
    cfg,
    have,
    want,
    have_netattach,
    want_netattach
    ):

    # Testing Fuction get_diff_merge()

    networkv2 = dcnm_networkv2_fixture

    data = load_data("dcnm_networkv2_data")

    config = data.get(cfg)
    have_create = data.get(have)
    want_create = data.get(want)
    have_attach = copy.deepcopy(data.get(have_netattach))
    want_attach = copy.deepcopy(data.get(want_netattach))

    networkv2.paths = DcnmNetworkv2.dcnm_network_paths[12]
    networkv2.fabric = "test_netv2"
    networkv2.params["state"] = "merged"

    networkv2.config.append(config)
    networkv2.have_create.append(have_create)
    networkv2.have_attach = have_attach
    networkv2.want_create.append(want_create)
    networkv2.want_attach = want_attach

    if tc_id == 4:
        del networkv2.have_attach[0]["lanAttachList"][0]

    networkv2.get_diff_merge()

    assert len(networkv2.diff_create) == 0
    assert len(networkv2.diff_attach) == 1
    assert len(networkv2.diff_create_update) == 1

@pytest.mark.parametrize(
    "tc_id, want, get_response",
    [(1, "networkv2_diff_create_00001", "get_response_00001"),
     (2, "networkv2_diff_create_00001", "get_response_00002"),
     (3, "networkv2_diff_create_00001", "get_response_00002"),],
)
def test_dcnm_networkv2_00013(
    tc_id,
    monkeypatch,
    dcnm_networkv2_fixture,
    want,
    get_response
    ):

    # Testing Function push_to_remote_update()

    networkv2 = dcnm_networkv2_fixture

    data = load_data("dcnm_networkv2_data")
    resp = load_data("dcnm_networkv2_response")
    want_create = data.get(want)
    get_resp = copy.deepcopy(resp.get(get_response))

    networkv2.diff_create_update = want_create

    dcnm_send_side_effect = []
    dcnm_send_side_effect.append(get_resp)
    mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
    monkeypatch.setattr(dcnm_networkv2, "dcnm_send", mock_dcnm_send)

    networkv2.fabric = "test_netv2"
    networkv2.paths = DcnmNetworkv2.dcnm_network_paths[12]

    try:
        if tc_id == 3:
            networkv2.push_to_remote(True)
        else:
            networkv2.push_to_remote()
    except Exception as e:
        assert "ERROR" in str(e)

@pytest.mark.parametrize(
    "tc_id, want, get_response",
    [(1, "networkv2_want_attach_00001", "get_response_00001"),
     (2, "networkv2_want_attach_00001", "get_response_00002"),
     (3, "networkv2_want_attach_00001", "get_response_00002"),],
)
def test_dcnm_networkv2_00014(
    tc_id,
    monkeypatch,
    dcnm_networkv2_fixture,
    want,
    get_response
    ):

    # Testing Function push_to_remote_detach()

    networkv2 = dcnm_networkv2_fixture

    data = load_data("dcnm_networkv2_data")
    resp = load_data("dcnm_networkv2_response")
    want_detach = data.get(want)
    get_resp = copy.deepcopy(resp.get(get_response))

    networkv2.diff_detach = want_detach

    dcnm_send_side_effect = []
    dcnm_send_side_effect.append(get_resp)
    mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
    monkeypatch.setattr(dcnm_networkv2, "dcnm_send", mock_dcnm_send)

    networkv2.fabric = "test_netv2"
    networkv2.paths = DcnmNetworkv2.dcnm_network_paths[12]
    networkv2.is_ms_fabric = False

    try:
        if tc_id == 3:
            networkv2.push_to_remote(True)
        else:
            networkv2.push_to_remote()
    except Exception as e:
        assert "ERROR" in str(e)

@pytest.mark.parametrize(
    "tc_id, undeploy, get_response",
    [(1, "networkv2_diff_deploy_00001", "get_response_00001"),
     (2, "networkv2_diff_deploy_00001", "get_response_00002"),
     (3, "networkv2_diff_deploy_00001", "get_response_00002"),],
)
def test_dcnm_networkv2_00015(
    tc_id,
    monkeypatch,
    dcnm_networkv2_fixture,
    undeploy,
    get_response
    ):

    # Testing Function push_to_remote_undeploy()

    networkv2 = dcnm_networkv2_fixture

    data = load_data("dcnm_networkv2_data")
    resp = load_data("dcnm_networkv2_response")
    want_undeploy = data.get(undeploy)
    get_resp = copy.deepcopy(resp.get(get_response))

    networkv2.diff_undeploy = want_undeploy
    networkv2.fabric = "test_netv2"
    networkv2.paths = DcnmNetworkv2.dcnm_network_paths[12]

    dcnm_send_side_effect = []
    dcnm_send_side_effect.append(get_resp)
    mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
    monkeypatch.setattr(dcnm_networkv2, "dcnm_send", mock_dcnm_send)

    try:
        if tc_id == 3:
            networkv2.push_to_remote(True)
        else:
            networkv2.push_to_remote()
    except Exception as e:
        assert "ERROR" in str(e)

@pytest.mark.parametrize(
    "tc_id, want, get_response",
    [(1, "networkv2_diff_create_00001", "get_response_00001"),
     (2, "networkv2_diff_create_00001", "get_response_00002"),
     (3, "networkv2_diff_create_00001", "get_response_00002"),],
)
def test_dcnm_networkv2_00016(
    tc_id,
    monkeypatch,
    dcnm_networkv2_fixture,
    want,
    get_response
    ):

    # Testing Function push_to_remote_create()

    networkv2 = dcnm_networkv2_fixture

    data = load_data("dcnm_networkv2_data")
    resp = load_data("dcnm_networkv2_response")
    want_create = data.get(want)
    get_resp = copy.deepcopy(resp.get(get_response))

    networkv2.diff_create = want_create

    dcnm_send_side_effect = []
    dcnm_send_side_effect.append(get_resp)
    mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
    monkeypatch.setattr(dcnm_networkv2, "dcnm_send", mock_dcnm_send)

    networkv2.fabric = "test_netv2"
    networkv2.paths = DcnmNetworkv2.dcnm_network_paths[12]

    try:
        if tc_id == 3:
            networkv2.push_to_remote(True)
        else:
            networkv2.push_to_remote()
    except Exception as e:
        assert "ERROR" in str(e)

@pytest.mark.parametrize(
    "tc_id, want, get_response",
    [(1, "networkv2_want_attach_00001", "attach_response_00001"),
     (2, "networkv2_want_attach_00001", "get_response_00002"),
     (3, "networkv2_want_attach_00001", "get_response_00002"),],
)
def test_dcnm_networkv2_00017(
    tc_id,
    monkeypatch,
    dcnm_networkv2_fixture,
    want,
    get_response
    ):

    # Testing Function push_to_remote_attach()

    networkv2 = dcnm_networkv2_fixture

    data = load_data("dcnm_networkv2_data")
    resp = load_data("dcnm_networkv2_response")
    want_attach = data.get(want)
    get_resp = copy.deepcopy(resp.get(get_response))

    networkv2.diff_attach = want_attach

    dcnm_send_side_effect = []
    dcnm_send_side_effect.append(get_resp)
    mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
    monkeypatch.setattr(dcnm_networkv2, "dcnm_send", mock_dcnm_send)

    networkv2.fabric = "test_netv2"
    networkv2.paths = DcnmNetworkv2.dcnm_network_paths[12]
    networkv2.is_ms_fabric = False

    try:
        if tc_id == 3:
            networkv2.push_to_remote(True)
        else:
            networkv2.push_to_remote()
    except Exception as e:
        assert "ERROR" in str(e)

@pytest.mark.parametrize(
    "tc_id, deploy, get_response",
    [(1, "networkv2_diff_deploy_00001", "get_response_00001"),
     (2, "networkv2_diff_deploy_00001", "get_response_00002"),
     (3, "networkv2_diff_deploy_00001", "get_response_00002"),],
)
def test_dcnm_networkv2_00018(
    tc_id,
    monkeypatch,
    dcnm_networkv2_fixture,
    deploy,
    get_response
    ):

    # Testing Function push_to_remote_deploy()

    networkv2 = dcnm_networkv2_fixture

    data = load_data("dcnm_networkv2_data")
    resp = load_data("dcnm_networkv2_response")
    want_deploy = data.get(deploy)
    get_resp = copy.deepcopy(resp.get(get_response))

    networkv2.diff_deploy = want_deploy
    networkv2.fabric = "test_netv2"
    networkv2.paths = DcnmNetworkv2.dcnm_network_paths[12]

    dcnm_send_side_effect = []
    dcnm_send_side_effect.append(get_resp)
    mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
    monkeypatch.setattr(dcnm_networkv2, "dcnm_send", mock_dcnm_send)

    try:
        if tc_id == 3:
            networkv2.push_to_remote(True)
        else:
            networkv2.push_to_remote()
    except Exception as e:
        assert "ERROR" in str(e)

@pytest.mark.parametrize(
    "tc_id, delete, get_response, get_netattach_response",
    [(1, "networkv2_diff_delete_00001", "get_response_00003", "networkv2_net_attach_objects_00001"),
     (2, "networkv2_diff_delete_00001", "get_response_00003", "networkv2_net_attach_objects_00001"),
     (3, "networkv2_diff_delete_00001", "get_response_00003", "networkv2_net_attach_objects_00001"),
     (4, "networkv2_diff_delete_00001", "get_response_00003", "networkv2_net_attach_objects_00001"),
     (5, "networkv2_diff_delete_00001", "get_response_00004", "networkv2_net_attach_objects_00001"),
     (6, "networkv2_diff_delete_00001", "get_response_00004", "networkv2_net_attach_objects_00001"),
     (7, "networkv2_diff_delete_00001", "get_response_00003", "networkv2_net_attach_objects_00001"),],
)
def test_dcnm_networkv2_00019(
    tc_id,
    monkeypatch,
    dcnm_networkv2_fixture,
    delete,
    get_response,
    get_netattach_response
    ):

    # Testing Function push_to_remote_deploy()

    networkv2 = dcnm_networkv2_fixture

    data = load_data("dcnm_networkv2_data")
    resp = load_data("dcnm_networkv2_response")
    get_resp = copy.deepcopy(resp.get(get_response))
    get_netattach_resp = copy.deepcopy(resp.get(get_netattach_response))
    get_netattach_resp1 = copy.deepcopy(resp.get(get_netattach_response))
    want_delete = data.get(delete)

    networkv2.diff_delete = want_delete
    networkv2.fabric = "test_netv2"
    networkv2.paths = DcnmNetworkv2.dcnm_network_paths[12]
    if tc_id == 1 or tc_id == 5 or tc_id == 6:
        get_netattach_resp["DATA"][0]["lanAttachList"][0]["lanAttachState"] = "NA"
    elif tc_id == 2:
        get_netattach_resp["DATA"][0]["lanAttachList"][0]["lanAttachState"] = "OUT-OF-SYNC"
        get_netattach_resp1["DATA"][0]["lanAttachList"][0]["lanAttachState"] = "NA"
    elif tc_id == 3:
        get_netattach_resp1["DATA"][0]["lanAttachList"][0]["lanAttachState"] = "NA"
    elif tc_id == 4 or tc_id == 7:
        get_netattach_resp["DATA"][0]["lanAttachList"][0]["lanAttachState"] = "OUT-OF-SYNC"

    dcnm_send_side_effect = []
    dcnm_send_side_effect.append(get_netattach_resp)
    if tc_id == 2 or tc_id == 3:
        dcnm_send_side_effect.append(get_netattach_resp1)
    elif tc_id == 4 or tc_id == 7:
        for i in range(10):
            dcnm_send_side_effect.append(get_netattach_resp)
    dcnm_send_side_effect.append(get_resp)
    mock_dcnm_send = Mock(side_effect=dcnm_send_side_effect)
    monkeypatch.setattr(dcnm_networkv2, "dcnm_send", mock_dcnm_send)

    try:
        if tc_id == 6 or tc_id == 7:
            networkv2.push_to_remote(True)
        else:
            networkv2.push_to_remote()
    except Exception as e:
        if tc_id == 4 or tc_id == 7:
            assert "Deletion of Networks net1 has failed" in str(e)
        else:
            assert "ERROR" in str(e)