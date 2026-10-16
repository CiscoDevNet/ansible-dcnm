"""PR725 review 6132068174: the integration checker on a FULL-TEMPLATE readback, as the controller returns it.

The R2 checker keeps every nvPair (extra="allow"), so a real readback carries the whole template while the expectation names a few
requested nvPairs. DeepDiff >= 8 then reported the two dicts as one change at 'root' (threshold_to_diff_deeper, default 0.33): a
correct expectation FAILED, a wrong or missing value failed without naming the field, and the whole readback (sensitive values
included) was printed as that root difference.

Fixture: fixtures/dcnm_interface_full_readback_trunk.json is CAPTURE_REPLAY of one `dcnm_interface state: query` result read from
NDFC 12.6.0.267 (one trunk Ethernet, 57 nvPairs), with the serial and the management address replaced by placeholders and nothing
else changed. Missing-field cases remove the field from a LOCAL COPY (MUTATED_LOCAL_CAPTURE); the controller did not omit it. The
sensitive value is synthetic. Every case runs the real action plugin (`r2_run`, see test_dcnm_interface_validator_r2.py).
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import os

import pytest
import yaml
from unittest.mock import patch
from ansible.plugins.action import ActionBase
from deepdiff import DeepDiff

from ansible_collections.cisco.dcnm.plugins.action.tests.integration import ndfc_interface_validate as validator
from ansible_collections.cisco.dcnm.plugins.action.tests.plugin_utils.pydantic_schemas.dcnm_interface import schemas as S

from .test_dcnm_interface_validator_r2 import R2_FAKE_VALUE, r2_back, r2_cfg, r2_run

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "dcnm_interface_full_readback_trunk.json")
CAPTURE_SWITCH, CAPTURE_SERIAL, CAPTURE_FABRIC = "LEAF101-MGMT", "LEAF101-SERIAL", "FAB1"
CAPTURE_IF = "Ethernet1/12"
LABEL = "ethernet1/12 on " + CAPTURE_SERIAL


class _Task(object):
    def __init__(self, args):
        self.args = args


def capture():
    with open(FIXTURE) as fh:
        return json.load(fh)


def capture_nvpairs(readback):
    (policy,) = readback["response"]
    (intf,) = policy["interfaces"]
    return intf["nvPairs"]


def run_capture(tmp_path, readback, value):
    """The real ActionModule.run() on the captured readback, expecting ONE registered field on the captured identity."""
    config = [{"name": CAPTURE_IF, "type": "eth", "switch": [CAPTURE_SWITCH], "profile": {"mode": "trunk", "flowcontrol_send": value}}]
    path = tmp_path / "expected.yaml"
    path.write_text(yaml.safe_dump(config))
    action = object.__new__(validator.ActionModule)
    action._task = _Task({"ndfc_data": readback, "config_path": str(path), "check_deleted": False,
                          "test_data": {"fabric": CAPTURE_FABRIC, "sw_sn": {CAPTURE_SWITCH: CAPTURE_SERIAL}}})
    with patch.object(ActionBase, "run", return_value={}):
        return action.run(task_vars={})


def differences(result):
    return result["msg"].split("Differences:", 1)[1] if "Differences:" in result["msg"] else ""


# ------------------------------------------------------------------ the capture really is a full template that triggers the collapse
def test_capture_is_the_full_template_and_default_deepdiff_collapses_it():
    nv = capture_nvpairs(capture())
    assert len(nv) == 57 and nv["flowcontrolSend"] == "off"
    want = {"FABRIC_NAME": CAPTURE_FABRIC, "INTF_NAME": "ethernet1/12", "flowcontrolSend": "off"}
    have = S.DcnmInterfaceQuerySchema.model_validate(capture()).model_dump(exclude_none=True)["response"][0]["interfaces"][0]["nvPairs"]
    # Pins the trigger: without the checker's per-key setting, DeepDiff reports the whole dict at root.
    assert "root" in [str(p) for p in DeepDiff(want, have).get("values_changed", {})]
    assert "values_changed" not in DeepDiff(want, have, threshold_to_diff_deeper=0)


# ------------------------------------------------------------------ correct, wrong value, missing field on the full readback
def test_correct_expectation_on_a_full_readback_passes(tmp_path):
    result = run_capture(tmp_path, capture(), "off")
    assert result["failed"] is False, result["msg"]
    assert "'flowcontrolSend': 'off'" in result["msg"].split("Actual data")[0]   # the requested field was in the comparison


def test_wrong_value_on_a_full_readback_names_the_interface_and_the_field(tmp_path):
    result = run_capture(tmp_path, capture(), "on")
    assert result["failed"] is True
    text = differences(result)
    assert LABEL in text and "'flowcontrolSend': {'expected': 'on', 'actual': 'off'}" in text
    assert "root" not in text and "ADMIN_STATE" not in text


def test_missing_field_on_a_full_readback_is_reported_missing(tmp_path):
    mutated = copy.deepcopy(capture())                      # MUTATED_LOCAL_CAPTURE
    del capture_nvpairs(mutated)["flowcontrolSend"]
    result = run_capture(tmp_path, mutated, "off")
    assert result["failed"] is True
    text = differences(result)
    assert LABEL in text and "'missing': ['flowcontrolSend']" in text and "root" not in text


# ------------------------------------------------------------------ sensitive value inside a wide readback: compared, never printed
def wide(extra):
    """The captured template's nvPairs (identity keys left to r2_back / r2_readback) plus the given ones."""
    nv = dict((k, v) for k, v in capture_nvpairs(capture()).items() if k not in ("FABRIC_NAME", "INTF_NAME", "SERIAL_NUMBER"))
    nv.update(extra)
    return nv


@pytest.mark.parametrize("key, nvpair", [("ospf_auth_key", "OSPF_AUTH_KEY"), ("ospf_authentication_key", "ospfAuthenticationKey")])
def test_sensitive_value_in_a_wide_readback_is_compared_and_never_printed(tmp_path, capsys, key, nvpair):
    cfg = [r2_cfg("int_routed_host", **{key: R2_FAKE_VALUE})]
    ok = r2_run(tmp_path, cfg, r2_back("int_routed_host", wide({nvpair: R2_FAKE_VALUE})))
    bad = r2_run(tmp_path, cfg, r2_back("int_routed_host", wide({nvpair: R2_FAKE_VALUE + "-other"})))
    missing = r2_run(tmp_path, cfg, r2_back("int_routed_host", wide({})))
    out = capsys.readouterr().out
    assert ok["failed"] is False, ok["msg"]
    assert bad["failed"] is True and missing["failed"] is True
    for text in (ok["msg"], bad["msg"], missing["msg"], out):
        assert R2_FAKE_VALUE not in text
    assert nvpair in differences(bad) and S.R2_REDACTED in differences(bad) and "root" not in differences(bad)
    assert "'missing': ['%s']" % nvpair in differences(missing)
