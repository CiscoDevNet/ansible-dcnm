"""The registry sources reproduce the versioned binding table, from this tree alone.

``plugins/module_utils/gie_binding_table.py`` is generated. Its canonical sources are ``tools/registry/slices/*.yaml`` and its
generator is ``tools/gie_generate_binding_table.py`` (see ``tools/registry/README.md``). These tests run both from a checkout and
from the installed collection tree that CI tests: ``tools/`` is part of the collection, and everything is located relative to the
imported table, never to an absolute or personal path.

Two groups:

* INTEGRITY (needs no sources): the shipped table is internally consistent.
* SOURCES (needs ``tools/`` in the tree): the table is exactly what the sources compile to, the result is deterministic and
  independent of the working directory, an altered copy of an input is detected, and the sources carry no private material.

The SOURCES group never skips silently. If ``tools/`` is absent the tests FAIL with the reason, unless the environment sets
``GIE_REGISTRY_SOURCES_OPTIONAL=1`` (an explicit, visible opt-out for a tree that deliberately omits development tooling).

NOT LIVE TESTED IN THIS GENERATION. Nothing here contacts a controller or a device.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from ansible_collections.cisco.dcnm.plugins.module_utils import gie_binding_table

ROOT = Path(gie_binding_table.__file__).resolve().parents[2]
GENERATOR = ROOT / "tools" / "gie_generate_binding_table.py"
SLICES = ROOT / "tools" / "registry" / "slices"
README = ROOT / "tools" / "registry" / "README.md"
TABLE = Path(gie_binding_table.__file__).resolve()

# A binding whose compiled value is changed by the negative test: any change to a compiled field must be detected.
MUTATED_PARENT, MUTATED_NVPAIR, MUTATED_FIELD = "int_vlan", "OSPF_AUTH_KEY_ID", "reset_wire"

PRIVATE = [
    ("absolute user path", re.compile(r"/Users/|/home/|C:\\\\Users")),
    ("private evidence path", re.compile(r"\bevidence/")),
    ("lab serial number", re.compile(r"\b9[A-Z0-9]{10}\b")),
    ("lab switch name", re.compile(r"\b(?:Leaf|Spine|Border)-\d+\b")),
    ("lab address", re.compile(r"\b192\.168\.\d+\.\d+|\b10\.\d+\.\d+\.\d+\b")),
    ("internal working document", re.compile(r"CLAUDE\.md")),
]


def _sources_or_fail():
    missing = [str(p.relative_to(ROOT)) for p in (GENERATOR, SLICES, README) if not p.exists()]
    if not missing:
        return
    if os.environ.get("GIE_REGISTRY_SOURCES_OPTIONAL") == "1":
        pytest.skip("GIE_REGISTRY_SOURCES_OPTIONAL=1 and this tree omits development tooling: {0}".format(", ".join(missing)))
    pytest.fail(
        "registry sources are missing from this tree ({0}). They ship with the collection; set "
        "GIE_REGISTRY_SOURCES_OPTIONAL=1 only for a tree that deliberately omits tools/.".format(", ".join(missing))
    )


@pytest.fixture(scope="module")
def generator():
    _sources_or_fail()
    spec = importlib.util.spec_from_file_location("gie_generate_binding_table_under_test", str(GENERATOR))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run(*args, cwd):
    """Run the generator as a user would: a fresh interpreter, a chosen working directory."""
    return subprocess.run(
        [sys.executable, str(GENERATOR)] + [str(a) for a in args],
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=False,
    )


# =====================================================================================
# INTEGRITY: needs no sources, so it also runs where tools/ is not present
# =====================================================================================
def test_the_provenance_hash_is_the_hash_of_the_shipped_rows():
    rows = [dict(row) for row in gie_binding_table.BINDING_TABLE]
    recomputed = hashlib.sha256(json.dumps(rows, sort_keys=True, default=list).encode()).hexdigest()
    assert recomputed == gie_binding_table.PROVENANCE_SHA256


def test_the_table_header_states_the_same_hash_as_the_constant():
    header = TABLE.read_text(encoding="utf-8").splitlines()[:6]
    assert "# provenance_sha256 = {0}".format(gie_binding_table.PROVENANCE_SHA256) in header


# =====================================================================================
# SOURCES
# =====================================================================================
def test_the_sources_reproduce_the_versioned_table_byte_for_byte(generator, tmp_path):
    """Run from an unrelated working directory: the command must not depend on where it is started."""
    result = _run("--check", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "{0} bindings".format(len(gie_binding_table.BINDING_TABLE)) in result.stdout
    assert str(ROOT.parent) not in result.stdout  # no absolute path of the machine leaks into the output


def test_regeneration_is_deterministic_and_matches_the_versioned_bytes(generator, tmp_path):
    """Two regenerations from two different working directories are identical to each other AND to the versioned file.

    The comparison with the versioned file is what makes this meaningful: comparing a generated file with itself proves nothing.
    """
    first, second = tmp_path / "first" / "table_a.py", tmp_path / "second" / "table_b.py"
    for target in (first, second):
        target.parent.mkdir()
    one = _run("--regenerate", "--table", first, cwd=first.parent)
    two = _run("--regenerate", "--table", second, cwd=ROOT)
    assert one.returncode == 0 and two.returncode == 0, (one.stderr, two.stderr)
    assert first.read_bytes() == second.read_bytes()
    assert first.read_bytes() == TABLE.read_bytes()


def test_the_legacy_explicit_form_still_produces_the_same_table(generator, tmp_path):
    target = tmp_path / "explicit.py"
    files = generator.slice_paths()
    result = _run(*files, target, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert target.read_bytes() == TABLE.read_bytes()


def test_slices_are_enumerated_by_file_name_and_every_slice_contributes(generator):
    paths = generator.slice_paths()
    names = [os.path.basename(p) for p in paths]
    assert names == sorted(names, key=lambda n: n.encode("utf-8"))
    assert set(names) == set(p.name for p in SLICES.glob("registry_slice_*.yaml"))
    assert len(names) == len(set(names)) >= 1
    for path in paths:
        with open(path, encoding="utf-8") as handle:
            doc = yaml.safe_load(handle)
        rows = doc.get("bindings", []) if isinstance(doc, dict) else doc
        assert rows, "{0} declares no binding".format(os.path.basename(path))


def test_the_generator_has_no_machine_specific_defaults(generator):
    assert generator.DEFAULT_SLICES_DIR == str(SLICES)
    assert Path(generator.DEFAULT_TABLE).resolve() == TABLE
    text = GENERATOR.read_text(encoding="utf-8")
    assert not re.search(r"/Users/|/home/|/private/|/tmp/", text)


def _mutated_copy(tmp_path):
    """A copy of every slice where ONE compiled value of ONE binding differs."""
    copy_dir = tmp_path / "slices_copy"
    shutil.copytree(str(SLICES), str(copy_dir))
    changed = []
    for path in sorted(copy_dir.glob("registry_slice_*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        rows = doc["bindings"] if isinstance(doc, dict) else doc
        for row in rows:
            if row["parent_template"] == MUTATED_PARENT and row["parent_nvpair"] == MUTATED_NVPAIR:
                before = row[MUTATED_FIELD]
                row[MUTATED_FIELD] = "9" if str(before) != "9" else "8"
                changed.append((path.name, before, row[MUTATED_FIELD]))
        if changed and changed[-1][0] == path.name:
            path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    assert len(changed) == 1, changed
    return copy_dir


def test_the_copy_without_changes_passes_so_the_negative_below_is_caused_by_the_alteration(generator, tmp_path):
    control = tmp_path / "control"
    shutil.copytree(str(SLICES), str(control))
    result = _run("--check", "--slices", control, cwd=tmp_path)
    assert result.returncode == 0, result.stderr


def test_an_altered_copy_of_a_relevant_input_is_detected(generator, tmp_path):
    altered = _mutated_copy(tmp_path)
    before = TABLE.read_bytes()
    result = _run("--check", "--slices", altered, cwd=tmp_path)
    assert result.returncode == 1, (result.returncode, result.stdout, result.stderr)
    assert "DIVERGENCE" in result.stderr
    assert MUTATED_FIELD in result.stderr  # the printed diff names the field that moved
    assert "--regenerate" in result.stderr  # and tells the maintainer what to do after reviewing
    assert TABLE.read_bytes() == before  # --check wrote nothing


def test_a_missing_slice_cannot_pass_as_a_reproduction(generator, tmp_path):
    reduced = tmp_path / "reduced"
    shutil.copytree(str(SLICES), str(reduced))
    victim = sorted(reduced.glob("registry_slice_*.yaml"))[0]
    victim.unlink()
    result = _run("--check", "--slices", reduced, cwd=tmp_path)
    assert result.returncode != 0
    assert "OK:" not in result.stdout


def test_the_sources_and_their_documentation_carry_no_private_material():
    _sources_or_fail()
    offenders = []
    for path in sorted(SLICES.glob("registry_slice_*.yaml")) + [README, GENERATOR]:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for label, pattern in PRIVATE:
                if pattern.search(line):
                    offenders.append("{0}:{1}: {2}".format(path.name, number, label))
    assert not offenders, offenders[:10]
