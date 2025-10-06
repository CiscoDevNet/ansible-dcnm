# API Endpoint Migration: Inheritance to Composition

This document demonstrates the migration from inheritance-based API endpoints to Pydantic models with composition.

## Benefits of the New Approach

1. **Centralized Path Management**: All base paths in one place (`base_paths.py`)
2. **Type Safety**: Pydantic validation and IDE autocomplete
3. **Testability**: Each endpoint is self-contained and easy to test
4. **Maintainability**: Clear, explicit endpoint definitions
5. **Flexibility**: No deep inheritance chains to navigate

## Side-by-Side Comparison

### Old Approach (Inheritance)

```python
# Deep inheritance chain:
# EpFabricConfigDeploy → Fabrics → Control → Rest → LanFabric → V1 → Api

from ..control import Control

class Fabrics(Control):
    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.fabric_types = FabricTypes()
        self.fabrics = f"{self.control}/fabrics"  # Builds on parent's path
        self._build_properties()

class EpFabricConfigDeploy(Fabrics):
    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.required_properties.add("fabric_name")
        self._build_properties()

    def _build_properties(self):
        super()._build_properties()
        self.properties["force_show_run"] = False
        self.properties["include_all_msd_switches"] = False
        self.properties["switch_id"] = None
        self.properties["verb"] = "POST"

    @property
    def path(self):
        _path = self.path_fabric_name
        _path += "/config-deploy"
        if self.switch_id:
            _path += f"/{self.switch_id}"
        _path += f"?forceShowRun={self.force_show_run}"
        if not self.switch_id:
            _path += f"&inclAllMSDSwitches={self.include_all_msd_switches}"
        return _path

    @property
    def fabric_name(self):
        return self.properties["fabric_name"]

    @fabric_name.setter
    def fabric_name(self, value):
        # Validation logic...
        self.properties["fabric_name"] = value

    # More boilerplate...
```

**Usage:**

```python
endpoint = EpFabricConfigDeploy()
endpoint.fabric_name = "MyFabric"
endpoint.switch_id = ["CHM1234567", "CHM7654321"]
endpoint.force_show_run = True
path = endpoint.path
verb = endpoint.verb
```

**Problems:**

- Must navigate 6 levels of inheritance to understand path building
- Path construction spread across multiple classes
- Heavy boilerplate (logging, properties dict, getters/setters)
- No type hints or validation
- Changing base paths requires editing multiple files

---

### New Approach (Pydantic + Composition with Query Parameters)

```python
from typing import Literal
from pydantic import BaseModel, Field
from ...base_paths import BasePath
from ...query_params import EndpointQueryParams, CompositeQueryParams

class ConfigDeployQueryParams(EndpointQueryParams):
    """Query parameters for config-deploy endpoint."""
    force_show_run: bool = False
    include_all_msd_switches: bool = False

class EpFabricConfigDeploy(BaseModel):
    """Fabric Config Deploy Endpoint"""

    # Path parameters (optional for property-style interface)
    fabric_name: str | None = Field(None, min_length=1)
    switch_id: str | list[str] | None = None

    # Query parameter objects (composition)
    query_params: ConfigDeployQueryParams = Field(default_factory=ConfigDeployQueryParams)

    @property
    def path(self) -> str:
        # Validate required parameters when path is accessed
        if self.fabric_name is None:
            raise ValueError("fabric_name must be set before accessing path")

        segments = [self.fabric_name, "config-deploy"]
        if self.switch_id:
            segments.append(self.switch_id)

        base_path = BasePath.control_fabrics(*segments)

        # Build composite query string
        composite = CompositeQueryParams()
        composite.add(self.query_params)

        query_string = composite.to_query_string()
        if query_string:
            return f"{base_path}?{query_string}"
        return base_path

    @property
    def verb(self) -> Literal["POST"]:
        return "POST"
```

**Usage (Full Property-Style Interface):**

```python
# Create empty endpoint
request = EpFabricConfigDeploy()

# Set path parameters via properties
request.fabric_name = "MyFabric"
request.switch_id = ["CHM1234567", "CHM7654321"]

# Set query parameters via properties
request.query_params.force_show_run = True
request.query_params.include_all_msd_switches = True

path = request.path
verb = request.verb
```

**Benefits:**

- **Consistent Interface**: Both path and query parameters use property-style interface
- **Separation of Concerns**: Path parameters vs query parameters clearly distinguished
- **Type-safe**: Pydantic validation on all parameters
- **Composable**: Query params can be mixed (endpoint-specific + Lucene filtering)
- **Flexible**: Set parameters in any order, validation happens when accessing path
- **Maintainable**: Base paths in `BasePath` class
- **Less code**: ~40 lines vs ~100+ lines (including query param class)

---

## Centralized Path Management

### Old Approach

Base paths scattered across inheritance hierarchy:

```python
# api.py
class Api:
    def __init__(self):
        self.api = "/appcenter/cisco/ndfc/api"

# v1.py
class V1(Api):
    def __init__(self):
        super().__init__()
        self.v1 = f"{self.api}/v1"

# lan_fabric.py
class LanFabric(V1):
    def __init__(self):
        super().__init__()
        self.lan_fabric = f"{self.v1}/lan-fabric"

# rest.py
class Rest(LanFabric):
    def __init__(self):
        super().__init__()
        self.rest = f"{self.lan_fabric}/rest"

# control.py
class Control(Rest):
    def __init__(self):
        super().__init__()
        self.control = f"{self.rest}/control"

# fabrics.py
class Fabrics(Control):
    def __init__(self):
        super().__init__()
        self.fabrics = f"{self.control}/fabrics"
```

To change `/appcenter/cisco/ndfc/api` → you must edit `api.py` (but affects all endpoints).

---

### New Approach

All base paths in ONE location:

```python
# base_paths.py
class BasePath:
    NDFC_API: Final = "/appcenter/cisco/ndfc/api"
    ONEMANAGE: Final = "/onemanage"

    @classmethod
    def control_fabrics(cls, *segments: str) -> str:
        return f"{cls.NDFC_API}/v1/lan-fabric/rest/control/fabrics/{'/'.join(segments)}"
```

To change base path → edit ONE constant in `base_paths.py`.

---

## Migration Strategy

### Phase 1: Create Infrastructure

1. ✅ Create `base_paths.py` with centralized path builders
2. ✅ Create example Pydantic endpoint models in `endpoints.py`

### Phase 2: Gradual Migration

1. Keep old inheritance-based endpoints for backward compatibility
2. Create new Pydantic endpoints alongside old ones
3. Update calling code to use new endpoints incrementally
4. Remove old endpoints when all callers migrated

### Phase 3: Cleanup

1. Remove old inheritance hierarchy (`fabrics.py`, `control.py`, etc.)
2. Update documentation and examples

---

## Testing Examples

### Old Approach Testing

```python
def test_fabric_config_deploy():
    endpoint = EpFabricConfigDeploy()
    endpoint.fabric_name = "MyFabric"
    endpoint.switch_id = "CHM1234567"
    endpoint.force_show_run = True

    expected_path = "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/MyFabric/config-deploy/CHM1234567?forceShowRun=True"
    assert endpoint.path == expected_path
    assert endpoint.verb == "POST"
```

### New Approach Testing

```python
def test_fabric_config_deploy():
    # Create empty endpoint, then set all parameters via properties
    request = EpFabricConfigDeploy()

    # Set path parameters
    request.fabric_name = "MyFabric"
    request.switch_id = "CHM1234567"

    # Set query parameters
    request.query_params.force_show_run = True

    expected_path = "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/MyFabric/config-deploy/CHM1234567?forceShowRun=true&inclAllMSDSwitches=false"
    assert request.path == expected_path
    assert request.verb == "POST"

# Bonus: Pydantic validation testing
def test_validation():
    request = EpFabricConfigDeploy()

    # Validation occurs when accessing path
    with pytest.raises(ValueError, match="fabric_name must be set"):
        _ = request.path  # Fails because fabric_name not set

    # Query params are type-safe via Pydantic
    request.fabric_name = "MyFabric"
    with pytest.raises(ValidationError):
        request.query_params.force_show_run = "yes"  # String not bool
```

---

## Real-World Usage Example

### In a Module or Utility Class

**Old:**

```python
from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.lan_fabric.rest.control.fabrics.fabrics import EpFabricConfigDeploy

def deploy_fabric_config(rest_send, fabric_name, switch_ids):
    endpoint = EpFabricConfigDeploy()
    endpoint.fabric_name = fabric_name
    endpoint.switch_id = switch_ids
    endpoint.force_show_run = True

    rest_send.path = endpoint.path
    rest_send.verb = endpoint.verb
    rest_send.commit()
```

**New:**

```python
from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.lan_fabric.endpoints import EpFabricConfigDeploy

def deploy_fabric_config(rest_send, fabric_name, switch_ids):
    # Create empty endpoint
    request = EpFabricConfigDeploy()

    # Set path parameters
    request.fabric_name = fabric_name
    request.switch_id = switch_ids

    # Set query parameters
    request.query_params.force_show_run = True
    request.query_params.include_all_msd_switches = False

    rest_send.path = request.path
    rest_send.verb = request.verb
    rest_send.commit()
```

---

## Query Parameter Composition

The new approach separates path parameters from query parameters and supports composition:

### Path Parameters vs Query Parameters

```python
# Create empty endpoint
request = EpFabricConfigDeploy()

# Path parameters: set using properties
request.fabric_name = "MyFabric"     # Path parameter
request.switch_id = "CHM1234567"     # Path parameter

# Query parameters: set using properties
request.query_params.force_show_run = True  # Query parameter
```

### Composing Multiple Query Parameter Types

For endpoints that support Lucene-style filtering:

```python
# Create endpoint
request = EpFabricsList()

# Set Lucene filtering parameters
lucene = request.lucene_params
lucene.filter = "name:Prod*"
lucene.max = 100
lucene.sort = "name:asc"

path = request.path
# Result: /api/v1/.../fabrics?filter=name:Prod*&max=100&sort=name:asc
```

### Benefits of Separation

1. **Clear distinction** between path construction and query parameters
2. **Reusable** query parameter classes across endpoints
3. **Extensible** - easy to add new query parameter types (e.g., pagination)
4. **Type-safe** - Pydantic validates both path and query parameters

---

## Summary

| Aspect | Old (Inheritance) | New (Pydantic + Composition) |
|--------|------------------|------------------------------|
| Lines of code | 100+ per endpoint | ~40 per endpoint (with query params) |
| Inheritance depth | 6 levels | 1 level (BaseModel) |
| Type safety | Manual validation | Automatic Pydantic validation |
| Query params | Mixed with path params | Separated via composition |
| Lucene filtering | Not supported | Easy to add via composition |
| IDE support | Limited | Full autocomplete |
| Path changes | Edit multiple files | Edit one file (`base_paths.py`) |
| Testability | Complex setup | Simple instantiation |
| Readability | Must trace inheritance | Self-contained |
| Boilerplate | Heavy (logging, props dict) | Minimal |

**Recommendation**: Use Pydantic + Composition approach for all new endpoints. The property-style interface for query parameters provides the flexibility you requested while maintaining type safety.
