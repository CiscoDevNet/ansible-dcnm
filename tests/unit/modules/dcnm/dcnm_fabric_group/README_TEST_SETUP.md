# FabricGroupCreate Unit Tests - Setup Instructions

## Overview

Comprehensive unit tests have been created for `FabricGroupCreate` following the same pattern used in `test_fabric_create.py`. The tests use the `Sender` class from `sender_file.py` to load mock payloads and controller responses from JSON fixture files.

## Files Created

### Test Files
- **test_fabric_group_create.py** - Main test file with 10 test functions
- **utils.py** - Utility functions, fixtures, and helper classes
- **fixture.py** - JSON fixture loader

### Fixture Files (JSON)
- **payloads_FabricGroupCreate.json** - Mock fabric group payloads
- **responses_FabricGroups.json** - Mock responses from FabricGroups.refresh()
- **responses_FabricGroupCreate.json** - Mock responses from fabric group create API

## Test Coverage

The tests cover the following scenarios:

1. **test_fabric_group_create_00000** - Class initialization
2. **test_fabric_group_create_00020** - Valid payloads setter
3. **test_fabric_group_create_00021** - Invalid payloads (not a list)
4. **test_fabric_group_create_00022** - Empty payload
5. **test_fabric_group_create_00023** - Missing mandatory parameters
6. **test_fabric_group_create_00024** - Payloads not set before commit
7. **test_fabric_group_create_00025** - Invalid FABRIC_TYPE
8. **test_fabric_group_create_00026** - rest_send not set before commit
9. **test_fabric_group_create_00030** - Successful fabric group create (200)
10. **test_fabric_group_create_00031** - Fabric group already exists (skipped)
11. **test_fabric_group_create_00032** - Server error (500)

## What You Need to Gather from the Controller

### 1. FabricGroups Responses (GET)

**Endpoint**: `GET /appcenter/cisco/ndfc/api/v1/onemanage/fabrics`

You need to gather two responses:

#### Empty Response (no fabric groups)
```bash
# For tests: 00030a, 00032a
# Execute on controller when NO fabric groups exist
curl -X GET "https://<controller>/appcenter/cisco/ndfc/api/v1/onemanage/fabrics" \
  -H "Authorization: Bearer <token>"
```

Expected response structure:
```json
{
  "DATA": [],
  "RETURN_CODE": 200,
  "MESSAGE": "OK"
}
```

Update in: `fixtures/responses_FabricGroups.json` → `test_fabric_group_create_00030a` and `test_fabric_group_create_00032a`

#### Response with Existing Fabric Group
```bash
# For test: 00031a
# Execute on controller when fabric group MFG1 exists
curl -X GET "https://<controller>/appcenter/cisco/ndfc/api/v1/onemanage/fabrics" \
  -H "Authorization: Bearer <token>"
```

Expected response structure:
```json
{
  "DATA": [
    {
      "fabricName": "MFG1",
      "fabricType": "MFD",
      "fabricTechnology": "VXLANFabric",
      "templateName": "MSD_Fabric",
      "nvPairs": { ... },
      "seedMember": { ... }
    }
  ],
  "RETURN_CODE": 200,
  "MESSAGE": "OK"
}
```

Update in: `fixtures/responses_FabricGroups.json` → `test_fabric_group_create_00031a`

### 2. FabricGroupCreate Responses (POST)

**Endpoint**: `POST /appcenter/cisco/ndfc/api/v1/onemanage/fabrics`

#### Successful Create (200)
```bash
# For test: 00030a
# POST request to create a fabric group
curl -X POST "https://<controller>/appcenter/cisco/ndfc/api/v1/onemanage/fabrics" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "fabricName": "MFG1",
    "fabricType": "MFD",
    "fabricTechnology": "VXLANFabric",
    "templateName": "MSD_Fabric",
    "nvPairs": {
      "FABRIC_NAME": "MFG1",
      "FABRIC_TYPE": "MFD",
      "BGP_RP_ASN": "65000",
      ...
    },
    "seedMember": {
      "clusterName": "nd-cluster-1",
      "fabricName": "FABRIC-1"
    }
  }'
```

Update in: `fixtures/responses_FabricGroupCreate.json` → `test_fabric_group_create_00030a`

#### Server Error (500)
```bash
# For test: 00032a
# POST request that triggers a server error
# (You may need to intentionally use invalid data)
```

Expected response structure:
```json
{
  "DATA": "Error in validating provided name value pair",
  "RETURN_CODE": 500,
  "MESSAGE": "Internal Server Error"
}
```

Update in: `fixtures/responses_FabricGroupCreate.json` → `test_fabric_group_create_00032a`

## How to Update the Fixtures

1. **Gather the actual controller responses** using the curl commands above
2. **Open the JSON fixture files** in `tests/unit/modules/dcnm/dcnm_fabric_group/fixtures/`
3. **Replace the TODO sections** with actual controller responses
4. **Maintain the structure**: Ensure you keep the RETURN_CODE, METHOD, REQUEST_PATH, MESSAGE, and DATA fields

## Running the Tests

Once you've updated the fixtures with real controller responses:

```bash
# Run all fabric group create tests
pytest tests/unit/modules/dcnm/dcnm_fabric_group/test_fabric_group_create.py -v

# Run a specific test
pytest tests/unit/modules/dcnm/dcnm_fabric_group/test_fabric_group_create.py::test_fabric_group_create_00030 -v

# Run with coverage
coverage run -m pytest tests/unit/modules/dcnm/dcnm_fabric_group/test_fabric_group_create.py
coverage report
```

## Payload Structure

The payload structure in `payloads_FabricGroupCreate.json` follows the fabric group configuration format:

```json
{
  "FABRIC_NAME": "MFG1",
  "FABRIC_TYPE": "MFD",
  "BGP_RP_ASN": 65000,
  "L2_SEGMENT_ID_RANGE": "30000-49000",
  "L3_PARTITION_ID_RANGE": "50000-59000",
  "LOOPBACK100_IP_RANGE": "10.2.0.0/22",
  "DCI_SUBNET_RANGE": "10.33.0.0/16",
  "DCI_SUBNET_TARGET_MASK": 24,
  "seed_member": {
    "clusterName": "nd-cluster-1",
    "fabricName": "FABRIC-1"
  }
}
```

## Notes

- All tests follow the pattern established in `test_fabric_create.py`
- The `Sender` class uses `ResponseGenerator` to yield mock responses
- Tests verify both success and failure scenarios
- Black formatting has been verified (160 char line length)
- All imports are properly structured

## Next Steps

1. Gather actual controller responses as described above
2. Update the JSON fixture files with real data
3. Run the tests to verify they pass
4. Adjust payloads if needed based on actual controller behavior
5. Add additional test cases if you discover edge cases during testing
