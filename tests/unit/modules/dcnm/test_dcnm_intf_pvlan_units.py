"""Helper-level supplements for native Ethernet PVLAN (do not replace the real-main cases).

The measured-transition test replays every G5/G6 discovery pending through the pre-deploy
validator with its real before/after readbacks: the 46 transitions the controller and device
accepted must pass, and the two non-trunk partial removals (PU3 deploy 500, PX1) must not.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from .test_dcnm_intf_pvlan_harness import FIXTURE, TRANSITIONS


@pytest.mark.parametrize("case", sorted(TRANSITIONS))
def test_measured_transition_is_classified_as_measured(case):
    t = TRANSITIONS[case]
    blocks, global_lines = P.split_blocks(t["pending"])
    problems = P.validate_transition(blocks.get("ethernet1/7", []), P.render(t["pre_policy"], t["pre_nv"]), P.render(t["post_policy"], t["post_nv"]))
    assert global_lines == []
    if t["expect"] == "accept":
        assert problems == [], problems
    else:
        assert any("malformed VLAN number" in p for p in problems)


def test_measured_counts():
    expect = [t["expect"] for t in FIXTURE["transitions"]]
    assert (expect.count("accept"), expect.count("reject")) == (46, 2)


@pytest.mark.parametrize(
    "raw,pairs",
    [
        ("", []),
        ('{"MAPPING_LIST":[]}', []),
        ('{"MAPPING_LIST":[{"P_VLAN":"2210","S_VLAN":"2211"},{"P_VLAN":2210,"S_VLAN":"2212"}]}', [(2210, 2211), (2210, 2212)]),
        ('{"MAPPING_LIST":[{"P_VLAN":"2210","S_VLAN":"2211-2212"}]}', [(2210, 2211), (2210, 2212)]),
        ("{'MAPPING_LIST': [{'P_VLAN': '2210', 'S_VLAN': '2211'}]}", [(2210, 2211)]),
    ],
)
def test_have_wire_forms(raw, pairs):
    assert P.pairs_from_wire(raw, "MAPPING_LIST") == pairs


@pytest.mark.parametrize(
    "raw",
    [
        None,
        5,
        "x",
        '{"OTHER":[]}',
        '{"MAPPING_LIST":{}}',
        '{"MAPPING_LIST":[{"S_VLAN":"1"}]}',
        '{"MAPPING_LIST":[{"P_VLAN":"2210","S_VLAN":"2211"},{"P_VLAN":"2210","S_VLAN":"2211"}]}',
        '{"MAPPING_LIST":[{"P_VLAN":"5000","S_VLAN":"2211"}]}',
    ],
)
def test_malformed_have_wire_raises(raw):
    with pytest.raises(P.PvlanError):
        P.pairs_from_wire(raw, "MAPPING_LIST")


def test_canonical_wire_is_one_sorted_scalar_row_per_pair():
    assert (
        P.pairs_to_wire("MAPPING_LIST", [(2210, 2212), (2210, 2211)])
        == '{"MAPPING_LIST":[{"P_VLAN":"2210","S_VLAN":"2211"},{"P_VLAN":"2210","S_VLAN":"2212"}]}'
    )
    assert P.pairs_to_wire("ASSOCIATION_LIST", []) == '{"ASSOCIATION_LIST":[]}'


def test_allowed_and_native_equality_keep_none_and_unset_distinct():
    assert P.allowed_equal("2301,2302", "2302,2301") and P.allowed_equal("10-12", "10,11,12")
    assert not P.allowed_equal("", "none") and not P.allowed_equal("none", "1")
    assert not P.native_equal("1", "") and P.native_equal("2301", 2301)


def test_secondary_type_from_measured_network_records():
    nets = FIXTURE["networks"]
    assert P.classify_secondary(nets, 2212) == ("isolated", None)
    assert P.classify_secondary(nets, 2211) == ("community", None)
    assert P.classify_secondary(nets, 2210)[0] is None  # the primary is not a secondary
    assert P.classify_secondary(nets, 4000)[0] is None


def test_template_declarations_cover_every_sent_nvpair():
    declared = P.template_declared_names("##template variables\n" + FIXTURE["template_variables"])
    sent = set(P.reconcile("replaced", {"pvlan_mode": "trunk promiscuous"}, "Ethernet1/7", None, None)["nv"])
    assert sent <= declared, sent - declared


@pytest.mark.parametrize(
    "have,want,blocked",
    [
        ([(2210, 2211), (2210, 2212)], [(2210, 2212)], True),
        ([(2210, 2211), (2210, 2212)], [(2210, 2211), (2210, 2213)], True),
        ([(2210, 2211)], [(2210, 2211), (2210, 2212)], False),
        ([(2210, 2211), (2210, 2212)], [], False),
        ([(2210, 2211)], [(2210, 2211)], False),
    ],
)
def test_promiscuous_partial_removal_predicate(have, want, blocked):
    assert P.promiscuous_partial_removal("promiscuous", "promiscuous", have, want) is blocked
    assert P.promiscuous_partial_removal("trunk promiscuous", "trunk promiscuous", have, want) is False
