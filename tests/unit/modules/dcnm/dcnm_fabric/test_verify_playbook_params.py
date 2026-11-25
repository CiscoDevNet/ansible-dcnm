"""
Unit tests for VerifyPlaybookParams()
"""

# Copyright (c) 2024 Cisco and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# See the following regarding *_fixture imports
# https://pylint.pycqa.org/en/latest/user_guide/messages/warning/redefined-outer-name.html
# Due to the above, we also need to disable unused-import
# Also, fixtures need to use *args to match the signature of the function they are mocking
# pylint: disable=unused-import
# pylint: disable=redefined-outer-name
# pylint: disable=protected-access
# pylint: disable=unused-argument
# pylint: disable=invalid-name
# pylint: disable=too-many-lines

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"


import inspect

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.conversion import ConversionUtils
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.param_info import ParamInfo
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.ruleset import RuleSet
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.verify_playbook_params import VerifyPlaybookParams
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    does_not_raise,
    nv_pairs_verify_playbook_params,
    payloads_verify_playbook_params,
    templates_verify_playbook_params,
)


def test_verify_playbook_params_00010() -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - __init__()
        - _init_properties()
    - ConversionUtils
        - __init__()
    - ParamInfo
        - __init__()

    Summary
    - Verify the class attributes are initialized to expected values.

    Test
    - Class attributes are initialized to expected values
    - Exceptions are not raised
    """
    with does_not_raise():
        instance = VerifyPlaybookParams()
    assert instance.class_name == "VerifyPlaybookParams"
    assert isinstance(instance.conversion, ConversionUtils)
    assert isinstance(instance._param_info, ParamInfo)
    assert isinstance(instance._ruleset, RuleSet)
    assert not instance.bad_params
    assert instance.fabric_name == ""
    assert instance.local_params == {"DEPLOY"}
    assert instance.parameter == ""
    assert instance.params_are_valid == set()
    assert instance._config_playbook == {}
    assert instance._config_controller is None
    assert instance._template == {}


MATCH_OOO20 = r"VerifyPlaybookParams\.config_controller: "
MATCH_OOO20 += r"config_controller must be a dict, or None\."


@pytest.mark.parametrize(
    "value, returned, does_raise, expected",
    [
        ({"foo": "bar"}, {"foo": "bar"}, False, does_not_raise()),
        (None, {}, False, does_not_raise()),
        (10, None, True, pytest.raises(TypeError, match=MATCH_OOO20)),
        ({10, 20}, None, True, pytest.raises(TypeError, match=MATCH_OOO20)),
        ([10, "foo"], None, True, pytest.raises(TypeError, match=MATCH_OOO20)),
        (ParamInfo, None, True, pytest.raises(TypeError, match=MATCH_OOO20)),
    ],
)
def test_verify_playbook_params_00020(value, returned, does_raise, expected) -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - __init__()
        - config_controller.setter
        - config_controller.getter

    Summary
    -   Verify ``TypeError`` is raised when config_controller is not either
        a dict or None.
    """
    with does_not_raise():
        instance = VerifyPlaybookParams()
    with expected:
        instance.config_controller = value
    if not does_raise:
        assert instance.config_controller == returned


MATCH_OOO30 = r"VerifyPlaybookParams\.config_playbook: "
MATCH_OOO30 += r"config_playbook must be a dict\."


@pytest.mark.parametrize(
    "value, returned, does_raise, expected",
    [
        ({"foo": "bar"}, {"foo": "bar"}, False, does_not_raise()),
        (None, None, True, pytest.raises(TypeError, match=MATCH_OOO30)),
        (10, None, True, pytest.raises(TypeError, match=MATCH_OOO30)),
        ({10, 20}, None, True, pytest.raises(TypeError, match=MATCH_OOO30)),
        ([10, "foo"], None, True, pytest.raises(TypeError, match=MATCH_OOO30)),
        (ParamInfo, None, True, pytest.raises(TypeError, match=MATCH_OOO30)),
    ],
)
def test_verify_playbook_params_00030(value, returned, does_raise, expected) -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - __init__()
        - config_playbook.setter
        - config_playbook.getter

    Summary
    -   Verify ``TypeError`` is raised when config_playbook is not a dict.
    """
    with does_not_raise():
        instance = VerifyPlaybookParams()
    with expected:
        instance.config_playbook = value
    if not does_raise:
        assert instance.config_playbook == returned


MATCH_OOO40 = r"VerifyPlaybookParams\.template: "
MATCH_OOO40 += r"template must be a dict\."


@pytest.mark.parametrize(
    "value, returned, does_raise, expected",
    [
        ({"foo": "bar"}, {"foo": "bar"}, False, does_not_raise()),
        (None, None, True, pytest.raises(TypeError, match=MATCH_OOO40)),
        (10, None, True, pytest.raises(TypeError, match=MATCH_OOO40)),
        ({10, 20}, None, True, pytest.raises(TypeError, match=MATCH_OOO40)),
        ([10, "foo"], None, True, pytest.raises(TypeError, match=MATCH_OOO40)),
        (ParamInfo, None, True, pytest.raises(TypeError, match=MATCH_OOO40)),
    ],
)
def test_verify_playbook_params_00040(value, returned, does_raise, expected) -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - __init__()
        - template.setter
        - template.getter

    Summary
    -   Verify ``TypeError`` is raised when template is not a dict.
    """
    with does_not_raise():
        instance = VerifyPlaybookParams()
    with expected:
        instance.template = value
    if not does_raise:
        assert instance.template == returned


def test_verify_playbook_params_00050() -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - template.setter
        - config_playbook.setter
        - config_controller.setter
        - update_decision_set_for_na_rules() happy path
        - commit()

    Template
    -   Easy_Fabric

    Summary
    -   Verify exception is not raised when the playbook contains all
        dependent parameters to satisfy the rule for user parameter.
    -   User parameter: REPLICATION_MODE == "Ingress"
    -   Dependent parameters:
        -   UNDERLAY_IS_V6 != True
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"
    template_key = "easy_fabric"
    with does_not_raise():
        instance = VerifyPlaybookParams()
        instance.template = templates_verify_playbook_params(template_key)
        instance.config_playbook = payloads_verify_playbook_params(key)
        instance.config_controller = nv_pairs_verify_playbook_params(key)
        instance.commit()


def test_verify_playbook_params_00051() -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - validate_commit_parameters()
        - commit()

    Template
    -   Easy_Fabric

    Summary
    -   Verify ``ValueError`` is raised when commit() is called without having
        first set VerifyPlaybookParams().config_controller
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"
    template_key = "easy_fabric"
    with does_not_raise():
        instance = VerifyPlaybookParams()
        instance.template = templates_verify_playbook_params(template_key)
        instance.config_playbook = payloads_verify_playbook_params(key)
    match = r"VerifyPlaybookParams\.config_controller:\s+"
    match += r"config_controller must be set prior to accessing\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_verify_playbook_params_00052() -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - validate_commit_parameters()
        - commit()

    Template
    -   Easy_Fabric

    Summary
    -   Verify ``ValueError`` is raised when commit() is called without having
        first set VerifyPlaybookParams().config_playbook
    """
    template_key = "easy_fabric"
    with does_not_raise():
        instance = VerifyPlaybookParams()
        instance.template = templates_verify_playbook_params(template_key)
        instance.config_controller = None
    match = r"VerifyPlaybookParams\.validate_commit_parameters:\s+"
    match += r"instance\.config_playbook must be set prior to calling commit\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_verify_playbook_params_00053() -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - validate_commit_parameters()
        - commit()

    Template
    -   Easy_Fabric

    Summary
    -   Verify ``ValueError`` is raised when commit() is called without having
        first set VerifyPlaybookParams().template
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"
    with does_not_raise():
        instance = VerifyPlaybookParams()
        instance.config_playbook = payloads_verify_playbook_params(key)
        instance.config_controller = None
    match = r"VerifyPlaybookParams\.validate_commit_parameters:\s+"
    match += r"instance\.template must be set prior to calling commit\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_verify_playbook_params_00060() -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - template.setter
        - config_playbook.setter
        - config_controller.setter
        - update_decision_set_for_na_rules() sad path
        - commit()

    Template
    -   Easy_Fabric

    Summary
    - Verify ``ValueError`` is raised when:
        -   Playbook does not contain adequate dependent parameters to
            satisfy the rule.
        -   Controller configuration does not contain adequate dependent
            parameters to satisfy the rule.
        -   Default values are not such that the rule is satisfied.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"
    template_key = "easy_fabric"
    with does_not_raise():
        instance = VerifyPlaybookParams()
        instance.template = templates_verify_playbook_params(template_key)
        instance.config_playbook = payloads_verify_playbook_params(key)
        instance.config_controller = nv_pairs_verify_playbook_params(key)
    match = r"The following parameter\(value\) combination\(s\) are invalid\s+"
    match += r"and need to be reviewed: Fabric: f1,\s+REPLICATION_MODE"
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_verify_playbook_params_00070() -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - template.setter
        - config_playbook.setter
        - config_controller.setter
        - update_decision_set_for_na_rules() sad path
        - commit()

    Template
    -   Easy_Fabric

    Summary
    - Verify ``ValueError`` is raised when:
        -   Playbook does not contain adequate dependent parameters to
            satisfy the rule.
        -   Caller has indicated that the fabric does not yet exist (i.e.
            has set config_controller to None).
        -   Default values are not such that the rule is satisfied.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"
    template_key = "easy_fabric"
    with does_not_raise():
        instance = VerifyPlaybookParams()
        instance.template = templates_verify_playbook_params(template_key)
        instance.config_playbook = payloads_verify_playbook_params(key)
        instance.config_controller = None
    match = r"The following parameter\(value\) combination\(s\) are invalid\s+"
    match += r"and need to be reviewed: "
    match += r"Fabric: f1,\s+V6_SUBNET_RANGE"
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_verify_playbook_params_00080() -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - template.setter
        - config_playbook.setter
        - config_controller.setter
        - update_decision_set_for_na_rules() sad path
        - commit()

    Template
    -   Easy_Fabric

    Summary
    - Verify ``ValueError`` is raised when:
        -   Playbook does not contain adequate dependent parameters to
            satisfy the rule.
        -   Controller configuration does not contain the relevant dependent
            parameters.
        -   Default values are not such that the rule is satisfied.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"
    template_key = "easy_fabric"
    with does_not_raise():
        instance = VerifyPlaybookParams()
        instance.template = templates_verify_playbook_params(template_key)
        instance.config_playbook = payloads_verify_playbook_params(key)
        instance.config_controller = nv_pairs_verify_playbook_params(key)
    match = r"The following parameter\(value\) combination\(s\) are invalid\s+"
    match += r"and need to be reviewed: "
    match += r"Fabric: f1,\s+V6_SUBNET_RANGE"
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_verify_playbook_params_00090() -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - template.setter
        - config_playbook.setter
        - config_controller.setter
        - verify_parameter_value() sad path
        - commit()

    Template
    -   Easy_Fabric

    Summary
    - Verify ``ValueError`` is raised when:
        -   Playbook contains a parameter with an invalid value.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"
    template_key = "easy_fabric"
    with does_not_raise():
        instance = VerifyPlaybookParams()
        instance.template = templates_verify_playbook_params(template_key)
        instance.config_playbook = payloads_verify_playbook_params(key)
        instance.config_controller = None
    match = r"Parameter: REPLICATION_MODE, Invalid value:\s+"
    match += r"\(INVALID_VALUE\)\.\s+"
    match += r"Valid values: \['Ingress', 'Multicast'\]"
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_verify_playbook_params_00100() -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - template.setter
        - config_playbook.setter
        - config_controller.setter
        - commit()

    Template
    -   Easy_Fabric

    Summary
    - Verify ``ValueError`` is raised when:
        -   Playbook contains a parameter which accepts a boolean but the
            user provided 0 instead of False.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"
    template_key = "easy_fabric"
    with does_not_raise():
        instance = VerifyPlaybookParams()
        instance.template = templates_verify_playbook_params(template_key)
        instance.config_playbook = payloads_verify_playbook_params(key)
        instance.config_controller = None
    match = r"Parameter: ADVERTISE_PIP_BGP, Invalid value:\s+"
    match += r"\(0\)\.\s+"
    match += r"Valid values: \[False, True\]"
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_verify_playbook_params_00110() -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - verify_parameter() off/empty-value exemption
        - commit()

    Template
    -   Easy_Fabric

    Summary
    -   Verify exception is NOT raised when a dependency-gated parameter is
        set to an empty value (a clear), even though its IsShow dependency is
        not satisfied.
    -   User parameter: PER_VRF_LOOPBACK_IP_RANGE == "" (cleared)
    -   Unsatisfied dependency: PER_VRF_LOOPBACK_AUTO_PROVISION == true
        (playbook sets it to false)
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"
    template_key = "easy_fabric"
    with does_not_raise():
        instance = VerifyPlaybookParams()
        instance.template = templates_verify_playbook_params(template_key)
        instance.config_playbook = payloads_verify_playbook_params(key)
        instance.config_controller = None
        instance.commit()


def test_verify_playbook_params_00120() -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - verify_parameter() off/empty-value exemption
        - commit()

    Template
    -   Easy_Fabric

    Summary
    -   Verify exception is NOT raised when a dependency-gated boolean
        parameter is set to false (a disable), even though its IsShow
        dependency is not satisfied.
    -   User parameter: USE_LINK_LOCAL == false (disabled)
    -   Unsatisfied dependency: UNDERLAY_IS_V6 == true (playbook sets it
        to false)
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"
    template_key = "easy_fabric"
    with does_not_raise():
        instance = VerifyPlaybookParams()
        instance.template = templates_verify_playbook_params(template_key)
        instance.config_playbook = payloads_verify_playbook_params(key)
        instance.config_controller = None
        instance.commit()


def test_verify_playbook_params_00130() -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - verify_parameter() off/empty-value exemption (negative)
        - commit()

    Template
    -   Easy_Fabric

    Summary
    -   Verify the exemption does not over-reach: enabling a gated parameter
        (value true) while its IsShow dependency is not satisfied still raises.
    -   User parameter: USE_LINK_LOCAL == true (enabled)
    -   Unsatisfied dependency: UNDERLAY_IS_V6 == true (playbook sets it
        to false)
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"
    template_key = "easy_fabric"
    with does_not_raise():
        instance = VerifyPlaybookParams()
        instance.template = templates_verify_playbook_params(template_key)
        instance.config_playbook = payloads_verify_playbook_params(key)
        instance.config_controller = None
    match = r"The following parameter\(value\) combination\(s\) are invalid\s+"
    match += r"and need to be reviewed: Fabric: f1,\s+USE_LINK_LOCAL"
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_verify_playbook_params_00200() -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - template.setter
        - config_playbook.setter
        - config_controller.setter
        - update_decision_set_for_and_rules() happy path
        - commit()

    Template
    -   Easy_Fabric

    Rule type
    -   AND

    Summary
    - Verify Exception is not raised for AND'ed rule, when:
        -   Playbook contains all requisite parameters and values
            to satisfy the rule.
    - User parameter: V6_SUBNET_TARGET_MASK == 127
    - Dependent parameters:
        - UNDERLAY_IS_V6 == True
        - USE_LINK_LOCAL == False
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"
    template_key = "easy_fabric"
    with does_not_raise():
        instance = VerifyPlaybookParams()
        instance.template = templates_verify_playbook_params(template_key)
        instance.config_playbook = payloads_verify_playbook_params(key)
        instance.config_controller = None
        instance.commit()


def test_verify_playbook_params_00210() -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - template.setter
        - config_playbook.setter
        - config_controller.setter
        - update_decision_set_for_and_rules() sad path
        - commit()

    Template
    -   Easy_Fabric

    Rule type
    -   AND

    Summary
    - Verify ``ValueError`` is raised for AND'ed rule, when:
        -   Playbook contains all requisite parameters to satisfy
            the rule, but the value of one parameter does not satisfy
            the rule.
    - User parameter: V6_SUBNET_TARGET_MASK == 127
    - Dependent parameters:
        - UNDERLAY_IS_V6 == True
        - USE_LINK_LOCAL == True
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"
    template_key = "easy_fabric"
    with does_not_raise():
        instance = VerifyPlaybookParams()
        instance.template = templates_verify_playbook_params(template_key)
        instance.config_playbook = payloads_verify_playbook_params(key)
        instance.config_controller = None

    match = r"The following parameter\(value\) combination\(s\) are invalid\s+"
    match += r"and need to be reviewed: Fabric: f1,\s+"
    match += r"V6_SUBNET_TARGET_MASK\(127\) requires\s+"
    match += r"USE_LINK_LOCAL == False,\s+"
    match += r"USE_LINK_LOCAL valid values: \[False, True\]\.\s+"
    with pytest.raises(ValueError, match=match):
        instance.commit()


@pytest.mark.parametrize(
    "key",
    ["test_verify_playbook_params_00300a", "test_verify_playbook_params_00300b"],
)
def test_verify_playbook_params_00300(key) -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - template.setter
        - config_playbook.setter
        - config_controller.setter
        - update_decision_set_for_or_rules() happy path
        - commit()

    Template
    -   Easy_Fabric

    Rule type
    -   OR

    Summary
    - Verify Exception is not raised for OR'ed rule, when:
        -   Playbook contains all requisite parameters and values
            to satisfy the rule.
    - User parameter: STP_BRIDGE_PRIORITY == 45056
    - Dependent parameters:
        - STP_ROOT_OPTION == rpvst+, mst
    """
    template_key = "easy_fabric"
    with does_not_raise():
        instance = VerifyPlaybookParams()
        instance.template = templates_verify_playbook_params(template_key)
        instance.config_playbook = payloads_verify_playbook_params(key)
        instance.config_controller = None
        instance.commit()


def test_verify_playbook_params_00310() -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - template.setter
        - config_playbook.setter
        - config_controller.setter
        - update_decision_set_for_or_rules() sad path
        - commit()

    Template
    -   Easy_Fabric

    Rule type
    -   OR

    Summary
    - Verify ``ValueError`` is raised for OR'ed rule, when:
        -   Playbook does not contain all requisite parameters and values
            to satisfy the rule.
        -   The caller has indicated that the controller fabric does not exist.
    - User parameter: STP_BRIDGE_PRIORITY == 45056
    - Dependent parameters:
        - STP_ROOT_OPTION == Missing from playbook
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"
    template_key = "easy_fabric"
    with does_not_raise():
        instance = VerifyPlaybookParams()
        instance.template = templates_verify_playbook_params(template_key)
        instance.config_playbook = payloads_verify_playbook_params(key)
        instance.config_controller = None

    match = r"The following parameter\(value\) combination\(s\) are invalid\s+"
    match += r"and need to be reviewed: Fabric: f1,\s+"
    match += r"STP_BRIDGE_PRIORITY\(45056\) requires\s+"
    match += r"STP_ROOT_OPTION to be one of \[mst, rpvst\+\].\s+"
    match += r"STP_ROOT_OPTION valid values:\s+"
    match += r"\['mst', 'rpvst\+', 'unmanaged'\]\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_verify_playbook_params_00400() -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - eval_parameter_rule()

    Summary
    -   Verify ``KeyError`` is raised when rule ``parameter`` key
        is missing.
    """
    with does_not_raise():
        instance = VerifyPlaybookParams()

    rule = {
        "operator": "==",
        "rule_value": "mst",
        "value": "45056",
    }
    match = r"^.*'parameter' not found in rule:.*$"
    with pytest.raises(KeyError, match=match):
        instance.eval_parameter_rule(rule)


def test_verify_playbook_params_00410() -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - eval_parameter_rule()

    Summary
    -   Verify ``KeyError`` is raised when rule ``user_value`` key
        is missing.
    """
    with does_not_raise():
        instance = VerifyPlaybookParams()

    rule = {
        "operator": "==",
        "parameter": "STP_BRIDGE_PRIORITY",
        "value": "mst",
    }
    match = r"^.*'user_value' not found in parameter STP_BRIDGE_PRIORITY rule:.*$"
    with pytest.raises(KeyError, match=match):
        instance.eval_parameter_rule(rule)


def test_verify_playbook_params_00420() -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - eval_parameter_rule()

    Summary
    -   Verify ``KeyError`` is raised when rule ``value`` key
        is missing.
    """
    with does_not_raise():
        instance = VerifyPlaybookParams()

    rule = {
        "operator": "==",
        "parameter": "STP_BRIDGE_PRIORITY",
        "user_value": "45056",
    }
    match = r"^.*'value' not found in parameter STP_BRIDGE_PRIORITY rule:.*$"
    with pytest.raises(KeyError, match=match):
        instance.eval_parameter_rule(rule)


def test_verify_playbook_params_00430() -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - eval_parameter_rule()

    Summary
    -   Verify ``KeyError`` is raised when rule ``operator`` key
        is missing.
    """
    with does_not_raise():
        instance = VerifyPlaybookParams()

    rule = {
        "parameter": "STP_BRIDGE_PRIORITY",
        "user_value": "45056",
        "value": "mst",
    }
    match = r"^.*'operator' not found in parameter STP_BRIDGE_PRIORITY rule:.*$"
    with pytest.raises(KeyError, match=match):
        instance.eval_parameter_rule(rule)


def test_verify_playbook_params_00500(monkeypatch) -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - update_decision_set()

    Summary
    -   Verify update_decision_set() re-raises ``KeyError`` when
        controller_param_is_valid() raises ``KeyError``.
    """

    def mock_controller_param_is_valid(*args):
        msg = "controller_param_is_valid: KeyError"
        raise KeyError(msg)

    with does_not_raise():
        instance = VerifyPlaybookParams()

    monkeypatch.setattr(instance, "controller_param_is_valid", mock_controller_param_is_valid)
    item = {"operator": "==", "parameter": "STP_ROOT_OPTION", "value": "rpvst+"}
    match = r"controller_param_is_valid: KeyError"
    with pytest.raises(KeyError, match=match):
        instance.update_decision_set(item)


def test_verify_playbook_params_00510(monkeypatch) -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - update_decision_set()

    Summary
    -   Verify update_decision_set() re-raises ``KeyError`` when
        playbook_param_is_valid() raises ``KeyError``.
    """

    def mock_playbook_param_is_valid(*args):
        msg = "playbook_param_is_valid: KeyError"
        raise KeyError(msg)

    with does_not_raise():
        instance = VerifyPlaybookParams()
        instance.config_controller = None

    monkeypatch.setattr(instance, "playbook_param_is_valid", mock_playbook_param_is_valid)
    item = {"operator": "==", "parameter": "STP_ROOT_OPTION", "value": "rpvst+"}
    match = r"playbook_param_is_valid: KeyError"
    with pytest.raises(KeyError, match=match):
        instance.update_decision_set(item)


def test_verify_playbook_params_00520(monkeypatch) -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - update_decision_set()

    Summary
    -   Verify update_decision_set() re-raises ``KeyError`` when
        default_param_is_valid() raises ``KeyError``.
    """

    def mock_default_param_is_valid(*args):
        msg = "default_param_is_valid: KeyError"
        raise KeyError(msg)

    def mock_playbook_param_is_valid(*args):
        return True

    with does_not_raise():
        instance = VerifyPlaybookParams()
        instance.config_controller = None

    monkeypatch.setattr(instance, "default_param_is_valid", mock_default_param_is_valid)
    monkeypatch.setattr(instance, "playbook_param_is_valid", mock_playbook_param_is_valid)

    item = {"operator": "==", "parameter": "STP_ROOT_OPTION", "value": "rpvst+"}
    match = r"default_param_is_valid: KeyError"
    with pytest.raises(KeyError, match=match):
        instance.update_decision_set(item)


def test_verify_playbook_params_00600(monkeypatch) -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - update_decision_set_for_or_rules()

    Rule type
    -   OR

    Summary
    -   Verify update_decision_set_for_or_rules() raises ``ValueError`` when
        param_rule contains terms with more than one parameter.

    Notes
        -   OR'd parameters have (thus far) only had one dependent parameter.
            Specifically, STP_BRIDGE_PRIORITY has two rule terms, each with the
            same dependent parameter (STP_ROOT_OPTION) but with different
            values (mst and rstp+).  The code raises a ValueError here to alert
            us if this ever changes.
    """

    def mock_default_param_is_valid(*args):
        return False

    def mock_playbook_param_is_valid(*args):
        return False

    with does_not_raise():
        instance = VerifyPlaybookParams()
        instance.config_controller = None

    monkeypatch.setattr(instance, "default_param_is_valid", mock_default_param_is_valid)
    monkeypatch.setattr(instance, "playbook_param_is_valid", mock_playbook_param_is_valid)

    param_rule = {
        "terms": {
            "or": [
                {"operator": "==", "parameter": "PARAM_1", "value": "foo"},
                {"operator": "==", "parameter": "PARAM_2", "value": "bar"},
            ]
        }
    }
    match = r"VerifyPlaybookParams\.update_decision_set_for_or_rules: "
    match += r"OR'd parameters must have one dependent parameter.\s+"
    match += r"Got: \['PARAM_1', 'PARAM_2'\]\.\s+"
    with pytest.raises(ValueError, match=match):
        instance.update_decision_set_for_or_rules(param_rule)


def test_verify_playbook_params_00700(monkeypatch) -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - controller_param_is_valid()

    Summary
    -   Verify controller_param_is_valid() re-raises ``KeyError`` when
        self.eval_parameter_rule() raises ``KeyError``.
    """

    def mock_eval_parameter_rule(*args):
        msg = "eval_parameter_rule_00700: KeyError."
        raise KeyError(msg)

    item = {"operator": "==", "parameter": "PARAM_1", "value": "foo"}
    config_controller = {"PARAM_1": "foo"}

    with does_not_raise():
        instance = VerifyPlaybookParams()
        instance.config_controller = config_controller

    monkeypatch.setattr(instance, "eval_parameter_rule", mock_eval_parameter_rule)
    match = r"eval_parameter_rule_00700: KeyError\."
    with pytest.raises(KeyError, match=match):
        instance.controller_param_is_valid(item)


def test_verify_playbook_params_00710(monkeypatch) -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - playbook_param_is_valid()

    Summary
    -   Verify playbook_param_is_valid() re-raises ``KeyError`` when
        self.eval_parameter_rule() raises ``KeyError``.
    """

    def mock_eval_parameter_rule(*args):
        msg = "eval_parameter_rule_00710: KeyError."
        raise KeyError(msg)

    item = {"operator": "==", "parameter": "PARAM_1", "value": "foo"}
    config_playbook = {"PARAM_1": "foo"}

    with does_not_raise():
        instance = VerifyPlaybookParams()
        instance.config_playbook = config_playbook

    monkeypatch.setattr(instance, "eval_parameter_rule", mock_eval_parameter_rule)
    match = r"eval_parameter_rule_00710: KeyError\."
    with pytest.raises(KeyError, match=match):
        instance.playbook_param_is_valid(item)


def test_verify_playbook_params_00720(monkeypatch) -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - default_param_is_valid()

    Summary
    -   Verify default_param_is_valid() re-raises ``KeyError`` when
        self.eval_parameter_rule() raises ``KeyError``.
    """

    def mock_eval_parameter_rule(*args):
        msg = "eval_parameter_rule_00720: KeyError."
        raise KeyError(msg)

    def mock_param_info_parameter(*args):
        return {"default": "foo"}

    with does_not_raise():
        instance = VerifyPlaybookParams()
        instance.config_playbook = {"PARAM_2": "foo"}
        instance.config_controller = None

    monkeypatch.setattr(instance, "eval_parameter_rule", mock_eval_parameter_rule)
    monkeypatch.setattr(instance._param_info, "parameter", mock_param_info_parameter)

    item = {"operator": "==", "parameter": "PARAM_1", "value": "foo"}

    match = r"eval_parameter_rule_00720: KeyError\."
    with pytest.raises(KeyError, match=match):
        instance.default_param_is_valid(item)


def test_verify_playbook_params_00800(monkeypatch) -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - default_param_is_valid()

    Summary
    -   Verify default_param_is_valid() returns None when the parameter
        has no default value.
    """

    def mock_param_info_parameter(*args):
        return {"default_key_is_missing": "foo"}

    with does_not_raise():
        instance = VerifyPlaybookParams()
        instance.config_playbook = {"PARAM_2": "foo"}
        instance.config_controller = None

    monkeypatch.setattr(instance._param_info, "parameter", mock_param_info_parameter)

    item = {"operator": "==", "parameter": "PARAM_1", "value": "foo"}

    with does_not_raise():
        value = instance.default_param_is_valid(item)
    assert value is None


@pytest.mark.parametrize(
    "key",
    ["test_verify_playbook_params_00900a", "test_verify_playbook_params_00900b"],
)
def test_verify_playbook_params_00900(key) -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - template.setter
        - config_playbook.setter
        - config_controller.setter
        - update_decision_set_for_multi_rules() happy path
        - commit()

    Template
    -   Easy_Fabric_eBGP

    Rule type
    -   Multi

    Summary
    - Verify Exception is not raised for Multi rule, when:
        -   Playbook contains all requisite parameters and values to satisfy the rule.
    - User parameter: L3VNI_MCAST_GROUP == "239.1.1.1"
    - Dependent parameters (these are OR'ed):
        - ENABLE_TRM == true and UNDERLAY_IS_V6 != true
        - ENABLE_TRMv6 == true and UNDERLAY_IS_V6 != true
    """
    template_key = "easy_fabric_ebgp"
    with does_not_raise():
        instance = VerifyPlaybookParams()
        instance.template = templates_verify_playbook_params(template_key)
        instance.config_playbook = payloads_verify_playbook_params(key)
        instance.config_controller = None
        instance.commit()


@pytest.mark.parametrize(
    "key",
    ["test_verify_playbook_params_00910a", "test_verify_playbook_params_00910b"],
)
def test_verify_playbook_params_00910(key) -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - template.setter
        - config_playbook.setter
        - config_controller.setter
        - update_decision_set_for_multi_rules() sad path
        - commit()

    Template
    -   Easy_Fabric_eBGP

    Rule type
    -   Multi

    Summary
    - Verify Exception is raised for Multi rule, when:
        -   Playbook does not contain all requisite parameters and values to satisfy the rule.
    - User parameter: L3VNI_MCAST_GROUP == "239.1.1.1"
    - Dependent parameters (these are OR'ed):
        - ENABLE_TRM == true and UNDERLAY_IS_V6 != true
        - ENABLE_TRMv6 == true and UNDERLAY_IS_V6 != true
    """
    template_key = "easy_fabric_ebgp"
    match = r"The following parameter\(value\) combination\(s\) are invalid and need to be reviewed:"
    with pytest.raises(ValueError, match=match):
        instance = VerifyPlaybookParams()
        instance.template = templates_verify_playbook_params(template_key)
        instance.config_playbook = payloads_verify_playbook_params(key)
        instance.config_controller = None
        instance.commit()


def _verify_easy_fabric(playbook_params, controller_params):
    """
    Run VerifyPlaybookParams().commit() with the easy_fabric template.
    """
    instance = VerifyPlaybookParams()
    instance.template = templates_verify_playbook_params("easy_fabric")
    instance.config_playbook = {"FABRIC_NAME": "f1", "FABRIC_TYPE": "VXLAN_EVPN", **playbook_params}
    instance.config_controller = controller_params
    instance.commit()


@pytest.mark.parametrize(
    "playbook_params, controller_params",
    [
        ({"ENABLE_PVLAN": True, "default_pvlan_sec_network": "Pvlan_Secondary_Network"}, None),
        (
            {"ENABLE_PVLAN": True, "default_pvlan_sec_network": "Pvlan_Secondary_Network"},
            {"default_pvlan_sec_network": "Custom_Secondary"},
        ),
        (
            {"ENABLE_PVLAN": True, "default_pvlan_sec_network": "Custom_Secondary"},
            {"default_pvlan_sec_network": "Custom_Secondary"},
        ),
        ({"default_network": "Default_Network_Universal"}, None),
        ({"default_network": "Service_Network_Universal"}, {"default_network": "Service_Network_Universal"}),
        ({"ENABLE_PVLAN": True}, None),
    ],
)
def test_verify_playbook_params_01000(playbook_params, controller_params) -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - verify_parameter_value()
        - known_dynamic_choice_values()
        - commit()

    Template
    -   Easy_Fabric

    Summary
    -   Verify a parameter whose Enum is a ``%TEMPLATES.<name>`` marker
        accepts the template default, and the value already set on the
        controller for this fabric.
    -   Verify omitting the parameter is still accepted.
    """
    with does_not_raise():
        _verify_easy_fabric(playbook_params, controller_params)


@pytest.mark.parametrize(
    "playbook_params, controller_params",
    [
        ({"ENABLE_PVLAN": True, "default_pvlan_sec_network": "%TEMPLATES.pvlanSecNetwork"}, None),
        (
            {"ENABLE_PVLAN": True, "default_pvlan_sec_network": "%TEMPLATES.pvlanSecNetwork"},
            {"default_pvlan_sec_network": "%TEMPLATES.pvlanSecNetwork"},
        ),
        ({"ENABLE_PVLAN": True, "default_pvlan_sec_network": "Custom_Secondary"}, None),
        (
            {"ENABLE_PVLAN": True, "default_pvlan_sec_network": "Other_Secondary"},
            {"default_pvlan_sec_network": "Custom_Secondary"},
        ),
        ({"ENABLE_PVLAN": True, "default_pvlan_sec_network": ""}, None),
        ({"ENABLE_PVLAN": True, "default_pvlan_sec_network": " Pvlan_Secondary_Network"}, None),
        ({"ENABLE_PVLAN": True, "default_pvlan_sec_network": 5}, None),
        ({"ENABLE_PVLAN": True, "default_pvlan_sec_network": True}, None),
        ({"default_network": "Service_Network_Universal"}, None),
    ],
)
def test_verify_playbook_params_01010(playbook_params, controller_params) -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - verify_parameter_value()
        - known_dynamic_choice_values()
        - commit()

    Template
    -   Easy_Fabric

    Summary
    -   Verify a parameter whose Enum is a ``%TEMPLATES.<name>`` marker
        rejects the literal marker (also when the controller holds it),
        a template name that is neither the template default nor the
        controller value, an empty value, a whitespace-padded value, and
        non-string values.
    """
    match = r"VerifyPlaybookParams\.verify_parameter_value:\s+"
    match += r"Parameter: (default_pvlan_sec_network|default_network),\s+"
    match += r"Invalid value: .*\. The template also allows the controller "
    match += r"templates in \['%TEMPLATES\.(pvlanSecNetwork|network)'\]"
    with pytest.raises(ValueError, match=match):
        _verify_easy_fabric(playbook_params, controller_params)


@pytest.mark.parametrize("enable_pvlan", [False, None])
def test_verify_playbook_params_01020(enable_pvlan) -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - verify_parameter_value()
        - verify_parameter()
        - commit()

    Template
    -   Easy_Fabric

    Summary
    -   Verify the template default of default_pvlan_sec_network passes
        the value check and is then subject to its dependency rule
        (ENABLE_PVLAN == true), with ENABLE_PVLAN false or omitted.
    """
    playbook_params = {"default_pvlan_sec_network": "Pvlan_Secondary_Network"}
    if enable_pvlan is not None:
        playbook_params["ENABLE_PVLAN"] = enable_pvlan
    match = r"The following parameter\(value\) combination\(s\) are invalid and need to be reviewed:\s+"
    match += r"Fabric: f1, default_pvlan_sec_network\(Pvlan_Secondary_Network\) requires ENABLE_PVLAN"
    with pytest.raises(ValueError, match=match):
        _verify_easy_fabric(playbook_params, None)


def test_verify_playbook_params_01030() -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - verify_parameter_value()
        - commit()

    Template
    -   Easy_Fabric

    Summary
    -   Verify a static Enum still rejects a ``%TEMPLATES.<name>`` value
        with the unchanged error message.
    """
    match = r"VerifyPlaybookParams\.verify_parameter_value:\s+"
    match += r"Parameter: REPLICATION_MODE,\s+"
    match += r"Invalid value: \(%TEMPLATES\.network\)\.\s+"
    match += r"Valid values: \['Ingress', 'Multicast'\]$"
    with pytest.raises(ValueError, match=match):
        _verify_easy_fabric({"REPLICATION_MODE": "%TEMPLATES.network"}, None)


@pytest.mark.parametrize(
    "default, controller_value, expected",
    [
        ("Pvlan_Secondary_Network", None, ["Pvlan_Secondary_Network"]),
        ("Pvlan_Secondary_Network", "Custom", ["Pvlan_Secondary_Network", "Custom"]),
        ("Pvlan_Secondary_Network", "Pvlan_Secondary_Network", ["Pvlan_Secondary_Network"]),
        (None, "Custom", ["Custom"]),
        ("", "", []),
        ("%TEMPLATES.pvlanSecNetwork", "%TEMPLATES.pvlanSecNetwork", []),
        (" Padded", "Padded ", []),
        (1, True, []),
    ],
)
def test_verify_playbook_params_01040(default, controller_value, expected) -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - known_dynamic_choice_values()

    Summary
    -   Verify known_dynamic_choice_values() returns the template default
        and the controller value, once each, and skips empty, non-string,
        whitespace-padded and ``%``-prefixed values.
    """
    instance = VerifyPlaybookParams()
    instance.parameter = "default_pvlan_sec_network"
    controller_params = {}
    if controller_value is not None:
        controller_params["default_pvlan_sec_network"] = controller_value
    instance.config_controller = controller_params
    assert instance.known_dynamic_choice_values({"default": default}) == expected
