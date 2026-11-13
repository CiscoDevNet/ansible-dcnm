"""Load the registry generator and its slice rows from this tree."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import importlib.util
from pathlib import Path
from ansible_collections.cisco.dcnm.plugins.module_utils import gie_binding_table


# compile_rows() validates slice rows; BINDING_TABLE is its output. Three schema fields
# -- presence_model, emit_when, parent_resolution -- are documentation-only and FIELDS omits
# them from the table, so a table row is not a valid compiler input.
#
# Reusing output as input only worked while the generator did not validate the schema.
# Validation moved into the generator after two separate checkers had gone unused for four
# batches. Compiler tests now restore those three fields to exercise compilation rules
# (allowlists, duplicates, profile_key), not schema validation, which has separate tests.
#
# Adding the fields to FIELDS instead would change the binding table and enlarge the
# runtime artifact with metadata that no runtime consumer reads.
def _as_slice_rows(rows):
    """Restore slice-only schema fields to binding table rows for compiler tests."""
    return [
        dict(r, presence_model="two_axis", emit_when="explicit_only",
             parent_resolution="desired_parent")
        for r in rows
    ]


def _load_generator():
    path = (
        Path(gie_binding_table.__file__).resolve().parents[2]
        / "tools"
        / "gie_generate_binding_table.py"
    )
    spec = importlib.util.spec_from_file_location("gie_table_generator_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
