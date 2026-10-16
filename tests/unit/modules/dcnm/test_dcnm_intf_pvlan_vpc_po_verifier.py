"""VPC-HOST-E3: the Po G2 deletion verifier (verified=False, failure after the reads run out, members not empty) is adopted into this copy with
Beta's `kind == "po"` filter. These tests show the two halves of that integration with the real main():

  * a deleted vPC is verified by the vPC verifier and the Po verifier does not touch it (it issues no request for a vPC target); a vPC target has
    no `members`, which the G2 Po verifier REJECTS ("names no member"), so without the filter a valid vPC deletion would fail (the fail-before is
    the mutant that removes the filter, recorded in evidence/VPC-HOST-E3/results);
  * a vPC whose release cannot be verified still fails (the vPC verifier, not the Po one).
NOT LIVE TESTED; same synthetic harness as the other vPC tests."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module

from .test_dcnm_intf_pvlan_vpc_harness import SN1, SN2, VPC, created_ctrl, delete_previews, run_vpc, vpc_del_item


class SpyPoVerifier(object):
    """Wraps the Po verifier: records how many requests it sent and how many deletion targets it could see."""

    def __init__(self, ctrl):
        self.ctrl, self.requests, self.targets = ctrl, None, None
        self.original = module.DcnmIntf.dcnm_intf_pvlan_po_verify_deleted

    def __enter__(self):
        spy = self

        def wrapped(obj):
            before = len(spy.ctrl.calls)
            spy.targets = [t for t in obj.dcnm_intf_pvlan_target_map().values() if t.get("deletes")]
            result = spy.original(obj)
            spy.requests = len(spy.ctrl.calls) - before
            return result

        module.DcnmIntf.dcnm_intf_pvlan_po_verify_deleted = wrapped
        return self

    def __exit__(self, *exc):
        module.DcnmIntf.dcnm_intf_pvlan_po_verify_deleted = self.original


def test_a_deleted_vpc_is_verified_by_the_vpc_verifier_and_the_po_verifier_sends_nothing_for_it():
    ctrl = created_ctrl()
    delete_previews(ctrl)
    with SpyPoVerifier(ctrl) as spy:
        status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit" and result["pvlan_verification"][VPC]["state"] == "verified", result.get("msg")
    assert [t.get("kind") for t in spy.targets] == ["vpc"], "the Po verifier is reached and SEES the vPC target"
    assert spy.requests == 0, "...and issues no request for it (kind == po filter)"
    assert result["pvlan_verification"][VPC]["peers"] == {SN1: "verified", SN2: "verified"}


def test_a_vpc_whose_release_cannot_be_verified_still_fails_through_the_vpc_verifier():
    ctrl = created_ctrl()
    ctrl.policy_failures = {SN1: [True] * 40, SN2: [True] * 40}
    delete_previews(ctrl)
    with SpyPoVerifier(ctrl) as spy:
        status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail" and "release could not be verified on every peer" in result["msg"]
    assert result["pvlan_verification"][VPC]["state"] == "failed" and spy.requests == 0
