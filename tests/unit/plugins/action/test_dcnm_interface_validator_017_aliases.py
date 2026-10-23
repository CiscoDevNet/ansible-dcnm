"""SMU 017: the integration checker must validate the documented OSPF boolean aliases against the 017 mode nvPairs.

``ospf_bfd`` (loopback, subinterface) and ``ospf_passive_interface`` (subinterface) are not registry identities since SMU
4.3.1.0175006017 replaced their nvPairs with ``ospfBfdMode`` and ``ospfPassiveMode``, but the module still accepts both as
input: true means enable or passive, false means no local override (``noChange``), never the explicit ``disable`` or
``noPassive``. The checker builds its expected nvPairs from the registered keys, so an alias used to be skipped without a
diagnosis and a test YAML requesting ``ospf_bfd: true`` passed against any readback.

Every case runs the REAL action plugin ``ndfc_interface_validate`` (the repository's r2_cfg / r2_back / r2_run helpers). The
first group is the reproducer of the review finding: a correct readback passes, a wrong and a missing one fail. Serials and
addresses are synthetic.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.tests.unit.plugins.action.test_dcnm_interface_validator_r2 import (
    r2_back,
    r2_cfg,
    r2_run,
)

LO, SUB, ROUTED, SVI = "int_loopback", "int_subif", "int_routed_host", "int_vlan"
# (parent, nvPair, alias key, mode key, positive mode word, explicit negative mode word, positive wire, negative wire)
FIELDS = [
    (LO, "ospfBfdMode", "ospf_bfd", "ospf_bfd_mode", "enable", "disable", "enable", "disable"),
    (SUB, "ospfBfdMode", "ospf_bfd", "ospf_bfd_mode", "enable", "disable", "enable", "disable"),
    (SUB, "ospfPassiveMode", "ospf_passive_interface", "ospf_passive_mode", "passive", "no_passive", "passive", "noPassive"),
]
IDS = ["%s-%s" % (f[0], f[2]) for f in FIELDS]


def run(tmp_path, parent, profile, readback):
    return r2_run(tmp_path, [r2_cfg(parent, **profile)], r2_back(parent, readback))


def readbacks(tmp_path, parent, profile, nvpair, good, bad_values):
    """(correct readback result, [wrong readback results], missing readback result)."""
    ok = run(tmp_path, parent, profile, {nvpair: good})
    wrong = [run(tmp_path, parent, profile, {nvpair: b}) for b in bad_values]
    missing = run(tmp_path, parent, profile, {})
    return ok, wrong, missing


# ------------------------------------------------------------------ the finding: an alias is checked against the readback
@pytest.mark.parametrize("parent,nvpair,alias,mode,pos,neg,pos_wire,neg_wire", FIELDS, ids=IDS)
def test_alias_true_is_checked_against_the_positive_mode(tmp_path, parent, nvpair, alias, mode, pos, neg, pos_wire, neg_wire):
    ok, wrong, missing = readbacks(tmp_path, parent, {alias: True}, nvpair, pos_wire, [neg_wire, "noChange"])
    assert ok["failed"] is False, ok.get("msg")
    assert all(w["failed"] is True for w in wrong), "a wrong readback passed for %s: true" % alias
    assert missing["failed"] is True, "a missing readback passed for %s: true" % alias


@pytest.mark.parametrize("parent,nvpair,alias,mode,pos,neg,pos_wire,neg_wire", FIELDS, ids=IDS)
def test_alias_false_means_no_change_not_the_explicit_negative(tmp_path, parent, nvpair, alias, mode, pos, neg, pos_wire, neg_wire):
    ok, wrong, missing = readbacks(tmp_path, parent, {alias: False}, nvpair, "noChange", [neg_wire, pos_wire])
    assert ok["failed"] is False, ok.get("msg")
    assert wrong[0]["failed"] is True, "false must not be satisfied by the explicit %s" % neg_wire
    assert wrong[1]["failed"] is True
    assert missing["failed"] is True, "a missing readback passed for %s: false" % alias


# ------------------------------------------------------------------ the mode keys stay checked (controls)
@pytest.mark.parametrize("parent,nvpair,alias,mode,pos,neg,pos_wire,neg_wire", FIELDS, ids=IDS)
@pytest.mark.parametrize("word,wire", [("pos", None), ("neg", None), ("no_change", "noChange")])
def test_mode_keys_are_checked(tmp_path, parent, nvpair, alias, mode, pos, neg, pos_wire, neg_wire, word, wire):
    requested = {"pos": pos, "neg": neg, "no_change": "no_change"}[word]
    good = {"pos": pos_wire, "neg": neg_wire, "no_change": "noChange"}[word]
    others = [w for w in (pos_wire, neg_wire, "noChange") if w != good]
    ok, wrong, missing = readbacks(tmp_path, parent, {mode: requested}, nvpair, good, others)
    assert ok["failed"] is False, ok.get("msg")
    assert all(w["failed"] is True for w in wrong)
    assert missing["failed"] is True


# ------------------------------------------------------------------ both spellings in one profile
@pytest.mark.parametrize("parent,nvpair,alias,mode,pos,neg,pos_wire,neg_wire", FIELDS, ids=IDS)
def test_agreeing_spellings_are_checked_once(tmp_path, parent, nvpair, alias, mode, pos, neg, pos_wire, neg_wire):
    profile = {alias: True, mode: pos}
    ok, wrong, missing = readbacks(tmp_path, parent, profile, nvpair, pos_wire, [neg_wire, "noChange"])
    assert ok["failed"] is False, ok.get("msg")
    assert all(w["failed"] is True for w in wrong)
    assert missing["failed"] is True


@pytest.mark.parametrize("parent,nvpair,alias,mode,pos,neg,pos_wire,neg_wire", FIELDS, ids=IDS)
@pytest.mark.parametrize("alias_value,mode_word", [(True, "no_change"), (False, "positive")])
def test_conflicting_spellings_are_diagnosed_never_ignored(tmp_path, parent, nvpair, alias, mode, pos, neg, pos_wire, neg_wire,
                                                           alias_value, mode_word):
    mode_value = pos if mode_word == "positive" else "no_change"
    for readback in ({nvpair: pos_wire}, {nvpair: "noChange"}, {}):
        res = run(tmp_path, parent, {alias: alias_value, mode: mode_value}, readback)
        assert res["failed"] is True, "a conflicting pair was accepted"
        assert "cannot be validated" in res["msg"] and alias in res["msg"] and mode in res["msg"], res["msg"]


# ------------------------------------------------------------------ input the module refuses is diagnosed, not skipped
@pytest.mark.parametrize("bad", ["yes-please", 1, None])
@pytest.mark.parametrize("parent,nvpair,alias,mode,pos,neg,pos_wire,neg_wire", FIELDS, ids=IDS)
def test_a_non_boolean_alias_is_diagnosed_without_echoing_it(tmp_path, parent, nvpair, alias, mode, pos, neg, pos_wire, neg_wire,
                                                             bad):
    res = run(tmp_path, parent, {alias: bad}, {nvpair: pos_wire})
    assert res["failed"] is True
    assert "cannot be validated" in res["msg"] and alias in res["msg"] and "boolean" in res["msg"], res["msg"]
    assert "yes-please" not in res["msg"]


@pytest.mark.parametrize("parent,alias", [(ROUTED, "ospf_bfd"), (SVI, "ospf_bfd"), (LO, "ospf_passive_interface"),
                                          (ROUTED, "ospf_passive_interface"), (SVI, "ospf_passive_interface")])
def test_an_alias_on_a_parent_that_does_not_register_it_is_diagnosed(tmp_path, parent, alias):
    res = run(tmp_path, parent, {alias: True}, {})
    assert res["failed"] is True
    assert "cannot be validated" in res["msg"] and alias in res["msg"], res["msg"]


def test_an_alias_with_an_unknown_expected_parent_is_diagnosed(tmp_path):
    cfg = r2_cfg(LO, ospf_bfd=True)
    cfg["type"] = "eth"
    cfg["profile"]["mode"] = "not-a-mode"
    res = r2_run(tmp_path, [cfg], r2_back(LO, {"ospfBfdMode": "enable"}))
    assert res["failed"] is True
    assert "ospf_bfd" in res["msg"]


# ------------------------------------------------------------------ nothing else changed
def test_a_profile_without_an_alias_is_unaffected(tmp_path):
    res = run(tmp_path, LO, {"ospf_cost": 11}, {"ospfCost": "11"})
    assert res["failed"] is False, res.get("msg")
    assert run(tmp_path, LO, {"ospf_cost": 11}, {"ospfCost": "12"})["failed"] is True
