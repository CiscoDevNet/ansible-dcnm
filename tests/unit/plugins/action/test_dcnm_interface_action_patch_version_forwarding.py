"""PR725-PATCH-VERSION-001 -- action-plugin forwarding of the new `patch_version` argument.

The action plugin's existing preprocessing only inspects/mutates `config` (flattening a
`switch` list and renaming a misspelled `profile` key); it never reads or sets
`patch_version`. These cases pin that: the exact top-level value the caller wrote in
`self._task.args` reaches the base `ActionNetworkModule.run()` call unchanged, and an
absent value stays absent -- no implicit default is added at this layer either.

NOT LIVE TESTED IN THIS GENERATION. No controller, Nexus or Jenkins is contacted.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import MagicMock, patch

from ansible_collections.cisco.dcnm.plugins.action import dcnm_interface as action_module


def _bare_action_module():
    return object.__new__(action_module.ActionModule)


def test_patch_version_survives_action_preprocessing_unchanged():
    am = _bare_action_module()
    am._task = MagicMock()
    am._task.args = {
        "fabric": "FAB1",
        "state": "merged",
        "patch_version": "4.3.1.0175006011",
        "config": [
            {"name": "eth1/1", "type": "eth", "switch": ["10.0.0.1"],
             "profile": {"mode": "access"}}
        ],
    }
    captured = {}

    def fake_super_run(self, tmp=None, task_vars=None):
        captured["args"] = dict(self._task.args)
        return {"changed": False}

    with patch.object(action_module.ActionNetworkModule, "run", fake_super_run):
        result = am.run(task_vars={})

    assert captured["args"]["patch_version"] == "4.3.1.0175006011", (
        "the action plugin must forward the exact caller-supplied value, unmodified")
    assert result == {"changed": False}


def test_patch_version_absent_stays_absent_not_defaulted():
    am = _bare_action_module()
    am._task = MagicMock()
    am._task.args = {
        "fabric": "FAB1",
        "state": "merged",
        "config": [
            {"name": "eth1/1", "type": "eth", "switch": ["10.0.0.1"],
             "profile": {"mode": "access"}}
        ],
    }
    captured = {}

    def fake_super_run(self, tmp=None, task_vars=None):
        captured["args"] = dict(self._task.args)
        return {"changed": False}

    with patch.object(action_module.ActionNetworkModule, "run", fake_super_run):
        am.run(task_vars={})

    assert "patch_version" not in captured["args"], (
        "the action layer must not invent a patch_version default when the caller omits it")


def test_patch_version_survives_the_config_none_early_return_path():
    """`config is None` takes the action plugin's early-return branch (query/no interfaces
    named). patch_version must still reach the base run() call on that path too."""
    am = _bare_action_module()
    am._task = MagicMock()
    am._task.args = {
        "fabric": "FAB1",
        "state": "query",
        "patch_version": "4.3.1.0175006011",
        "config": None,
    }
    captured = {}

    def fake_super_run(self, tmp=None, task_vars=None):
        captured["args"] = dict(self._task.args)
        return {"changed": False}

    with patch.object(action_module.ActionNetworkModule, "run", fake_super_run):
        result = am.run(task_vars={})

    assert captured["args"]["patch_version"] == "4.3.1.0175006011"
    assert result == {"changed": False}
