# Property-Style Interface: Constructor vs Property-Based

This document compares two approaches for setting endpoint parameters and recommends the fully property-based approach for consistency.

## Current Approach: Mixed (Constructor + Properties)

### How It Works (constructor + properties)

**Path parameters** are passed in the constructor, **query parameters** use properties:

```python
# Path parameters in constructor
request = EpFabricConfigDeploy(
    fabric_name="MyFabric",
    switch_id="CHM1234567"
)

# Query parameters via properties
request.query_params.force_show_run = True
request.lucene_params.filter = "name:Foo*"
```

### Pros (path params in constructor)

- ✅ Forces required path parameters to be set upfront
- ✅ Constructor provides immediate validation of path parameters
- ✅ IDE autocomplete shows required parameters in constructor

### Cons (path params in constructor)

- ❌ **Inconsistent interface**: Path params (constructor) vs Query params (properties)
- ❌ **Less flexible**: Can't conditionally set path parameters
- ❌ **Harder to compose**: Can't easily build requests programmatically
- ❌ **Mixed patterns**: Two different ways to set parameters

---

## Proposed Approach: Fully Property-Based

### How It Works (fully property-based)

**ALL parameters** (path and query) use the same property-style interface:

```python
# Create empty endpoint
request = EpFabricConfigDeploy()

# Set path parameters via properties
request.fabric_name = "MyFabric"
request.switch_id = "CHM1234567"

# Set query parameters via properties (same style!)
request.query_params.force_show_run = True
request.lucene_params.filter = "name:Foo*"

# Access path when ready
path = request.path
```

### Pros (path params as properties)

- ✅ **Fully consistent interface**: All parameters use properties
- ✅ **More flexible**: Set parameters in any order
- ✅ **Better composition**: Easy to build requests programmatically
- ✅ **Clearer intent**: Explicit about what's being configured
- ✅ **Same pattern everywhere**: Path, endpoint query, and Lucene query params all work the same way

### Cons (path params as properties)

- ⚠️ **Validation delayed**: Path parameter validation happens when `.path` is accessed
- ⚠️ **More verbose**: Must check for `None` values in path property
- ⚠️ **Less obvious**: Required parameters not enforced by constructor

---

## Side-by-Side Comparison

### Example: Fabric Config Deploy

#### Current Approach (Mixed)

```python
# Create with path params in constructor
request = EpFabricConfigDeploy(
    fabric_name="MyFabric",
    switch_id=["CHM1234567", "CHM7654321"]
)

# Set query params via properties
request.query_params.force_show_run = True
request.query_params.include_all_msd_switches = False

# Add Lucene filtering via properties
request.lucene_params.filter = "serial:FDO*"
request.lucene_params.max = 50

path = request.path
```

#### Property-Based Approach

```python
# Create empty request
request = EpFabricConfigDeploy()

# Set path params via properties
request.fabric_name = "MyFabric"
request.switch_id = ["CHM1234567", "CHM7654321"]

# Set query params via properties (same style!)
request.query_params.force_show_run = True
request.query_params.include_all_msd_switches = False

# Add Lucene filtering via properties (same style!)
request.lucene_params.filter = "serial:FDO*"
request.lucene_params.max = 50

path = request.path
```

---

## Use Cases That Benefit from Full Property-Style

### 1. Conditional Path Parameters

```python
request = EpFabricConfigDeploy()
request.fabric_name = "MyFabric"

# Conditionally add switch_id
if deploy_specific_switch:
    request.switch_id = switch_serial

path = request.path
```

### 2. Building Requests from Configuration

```python
def build_request_from_config(config: dict):
    request = EpFabricConfigDeploy()

    # Set path params from config
    request.fabric_name = config["fabric_name"]
    if "switch_id" in config:
        request.switch_id = config["switch_id"]

    # Set query params from config
    request.query_params.force_show_run = config.get("force_show_run", False)

    # Set filtering from config
    if "filter" in config:
        request.lucene_params.filter = config["filter"]

    return request
```

### 3. Programmatic Request Building

```python
# Build request step by step
request = EpFabricConfigDeploy()

# Step 1: Basic path params
request.fabric_name = get_fabric_name()

# Step 2: Conditional parameters
if switches := get_switch_list():
    request.switch_id = switches

# Step 3: Configuration-specific params
if should_force_show_run():
    request.query_params.force_show_run = True

# Step 4: Apply filtering rules
apply_filters(request.lucene_params)

# Step 5: Get final path
path = request.path
```

---

## Implementation Details

### Validation Strategy

**Current (Constructor):**

```python
class EpFabricConfigDeploy(BaseModel):
    # Required parameters enforced by Pydantic
    fabric_name: str = Field(..., min_length=1)
    switch_id: str | None = None
```

**Property-Based:**

```python
class EpFabricConfigDeploy(BaseModel):
    # All parameters optional, validated when path is accessed
    fabric_name: str | None = Field(None, min_length=1)
    switch_id: str | None = None

    @property
    def path(self) -> str:
        # Validate required parameters
        if self.fabric_name is None:
            raise ValueError("fabric_name must be set before accessing path")

        # Build path...
```

### Error Handling

**Constructor Approach:**

```python
# Error at instantiation
try:
    request = EpFabricConfigDeploy(fabric_name="")  # ❌ Fails immediately
except ValidationError as e:
    print(f"Invalid parameters: {e}")
```

**Property Approach:**

```python
# Error when accessing path
request = EpFabricConfigDeploy()
request.fabric_name = ""  # ❌ Fails during Pydantic validation

try:
    path = request.path  # ❌ Or fails here if not set
except ValueError as e:
    print(f"Missing required parameter: {e}")
```

---

## Comparison Table

| Aspect | Constructor + Properties | Full Property-Style |
|--------|-------------------------|---------------------|
| **Consistency** | ❌ Mixed interface | ✅ Uniform interface |
| **Flexibility** | ⚠️ Limited (must set upfront) | ✅ High (set anytime) |
| **Validation timing** | ✅ Immediate | ⚠️ Delayed (on .path access) |
| **Composition** | ⚠️ Harder | ✅ Easier |
| **IDE support** | ✅ Good (constructor hints) | ✅ Good (property hints) |
| **Required params** | ✅ Enforced by type system | ⚠️ Enforced at runtime |
| **Code clarity** | ⚠️ Two patterns | ✅ One pattern |
| **Learning curve** | ⚠️ Must learn both styles | ✅ One style to learn |

---

## Recommendation

**Use the fully property-based approach** for maximum consistency and flexibility.

### Why?

1. **Consistency is King**: Having one way to set all parameters (path, query, Lucene) makes the API easier to learn and use
2. **Flexibility**: Allows building requests programmatically and conditionally
3. **Composition**: Fits better with the query parameter composition pattern you've already adopted
4. **Future-proof**: Easier to extend with new parameter types

### Migration Path

1. ✅ Create new `endpoints_property_style.py` with property-based approach
2. ✅ Migrate all 10 endpoint classes to property-style interface
3. ✅ All linters passing (black, isort, pylint 10/10, mypy)
4. ✅ Update documentation (MIGRATION_EXAMPLE.md, PROPERTY_STYLE_COMPARISON.md)
5. ✅ Replace old `endpoints.py` with property-style version
6. ⬜ Test thoroughly with real use cases
7. ⬜ Gradually migrate calling code

### Trade-offs to Accept

- **Delayed validation**: Accept that some errors appear when accessing `.path` instead of at instantiation
- **More explicit checks**: Add `if self.fabric_name is None` checks in path properties
- **Documentation**: Clearly document which parameters are required

---

## Example Implementation

See `endpoints.py` for complete working examples with:

- Full property-style interface for all parameters (path and query)
- Proper validation in path properties (raises ValueError if required params not set)
- Comprehensive docstrings with usage examples
- All linters passing (black, isort, pylint 10/10, mypy)
- 10 endpoint classes fully migrated:
  - EpFabricConfigDeploy, EpFabricConfigSave, EpFabricCreate, EpFabricsList
  - EpMaintenanceModeDeploy, EpFabricDelete, EpFabricDetails, EpFabricUpdate
  - EpMaintenanceModeEnable, EpMaintenanceModeDisable

The implementation demonstrates that the property-based approach works well and provides the consistency you're looking for!
