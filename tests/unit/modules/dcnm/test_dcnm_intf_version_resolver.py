# Focused tests for the NDFC version resolver (_ndfc_version_gte).
#
# The resolver must compare as many version segments as the TARGET specifies:
#   - a 4-part target (patched OSPF-MD floor "12.6.0.267") enforces the build number
#   - a 3-part target (fec "12.4.1") keeps its original 3-part behavior
# Unknown/invalid versions fail closed.

from ansible_collections.cisco.dcnm.plugins.modules.dcnm_interface import DcnmIntf


class _Stub:
    """Minimal stand-in carrying only ndfc_version (all _ndfc_version_gte reads)."""

    def __init__(self, ndfc_version):
        self.ndfc_version = ndfc_version


def gte(current, target):
    return DcnmIntf._ndfc_version_gte(_Stub(current), target)


FLOOR = "12.6.0.267"  # OSPF-MD assumed floor (validated_on)


# --- 4-part target: the build number IS enforced -----------------------------
def test_below_build_not_supported():
    assert gte("12.6.0.266", FLOOR) is False


def test_exact_build_supported():
    assert gte("12.6.0.267", FLOOR) is True


def test_higher_build_supported():
    assert gte("12.6.0.300", FLOOR) is True


def test_higher_patch_supported():
    assert gte("12.6.1.0", FLOOR) is True


def test_lower_build_that_old_3part_would_wrongly_pass():
    # With the old [:3] comparator, (12,6,0) >= (12,6,0) => wrongly True.
    # The 4-part comparator must reject it.
    assert gte("12.6.0.100", FLOOR) is False


# --- fail-closed on unknown/invalid ------------------------------------------
def test_unknown_version_fails_closed():
    assert gte(None, FLOOR) is False


def test_empty_version_fails_closed():
    assert gte("", FLOOR) is False


def test_invalid_version_fails_closed():
    assert gte("not.a.version", FLOOR) is False


# --- 3-part target (fec): behavior unchanged, build ignored ------------------
def test_fec_3part_still_supported():
    assert gte("12.4.1.245", "12.4.1") is True


def test_fec_3part_below_not_supported():
    assert gte("12.4.0.999", "12.4.1") is False


def test_fec_exact_3part_supported():
    assert gte("12.4.1", "12.4.1") is True
