"""Interface-policy read cost, bounded recovery and the 1,000/5,000-interface module path."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import collections
import copy
import ipaddress
import json
import pytest

from unittest import mock
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface
from ansible.module_utils import basic
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import AnsibleExitJson
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import AnsibleFailJson
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import exit_json
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import fail_json
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import set_module_args
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module

from .helpers.have_reader import _stub
from .helpers import binding_harness as H


# ====================================================================================================
# Formerly test_pr725_read_budget_characterization.py
# PR725 / B1: what the interface-policy read path costs, and what it concludes.
#
# The existing `test_read_authority.py` already pins the *authority*
# semantics of these readers -- present, authoritatively absent, unavailable -- and
# nothing here weakens or duplicates that. This file pins the dimension no test
# currently covers: **how many controller requests and how much scheduled sleep the
# read path spends to reach that conclusion**, and how that work scales with the
# number of requested interfaces.
#
# Two properties must survive any future bound, and each has a test here that would
# fail if a fix bought its constant by breaking them:
#
#   * a failed bulk endpoint does NOT prove individual reads fail, so successful
#     per-interface fallback must keep working (`TestFallbackMustSurvive`);
#   * authoritative absence must stay distinguishable from failure, and failure
#     bookkeeping for one switch must not contaminate another.
#
# Counts are of real requests issued by real readers. Only the transport
# (`dcnm_send`) and the module's `time` are replaced; every parser, identity check,
# cache and authority helper is the production one. Sleep figures are the seconds
# the module *scheduled*, never elapsed wall time.
#
# NOT LIVE TESTED. No controller, Nexus device or Jenkins job is
# contacted. Synthetic identities only: SN1, SN2, PEER, SN1~PEER.
# ====================================================================================================
DcnmIntf = dcnm_interface.DcnmIntf
POLICY = "int_routed_host"
# Production NDFC 12 templates rather than the fixture's shortened stand-ins: the
# individual path is a strict extension of the bulk path, and a classifier that
# gets that wrong would silently report every individual GET as a bulk GET.
PATHS = DcnmIntf.dcnm_intf_paths[12]
BULK_PREFIX = PATHS["IF_WITH_SNO"].split("{", maxsplit=1)[0]
INDIVIDUAL_MARKER = "&ifName="


class _Clock(object):
    """The module's `time`, recording scheduled seconds without waiting."""

    def __init__(self):
        self.sleeps = []

    def sleep(self, seconds):
        self.sleeps.append(seconds)

    @property
    def calls(self):
        return len(self.sleeps)

    @property
    def seconds(self):
        return sum(self.sleeps)


class _Transport(object):
    """Counts GETs by endpoint kind and refuses to answer a mutating verb."""

    def __init__(self, responder):
        self.responder = responder
        self.counts = collections.Counter()
        self.mutations = []

    def __call__(self, module, method, path, *args, **kwargs):
        if method != "GET":
            self.mutations.append((method, path))
            raise AssertionError("read probe received %s %s" % (method, path))
        if INDIVIDUAL_MARKER in path:
            kind = "individual"
        elif path.startswith(BULK_PREFIX):
            kind = "bulk"
        else:
            kind = "other"
        self.counts[kind] += 1
        return self.responder(kind, path, self.counts)

    @property
    def total(self):
        return sum(self.counts.values())


def _ok(data):
    return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": data}


ERROR_500 = {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": []}
MALFORMED_200 = {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {}}


def _group(if_name, serial="SN1", if_type="INTERFACE_ETHERNET", policy=POLICY):
    return {
        "policy": policy,
        "interfaceType": if_type,
        "interfaces": [
            {
                "ifName": if_name,
                "serialNumber": serial,
                "interfaceType": if_type,
                "nvPairs": {"DESC": "characterization"},
            }
        ],
    }


def _serial_in(path):
    return path.split("serialNumber=", 1)[1].split("&", 1)[0]


def _ifname_in(path):
    return path.split(INDIVIDUAL_MARKER, 1)[1]


def _state(want):
    state = _stub()
    state.paths = dict(PATHS)
    state.have = []
    state.want = want
    state.dcnm_intf_bulk_fetch_intf_info = (
        lambda serial, refresh=False: DcnmIntf.dcnm_intf_bulk_fetch_intf_info(
            state, serial, refresh
        )
    )
    state.dcnm_intf_get_intf_info = (
        lambda name, serial, kind: DcnmIntf.dcnm_intf_get_intf_info(
            state, name, serial, kind
        )
    )
    state.dcnm_intf_get_intf_info_from_dcnm = (
        lambda intf: DcnmIntf.dcnm_intf_get_intf_info_from_dcnm(state, intf)
    )
    return state


def _want(count, serial="SN1", if_type="INTERFACE_ETHERNET", first=1, prefix="Ethernet1/"):
    return [
        {
            "policy": POLICY,
            "interfaces": [
                {
                    "ifName": "%s%d" % (prefix, index),
                    "serialNumber": serial,
                    "interfaceType": if_type,
                    "nvPairs": {"DESC": "characterization"},
                }
            ],
        }
        for index in range(first, first + count)
    ]


def _run_get_have(want, responder, vpc_ip_sn=None):
    """Run the real `dcnm_intf_get_have` and return (state, transport, clock)."""
    state = _state(want)
    if vpc_ip_sn:
        state.vpc_ip_sn = dict(vpc_ip_sn)
    transport = _Transport(responder)
    clock = _Clock()
    with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
        dcnm_interface, "time", clock
    ):
        DcnmIntf.dcnm_intf_get_have(state)
    return state, transport, clock


def _constant(value):
    def responder(kind, path, counts):
        if isinstance(value, BaseException):
            raise value
        return value

    return responder


def _unavailable(state, want):
    return [
        (intf["serialNumber"], intf["ifName"])
        for elem in want
        for intf in elem["interfaces"]
        if DcnmIntf.dcnm_intf_detail_unavailable(state, intf["ifName"], intf["serialNumber"])
    ]


# ===========================================================================
# C1 / C2 — a usable bulk answer ends the work, whatever it says
# ===========================================================================
@pytest.mark.parametrize("count", [1, 10, 200])
def test_valid_populated_bulk_serves_every_interface_from_cache(count):
    """One bulk GET answers N interfaces: no individual GET, no sleep."""
    want = _want(count)
    groups = [_group("Ethernet1/%d" % index) for index in range(1, count + 1)]

    state, transport, clock = _run_get_have(want, _constant(_ok(groups)))

    assert transport.counts["bulk"] == 1
    assert transport.counts["individual"] == 0
    assert clock.calls == 0
    assert len(state.have) == count
    assert _unavailable(state, want) == []


@pytest.mark.parametrize("count", [1, 10, 200])
@pytest.mark.parametrize(
    "response,label",
    [(_ok([]), "valid empty list"), ([], "bare empty body")],
    ids=["valid_empty_list", "bare_empty_body"],
)
def test_authoritative_empty_bulk_costs_one_get_and_is_not_failure(
    count, response, label
):
    """Confirmed emptiness is an ANSWER: one GET, no fallback, no failure marks.

    Both shapes are characterized deliberately. See
    `test_bare_empty_body_contract_is_absence_not_unavailable` below for the
    documented contradiction around the bare-list shape.
    """
    want = _want(count)

    state, transport, clock = _run_get_have(want, _constant(response))

    assert transport.total == 1
    assert clock.calls == 0
    assert state.have == []
    assert _unavailable(state, want) == []
    assert state.intf_detail_fetch_failed_snos == set()
    assert "SN1" in state.intf_detail_cached_snos


def test_bare_empty_body_contract_is_absence_not_unavailable():
    """A bare `[]` is authoritative absence, and the docstring now says so.

    `_dcnm_intf_get_with_retries` used to document the opposite -- "Callers still
    treat bare [] as unavailable because it lacks the required DATA envelope" --
    while both callers recorded a bare `[]` as AUTHORITATIVE ABSENCE, strong
    enough to authorize a create. The behaviour below is unchanged and is what it
    always was; only the stale sentence was corrected. The docstring assertion is
    kept, inverted, so the two halves cannot drift apart again silently.
    """
    state = _state([])
    with mock.patch.object(dcnm_interface, "dcnm_send", return_value=[]), mock.patch.object(
        dcnm_interface, "time", _Clock()
    ):
        DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)
        individual = DcnmIntf.dcnm_intf_get_intf_info(
            state, "Loopback0", "SN2", "INTERFACE_LOOPBACK"
        )

    assert "SN1" in state.intf_detail_cached_snos
    assert DcnmIntf.dcnm_intf_detail_unavailable(state, "Loopback0", "SN1") is False
    assert individual == []
    assert ("SN2", "loopback0") in state.intf_detail_authoritative_absent_keys
    assert DcnmIntf.dcnm_intf_detail_unavailable(state, "Loopback0", "SN2") is False
    docstring = DcnmIntf._dcnm_intf_get_with_retries.__doc__
    assert "treat bare [] as unavailable" not in docstring, (
        "the withdrawn sentence is back in the retry helper's docstring; it "
        "contradicts both callers and both absence tests above"
    )
    assert "AUTHORITATIVE ABSENCE" in docstring, (
        "the retry helper must keep documenting what its callers actually do "
        "with a bare []"
    )


def test_real_httpapi_never_produces_the_bare_empty_body_shape():
    """An empty 2xx body arrives as RETURN_CODE 200 with DATA {}, not as [].

    Evidence that the bare-`[]` branch is not reachable through this collection's
    own httpapi: the plugin always wraps a successful response in the RETURN_CODE
    envelope, so an empty body is the MALFORMED-200 case, not confirmed absence.
    """
    from ansible_collections.cisco.dcnm.plugins.httpapi.dcnm import HttpApi

    response = mock.Mock()
    response.getcode.return_value = 200
    response.geturl.return_value = "/if"
    response.msg = "OK"
    body = mock.Mock()
    body.getvalue.return_value = b""

    httpapi = HttpApi(mock.Mock())
    result = httpapi._verify_response(response, "GET", "/if", body)

    assert isinstance(result, dict)
    assert result["RETURN_CODE"] == 200
    assert result["DATA"] == {}
    assert result != []


# ===========================================================================
# C3 / C4 — failed recovery is charged once per interface, not once per switch
# ===========================================================================
@pytest.mark.parametrize("count", [1, 2, 10, 50])
@pytest.mark.parametrize(
    "responder,label",
    [
        (_constant(ERROR_500), "http_500"),
        (
            _constant(dcnm_interface.AnsibleConnectionError("synthetic offline failure")),
            "transport_exception",
        ),
    ],
    ids=["http_500", "transport_exception"],
)
def test_persistent_failure_costs_one_bulk_cycle_and_one_probe(
    count, responder, label
):
    """One failed bulk cycle, one failed individual probe, then nothing.

    The retry helper still bounds a single invocation to three attempts; what is
    new is that the number of FAILED invocations per serial is bounded at two, so
    the cost no longer scales with the interface count. Before this change the
    same scenario spent `3 + 3N` requests and `3(N + 1)` scheduled seconds --
    3,003 of each at N = 1000. Those figures remain true of the diagnostic base.

    The conclusion is unchanged: every requested interface is still unavailable,
    nothing is cached, and no absence is invented for the interfaces never read.
    """
    want = _want(count)

    state, transport, clock = _run_get_have(want, responder)

    assert transport.counts["bulk"] == 3
    assert transport.counts["individual"] == 3
    assert transport.total == 6
    assert clock.calls == 6
    assert clock.seconds == 6
    assert state.have == []
    assert len(_unavailable(state, want)) == count
    assert state.intf_detail_authoritative_absent_keys == set()
    assert state.intf_detail_cache == {}
    assert transport.mutations == []


@pytest.mark.parametrize("count", [1, 2, 10, 50])
def test_malformed_http_200_is_bounded_to_two_requests(count):
    """Status alone does not establish authority, and it no longer buys N reads.

    The retry helper terminates on any `RETURN_CODE 200`, so a malformed 200 costs
    one attempt per invocation and schedules no sleep at all. Two failed
    invocations is the whole allowance, so the ceiling here is two requests --
    where the diagnostic base spent `1 + N` at full speed, 1,001 of them at
    N = 1000.

    A 200 that cannot be parsed is still a failure: nothing is cached, nothing
    becomes absent, and every requested interface is unavailable.
    """
    want = _want(count)

    state, transport, clock = _run_get_have(want, _constant(MALFORMED_200))

    assert transport.counts["bulk"] == 1
    assert transport.counts["individual"] == 1
    assert transport.total == 2
    assert clock.calls == 0
    assert state.have == []
    assert state.intf_detail_authoritative_absent_keys == set()
    assert len(_unavailable(state, want)) == count


# ===========================================================================
# C5 / C6 — useful recovery, which any bound must not destroy
# ===========================================================================
class TestFallbackMustSurvive:
    """Guards against a fix that buys its constant by discarding recovery."""

    @staticmethod
    def _bulk_transient(failures, groups):
        seen = collections.Counter()

        def responder(kind, path, counts):
            assert kind == "bulk", "no individual GET expected once bulk recovers"
            serial = _serial_in(path)
            seen[serial] += 1
            return ERROR_500 if seen[serial] <= failures else _ok(groups)

        return responder

    @staticmethod
    def _bulk_fails_individual_works(individual_failures=0):
        seen = collections.Counter()

        def responder(kind, path, counts):
            if kind == "bulk":
                return ERROR_500
            if_name = _ifname_in(path)
            seen[if_name] += 1
            if seen[if_name] <= individual_failures:
                return ERROR_500
            return _ok([_group(if_name, serial=_serial_in(path))])

        return responder

    @pytest.mark.parametrize("failures", [1, 2])
    @pytest.mark.parametrize("count", [1, 10])
    def test_transient_bulk_failure_then_valid_response_still_succeeds(
        self, failures, count
    ):
        want = _want(count)
        groups = [_group("Ethernet1/%d" % index) for index in range(1, count + 1)]

        state, transport, clock = _run_get_have(
            want, self._bulk_transient(failures, groups)
        )

        assert transport.counts["bulk"] == failures + 1
        assert transport.counts["individual"] == 0
        assert clock.calls == failures
        assert len(state.have) == count
        assert _unavailable(state, want) == []

    @pytest.mark.parametrize("count", [1, 10, 50])
    def test_bulk_unavailable_does_not_prove_individual_reads_fail(self, count):
        """A failed bulk endpoint with working per-interface reads: 3 + N.

        This is the case a naive total-request cap would destroy: every one of the
        N individual reads is legitimate and successful, and the only wasted work
        is the single failed bulk cycle.
        """
        want = _want(count)

        state, transport, clock = _run_get_have(
            want, self._bulk_fails_individual_works()
        )

        assert transport.counts["bulk"] == 3
        assert transport.counts["individual"] == count
        assert clock.calls == 3
        assert len(state.have) == count
        assert _unavailable(state, want) == []
        # The serial-wide bulk failure is deliberately NOT cleared by per-key
        # success: an interface nobody asked about stays unknown.
        assert "SN1" in state.intf_detail_fetch_failed_snos
        assert DcnmIntf.dcnm_intf_detail_unavailable(state, "Ethernet9/9", "SN1") is True

    @pytest.mark.parametrize("count", [1, 10])
    def test_individual_fallback_survives_its_own_transient_failure(self, count):
        want = _want(count)

        state, transport, clock = _run_get_have(
            want, self._bulk_fails_individual_works(individual_failures=1)
        )

        assert transport.counts["bulk"] == 3
        assert transport.counts["individual"] == 2 * count
        assert clock.calls == 3 + count
        assert len(state.have) == count
        assert _unavailable(state, want) == []


# ===========================================================================
# C7 — a well-formed HTTP answer that cannot be trusted is not absence
# ===========================================================================
@pytest.mark.parametrize(
    "payload,reason",
    [
        ([_group("Ethernet1/1", serial="WRONG")], "wrong identity"),
        ([_group("Ethernet1/1"), _group("ethernet1/1")], "duplicate identity"),
        ([{"interfaces": _group("Ethernet1/1")["interfaces"]}], "missing policy"),
        ([{"policy": POLICY, "interfaces": [{"ifName": "Ethernet1/1"}]}], "malformed payload"),
    ],
    ids=["wrong_identity", "duplicate_identity", "missing_policy", "malformed_payload"],
)
def test_untrustworthy_bulk_payload_is_unavailable_and_falls_back_once(payload, reason):
    """No fabricated absence: the switch is unavailable and the fallback is tried.

    The bulk payload is rejected without a retry (it was a valid HTTP 200), then
    each interface is probed individually, and the same rejection leaves it
    unavailable. Nothing is cached and no absence is invented.
    """
    want = _want(1)

    state, transport, clock = _run_get_have(want, _constant(_ok(payload)))

    assert transport.counts["bulk"] == 1
    assert transport.counts["individual"] == 1
    assert clock.calls == 0
    assert state.intf_detail_cache == {}
    assert state.intf_detail_authoritative_absent_keys == set()
    assert len(_unavailable(state, want)) == 1
    assert state.have == []


# ===========================================================================
# C8 — reuse, refresh, invalidation: the scope any budget would have to respect
# ===========================================================================
def test_repeated_get_have_reissues_a_full_bulk_read_each_time():
    """`dcnm_intf_get_have` prefetches with refresh=True, so it never reuses.

    Two runs of the same WANT cost two bulk reads. Any budget that persists across
    runs must therefore define explicitly whether a refresh resets it; today there
    is no budget and each run starts from a cleared authority for that serial.
    """
    want = _want(3)
    groups = [_group("Ethernet1/%d" % index) for index in range(1, 4)]
    state = _state(want)
    transport = _Transport(_constant(_ok(groups)))
    clock = _Clock()
    with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
        dcnm_interface, "time", clock
    ):
        DcnmIntf.dcnm_intf_get_have(state)
        state.have = []
        DcnmIntf.dcnm_intf_get_have(state)

    assert transport.counts["bulk"] == 2
    assert transport.counts["individual"] == 0
    assert len(state.have) == 3


def test_non_refresh_bulk_reuses_the_cached_authority_without_a_request():
    """The cheap path a bound must not disturb: a cached serial costs nothing."""
    state = _state([])
    transport = _Transport(_constant(_ok([_group("Ethernet1/1")])))
    with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
        dcnm_interface, "time", _Clock()
    ):
        DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1")
        DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1")

    assert transport.counts["bulk"] == 1


def test_a_second_read_after_one_failure_is_still_permitted():
    """One failed invocation leaves an allowance, so the retry still happens.

    The original version of this test claimed invalidation was a reset the budget
    had to honour. It is not, and this scenario never showed that it was: it
    consumes exactly one failed invocation, so the second read is permitted by the
    allowance itself, invalidation or no invalidation. The behavioural assertion
    is unchanged -- a serial that failed once can still be re-read and recover.
    """
    state = _state([])
    seen = collections.Counter()

    def responder(kind, path, counts):
        seen["bulk"] += 1
        return ERROR_500 if seen["bulk"] <= 3 else _ok([_group("Ethernet1/1")])

    transport = _Transport(responder)
    with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
        dcnm_interface, "time", _Clock()
    ):
        DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)
        assert DcnmIntf.dcnm_intf_detail_unavailable(state, "Ethernet1/1", "SN1") is True
        DcnmIntf.dcnm_intf_invalidate_serial_authority(state, "SN1")
        DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)

    assert transport.counts["bulk"] == 4
    assert DcnmIntf.dcnm_intf_detail_unavailable(state, "Ethernet1/1", "SN1") is False


# ===========================================================================
# C9 — identity isolation: per-switch and per-pair bookkeeping
# ===========================================================================
@pytest.mark.parametrize("count", [1, 10])
def test_failed_switch_does_not_consume_or_contaminate_another_switch(count):
    """Two switches, one broken: the healthy one still costs exactly one GET."""
    want = _want(count, serial="SN1") + _want(count, serial="SN2", first=count + 1)
    healthy = [
        _group("Ethernet1/%d" % index, serial="SN2")
        for index in range(count + 1, 2 * count + 1)
    ]

    def responder(kind, path, counts):
        return _ok(healthy) if _serial_in(path) == "SN2" else ERROR_500

    state, transport, clock = _run_get_have(want, responder)

    assert transport.counts["bulk"] == 4  # 3 failed for SN1, 1 successful for SN2
    # SN1 spends its own allowance on one probe; SN2 is served from its cache and
    # never pays for SN1's failures.
    assert transport.counts["individual"] == 3
    assert state.intf_detail_failed_reads == {"sn1": 2}
    assert len(state.have) == count
    assert state.intf_detail_fetch_failed_snos == {"SN1"}
    assert "SN2" in state.intf_detail_cached_snos
    failed = _unavailable(state, want)
    assert len(failed) == count
    assert {serial for serial, _interface in failed} == {"SN1"}


def test_combined_vpc_identity_failure_marks_the_pair_and_both_members():
    """A failed read for a pair marks the logical identity and both serials.

    A per-switch budget therefore has to decide its key deliberately: the request
    is sent with one query serial, while the failure is recorded against three
    identities.
    """
    want = _want(1, serial="SN1~PEER", if_type="INTERFACE_VPC", prefix="vPC")

    state, transport, clock = _run_get_have(
        want, _constant(ERROR_500), vpc_ip_sn={"192.0.2.1": "SN1~PEER"}
    )

    assert transport.counts["bulk"] == 3
    assert transport.counts["individual"] == 3
    assert {"SN1~PEER", "SN1", "PEER"}.issubset(state.intf_detail_fetch_failed_snos)
    assert DcnmIntf.dcnm_intf_detail_unavailable(state, "vPC1", "SN1~PEER") is True
    assert DcnmIntf.dcnm_intf_detail_unavailable(state, "Ethernet1/1", "PEER") is True


def test_pair_and_member_reads_share_one_bulk_query_serial():
    """One bulk GET covers both a pair interface and a member's physical port.

    The pair identity is prefetched first, so the physical member resolves from
    the same cached response. The endpoint actually queried is the first serial of
    the pair, which is the natural key for anything that counts requests.
    """
    want = [
        _want(1, serial="SN1~PEER", if_type="INTERFACE_VPC", prefix="vPC")[0],
        _want(1, serial="SN1", if_type="INTERFACE_ETHERNET")[0],
    ]
    payload = [
        _group("vPC1", serial="SN1~PEER", if_type="INTERFACE_VPC"),
        _group("Ethernet1/1", serial="SN1", if_type="INTERFACE_ETHERNET"),
    ]

    state, transport, clock = _run_get_have(
        want, _constant(_ok(payload)), vpc_ip_sn={"192.0.2.1": "SN1~PEER"}
    )

    assert transport.counts["bulk"] == 1
    assert transport.counts["individual"] == 0
    assert len(state.have) == 2
    assert _unavailable(state, want) == []


# ===========================================================================
# Module path. Everything below enters through the real `dcnm_interface.main()`
# so the amendment cases are measured where they actually happen, not on a
# reconstruction of the caller order.
# ===========================================================================

SWITCH = "192.0.2.1"  # RFC 5737 TEST-NET-1
SERIAL = "SYNTHSERIAL1"
FABRIC = "synthetic_fabric"
DETAIL_PREFIX = PATHS["IF_DETAIL_WITH_SNO"].split("{", maxsplit=1)[0]
ACCESS_MODE_PREFIX = PATHS["FABRIC_ACCESS_MODE"].split("{", maxsplit=1)[0]

INVENTORY = {
    SWITCH: {
        "logicalName": "synthetic-sw-1",
        "serialNumber": SERIAL,
        "isVpcConfigured": "False",
        "vpcDomain": 0,
        "switchRole": "Leaf",
        "managable": "True",
    }
}


class _ModuleTransport(object):
    """Every controller call a real run makes, classified and counted.

    The interface *summary*, the fabric access-mode probe and mutating verbs are
    counted apart from the interface-policy reads, so an amplification claim can
    never quietly absorb an unrelated request.
    """

    def __init__(self, policy_response, summary=()):
        self.policy_response = policy_response
        self.summary = list(summary)
        self.counts = collections.Counter()
        self.mutations = []

    def __call__(self, module, method, path, *args, **kwargs):
        if method != "GET":
            self.mutations.append((method, path))
            self.counts["mutating"] += 1
            return _ok({})
        if path.startswith(ACCESS_MODE_PREFIX):
            self.counts["access_mode"] += 1
            return _ok({"readonly": False})
        if path.startswith(DETAIL_PREFIX):
            self.counts["summary"] += 1
            return _ok(list(self.summary))
        if path.startswith(BULK_PREFIX):
            kind = "individual" if INDIVIDUAL_MARKER in path else "bulk"
            self.counts[kind] += 1
            return self.policy_response(kind, path, self.counts)
        self.counts["other"] += 1
        return _ok([])

    @property
    def policy_total(self):
        return self.counts["bulk"] + self.counts["individual"]


class _ModuleRun(object):
    def __init__(self, transport, clock, outcome, message):
        self.transport = transport
        self.clock = clock
        self.outcome = outcome
        self.message = message

    @property
    def counts(self):
        return self.transport.counts

    @property
    def policy_total(self):
        return self.transport.policy_total

    @property
    def mutations(self):
        return self.transport.mutations

    def report(self):
        return "bulk=%d individual=%d policy_total=%d summary=%d writes=%d sleep_s=%g outcome=%s" % (
            self.counts["bulk"],
            self.counts["individual"],
            self.policy_total,
            self.counts["summary"],
            self.counts["mutating"],
            self.clock.seconds,
            self.outcome,
        )


def _eth_config(count):
    return [
        {
            "name": "Ethernet1/%d" % index,
            "type": "eth",
            "switch": [SWITCH],
            "deploy": False,
            "profile": {"mode": "trunk"},
        }
        for index in range(1, count + 1)
    ]


def _summary_entries(count):
    """Interface summary records, the shape `dcnm_intf_get_have_all_with_sno`
    validates. Models a switch that already carries N interfaces, which is what
    an `overridden` sweep meets in a real fabric."""
    return [
        {
            "ifName": "Ethernet1/%d" % index,
            "serialNo": SERIAL,
            "fabricName": FABRIC,
            "ifType": "INTERFACE_ETHERNET",
            "isPhysical": True,
            "deletable": True,
            "markDeleted": False,
            "alias": "",
            "deleteReason": None,
            "complianceStatus": "In-Sync",
            "underlayPolicies": [],
        }
        for index in range(1, count + 1)
    ]


def run_module_path(count, policy_responder, state="merged", already_present=0):
    """Run the real `main()`; replace only transport, inventory, version, time."""
    transport = _ModuleTransport(
        policy_responder, summary=_summary_entries(already_present)
    )
    clock = _Clock()
    patches = [
        mock.patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json),
        mock.patch.object(dcnm_interface, "dcnm_send", transport),
        mock.patch.object(dcnm_interface, "time", clock),
        mock.patch.object(
            dcnm_interface, "get_fabric_inventory_details", return_value=INVENTORY
        ),
        mock.patch.object(
            dcnm_interface, "get_ip_sn_dict", return_value=({SWITCH: SERIAL}, {})
        ),
        mock.patch.object(dcnm_interface, "dcnm_version_supported", return_value=12),
        mock.patch.object(
            dcnm_interface, "dcnm_get_bulk_api_support", return_value=False
        ),
    ]
    set_module_args(
        dict(state=state, fabric=FABRIC, config=_eth_config(count), deploy=False)
    )
    outcome, message = "returned", ""
    for patch in patches:
        patch.start()
    try:
        dcnm_interface.main()
    except AnsibleFailJson as exc:
        outcome, message = "fail_json", str(exc.args[0].get("msg", ""))
    except AnsibleExitJson as exc:
        outcome, message = "exit_json", "changed=%s" % exc.args[0].get("changed")
    finally:
        for patch in reversed(patches):
            patch.stop()
    return _ModuleRun(transport, clock, outcome, message)


def _persistent_500(kind, path, counts):
    return ERROR_500


def _valid_empty(kind, path, counts):
    return _ok([])


@pytest.mark.parametrize("count", [1, 10])
@pytest.mark.parametrize("state", ["merged", "replaced", "overridden"])
def test_module_path_is_bounded_then_refuses_to_write(count, state):
    """The real entry point spends the allowance, then fails closed as before.

    The diagnostic base spent `3 + 3N` requests and `3(N + 1)` scheduled seconds
    here before refusing. The refusal, its message and the zero writes are
    untouched; only the price changed.
    """
    run = run_module_path(count, _persistent_500, state=state)

    assert run.counts["bulk"] == 3
    assert run.counts["individual"] == 3
    assert run.policy_total == 6
    assert run.clock.seconds == 6
    assert run.outcome == "fail_json"
    assert "could not be read authoritatively" in run.message
    assert run.counts["mutating"] == 0
    assert run.mutations == []


@pytest.mark.parametrize("count", [1, 10])
def test_module_path_with_authoritative_state_does_write(count):
    """Control: the same harness DOES write when the state is authoritative.

    Without this, the zero-write assertions above would be satisfied by a harness
    that simply cannot issue a write.
    """
    run = run_module_path(count, _valid_empty, state="merged")

    assert run.policy_total == 1
    assert run.outcome == "exit_json"
    assert run.counts["mutating"] >= 1
    assert any(method == "POST" for method, _payload in run.mutations)


@pytest.mark.parametrize("count", [1, 10])
def test_overridden_second_pass_costs_nothing_once_the_allowance_is_spent(count):
    """The two `overridden` passes share one allowance, which is the whole point.

    `dcnm_intf_get_have` prefetches with `refresh=True`, then
    `dcnm_intf_get_diff_overridden` prefetches the same serial again with
    `refresh=False` and probes every `have_all` entry. `refresh=False` is not a
    cache hit after a failed read -- the early return only fires for identities in
    `intf_detail_cached_snos`, which a failed read never populates -- so on the
    diagnostic base the switch paid a second full cycle: `6 + 3(N + 1)` requests,
    3,009 at N = 1000.

    Because the counter is owned by the module instance and is reset only by a
    validated response, the second pass now issues nothing. A reset on
    invalidation, on `refresh`, or on entering a new diff phase would re-open it.
    """
    run = run_module_path(
        count, _persistent_500, state="overridden", already_present=count
    )

    assert run.counts["bulk"] == 3, run.report()
    assert run.counts["individual"] == 3, run.report()
    assert run.policy_total == 6, run.report()
    assert run.clock.seconds == 6, run.report()
    assert run.outcome == "fail_json"
    assert run.counts["mutating"] == 0


# ===========================================================================
# Invalidation and repeated passes: the reset points the contract must NOT use
# ===========================================================================
def test_invalidation_precedes_every_bulk_read_including_a_repeated_failure():
    """`dcnm_intf_bulk_fetch_intf_info` invalidates before it reads, always.

    Line 5346 runs unconditionally once the cached-identity early return has been
    passed, so a *failed* read invalidates too. Invalidation is therefore evidence
    that a read is about to be attempted, never evidence that the controller
    answered — which is exactly why it cannot be a budget reset point.
    """
    state = _state([])
    calls = []
    real = DcnmIntf.dcnm_intf_invalidate_serial_authority
    state.dcnm_intf_invalidate_serial_authority = lambda sno: (
        calls.append(sno),
        real(state, sno),
    )[1]
    transport = _Transport(_constant(ERROR_500))
    with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
        dcnm_interface, "time", _Clock()
    ):
        DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)
        DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=False)

    assert calls == ["SN1", "SN1"]
    assert transport.counts["bulk"] == 6


def test_repeated_pass_over_one_failed_serial_shares_one_allowance():
    """Invalidate + repeat: 6 requests, not the 12 the diagnostic base spent.

    This mirrors the real caller order of `overridden` at method level: prefetch,
    per-interface read, then the second prefetch and read of
    `get_diff_overridden`. The allowance carries across both passes.
    """
    state = _state([])
    transport = _Transport(_constant(ERROR_500))
    clock = _Clock()
    with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
        dcnm_interface, "time", clock
    ):
        DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)
        DcnmIntf.dcnm_intf_get_intf_info(state, "Ethernet1/1", "SN1", "INTERFACE_ETHERNET")
        DcnmIntf.dcnm_intf_invalidate_serial_authority(state, "SN1")
        DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=False)
        DcnmIntf.dcnm_intf_get_intf_info(state, "Ethernet1/1", "SN1", "INTERFACE_ETHERNET")

    assert transport.counts["bulk"] == 3
    assert transport.counts["individual"] == 3
    assert transport.total == 6
    assert clock.seconds == 6
    assert DcnmIntf.dcnm_intf_detail_unavailable(state, "Ethernet1/1", "SN1") is True


def test_a_cache_hit_issues_no_request_and_so_carries_no_new_evidence():
    """The path that must neither consume nor reset a budget.

    A cached serial short-circuits at 5343 and a cached key at 5423. Neither
    contacts the controller, so neither can be evidence about the controller.
    """
    state = _state([])
    transport = _Transport(_constant(_ok([_group("Ethernet1/1")])))
    with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
        dcnm_interface, "time", _Clock()
    ):
        DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)
        first = transport.total
        DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1")
        DcnmIntf.dcnm_intf_get_intf_info(state, "Ethernet1/1", "SN1", "INTERFACE_ETHERNET")
        DcnmIntf.dcnm_intf_get_intf_info(state, "Ethernet9/9", "SN1", "INTERFACE_ETHERNET")

    assert first == 1
    assert transport.total == 1


# ===========================================================================
# Post-deletion recovery: the loop the r1 contract wrongly thought needed a reset
# ===========================================================================
def _deferred_stub():
    """`refresh_deferred_deleted_member_defaults` with the real reader chain.

    Only the summary read, the parent-presence query and the payload builders are
    stubbed; the bulk reader, the individual reader, the invalidator and the
    authority predicate are the production ones.
    """
    state = _state([])
    state.deferred_delete_member_defaults = [
        {
            "ifName": "Ethernet1/1",
            "serialNumber": "SN1",
            "fabricName": "fab",
            "deploy": True,
            "parentIfName": "port-channel10",
        }
    ]
    state._deferred_delete_member_default_keys = {
        ("SN1", "ethernet1/1", "port-channel10")
    }
    state.have_all = [{"ifName": "Ethernet1/1", "serialNo": "SN1", "isPhysical": True}]
    state.diff_replace = []
    state.diff_deploy = []
    state.changed_dict = [{"replaced": [], "deploy": []}]
    state.dcnm_intf_get_have_all_with_sno = mock.Mock()
    state.dcnm_intf_parent_present_in_have_all = mock.Mock(return_value=False)
    state.dcnm_intf_get_default_eth_payload = mock.Mock(
        return_value={"policy": "int_access_host", "interfaces": [{"ifName": "Ethernet1/1"}]}
    )
    state.dcnm_intf_invalidate_serial_authority = (
        lambda sno: DcnmIntf.dcnm_intf_invalidate_serial_authority(state, sno)
    )
    state.dcnm_intf_detail_unavailable = (
        lambda name, sno: DcnmIntf.dcnm_intf_detail_unavailable(state, name, sno)
    )
    state.dcnm_intf_require_detail_authority = (
        lambda name, sno: DcnmIntf.dcnm_intf_require_detail_authority(state, name, sno)
    )
    state.dcnm_intf_merge_intf_info = mock.Mock()
    state.dcnm_compare_default_payload = mock.Mock(return_value="DIFF")
    state.module.fail_json.side_effect = RuntimeError("fail_json")
    return state


def test_deferred_recovery_loop_aborts_inside_its_first_iteration_on_failure():
    """The loop never spends its ten iterations on an unreadable switch.

    `dcnm_intf_require_detail_authority` (7119) runs inside iteration 1, so the
    ten-iteration parent-presence polling is already conditional on authoritative
    detail. Exactly three bulk requests are spent, and nothing is scheduled. This
    is the measurement that shows the loop does NOT need an unconditional budget
    reset to keep working.
    """
    state = _deferred_stub()
    transport = _Transport(_constant(ERROR_500))
    clock = _Clock()
    with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
        dcnm_interface, "time", clock
    ):
        with pytest.raises(RuntimeError, match="fail_json"):
            DcnmIntf.dcnm_intf_refresh_deferred_deleted_member_defaults(state)

    assert transport.counts["bulk"] == 3
    assert transport.counts["individual"] == 0
    assert transport.total == 3
    assert state.diff_replace == []
    assert state.diff_deploy == []
    assert state.changed_dict[0]["replaced"] == []
    assert state.changed_dict[0]["deploy"] == []
    assert transport.mutations == []


def test_deferred_recovery_loop_keeps_polling_while_responses_stay_valid():
    """Each iteration receives a freshly validated response, so recovery works.

    The parent is reported present for two iterations and gone on the third. Every
    iteration's bulk read returns a valid payload, which is a reset under the
    corrected contract, so a per-serial budget never interferes with this loop.
    """
    state = _deferred_stub()
    state.dcnm_intf_parent_present_in_have_all = mock.Mock(
        side_effect=[True, True, False, False, False, False]
    )
    transport = _Transport(_constant(_ok([_group("Ethernet1/1")])))
    clock = _Clock()
    with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
        dcnm_interface, "time", clock
    ):
        DcnmIntf.dcnm_intf_refresh_deferred_deleted_member_defaults(state)

    assert transport.counts["bulk"] == 3
    assert transport.counts["individual"] == 0
    assert clock.sleeps == [2, 2]
    assert DcnmIntf.dcnm_intf_detail_unavailable(state, "Ethernet1/1", "SN1") is False


# ===========================================================================
# Out of scope, and staying that way: summary, breakout and query readers
# ===========================================================================
def test_summary_and_breakout_readers_stay_one_invocation_per_switch():
    """Regression guard for the readers the budget deliberately excludes.

    They already cost one invocation per switch rather than one per interface, so
    they do not amplify. Their bookkeeping is separate from the interface-policy
    authority sets and must stay that way.
    """
    state = _state([])
    transport = _Transport(_constant(ERROR_500))
    clock = _Clock()
    with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
        dcnm_interface, "time", clock
    ):
        DcnmIntf.dcnm_intf_get_have_all_with_sno(state, "SN1")
        DcnmIntf.dcnm_intf_get_have_all_breakout_interfaces(state, "SN1")

    assert transport.counts["other"] == 6  # 3 attempts each, summary endpoint
    assert transport.counts["bulk"] == 0
    assert transport.counts["individual"] == 0
    assert clock.seconds == 6
    assert state.have_all_failed_snos == {"SN1"}
    assert state.have_breakout_failed_snos == {"SN1"}
    # Interface-policy authority is untouched by a summary failure.
    assert state.intf_detail_fetch_failed_snos == set()
    assert state.intf_detail_cached_snos == set()


def test_query_reader_has_no_retry_no_cache_and_no_authority_bookkeeping():
    """Regression guard: `query` bypasses the bounded helper entirely.

    `dcnm_intf_get_diff_query` (8146) calls `dcnm_send` directly. It builds no
    HAVE and authorizes no mutation, so it is outside the budget. One request per
    requested item, no retry, no authority recorded.
    """
    state = _state([])
    state.ip_sn = {"192.0.2.1": "SN1"}
    state.intf_info = [
        {"name": "", "switch": ["192.0.2.1"]},
        {"name": "", "switch": ["192.0.2.1"]},
    ]
    state.diff_query = []
    state.changed_dict = [{"query": []}]
    state.result = {"response": []}
    state.dcnm_intf_register_controller_secrets = (
        lambda payload: DcnmIntf.dcnm_intf_register_controller_secrets(state, payload)
    )
    transport = _Transport(_constant(ERROR_500))
    clock = _Clock()
    with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
        dcnm_interface, "time", clock
    ):
        DcnmIntf.dcnm_intf_get_diff_query(state)

    assert transport.counts["other"] == 2  # one per item, no retry
    assert transport.counts["bulk"] == 0
    assert transport.counts["individual"] == 0
    assert clock.calls == 0
    assert state.intf_detail_fetch_failed_snos == set()
    assert state.intf_detail_failed_keys == set()
    assert state.diff_query == []


# ===========================================================================
# B2 — the recovery contract itself: what spends the allowance, what restores it,
# what it is keyed by, and what exhaustion may and may not conclude.
# ===========================================================================
BUDGET = 2  # failed reader invocations per queried serial, per module instance


def _budget(state):
    return dict(state.intf_detail_failed_reads)


class TestAllowanceAccounting:
    """One failed invocation is one charge, whatever shape the failure took."""

    @pytest.mark.parametrize(
        "response,label",
        [
            (ERROR_500, "non-200"),
            (MALFORMED_200, "200 with non-list DATA"),
            (_ok([{"policy": POLICY}]), "200 with a group missing interfaces"),
            (_ok([_group("Ethernet1/1", serial="WRONG")]), "200 with wrong identity"),
            (
                _ok([_group("Ethernet1/1"), _group("ethernet1/1")]),
                "200 with a duplicate identity",
            ),
            (
                _ok([{"policy": POLICY, "interfaces": [
                    {"ifName": "Ethernet1/1", "serialNumber": "SN1", "nvPairs": "bad"}
                ]}]),
                "200 with malformed nvPairs",
            ),
        ],
        ids=[
            "non_200",
            "non_list_data",
            "missing_interfaces",
            "wrong_identity",
            "duplicate_identity",
            "malformed_nvpairs",
        ],
    )
    def test_every_validation_failure_branch_costs_the_allowance(self, response, label):
        """Not only HTTP errors: a structurally invalid 200 is a failed read too."""
        state = _state([])
        transport = _Transport(_constant(response))
        with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
            dcnm_interface, "time", _Clock()
        ):
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)

        assert _budget(state) == {"sn1": 1}, label
        assert DcnmIntf.dcnm_intf_detail_unavailable(state, "Ethernet1/1", "SN1") is True

    def test_transport_exception_costs_one_invocation_not_three_attempts(self):
        """The unit is the invocation. Three attempts inside it are still one charge."""
        state = _state([])
        transport = _Transport(
            _constant(dcnm_interface.AnsibleConnectionError("synthetic offline failure"))
        )
        with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
            dcnm_interface, "time", _Clock()
        ):
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)

        assert transport.counts["bulk"] == 3
        assert _budget(state) == {"sn1": 1}

    def test_an_exhausted_reader_issues_no_request_and_schedules_no_sleep(self):
        """Exhaustion is silence: no GET, no retry sleep, and still unavailable."""
        state = _state([])
        transport = _Transport(_constant(ERROR_500))
        clock = _Clock()
        with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
            dcnm_interface, "time", clock
        ):
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)
            DcnmIntf.dcnm_intf_get_intf_info(state, "Ethernet1/1", "SN1", "INTERFACE_ETHERNET")
            spent, slept = transport.total, clock.calls
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)
            for index in range(2, 12):
                DcnmIntf.dcnm_intf_get_intf_info(
                    state, "Ethernet1/%d" % index, "SN1", "INTERFACE_ETHERNET"
                )

        assert spent == 6 and slept == 6
        assert transport.total == 6, "an exhausted serial must issue no further GET"
        assert clock.calls == 6, "an exhausted serial must schedule no further sleep"
        assert DcnmIntf.dcnm_intf_detail_unavailable(state, "Ethernet1/7", "SN1") is True

    def test_exhaustion_never_becomes_absence(self):
        """The dangerous failure mode: a skipped read must not look like emptiness.

        If an exhausted reader recorded absence instead of unavailability, every
        mutation guard downstream would pass and the module would happily create
        over a switch it never read.
        """
        state = _state([])
        transport = _Transport(_constant(ERROR_500))
        with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
            dcnm_interface, "time", _Clock()
        ):
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)
            DcnmIntf.dcnm_intf_get_intf_info(state, "Ethernet1/1", "SN1", "INTERFACE_ETHERNET")
            skipped = DcnmIntf.dcnm_intf_get_intf_info(
                state, "Ethernet1/2", "SN1", "INTERFACE_ETHERNET"
            )

        assert skipped == []
        assert state.intf_detail_authoritative_absent_keys == set()
        assert state.intf_detail_cached_snos == set()
        assert ("SN1", "ethernet1/2") in state.intf_detail_failed_keys
        assert DcnmIntf.dcnm_intf_detail_unavailable(state, "Ethernet1/2", "SN1") is True

    def test_a_skipped_bulk_read_cannot_be_bypassed_by_a_stale_cache_entry(self):
        """Invalidation still runs before the read is skipped.

        Were the skip to short-circuit ahead of `dcnm_intf_invalidate_serial_
        authority`, a cache entry left by an earlier pass would survive and the
        authority guard would read it as current state.
        """
        state = _state([])
        transport = _Transport(_constant(ERROR_500))
        with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
            dcnm_interface, "time", _Clock()
        ):
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)
            DcnmIntf.dcnm_intf_get_intf_info(state, "Ethernet1/1", "SN1", "INTERFACE_ETHERNET")
            # A stale entry planted as an earlier, now-superseded pass would leave.
            state.intf_detail_cache[("SN1", "ethernet1/1")] = _group("Ethernet1/1")
            state.intf_detail_cached_snos.add("SN1")
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)

        assert state.intf_detail_cache == {}
        assert state.intf_detail_cached_snos == set()
        assert DcnmIntf.dcnm_intf_detail_unavailable(state, "Ethernet1/1", "SN1") is True


class TestWhatRestoresTheAllowance:
    """Only a newly obtained, fully validated response for that serial."""

    def test_a_validated_populated_response_restores_it(self):
        state = _state([])
        seen = collections.Counter()

        def responder(kind, path, counts):
            seen["bulk"] += 1
            return ERROR_500 if seen["bulk"] <= 3 else _ok([_group("Ethernet1/1")])

        transport = _Transport(responder)
        with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
            dcnm_interface, "time", _Clock()
        ):
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)
            assert _budget(state) == {"sn1": 1}
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)

        assert _budget(state) == {}
        assert ("SN1", "ethernet1/1") in state.intf_detail_cache

    @pytest.mark.parametrize(
        "response,label",
        [(_ok([]), "confirmed empty list"), ([], "bare empty body")],
        ids=["confirmed_empty", "bare_empty"],
    )
    def test_a_confirmed_absence_restores_it_too(self, response, label):
        """Authoritative emptiness is an answer, so it refunds the charge."""
        state = _state([])
        seen = collections.Counter()

        def responder(kind, path, counts):
            seen["n"] += 1
            return ERROR_500 if seen["n"] <= 3 else response

        transport = _Transport(responder)
        with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
            dcnm_interface, "time", _Clock()
        ):
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)

        assert _budget(state) == {}, label
        assert "SN1" in state.intf_detail_cached_snos

    def test_an_individual_confirmed_absence_restores_it(self):
        state = _state([])
        seen = collections.Counter()

        def responder(kind, path, counts):
            seen["n"] += 1
            return ERROR_500 if kind == "bulk" else _ok([])

        transport = _Transport(responder)
        with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
            dcnm_interface, "time", _Clock()
        ):
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)
            assert _budget(state) == {"sn1": 1}
            result = DcnmIntf.dcnm_intf_get_intf_info(
                state, "Ethernet1/1", "SN1", "INTERFACE_ETHERNET"
            )

        assert result == []
        assert _budget(state) == {}
        assert ("SN1", "ethernet1/1") in state.intf_detail_authoritative_absent_keys

    @pytest.mark.parametrize(
        "trigger",
        ["refresh", "invalidation", "cache_hit", "unvalidated_200"],
    )
    def test_nothing_else_restores_it(self, trigger):
        """The four non-events, each of which r1 or a naive fix would have used.

        `refresh` and a new pass are a caller's intent to re-read. Invalidation is
        what the bulk reader does before *every* read, a failed one included. A
        cache hit contacts nothing. An unvalidated 200 is the malformed case the
        whole authority model exists to reject. None of them is evidence that the
        controller answered.
        """
        state = _state([])
        transport = _Transport(_constant(ERROR_500))
        with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
            dcnm_interface, "time", _Clock()
        ):
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)
            assert _budget(state) == {"sn1": 1}

            if trigger == "refresh":
                DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)
                expected = 2
            elif trigger == "invalidation":
                DcnmIntf.dcnm_intf_invalidate_serial_authority(state, "SN1")
                expected = 1
            elif trigger == "cache_hit":
                state.intf_detail_cache[("SN1", "ethernet9/9")] = _group("Ethernet9/9")
                DcnmIntf.dcnm_intf_get_intf_info(
                    state, "Ethernet9/9", "SN1", "INTERFACE_ETHERNET"
                )
                expected = 1
            else:  # unvalidated_200
                transport.responder = _constant(MALFORMED_200)
                DcnmIntf.dcnm_intf_get_intf_info(
                    state, "Ethernet1/1", "SN1", "INTERFACE_ETHERNET"
                )
                expected = 2

        assert _budget(state) == {"sn1": expected}, trigger

    @pytest.mark.parametrize("reader", ["bulk", "individual"])
    def test_two_unvalidated_200_reads_of_one_reader_exhaust_the_allowance(self, reader):
        """Consecutive malformed 200s must accumulate, in EACH reader separately.

        A single malformed 200 is not enough to see this: a reset placed before
        the charge still leaves the count at one after one call, so the failure
        only shows on the second. Both readers are covered because each owns its
        own charge site, and a mutation of one is invisible to a test that drives
        the other -- which is exactly how the first version of this suite missed
        it.
        """
        state = _state([])
        transport = _Transport(_constant(MALFORMED_200))
        with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
            dcnm_interface, "time", _Clock()
        ):
            for index in range(1, 4):
                if reader == "bulk":
                    DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)
                else:
                    DcnmIntf.dcnm_intf_get_intf_info(
                        state, "Ethernet1/%d" % index, "SN1", "INTERFACE_ETHERNET"
                    )

        assert _budget(state) == {"sn1": 2}, (
            "an unvalidated 200 must never refund the charge"
        )
        assert transport.counts[reader] == 2, (
            "the third read must be skipped; %d requests were issued"
            % transport.counts[reader]
        )

    def test_a_summary_response_cannot_restore_it(self):
        """The summary endpoint is outside the budget in both directions."""
        state = _state([])

        def responder(kind, path, counts):
            return ERROR_500 if kind == "bulk" else _ok([])

        transport = _Transport(responder)
        with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
            dcnm_interface, "time", _Clock()
        ):
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)
            DcnmIntf.dcnm_intf_get_have_all_with_sno(state, "SN1")

        assert _budget(state) == {"sn1": 1}

    def test_a_new_module_instance_starts_fresh(self):
        """The counter's lifetime is one run; a later invocation is not punished."""
        first = _state([])
        transport = _Transport(_constant(ERROR_500))
        with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
            dcnm_interface, "time", _Clock()
        ):
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(first, "SN1", refresh=True)
            DcnmIntf.dcnm_intf_get_intf_info(first, "Ethernet1/1", "SN1", "INTERFACE_ETHERNET")
            assert _budget(first) == {"sn1": 2}

            second = _state([])
            assert _budget(second) == {}
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(second, "SN1", refresh=True)

        assert _budget(second) == {"sn1": 1}
        assert transport.counts["bulk"] == 6  # the new instance really did read

    def test_recovery_then_a_new_failure_episode_gets_the_full_allowance(self):
        """failure -> validated success -> failure again, with no carry-over."""
        state = _state([])
        script = [ERROR_500] * 3 + [_ok([_group("Ethernet1/1")])] + [ERROR_500] * 6
        calls = iter(script)
        transport = _Transport(lambda kind, path, counts: next(calls))
        clock = _Clock()
        with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
            dcnm_interface, "time", clock
        ):
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)
            assert _budget(state) == {"sn1": 1}
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)
            assert _budget(state) == {}, "a validated response must refund the charge"
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)
            DcnmIntf.dcnm_intf_get_intf_info(state, "Ethernet1/1", "SN1", "INTERFACE_ETHERNET")

        assert _budget(state) == {"sn1": 2}
        assert transport.total == 10  # 3 failed + 1 ok + 3 failed + 3 failed
        assert DcnmIntf.dcnm_intf_detail_unavailable(state, "Ethernet1/1", "SN1") is True


class TestBudgetIdentity:
    """One endpoint, one allowance. Nothing borrows or refills another's."""

    def test_the_key_is_the_queried_serial_not_the_policy_identity(self):
        """A pair's request goes to one endpoint, so only that one is charged."""
        state = _state([])
        state.vpc_ip_sn = {"192.0.2.1": "SN1~PEER"}
        transport = _Transport(_constant(ERROR_500))
        with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
            dcnm_interface, "time", _Clock()
        ):
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1~PEER", refresh=True)

        assert _budget(state) == {"sn1": 1}
        assert "peer" not in state.intf_detail_failed_reads
        # Authority bookkeeping is a different model and still marks all three.
        assert {"SN1~PEER", "SN1", "PEER"}.issubset(state.intf_detail_fetch_failed_snos)

    def test_the_peer_keeps_its_own_untouched_allowance(self):
        """The peer's endpoint was never contacted, so it may still be read."""
        state = _state([])
        state.vpc_ip_sn = {"192.0.2.1": "SN1~PEER"}

        def responder(kind, path, counts):
            return _ok([_group("Ethernet1/1", serial="PEER")]) if "PEER" in path else ERROR_500

        transport = _Transport(responder)
        with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
            dcnm_interface, "time", _Clock()
        ):
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1~PEER", refresh=True)
            DcnmIntf.dcnm_intf_get_intf_info(state, "vPC1", "SN1~PEER", "INTERFACE_VPC")
            assert _budget(state) == {"sn1": 2}
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "PEER", refresh=True)

        assert _budget(state) == {"sn1": 2}
        assert ("PEER", "ethernet1/1") in state.intf_detail_cache
        assert DcnmIntf.dcnm_intf_detail_unavailable(state, "Ethernet1/1", "PEER") is False

    @pytest.mark.parametrize("second", ["sn1", "Sn1", "SN1"])
    def test_case_variants_of_one_serial_share_one_allowance(self, second):
        """Otherwise a differently spelled serial would buy a second allowance."""
        state = _state([])
        transport = _Transport(_constant(ERROR_500))
        with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
            dcnm_interface, "time", _Clock()
        ):
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, second, refresh=True)
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, second, refresh=True)

        assert transport.counts["bulk"] == 6, "the third read must be skipped"
        assert set(state.intf_detail_failed_reads) == {"sn1"}

    def test_one_switch_failing_does_not_spend_or_refill_another(self):
        state = _state([])

        def responder(kind, path, counts):
            return _ok([_group("Ethernet1/1", serial="SN2")]) if "SN2" in path else ERROR_500

        transport = _Transport(responder)
        with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
            dcnm_interface, "time", _Clock()
        ):
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)
            DcnmIntf.dcnm_intf_get_intf_info(state, "Ethernet1/1", "SN1", "INTERFACE_ETHERNET")
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN2", refresh=True)
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN3", refresh=True)

        assert _budget(state) == {"sn1": 2, "sn3": 1}
        assert "SN2" in state.intf_detail_cached_snos
        assert DcnmIntf.dcnm_intf_detail_unavailable(state, "Ethernet1/1", "SN1") is True
        assert DcnmIntf.dcnm_intf_detail_unavailable(state, "Ethernet1/1", "SN2") is False

    def test_a_successful_individual_read_proves_only_its_own_object(self):
        """Refunding the allowance must not make other identities authoritative."""
        state = _state([])

        def responder(kind, path, counts):
            if kind == "bulk":
                return ERROR_500
            return _ok([_group("Ethernet1/2")]) if "Ethernet1/2" in path else ERROR_500

        transport = _Transport(responder)
        with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
            dcnm_interface, "time", _Clock()
        ):
            DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)
            DcnmIntf.dcnm_intf_get_intf_info(state, "Ethernet1/2", "SN1", "INTERFACE_ETHERNET")

        assert _budget(state) == {}, "a validated individual response refunds the charge"
        assert DcnmIntf.dcnm_intf_detail_unavailable(state, "Ethernet1/2", "SN1") is False
        # Everything else on that switch is still unknown, and the serial-wide
        # bulk failure marker is untouched.
        assert "SN1" in state.intf_detail_fetch_failed_snos
        assert DcnmIntf.dcnm_intf_detail_unavailable(state, "Ethernet1/9", "SN1") is True

    def test_an_earlier_failed_key_stays_unavailable_after_another_key_succeeds(self):
        """Refunding the allowance must not rehabilitate an already-failed key.

        Entered directly through the individual reader -- the path
        `dcnm_intf_get_diff_overridden` takes for a serial whose bulk succeeded
        earlier -- so the first failure does not also carry a bulk charge and the
        second read is still permitted. That ordering is what makes the property
        observable: with a failed bulk first, the allowance is gone before the
        second interface is reached, which is the tradeoff case below.
        """
        state = _state([])

        def responder(kind, path, counts):
            return _ok([_group("Ethernet1/2")]) if "Ethernet1/2" in path else ERROR_500

        transport = _Transport(responder)
        with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
            dcnm_interface, "time", _Clock()
        ):
            DcnmIntf.dcnm_intf_get_intf_info(state, "Ethernet1/1", "SN1", "INTERFACE_ETHERNET")
            assert _budget(state) == {"sn1": 1}
            DcnmIntf.dcnm_intf_get_intf_info(state, "Ethernet1/2", "SN1", "INTERFACE_ETHERNET")

        assert _budget(state) == {}
        assert ("SN1", "ethernet1/1") in state.intf_detail_failed_keys
        assert DcnmIntf.dcnm_intf_detail_unavailable(state, "Ethernet1/1", "SN1") is True
        assert DcnmIntf.dcnm_intf_detail_unavailable(state, "Ethernet1/2", "SN1") is False
        assert ("SN1", "ethernet1/2") in state.intf_detail_cache


def test_the_pathological_first_probe_tradeoff_is_real():
    """B = 2 has a cost, and it is not the same as the old error path.

    Bulk fails; the first interface probed also fails; a later interface that
    WOULD have answered is never read. With the same transport and a WANT whose
    first interface answers, all of them are served. The difference is the
    accepted tradeoff, stated as an executable fact rather than an
    assurance that nothing changed.
    """
    def responder(kind, path, counts):
        if kind == "bulk":
            return ERROR_500
        if _ifname_in(path) == "Ethernet1/1":
            return ERROR_500
        return _ok([_group(_ifname_in(path))])

    unlucky = _want(3)                       # Ethernet1/1 first: it is the probe
    lucky = _want(2, first=2)                # Ethernet1/2 first: it answers

    unlucky_state, unlucky_tx, _unlucky_result = _run_get_have(unlucky, responder)
    lucky_state, lucky_tx, _lucky_result = _run_get_have(lucky, responder)

    # Unlucky: the probe burns the allowance and the other two are never read.
    assert unlucky_tx.counts["individual"] == 3
    assert unlucky_state.have == []
    assert len(_unavailable(unlucky_state, unlucky)) == 3

    # Lucky: the probe succeeds, refunds the allowance, and every read proceeds.
    assert lucky_tx.counts["individual"] == 2
    assert len(lucky_state.have) == 2
    assert _unavailable(lucky_state, lucky) == []


# ====================================================================================================
# Formerly test_pr725_read_budget_bound.py
# PR725: acceptance tests for the implemented bounded-recovery contract.
#
# The candidate must pass all 11 cases. As a negative control, the scaling cases
# fail on the accepted indexing base `64e6b0ce95de0780b9b788aa1eec054ab024b3d0`,
# before recovery was implemented. They fail on request-count assertions, not on
# an import, a fixture or a skip. The earlier diagnostic base `dd0a456b` has the
# same read-path behavior; its evidence remains separate.
#
# Three parametrizations PASS on the baseline, and that is the point: with a single
# requested interface and a single pass the baseline already spends 3 + 3 = 6
# requests, exactly the accepted ceiling. The contract does not change the small
# case; it stops the cost from growing with the interface count, with a second
# pass, or across an invalidation. A run of this file on the frozen baseline is
# expected to report **8 failed, 3 passed**.
#
# Do not add a skip marker, an `xfail`, or a mock that bypasses the reader. The
# file must remain red for the right reason on the baseline and green on the
# implemented candidate, without weakening its assertions.
#
# IMPLEMENTED CONTRACT, REVISION 2
# --------------------------------
# Revision 1 reset the budget on `dcnm_intf_invalidate_serial_authority`. That was
# wrong and is withdrawn: the bulk reader invalidates the serial before *every*
# read, including a repeated failed one, so the reset would have handed a real
# `overridden` run a second full budget. Design applied here: a counter, B = 2, per queried
# physical serial, per module instance.
#
# Unit      one FAILED read invocation = one call to the bounded GET helper from an
#           interface-policy reader whose outcome is "unavailable" (transport
#           exception, non-200, or a 200 whose payload cannot be trusted).
# Key       the normalized physical query serial actually sent to the endpoint,
#           `_dcnm_intf_normalize_serial(serialNumber)`, folded case-insensitively.
#           One endpoint, one budget.
# Bound     B = 2 consecutive failed invocations per serial per module run.
#           Two, not one: the first is spent on the bulk endpoint before any
#           individual read exists, so B = 1 would delete the per-interface
#           fallback that `TestFallbackMustSurvive` requires.
# Reset     ONLY a newly obtained, validated response for that same serial in this
#           run. NOT on invalidation, NOT on `refresh=True`, NOT on a second pass
#           or a different diff phase, NOT on a cache hit, and NOT on a bare
#           RETURN_CODE 200 whose payload fails validation.
# Lifetime  one `DcnmIntf` instance. It deliberately spans states, diff phases and
#           repeated passes over the same serial — that span IS the bound.
# Exhausted the reader issues no further request for that serial and marks the
#           target unavailable without one. Existing fail-closed guards still
#           refuse writes over unknown state. A pathological first individual
#           probe can withhold later healthy interfaces; this is an accepted
#           availability tradeoff, not proof that those interfaces are absent.
#
# WHAT THE CEILING MEANS, PRECISELY
# ---------------------------------
# During a persistent-failure episode against one switch: at most 6 interface-
# policy requests and at most 6 seconds of SCHEDULED sleep for that switch, for the
# lifetime of one module run, whatever the interface count. A malformed 200 ends
# its invocation after one attempt, so its ceiling is 2 requests and no sleep.
#
# It is NOT a ceiling on the module's wall-clock duration, NOT a ceiling on all of
# the module's requests (successful per-interface reads stay unbounded: `3 + N`
# remains `3 + N`), and NOT a ceiling on the summary, breakout, access-mode or
# `query` endpoints, which stay outside this budget and keep their current
# behaviour — see the `24` group in the characterization file.
#
# Baseline for comparison, one switch, N interfaces (measured on the diagnostic base):
#     persistent failure   3 + 3N requests, 3(N + 1) scheduled seconds
#     malformed HTTP 200   1 + N requests, 0 seconds
#
# NOT LIVE TESTED. Synthetic identities only.
# ====================================================================================================
# Historical constant names are retained; these values implement contract r2.
PROPOSED_FAILED_INVOCATIONS = 2
ATTEMPTS_PER_INVOCATION = 3
REQUEST_CEILING_PER_SWITCH = PROPOSED_FAILED_INVOCATIONS * ATTEMPTS_PER_INVOCATION
SLEEP_CEILING_PER_SWITCH = REQUEST_CEILING_PER_SWITCH
# A 200 ends its invocation on the first attempt, so it can never reach the
# three-attempt ceiling.
REQUEST_CEILING_PER_SWITCH_NO_RETRY = PROPOSED_FAILED_INVOCATIONS

LARGE = 50


def _report(transport, clock):
    return "bulk=%d individual=%d total=%d sleeps=%d sleep_s=%g" % (
        transport.counts["bulk"],
        transport.counts["individual"],
        transport.total,
        clock.calls,
        clock.seconds,
    )


@pytest.mark.parametrize(
    "responder,label",
    [
        (_constant(ERROR_500), "persistent HTTP 500"),
        (
            _constant(dcnm_interface.AnsibleConnectionError("synthetic offline failure")),
            "persistent transport exception",
        ),
    ],
    ids=["http_500", "transport_exception"],
)
@pytest.mark.parametrize("count", [1, LARGE])
def test_failed_recovery_is_bounded_per_switch_not_per_interface(
    responder, label, count
):
    """Unreadable switch: the failed work must not scale with the interface count."""
    want = _want(count)

    state, transport, clock = _run_get_have(want, responder)

    assert transport.total <= REQUEST_CEILING_PER_SWITCH, (
        "%s with %d requested interfaces spent %d interface-policy requests; the "
        "proposed contract allows at most %d per switch regardless of N (%s)"
        % (label, count, transport.total, REQUEST_CEILING_PER_SWITCH, _report(transport, clock))
    )
    assert clock.seconds <= SLEEP_CEILING_PER_SWITCH, (
        "%s with %d requested interfaces scheduled %g seconds of sleep; the "
        "proposed contract allows at most %d per switch (%s)"
        % (label, count, clock.seconds, SLEEP_CEILING_PER_SWITCH, _report(transport, clock))
    )
    # Exhausting the budget must change only the COST, never the conclusion.
    assert state.have == []
    assert len(_unavailable(state, want)) == count, (
        "a bound must not turn an unread interface into absence: %d of %d "
        "requested interfaces were still reported unavailable"
        % (len(_unavailable(state, want)), count)
    )
    assert transport.mutations == []


@pytest.mark.parametrize("count", [1, LARGE])
def test_malformed_http_200_is_bounded_and_never_becomes_absence(count):
    """A trusted-looking 200 that cannot be parsed must not be polled per interface."""
    want = _want(count)

    state, transport, clock = _run_get_have(want, _constant(MALFORMED_200))

    assert transport.total <= REQUEST_CEILING_PER_SWITCH_NO_RETRY, (
        "malformed HTTP 200 with %d requested interfaces spent %d interface-policy "
        "requests at full speed; the proposed contract allows at most %d per switch "
        "(%s)"
        % (count, transport.total, REQUEST_CEILING_PER_SWITCH_NO_RETRY, _report(transport, clock))
    )
    assert clock.calls == 0
    assert state.have == []
    assert state.intf_detail_authoritative_absent_keys == set()
    assert len(_unavailable(state, want)) == count


def test_the_budget_is_per_switch_so_it_scales_with_switches_not_interfaces():
    """Two unreadable switches cost two budgets, not two budgets times N."""
    want = _want(LARGE, serial="SN1") + _want(LARGE, serial="SN2", first=LARGE + 1)

    state, transport, clock = _run_get_have(want, _constant(ERROR_500))

    ceiling = 2 * REQUEST_CEILING_PER_SWITCH
    assert transport.total <= ceiling, (
        "two unreadable switches with %d interfaces each spent %d interface-policy "
        "requests; the proposed contract allows at most %d (%s)"
        % (LARGE, transport.total, ceiling, _report(transport, clock))
    )
    assert len(_unavailable(state, want)) == 2 * LARGE
    assert state.intf_detail_fetch_failed_snos == {"SN1", "SN2"}


# ===========================================================================
# Revision 2 additions. These are the cases the withdrawn r1 reset rule would
# have let through: each one crosses an invalidation, a new pass, or both.
# ===========================================================================
def test_budget_survives_invalidation_and_a_repeated_pass_over_one_serial():
    """One serial, one interface, two passes: still one budget.

    This is the real caller order of `overridden` at method level: prefetch,
    per-interface read, then the second prefetch and read of
    `dcnm_intf_get_diff_overridden`. `dcnm_intf_bulk_fetch_intf_info` invalidates
    the serial before every read (line 5346), so if invalidation reset the budget
    the second pass would start from zero and the bound would be meaningless.
    """
    state = _state([])
    transport = _Transport(_constant(ERROR_500))
    clock = _Clock()

    with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
        dcnm_interface, "time", clock
    ):
        DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)
        DcnmIntf.dcnm_intf_get_intf_info(state, "Ethernet1/1", "SN1", "INTERFACE_ETHERNET")
        DcnmIntf.dcnm_intf_invalidate_serial_authority(state, "SN1")
        DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=False)
        DcnmIntf.dcnm_intf_get_intf_info(state, "Ethernet1/1", "SN1", "INTERFACE_ETHERNET")

    assert transport.total <= REQUEST_CEILING_PER_SWITCH, (
        "an invalidation and a repeated pass over one serial spent %d "
        "interface-policy requests for a single interface; the proposed contract "
        "allows at most %d per serial for the whole run, because neither "
        "invalidation nor a new pass is a reset (bulk=%d individual=%d sleep_s=%g)"
        % (
            transport.total,
            REQUEST_CEILING_PER_SWITCH,
            transport.counts["bulk"],
            transport.counts["individual"],
            clock.seconds,
        )
    )
    assert clock.seconds <= SLEEP_CEILING_PER_SWITCH
    assert DcnmIntf.dcnm_intf_detail_unavailable(state, "Ethernet1/1", "SN1") is True


@pytest.mark.parametrize("count", [1, 10])
def test_overridden_on_a_populated_switch_stays_within_one_budget(count):
    """The bound holds through the REAL `main()`, across both overridden passes.

    `dcnm_intf_get_have` prefetches the serial, then
    `dcnm_intf_get_diff_overridden` prefetches it again and probes every
    `have_all` entry. A per-pass budget would permit twice the ceiling; the
    contract's budget is per serial per run.
    """
    run = run_module_path(
        count, _persistent_500, state="overridden", already_present=count
    )

    assert run.policy_total <= REQUEST_CEILING_PER_SWITCH, (
        "overridden over a switch already carrying %d interfaces spent %d "
        "interface-policy requests across its two passes; the proposed contract "
        "allows at most %d per serial for the whole run (%s)"
        % (count, run.policy_total, REQUEST_CEILING_PER_SWITCH, run.report())
    )
    assert run.clock.seconds <= SLEEP_CEILING_PER_SWITCH, (
        "overridden scheduled %g seconds of sleep; the proposed contract allows "
        "at most %d per serial (%s)"
        % (run.clock.seconds, SLEEP_CEILING_PER_SWITCH, run.report())
    )
    # Cheaper, never more permissive: the refusal and the zero writes stand.
    assert run.outcome == "fail_json"
    assert "could not be read authoritatively" in run.message
    assert run.counts["mutating"] == 0
    assert run.mutations == []


def test_post_deletion_recovery_does_not_reopen_an_exhausted_budget():
    """An exhausted serial stays exhausted through the deferred-member loop.

    `dcnm_intf_refresh_deferred_deleted_member_defaults` invalidates and re-reads
    inside a ten-iteration loop. Measured on the baseline, that loop already
    aborts inside its first iteration when detail is unavailable
    (`test_deferred_recovery_loop_aborts_inside_its_first_iteration_on_failure`),
    so it does not need a fresh budget to behave correctly -- it needs only to
    stop paying for reads of a switch already proven unreadable.

    The decision must not change: the loop still refuses, still schedules no
    replacement and still writes nothing.
    """
    state = _deferred_stub()
    transport = _Transport(_constant(ERROR_500))
    clock = _Clock()

    with mock.patch.object(dcnm_interface, "dcnm_send", transport), mock.patch.object(
        dcnm_interface, "time", clock
    ):
        # Spend the whole budget on this serial first, exactly as an earlier
        # phase of a `deleted` run would.
        DcnmIntf.dcnm_intf_bulk_fetch_intf_info(state, "SN1", refresh=True)
        DcnmIntf.dcnm_intf_get_intf_info(state, "Ethernet1/1", "SN1", "INTERFACE_ETHERNET")
        spent_before = transport.total

        with pytest.raises(RuntimeError, match="fail_json"):
            DcnmIntf.dcnm_intf_refresh_deferred_deleted_member_defaults(state)

    spent_by_loop = transport.total - spent_before
    assert spent_by_loop == 0, (
        "the post-deletion recovery loop spent %d further interface-policy "
        "requests on a serial whose budget was already exhausted (%d spent "
        "before); under the proposed contract it must issue none and reach the "
        "same refusal (bulk=%d individual=%d sleep_s=%g)"
        % (
            spent_by_loop,
            spent_before,
            transport.counts["bulk"],
            transport.counts["individual"],
            clock.seconds,
        )
    )
    assert transport.total <= REQUEST_CEILING_PER_SWITCH
    # The conclusion is unchanged: refuse, schedule nothing, write nothing.
    assert state.diff_replace == []
    assert state.diff_deploy == []
    assert state.changed_dict[0]["replaced"] == []
    assert state.changed_dict[0]["deploy"] == []
    assert transport.mutations == []


# ====================================================================================================
# Formerly test_pr725_scale_module_path.py
# PR725 advisory 5766305127, item 4: a synthetic 1,000 / 5,000-interface regression through the real `main()`.
#
# What runs: the module's real argument spec, validation, builder, `gie_contribute_nvpairs`, comparator, carry-forward / withdrawal and
# request assembly (`helpers/binding_harness.run_configs`). Only inventory, transport and sleep are replaced. One switch, routed
# Ethernet interfaces with the OSPF context and two registered bindings that have a reset (`ospf_mtu_ignore`, `ospf_shutdown`).
#
# What is asserted (deterministic, CI-safe):
# - calls per endpoint do not grow with the interface count; writes are one bulk request or none;
# - every outbound interface entry equals the model (the module's own single-interface entry, with only the name and address varied),
#   so the serialized size is the model's size, byte for byte;
# - merged omission preserves the registered fields with zero writes; an identical second application writes nothing;
# - replaced / overridden omission withdraw them to their reset (no general carry-forward);
# - a persistently failing interface read keeps the refusal with zero writes and a bounded number of requests and scheduled sleeps.
#
# What is NOT asserted: wall-clock time, controller limits, controller CPU, or any live performance. Synthetic identities only (RFC 2544 benchmarking range);
# NOT LIVE TESTED.
# ====================================================================================================
SIZES = (1000, 5000)
NET = ipaddress.ip_network("198.18.0.0/15")
REGISTERED = {"ospf_mtu_ignore": True, "ospf_shutdown": True}
REGISTERED_WIRE = ("ospfMtuIgnore", "ospfShutdown")
READ_ENDPOINTS = {"accessmode": 1, "policies": 1, "bulk": 1, "summary": 1}
# The bounded-recovery contract (test_read_budget_and_scale.py): two failed invocations x three attempts per switch.
FAILED_READ_CEILING = 6
# The harness transport, captured before any test patches `H._transport`.
REAL_TRANSPORT = H._transport


def name(i):
    return "Ethernet1/%d" % (i + 1)


def addr(i):
    return str(NET.network_address + 4 * i + 1)


def configs(n, omit=(), **extra):
    out = []
    for i in range(n):
        prof = H.base_for(H.ROUTED, **dict(H.OSPF_CTX, **dict(REGISTERED, **extra)))
        for key in omit:
            prof.pop(key)
        prof["ipv4_addr"] = addr(i)
        out.append(H.cfg(name(i), prof, deploy=False))
    return out


def endpoint(path):
    if "accessmode" in path:
        return "accessmode"
    if "/control/policies/switches/" in path:
        return "policies"
    if "/interface/detail" in path:
        return "summary"
    if "/interface?" in path:
        return "individual" if "&ifName=" in path else "bulk"
    return "other"


def read_counts(calls):
    counts = {}
    for c in H.split_calls(calls)["reads"]:
        counts[endpoint(c["path"])] = counts.get(endpoint(c["path"]), 0) + 1
    return counts


def entries(calls):
    found = []
    H._collect_policies([c["payload"] for c in H.split_calls(calls)["updates"]], found)
    return found


def have_from(calls):
    """The module's own outbound policies, stored as the controller would return them."""
    have = copy.deepcopy(entries(calls))
    for policy in have:
        for intf in policy["interfaces"]:
            intf["interfaceType"] = "INTERFACE_ETHERNET"
            intf["fabricName"] = H.FABRIC
    return have


def run(n_or_configs, state, have=None, **kw):
    cfgs = configs(n_or_configs) if isinstance(n_or_configs, int) else n_or_configs
    return H.run_configs(cfgs, state, have=have, deploy=False, **kw)


_MODEL = {}


def model():
    """One interface's outbound entry and the nvPairs that carry the per-interface name and address, from two real runs."""
    if not _MODEL:
        result, calls = run(2, "merged")
        assert result.get("changed") is True, result.get("msg")
        (policy,) = entries(calls)
        first, second = policy["interfaces"]
        varying = sorted(k for k in first["nvPairs"] if first["nvPairs"][k] != second["nvPairs"][k])
        _MODEL.update(policy=policy["policy"], template=first, varying=varying,
                      head={k: v for k, v in policy.items() if k != "interfaces"})
    return _MODEL


def expected_entry(i):
    m = model()
    entry = copy.deepcopy(m["template"])
    entry["ifName"] = name(i)
    for key in m["varying"]:
        value = entry["nvPairs"][key]
        entry["nvPairs"][key] = value.replace(name(0), name(i)).replace(addr(0), addr(i))
    return entry


def assert_one_bulk_update_matching_the_model(calls, n):
    split = H.split_calls(calls)
    assert len(split["updates"]) == 1 and split["deploys"] == [] and split["other"] == []
    (policy,) = entries(calls)
    m = model()
    assert {k: v for k, v in policy.items() if k != "interfaces"} == m["head"]
    assert len(policy["interfaces"]) == n
    expected = [expected_entry(i) for i in range(n)]
    assert policy["interfaces"] == expected
    sent = split["updates"][0]["payload"]
    model_policy = dict(m["head"], interfaces=expected)
    model_payload = [model_policy] if isinstance(sent, list) else model_policy
    # Byte for byte, in the module's own key order: the serialized request is exactly the model's.
    assert json.dumps(sent) == json.dumps(model_payload)
    return len(json.dumps(sent))


# ------------------------------------------------------------------ model sanity
def test_the_model_varies_only_the_name_and_address_and_carries_the_registered_fields():
    m = model()
    assert m["policy"] == H.ROUTED
    assert set(m["varying"]) <= {"INTF_NAME", "IP", "CONF", "DESC"} and "IP" in m["varying"]
    for wire in REGISTERED_WIRE:
        assert m["template"]["nvPairs"][wire] == "true"


# ------------------------------------------------------------------ both sizes: healthy path, repeat, merged omission, failed read
@pytest.mark.parametrize("n", SIZES)
def test_healthy_create_reads_a_constant_number_of_times_and_sends_one_model_payload(n):
    result, calls = run(n, "merged")
    assert result.get("changed") is True, result.get("msg")
    assert read_counts(calls) == READ_ENDPOINTS
    assert_one_bulk_update_matching_the_model(calls, n)


@pytest.mark.parametrize("n", SIZES)
def test_identical_second_application_writes_nothing(n):
    _result, calls = run(n, "merged")
    result, calls2 = run(n, "merged", have=have_from(calls))
    assert result.get("changed") is False, result.get("msg")
    assert H.writes(calls2) == []
    assert read_counts(calls2) == READ_ENDPOINTS


@pytest.mark.parametrize("n", SIZES)
def test_merged_omission_preserves_the_registered_fields_with_zero_writes(n):
    _result, calls = run(n, "merged")
    result, calls2 = run(configs(n, omit=REGISTERED), "merged", have=have_from(calls))
    assert result.get("changed") is False, result.get("msg")
    assert H.writes(calls2) == []


def failing_transport(calls, have):
    real = REAL_TRANSPORT(calls, have)

    def send(mod, method, path, payload=None):
        if method == "GET" and "/interface?" in path:
            calls.append({"method": method, "path": path, "payload": None})
            return {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": []}
        return real(mod, method, path, payload)
    return send


@pytest.mark.parametrize("n", SIZES)
def test_failed_interface_read_keeps_the_refusal_with_bounded_requests_and_zero_writes(n):
    sleeps = []
    with mock.patch.object(H, "_transport", failing_transport):
        result, calls = run(n, "merged", extra_patch=mock.patch.object(module.time, "sleep", side_effect=sleeps.append))
    assert result.get("failed") is True
    assert "could not be read authoritatively" in result["msg"]
    assert H.writes(calls) == []
    counts = read_counts(calls)
    assert counts.get("bulk", 0) + counts.get("individual", 0) <= FAILED_READ_CEILING
    assert len(sleeps) <= FAILED_READ_CEILING and sum(sleeps) <= FAILED_READ_CEILING


# ------------------------------------------------------------------ 1,000 only: state semantics at scale
N_STATES = 1000


@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_replaced_and_overridden_omission_withdraw_the_registered_fields_to_their_reset(state):
    _result, calls = run(N_STATES, "merged")
    result, calls2 = run(configs(N_STATES, omit=REGISTERED), state, have=have_from(calls))
    assert result.get("changed") is True, result.get("msg")
    split = H.split_calls(calls2)
    assert len(split["updates"]) == 1 and split["deploys"] == []
    sent = [i for p in entries(calls2) for i in p["interfaces"]]
    assert sorted(i["ifName"] for i in sent) == sorted(name(i) for i in range(N_STATES))
    for intf in sent:
        assert all(intf["nvPairs"][wire] == "false" for wire in REGISTERED_WIRE), intf["ifName"]


def test_merged_unrelated_change_carries_the_omitted_registered_fields_forward():
    _result, calls = run(N_STATES, "merged")
    result, calls2 = run(configs(N_STATES, omit=REGISTERED, description="scale-changed"), "merged", have=have_from(calls))
    assert result.get("changed") is True, result.get("msg")
    sent = [i for p in entries(calls2) for i in p["interfaces"]]
    assert len(sent) == N_STATES and len(H.split_calls(calls2)["updates"]) == 1
    for intf in sent:
        assert intf["nvPairs"]["DESC"] == "scale-changed"
        assert all(intf["nvPairs"][wire] == "true" for wire in REGISTERED_WIRE), intf["ifName"]


def transient_bulk_failure(failed_attempts):
    def factory(calls, have):
        real = REAL_TRANSPORT(calls, have)
        seen = {"bulk": 0}

        def send(mod, method, path, payload=None):
            if method == "GET" and "/interface?" in path and "&ifName=" not in path:
                seen["bulk"] += 1
                if seen["bulk"] <= failed_attempts:
                    calls.append({"method": method, "path": path, "payload": None})
                    return {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": []}
            return real(mod, method, path, payload)
        return send
    return factory


@pytest.mark.parametrize("failed_attempts,bulk,individual", [(1, 2, 0), (3, 3, N_STATES)],
                         ids=["recovered_within_the_retry", "bulk_invocation_failed"])
def test_read_recovery_cost_at_scale(failed_attempts, bulk, individual):
    """The existing recovery contract at 1,000 interfaces (test_read_budget_and_scale.py): one failed attempt is absorbed by the
    retry; a failed bulk invocation falls back to one successful individual read per interface (3 + N), then writes once."""
    with mock.patch.object(H, "_transport", transient_bulk_failure(failed_attempts)):
        result, calls = run(N_STATES, "merged")
    assert result.get("changed") is True and not result.get("failed"), result.get("msg")
    counts = read_counts(calls)
    assert counts.get("bulk") == bulk and counts.get("individual", 0) == individual
    assert len(H.split_calls(calls)["updates"]) == 1
