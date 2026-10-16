"""PR725-PATCH-VERSION-001 / DELTA R2 finding 1 -- regression for the published EXAMPLES
entry itself, not a hand-written restatement of it.

R1 review found that the module's own "Create a dot1q-tunnel vPC" EXAMPLES entry sets two
registered generic-binding-registry fields (disable_lldp_transmit/disable_lldp_receive)
without declaring patch_version, so the documented playbook -- replayed as written -- now
fails before any write. This file parses `DcnmIntf`'s real EXAMPLES string with the stdlib
AST/YAML parsers (the same approach the architect's review probe used), extracts that exact
entry's config/profile, and drives it through the real module `main()` with transport
mocked. It fails if the shipped example ever regresses again, in either direction: if the
example stops requiring the approved patch, or if the approved patch stops making it work.

NOT LIVE TESTED IN THIS GENERATION. No controller, Nexus or Jenkins is contacted.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import ast

import yaml

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface

from .gie_withdrawal_harness import PATCH_KEY_OMITTED, SUPPORTED_PATCH, run, writes


def _parse_examples_block():
    """The module's real EXAMPLES string, parsed exactly as PyYAML/Ansible would read it.

    Reading the live attribute off the imported module (not a copy of the source text)
    means this test sees whatever EXAMPLES actually contains at import time -- it cannot
    drift from the shipped documentation by construction.
    """
    with open(dcnm_interface.__file__) as handle:
        tree = ast.parse(handle.read())
    examples_src = next(
        ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "EXAMPLES" for t in node.targets)
    )
    return yaml.safe_load(examples_src)


def _dot1q_vpc_task():
    entries = _parse_examples_block()
    task = next(
        e for e in entries
        if e.get("name") == "Create a dot1q-tunnel vPC"
    )
    args = task["cisco.dcnm.dcnm_interface"]
    profile = next(
        c["profile"] for c in args["config"]
        if "disable_lldp_transmit" in (c.get("profile") or {})
    )
    return args, profile


def test_the_example_declares_the_approved_patch_in_source():
    """Guards the fix itself: the shipped task-level argument must be the exact approved
    string, not merely present. A typo or a different value would pass every other case
    in this file for the wrong reason if this check did not exist."""
    args, _profile = _dot1q_vpc_task()
    assert args.get("patch_version") == SUPPORTED_PATCH, (
        "the published dot1q-tunnel vPC example must declare the exact approved patch; "
        "got %r" % args.get("patch_version"))


def test_the_example_profile_still_sets_the_two_registered_lldp_fields():
    """Pins WHY this example needs the argument at all. If a future edit removed both
    registered fields from the example, the two regression cases below would trivially
    pass without exercising the patch gate -- this guards against that silent drift."""
    _args, profile = _dot1q_vpc_task()
    assert profile.get("disable_lldp_transmit") is True
    assert profile.get("disable_lldp_receive") is True


def test_the_documented_task_succeeds_as_shipped():
    """Replays the EXACT shipped task (including its own patch_version) through real
    main(). This is the straightforward regression: the example, run as published, must
    actually work."""
    args, profile = _dot1q_vpc_task()
    result, calls = run(
        profile, args.get("state", "merged"), parent="int_vpc_dot1q_tunnel",
        patch_version=args["patch_version"],
    )
    assert not result.get("failed"), (
        "the published dot1q-tunnel vPC example must succeed as shipped: %s"
        % result.get("msg"))
    assert writes(calls), "the shipped example must actually configure something"


def test_the_same_profile_without_any_patch_argument_fails_before_any_write():
    """The other half of the regression: if an operator deletes the patch_version line the
    fix added (reverting to the pre-R2 shipped example), the module must still reject it
    cleanly -- not silently drop the two LLDP fields and report success."""
    _args, profile = _dot1q_vpc_task()
    result, calls = run(
        profile, "merged", parent="int_vpc_dot1q_tunnel",
        patch_version=PATCH_KEY_OMITTED,
    )
    assert result.get("failed"), (
        "the documented profile without patch_version must fail, not silently succeed")
    assert writes(calls) == [], "no write may precede the rejection"
    assert "disable_lldp_transmit" in result.get("msg", "") or (
        "disable_lldp_receive" in result.get("msg", "")
    ), result.get("msg")
