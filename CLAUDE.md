# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **cisco.dcnm** Ansible collection for managing Cisco Nexus Dashboard Fabric Controller (NDFC) and Data Center Network Manager (DCNM). It provides 20+ modules for fabric, network, interface, VRF, image, and service management.

**Key Info:**
- Supports DCNM 11.4(1)+, NDFC 12.2.1-12.2.3, Nexus Dashboard 4.1.1g
- Uses httpapi connection plugin (cisco.dcnm.dcnm)
- Apache 2.0 licensed (not GPL - important for sanity tests)

## Essential Commands

### Linting
```bash
# Run ansible-lint (respects .ansible-lint config)
ansible-lint

# Config excludes .github/ and .git/, skips ignore-errors rule
# YAML lint fixes: Fix hyphens, truthy, indentation, colons, comments
# Do NOT add yaml-lint violations to skip_list - resolve them instead
```

### Testing
```bash
# Sanity tests (from CI/CD)
ansible-test sanity --docker --python <version> -v --color --truncate 0

# Unit tests with coverage
coverage run --source=. -m pytest tests/unit/. -vvvv
coverage report

# Integration test (specific test)
ansible-playbook -i playbooks/roles/<module>/dcnm_hosts.yaml \
  playbooks/roles/<module>/dcnm_tests.yaml \
  -e "testcase=<test_name>"
```

### Build
```bash
ansible-galaxy collection build --output-path <dir>
ansible-galaxy collection install <tarball>
```

## Architecture Patterns

### 1. Module Structure (ALL modules follow this)

```python
# Every module has these state handler classes:
class Common:           # Base class with shared functionality
class Merged(Common):   # Handle state: merged
class Deleted(Common):  # Handle state: deleted
class Query(Common):    # Handle state: query
class Replaced(Common): # Handle state: replaced
# Some modules also have Overridden

def main():
    # 1. Define argument_spec
    # 2. Create AnsibleModule with check_mode support
    # 3. Setup communication stack (Sender → RestSend → ResponseHandler)
    # 4. Route to appropriate state handler based on params["state"]
    # 5. Call task.commit(), build results, return to Ansible
```

**CRITICAL**: Each state class delegates complex logic to specialized classes in `plugins/module_utils/<module>/` (e.g., FabricCreate, NetworkUpdate).

### 2. Communication Stack (Layered Architecture)

```
User Module
    ↓
RestSend (retry/timeout/result building)
    ↓
Sender (dependency injection - enables testing)
    ↓
dcnm_send() or requests library
    ↓
ResponseHandler (parse response, calculate success/failure)
    ↓
Results (collect responses across operations)
```

**Setup Pattern** (in every module's main()):
```python
sender = Sender()
sender.ansible_module = ansible_module

rest_send = RestSend(params)
rest_send.sender = sender
rest_send.response_handler = ResponseHandler()

# State handler uses rest_send:
task = Merged(params)
task.rest_send = rest_send
task.commit()
```

### 3. API Endpoint Pattern

Endpoints live in `plugins/module_utils/common/api/v1/` and mirror REST API structure:

```python
# Example: EpFabricCreate
class EpFabricCreate(Fabrics):
    def __init__(self):
        super().__init__()
        self.required_properties = {"fabric_name", "template_name"}

    @property
    def path(self):
        return f"{self.fabrics}/{self.fabric_name}/{self.template_name}"

    @property
    def verb(self):
        return "POST"

# Usage:
ep = EpFabricCreate()
ep.fabric_name = "MyFabric"
ep.template_name = "Easy_Fabric"
rest_send.path = ep.path
rest_send.verb = ep.verb
```

**Key**: Endpoints are classes with `.path` and `.verb` properties. They validate required properties before returning values.

### 4. Results Collection Pattern

```python
# Track all operations in a task:
results = Results()

# After each operation:
results.action = "fabric_create"
results.response_current = rest_send.response_current
results.result_current = rest_send.result_current
results.diff_current = {"before": {}, "after": {...}}
results.register_task_result()

# Final result:
results.build_final_result()
# Returns: {changed: bool, failed: bool, diff: [...], response: [...], result: [...]}

if True in results.failed:
    ansible_module.fail_json(**results.final_result)
ansible_module.exit_json(**results.final_result)
```

### 5. Properties Decorator Pattern

Common properties added via class decorators:

```python
from ..common.properties import Properties

@Properties.add_rest_send
@Properties.add_results
class FabricCreate:
    """Decorators add type-checked properties for rest_send and results"""
    pass
```

### 6. Module Utils Organization

Each major module has a dedicated package in `plugins/module_utils/`:

```
module_utils/
├── common/              # Shared across all modules
│   ├── rest_send_v2.py
│   ├── sender_*.py
│   ├── response_handler.py
│   ├── results.py
│   ├── properties.py
│   ├── conversion.py
│   ├── exceptions.py
│   └── api/v1/         # API endpoint definitions
├── fabric/             # Fabric module classes
│   ├── create.py
│   ├── delete.py
│   ├── query.py
│   ├── update.py
│   └── verify_playbook_params.py
├── image_upgrade/      # Image upgrade classes
├── network/dcnm/       # DCNM network utilities
└── <module>/           # Per-module specialized classes
```

**Pattern**: Module delegates to these classes. E.g., `dcnm_fabric.py` → `module_utils/fabric/create.py` → `FabricCreate` class.

### 7. HTTPAPI Authentication

`plugins/httpapi/dcnm.py` handles authentication for both DCNM v11 and NDFC v12+:

```python
# Tries methods in order:
# 1. NDFC v12: POST /login with userName/userPasswd/domain
# 2. NDFC v12 legacy: POST /login with username/password/domain
# 3. DCNM v11: POST /rest/logon with basic auth

# Sets connection._auth:
# - DCNM v11: {"Dcnm-Token": token}
# - NDFC v12: {"Authorization": "Bearer {token}", "Cookie": "AuthCookie={token}"}
```

### 8. Integration Test Structure

```
tests/integration/targets/<module_name>/
├── defaults/main.yaml      # Test variables (testcase: "*")
├── meta/main.yaml          # Dependencies (usually empty)
├── tasks/
│   ├── main.yaml          # Includes dcnm.yaml
│   └── dcnm.yaml          # Test discovery (ansible.builtin.find)
└── tests/
    └── *.yaml             # Test playbooks (SETUP → TEST → CLEANUP)
```

**Test Pattern**: Each test has three phases:
1. **SETUP**: Delete existing resources, verify clean state
2. **TEST**: Create/modify resources, verify with assertions
3. **CLEANUP**: Delete test resources

### 9. Validation Patterns

**Module-level** (all modules):
```python
verify = VerifyPlaybookParams()
verify.config_controller = current_config
verify.template = template_data
verify.config_playbook = user_config
verify.commit()  # Raises ValueError/KeyError on failure
```

**Action plugin level** (interface, network, vpc_pair):
- Uses Pydantic schemas in `plugins/action/tests/plugin_utils/pydantic_schemas/`
- Schemas define 100+ fields with validators
- Used for test validation, not module execution

### 10. Logging Pattern

```python
# Setup once in main():
from ..module_utils.common.log_v2 import Log
log = Log()
log.commit()

# Use throughout code:
import logging
self.log = logging.getLogger(f"dcnm.{self.class_name}")
self.log.debug(f"Details: {variable}")
```

## Common Development Tasks

### Adding a New Module

1. Create `plugins/modules/dcnm_<name>.py`:
   - Follow state handler pattern (Common + Merged/Deleted/Query/Replaced)
   - Define DOCUMENTATION, EXAMPLES, RETURN strings
   - Setup communication stack in main()

2. Create supporting classes in `plugins/module_utils/<name>/`:
   - `common.py` - Base class
   - `create.py`, `delete.py`, `query.py`, `update.py` - Operation classes
   - `verify_playbook_params.py` - Validation (if applicable)

3. Add API endpoints in `plugins/module_utils/common/api/v1/<api_area>/`:
   - Define classes with `.path` and `.verb` properties
   - Set `required_properties`

4. Create integration tests in `tests/integration/targets/dcnm_<name>/`:
   - `defaults/main.yaml`, `meta/main.yaml`
   - `tasks/main.yaml`, `tasks/dcnm.yaml`
   - `tests/<test_name>.yaml` (SETUP → TEST → CLEANUP)

5. Create unit tests in `tests/unit/modules/dcnm/test_dcnm_<name>.py`

6. Add playbook examples in `playbooks/roles/dcnm_<name>/`

### Fixing Lint Violations

**YAML in module docstrings**:
- Hyphen spacing: exactly 1 space after `-` in lists
- Truthy values: lowercase `true`/`false` (not `True`/`False`)
- Indentation: must match YAML spec (usually 2-space increments)
- Colons: exactly 1 space after `:`
- Comments: space after `#`

**Python**:
- Black formatter: `black <file>`
- Flake8: `flake8 <file>`

### Sanity Test Ignores

Located in `tests/sanity/ignore-2.15.txt` through `ignore-2.18.txt`:

**Expected ignores**:
```
# Test utilities don't need module docs
plugins/action/tests/**/*.py action-plugin-docs

# Collection uses Apache 2.0, not GPL
plugins/**/*.py validate-modules:missing-gplv3-license
```

**Import errors** should be fixed by adding try/except blocks, not ignoring:
```python
try:
    from pydantic import BaseModel
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    BaseModel = object  # Dummy for import
```

## Key Files to Understand

When understanding module flow, read in this order:

1. `plugins/modules/dcnm_<name>.py` - Module entry point
2. `plugins/module_utils/<name>/common.py` - Shared logic
3. `plugins/module_utils/<name>/<operation>.py` - Specific operations
4. `plugins/module_utils/common/rest_send_v2.py` - Communication layer
5. `plugins/module_utils/common/api/v1/<area>/*.py` - API definitions

For authentication issues:
- `plugins/httpapi/dcnm.py`

For result handling:
- `plugins/module_utils/common/response_handler.py`
- `plugins/module_utils/common/results.py`

## Dependencies

**Runtime** (requirements.txt):
- ansible
- requests

**Development** (test-requirements.txt):
- black==24.3.0
- pytest==7.4.4
- coverage==7.3.4 or 4.5.4
- deepdiff==8.6.1
- pydantic==2.11.4
- yamllint
- flake8

**Note**: Pydantic/DeepDiff must have graceful import fallbacks in code (not hard dependencies).

## CI/CD Matrix

GitHub Actions workflow tests across:
- **Ansible**: 2.15.13, 2.16.14, 2.17.12, 2.18.6
- **Python**: 3.9, 3.10, 3.11 (with version compatibility exclusions)
- **Jobs**: build → sanity (matrix) → unit-tests

## Important Notes

- All modules support `check_mode`
- Results always include: `changed`, `failed`, `diff`, `response`, `result`
- Module sizes: 1500-6000 lines (largest: dcnm_interface ~5800 lines)
- Error messages use `inspect.stack()` for method names
- Collection version in `galaxy.yml` (currently 3.9.0-dev)
- Supports both DCNM v11 (token auth) and NDFC v12 (bearer auth)
