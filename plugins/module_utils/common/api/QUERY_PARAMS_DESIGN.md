# Query Parameters Design: Composition-Based Approach

This document explains the design pattern for separating path parameters, endpoint-specific query parameters, and Lucene-style filtering query parameters using composition.

## Problem Statement

### Requirements

1. **Distinguish** between path parameters (e.g., `fabric_name`, `serial_number`) and query parameters (e.g., `forceShowRun`, `filter`)
2. **Support endpoint-specific query parameters** (e.g., `ticketId`, `waitForModeChange`)
3. **Support generic Lucene-style filtering** (e.g., `filter=name:Foo*&max=100&sort=name:asc`)
4. **Fully property-style interface** for ALL parameters - path and query (consistent interface)
5. **Composable** - allow combining different parameter types without coupling

### The Challenge

In the previous simpler design, we passed everything to the constructor:

```python
# Old approach - everything mixed together
request = EpFabricConfigDeploy(
    fabric_name="MyFabric",        # Path parameter
    switch_id="CHM123",            # Path parameter
    force_show_run=True,           # Query parameter
    filter="name:Foo*"             # Different type of query parameter
)
```

This doesn't distinguish between:

- **Path parameters** (part of the URL path)
- **Endpoint-specific query parameters** (like `forceShowRun`)
- **Generic Lucene filtering** (like `filter`, `max`, `sort`)

---

## Solution: Composition with Separate Parameter Objects

### Design Overview

```text
┌─────────────────────────────────────────────────────────┐
│           EpFabricConfigDeploy                          │
│  (Main endpoint request class)                          │
├─────────────────────────────────────────────────────────┤
│  Path Parameters:                                       │
│  - fabric_name: str                                     │
│  - switch_id: str | None                                │
├─────────────────────────────────────────────────────────┤
│  Query Parameter Objects (composition):                 │
│                                                         │
│  ┌────────────────────────────────────────┐             │
│  │  query_params: ConfigDeployQueryParams │             │
│  │  - force_show_run: bool                │             │
│  │  - include_all_msd_switches: bool      │             │
│  └────────────────────────────────────────┘             │
│                                                         │
│  ┌────────────────────────────────────────┐             │
│  │  lucene_params: LuceneQueryParams      │             │
│  │  - filter: str | None                  │             │
│  │  - max: int | None                     │             │
│  │  - sort: str | None                    │             │
│  └────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────┘
```

### Key Classes

#### 1. `EndpointQueryParams` (Base Class)

Abstract base for endpoint-specific query parameters.

```python
class ConfigDeployQueryParams(EndpointQueryParams):
    force_show_run: bool = False
    include_all_msd_switches: bool = False
```

#### 2. `LuceneQueryParams`

Generic Lucene-style filtering parameters.

```python
class LuceneQueryParams(BaseModel):
    filter: str | None = None
    max: int | None = None
    offset: int | None = None
    sort: str | None = None
    fields: str | None = None
```

#### 3. `CompositeQueryParams`

Composes multiple parameter objects into a single query string.

```python
composite = CompositeQueryParams()
composite.add(endpoint_params)
composite.add(lucene_params)
query_string = composite.to_query_string()
# Result: "forceShowRun=true&filter=name:Foo*&max=100"
```

---

## Usage Examples

### Example 1: Full Property-Style Interface (Recommended)

```python
# Create empty endpoint request
request = EpFabricConfigDeploy()

# Set path parameters using properties
request.fabric_name = "MyFabric"
request.switch_id = "CHM1234567"

# Set endpoint-specific query params using properties
query = request.query_params
query.force_show_run = True
query.include_all_msd_switches = False

# Set Lucene filtering params using properties
lucene = request.lucene_params
lucene.filter = "name:Switch*"
lucene.max = 100
lucene.sort = "name:asc"

# Build the complete path with all query parameters
path = request.path
# Result: /api/v1/.../config-deploy/CHM1234567?forceShowRun=true&inclAllMSDSwitches=false&filter=name:Switch*&max=100&sort=name:asc

verb = request.verb  # "POST"
```

### Example 2: Minimal Property-Style (No Optional Params)

```python
# Create empty endpoint request
request = EpFabricConfigDeploy()

# Set only required path parameter
request.fabric_name = "MyFabric"

# Set query parameters
request.query_params.force_show_run = True
request.lucene_params.filter = "state:deployed"
request.lucene_params.max = 50

path = request.path
```

### Example 3: Endpoint Without Lucene Filtering

```python
# Some endpoints don't need Lucene filtering
request = EpFabricConfigSave()
request.fabric_name = "MyFabric"
request.query_params.ticket_id = "CHG0012345"

path = request.path
# Result: /api/v1/.../config-save?ticketId=CHG0012345
```

### Example 4: Query-Only Endpoint (List with Filtering)

```python
# List all fabrics with Lucene filtering
request = EpFabricsList()

lucene = request.lucene_params
lucene.filter = "name:Prod* AND state:deployed"
lucene.max = 50
lucene.sort = "created:desc"

path = request.path
# Result: /api/v1/.../fabrics?filter=name:Prod*%20AND%20state:deployed&max=50&sort=created:desc
```

---

## Benefits of This Design

### 1. **Clear Separation of Concerns**

- Path parameters: In the main request class
- Endpoint-specific query params: In `query_params` object
- Generic filtering: In `lucene_params` object

### 2. **Type Safety**

```python
request.query_params.force_show_run = "yes"  # ❌ Pydantic validation error
request.query_params.force_show_run = True   # ✅ Type-safe

request.lucene_params.max = -1               # ❌ Validation error (min=1)
request.lucene_params.max = 100              # ✅ Valid
```

### 3. **Composability**

You can mix and match different parameter types:

```python
# Only endpoint params
request.query_params.force_show_run = True

# Only Lucene params
request.lucene_params.filter = "name:Foo*"

# Both together
request.query_params.force_show_run = True
request.lucene_params.filter = "name:Foo*"
```

### 4. **Extensibility**

Adding new parameter types is easy:

```python
# Future: Add pagination parameters
class PaginationQueryParams(EndpointQueryParams):
    page: int = 1
    page_size: int = 50

class MyRequest(BaseModel):
    fabric_name: str | None = Field(None, min_length=1)
    query_params: ConfigDeployQueryParams = Field(default_factory=ConfigDeployQueryParams)
    lucene_params: LuceneQueryParams = Field(default_factory=LuceneQueryParams)
    pagination_params: PaginationQueryParams = Field(default_factory=PaginationQueryParams)

# Usage with property-style interface
request = MyRequest()
request.fabric_name = "MyFabric"
request.pagination_params.page = 2
request.pagination_params.page_size = 100
```

### 5. **Testability**

Each parameter type can be tested independently:

```python
def test_config_deploy_query_params():
    params = ConfigDeployQueryParams(force_show_run=True)
    assert params.to_query_string() == "forceShowRun=true&inclAllMSDSwitches=false"

def test_lucene_query_params():
    params = LuceneQueryParams(filter="name:Foo*", max=100)
    assert params.to_query_string() == "filter=name:Foo*&max=100"

def test_composite():
    endpoint = ConfigDeployQueryParams(force_show_run=True)
    lucene = LuceneQueryParams(filter="name:Foo*")

    composite = CompositeQueryParams()
    composite.add(endpoint).add(lucene)

    assert composite.to_query_string() == "forceShowRun=true&inclAllMSDSwitches=false&filter=name:Foo*"
```

---

## Integrating Your Lucene Filter Class

If you already have a Lucene filter implementation, you can integrate it easily:

```python
# Your existing filter class
class YourLuceneFilter:
    def __init__(self):
        self.max = None
        self.filter = None
        self.sort = None

    def build_query_string(self) -> str:
        # Your existing implementation
        pass

# Adapter to make it work with the composition pattern
class LuceneQueryParamsAdapter(BaseModel):
    _filter_instance: YourLuceneFilter = None

    def __init__(self, filter_instance: YourLuceneFilter):
        super().__init__()
        self._filter_instance = filter_instance

    def to_query_string(self) -> str:
        return self._filter_instance.build_query_string()

    def is_empty(self) -> bool:
        return len(self.to_query_string()) == 0

# Use it in endpoint requests
request = EpFabricsList()
request.lucene_params = LuceneQueryParamsAdapter(your_existing_filter)
```

---

## Comparison: Old vs New Approach

### Old Approach (All Parameters Mixed)

```python
# Problem: Can't tell path params from query params
request = EpFabricConfigDeploy(
    fabric_name="MyFabric",        # Path
    switch_id="CHM123",            # Path
    force_show_run=True,           # Query
    include_all_msd_switches=True, # Query
    filter="name:Foo*",            # Lucene query
    max=100,                       # Lucene query
    sort="name:asc"                # Lucene query
)
```

**Problems:**

- ❌ No distinction between path and query parameters
- ❌ Can't reuse Lucene filtering across endpoints
- ❌ Hard to add new parameter types
- ❌ Everything coupled in one constructor

### New Approach (Composition with Separate Objects + Property-Style)

```python
# Create empty endpoint
request = EpFabricConfigDeploy()

# Path parameters set via properties
request.fabric_name = "MyFabric"
request.switch_id = "CHM123"

# Endpoint-specific query parameters
request.query_params.force_show_run = True
request.query_params.include_all_msd_switches = True

# Lucene filtering parameters
request.lucene_params.filter = "name:Foo*"
request.lucene_params.max = 100
request.lucene_params.sort = "name:asc"

path = request.path
```

**Benefits:**

- ✅ Clear distinction: path vs endpoint query vs Lucene query
- ✅ Fully consistent property-style interface for ALL parameters
- ✅ Lucene filtering is reusable across all endpoints
- ✅ Easy to extend with new parameter types
- ✅ Type-safe with Pydantic validation
- ✅ Flexible: set parameters in any order

---

## Migration Path

### Phase 1: Create Query Parameter Infrastructure

1. ✅ Create `query_params.py` with base classes
2. ✅ Create endpoint-specific param classes (ConfigDeployQueryParams, TicketIdQueryParams, MaintenanceModeQueryParams)
3. ✅ Create `LuceneQueryParams`
4. ✅ Create `CompositeQueryParams`

### Phase 2: Update Endpoint Classes

1. ✅ Add `query_params` field to endpoint requests
2. ✅ Add `lucene_params` field where applicable
3. ✅ Update `path` property to use `CompositeQueryParams`
4. ✅ Convert all path parameters to optional (property-style interface)
5. ✅ Add validation in `path` property for required parameters
6. ✅ All 10 endpoint classes migrated to full property-style interface

### Phase 3: Integrate Your Existing Lucene Filter

1. ⬜ Create adapter for your existing filter class (if needed)
2. ✅ New `LuceneQueryParams` class available for use
3. ⬜ Update calling code to use new interface

---

## Summary

The composition-based query parameter design provides:

1. **Clear separation** between path parameters, endpoint-specific query parameters, and Lucene filtering
2. **Property-style interface** for setting parameters (`request.query_params.force_show_run = True`)
3. **Type safety** through Pydantic validation
4. **Composability** - mix and match parameter types
5. **Reusability** - Lucene filtering works across all endpoints
6. **Extensibility** - easy to add new parameter types

This design allows you to integrate your existing Lucene filter implementation while keeping the codebase clean and maintainable.
