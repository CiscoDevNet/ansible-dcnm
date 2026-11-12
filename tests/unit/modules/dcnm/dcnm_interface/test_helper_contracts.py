"""Contracts of the shared test helpers that the suites rely on."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import hashlib
import json
import os

import pytest

from .helpers import fixture_cases as fc

BUNDLE = {
    "_bundle": "synthetic",
    "sources": {"cap": {"file": "cap.json", "sha256": "0" * 64}},
    "baselines": {"cap.base": {"a": "1", "b": False, "c": None, "d": 0}},
    "cases": {"cap": {
        "same": {"$baseline": "cap.base"},
        "changed": {"$baseline": "cap.base", "$set": {"b": "false", "e": "new"}, "$unset": ["d"]},
        "nulled": {"$baseline": "cap.base", "$set": {"a": None}},
        "items": [{"$baseline": "cap.base"}, {"plain": True}],
    }},
}


@pytest.fixture
def synthetic(tmp_path, monkeypatch):
    def install(bundle):
        (tmp_path / "synthetic.json").write_text(json.dumps(bundle))
        monkeypatch.setattr(fc, "FIXTURE_DIR", str(tmp_path))
        monkeypatch.setattr(fc, "_FILES", {})
        monkeypatch.setattr(fc, "SOURCES", {"cap": ("synthetic.json", "cap")})
    return install


def test_baseline_reference_is_expanded_with_types_and_order_kept(synthetic):
    synthetic(BUNDLE)
    case = fc.load_case("cap")
    assert json.dumps(case["same"]) == json.dumps({"a": "1", "b": False, "c": None, "d": 0})
    # $set replaces in place and appends a new key; a string "false" stays a string; $unset deletes
    assert json.dumps(case["changed"]) == json.dumps({"a": "1", "b": "false", "c": None, "e": "new"})
    # a null override sets null, it does not delete the key
    assert "a" in case["nulled"] and case["nulled"]["a"] is None
    assert case["items"] == [{"a": "1", "b": False, "c": None, "d": 0}, {"plain": True}]


def test_every_call_returns_a_fresh_copy(synthetic):
    synthetic(BUNDLE)
    first = fc.load_case("cap")
    first["same"]["a"] = "mutated"
    first["items"].append("extra")
    second = fc.load_case("cap")
    assert second["same"]["a"] == "1" and len(second["items"]) == 2


@pytest.mark.parametrize("ref, error", [
    ({"$baseline": "missing"}, KeyError),
    ({"$baseline": "cap.base", "$unset": ["absent"]}, KeyError),
    ({"$baseline": "cap.base", "$sett": {"a": "2"}}, ValueError),
], ids=["unknown-baseline", "unset-missing-key", "unknown-marker-key"])
def test_malformed_references_are_refused(synthetic, ref, error):
    bundle = json.loads(json.dumps(BUNDLE))
    bundle["cases"]["cap"] = {"node": ref}
    synthetic(bundle)
    with pytest.raises(error):
        fc.load_case("cap")


def test_a_baseline_may_not_refer_to_another_baseline(synthetic):
    bundle = json.loads(json.dumps(BUNDLE))
    bundle["baselines"]["cap.nested"] = {"inner": {"$baseline": "cap.base"}}
    synthetic(bundle)
    with pytest.raises(ValueError):
        fc.load_case("cap")


def test_every_capture_loads_and_every_bundle_lists_exactly_its_captures():
    by_file = {}
    for name, (filename, key) in fc.SOURCES.items():
        by_file.setdefault(filename, set()).add(key)
        if key is not None and set(fc._read(filename)["cases"][key]) == {"text", "sha256"}:
            assert isinstance(fc.load_text(name), str)
            with pytest.raises(TypeError):
                fc.load_case(name)
        else:
            assert fc.load_case(name)
    on_disk = set(os.listdir(fc.FIXTURE_DIR))
    assert on_disk == set(by_file), "every bundle is referenced and every referenced bundle exists"
    for filename, keys in by_file.items():
        if keys != {None}:
            data = fc._read(filename)
            assert set(data["sources"]) == keys == set(data["cases"]), filename


def test_text_captures_match_their_recorded_sha256():
    for name, (filename, key) in fc.SOURCES.items():
        case = fc._read(filename)["cases"].get(key) if key else None
        if isinstance(case, dict) and set(case) == {"text", "sha256"}:
            assert hashlib.sha256(fc.load_text(name).encode("utf-8")).hexdigest() == case["sha256"], name
