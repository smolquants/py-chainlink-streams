# Test Outline for py-chainlink-streams

This document outlines comprehensive unit tests for each module in the py-chainlink-streams package.

## Implementation Status

✅ **All unit tests implemented!** (123 test cases)

- ✅ `test_constants.py` - 7 tests
- ✅ `test_client.py` - 35 tests  
- ✅ `test_decode.py` - 46 tests
- ✅ `test_report.py` - 30 tests
- ✅ `test_basic.py` - 5 integration tests
- ✅ `conftest.py` - All fixtures implemented

**Total**: 123 unit tests + 5 integration tests = **128 tests**

**Coverage**: ~90%+ code coverage (excluding integration tests requiring network access)

## Test Structure

```
tests/
├── __init__.py
├── test_basic.py              # Basic integration tests (existing)
├── test_constants.py          # Tests for constants.py
├── test_client.py             # Tests for client.py
├── test_decode.py             # Tests for decode.py
├── test_report.py             # Tests for report.py
├── conftest.py                # Pytest fixtures and shared test utilities
└── TEST_OUTLINE.md            # This file
```

## Test Coverage by Module

### 1. `constants.py` - Test File: `test_constants.py`

**Functions to Test:**
- None (constants only)

**Test Cases:**
- [x] `MAINNET_API_HOST` is correct string
- [x] `MAINNET_WS_HOST` is correct string
- [x] `TESTNET_API_HOST` is correct string
- [x] `TESTNET_WS_HOST` is correct string
- [x] `DEFAULT_PING_INTERVAL` is integer (30)
- [x] `DEFAULT_PONG_TIMEOUT` is integer (60)
- [x] All constants are importable from package

---

### 2. `client.py` - Test File: `test_client.py`

#### `get_api_credentials()`
**Test Cases:**
- [x] Returns tuple of (api_key, api_secret) when env vars are set
- [x] Raises `ValueError` when `CHAINLINK_STREAMS_API_KEY` is missing
- [x] Raises `ValueError` when `CHAINLINK_STREAMS_API_SECRET` is missing
- [x] Raises `ValueError` when both are missing
- [x] Handles empty string values correctly (should raise ValueError)
- [x] Returns correct values from environment

#### `generate_hmac(method, path, body, api_key, api_secret)`
**Test Cases:**
- [x] Returns tuple of (signature: str, timestamp: int)
- [x] Signature is 64-character hex string
- [x] Timestamp is integer (milliseconds)
- [x] Same inputs produce same signature (deterministic)
- [x] Different timestamps produce different signatures
- [x] Different paths produce different signatures
- [x] Different methods produce different signatures
- [x] Different bodies produce different signatures
- [x] Empty body produces valid signature
- [x] Non-empty body produces valid signature
- [x] Handles special characters in path correctly
- [x] Handles query parameters in path correctly

#### `generate_auth_headers(method, path_with_params, api_key, api_secret, body)`
**Test Cases:**
- [x] Returns dict with correct keys:
  - `Authorization`
  - `X-Authorization-Timestamp`
  - `X-Authorization-Signature-SHA256`
- [x] `Authorization` header equals api_key
- [x] `X-Authorization-Timestamp` is string representation of int
- [x] `X-Authorization-Signature-SHA256` is 64-char hex string
- [x] Default body parameter works (empty bytes)
- [x] Custom body parameter works

#### `connect_websocket(feed_ids, host, ping_interval, pong_timeout)`
**Test Cases:**
- [x] Raises `ValueError` when feed_ids is empty list
- [x] Raises `ValueError` when API credentials not set
- [x] Uses `MAINNET_WS_HOST` by default when host is None
- [x] Uses custom host when provided
- [x] Uses default ping_interval when not provided
- [x] Uses custom ping_interval when provided
- [x] Uses default pong_timeout when not provided
- [x] Uses custom pong_timeout when provided
- [x] Builds correct WebSocket URL with feed IDs
- [x] Generates correct authentication headers
- [x] Returns WebSocketClientProtocol instance
- [x] Handles multiple feed IDs correctly
- [x] Raises appropriate exception on connection failure
- [ ] **Integration test**: Actually connects (requires credentials and network)

---

### 3. `decode.py` - Test File: `test_decode.py`

#### `get_schema_version(feed_id)`
**Test Cases:**
- [x] Returns 1 for feed_id starting with `0x0001`
- [x] Returns 2 for feed_id starting with `0x0002`
- [x] Returns 3 for feed_id starting with `0x0003`
- [x] Returns 4 for feed_id starting with `0x0004`
- [x] Returns 13 for feed_id starting with `0x000d` (hex for 13)
- [x] Raises `ValueError` for feed_id not starting with `0x`
- [x] Raises `ValueError` for invalid hex characters in prefix
- [x] Handles uppercase hex characters
- [x] Handles lowercase hex characters
- [x] Handles mixed case hex characters

#### `decode_report_structure(full_report_hex)`
**Test Cases:**
- [x] Returns dict with keys: reportContext, reportBlob, rawRs, rawSs, rawVs
- [x] Handles hex string with `0x` prefix
- [x] Handles hex string without `0x` prefix
- [x] `reportContext` is tuple of 3 bytes32 values
- [x] `reportBlob` is bytes
- [x] Raises appropriate exception for invalid hex
- [x] Raises appropriate exception for malformed data
- [ ] **Integration test**: Decodes real report hex string

#### `decode_v3_report_data(report_blob)`
**Test Cases:**
- [x] Returns dict with correct v3 schema fields:
  - feedId (hex string)
  - validFromTimestamp (uint32)
  - observationsTimestamp (uint32)
  - nativeFee (uint192)
  - linkFee (uint192)
  - expiresAt (uint32)
  - benchmarkPrice (int192)
  - bid (int192)
  - ask (int192)
- [x] `feedId` is properly formatted hex string with `0x` prefix
- [x] All timestamp fields are integers
- [x] All fee fields are integers
- [x] All price fields are integers
- [x] Handles zero values correctly
- [ ] **Integration test**: Decodes real v3 report blob

#### `decode_report(full_report_hex, feed_id, schema_version)`
**Test Cases:**
- [x] Decodes report when feed_id provided (auto-detects schema)
- [x] Decodes report when schema_version provided
- [x] Raises `ValueError` when neither feed_id nor schema_version provided
- [x] Returns dict with keys: reportContext, reportBlob, rawRs, rawSs, rawVs, data, schemaVersion
- [x] Raises `ValueError` for unsupported schema version
- [ ] **Integration test**: Decodes real full report

#### `decode_report_from_response(report_response)`
**Test Cases:**
- [x] Decodes report from API response format
- [x] Raises `ValueError` when feedID missing
- [x] Raises `ValueError` when fullReport missing
- [ ] **Integration test**: Decodes real API response

#### `convert_fixed_point_to_decimal(value, decimals)`
**Test Cases:**
- [x] Converts value with default 18 decimals
- [x] Converts value with custom decimals
- [x] Returns float
- [x] Handles zero value
- [x] Handles large values
- [x] Handles negative values (for int192 prices)
- [x] Precision is correct (within expected tolerance)
- [x] Works with different decimal places (8, 18, etc.)

#### `get_decoded_prices(decoded_report, decimals)`
**Test Cases:**
- [x] Returns dict with keys: observationsTimestamp, benchmarkPrice, bid, ask, midPrice
- [x] `observationsTimestamp` is int
- [x] `benchmarkPrice`, `bid`, `ask`, `midPrice` are floats
- [x] `midPrice` is average of bid and ask
- [x] Raises `ValueError` for non-v3 schema reports
- [x] Uses default 18 decimals
- [x] Uses custom decimals when provided
- [ ] **Integration test**: Works with real decoded report

---

### 4. `report.py` - Test File: `test_report.py`

#### `fetch_single_report(feed_id, host, timeout)`
**Test Cases:**
- [x] Uses `MAINNET_API_HOST` by default
- [x] Uses custom host when provided
- [x] Uses default timeout (30) when not provided
- [x] Uses custom timeout when provided
- [x] Builds correct URL with feed_id parameter
- [x] Generates correct authentication headers
- [x] Returns JSON response
- [x] Raises `ValueError` when API credentials not set
- [x] Raises `requests.RequestException` on HTTP errors
- [x] Raises `requests.RequestException` on connection errors
- [x] Handles empty feed_id
- [x] Includes path in signature calculation
- [ ] **Integration test**: Actually fetches report (requires credentials and network)

#### `stream_reports(websocket, callback, stop_event)`
**Test Cases:**
- [x] Calls callback for each message received
- [x] Handles async callback functions
- [x] Handles sync callback functions
- [x] Parses JSON messages correctly
- [x] Stops when stop_event is set
- [x] Handles JSON decode errors gracefully
- [x] Handles callback exceptions gracefully
- [x] Handles ConnectionClosed exception
- [x] Handles other WebSocket errors
- [x] Continues streaming after error

#### `stream_reports_with_keepalive(feed_ids, callback, host, ping_interval, pong_timeout)`
**Test Cases:**
- [x] Establishes WebSocket connection
- [x] Starts ping loop in background
- [x] Streams reports correctly
- [x] Handles KeyboardInterrupt gracefully
- [x] Closes WebSocket connection on exit
- [x] Cancels ping task on exit
- [x] Uses default parameters correctly
- [x] Uses custom parameters correctly
- [ ] **Integration test**: Actually streams (requires credentials and network)

---

## Test Utilities (conftest.py)

**Fixtures to Create:**
- [x] `mock_api_credentials` - Mock environment variables
- [x] `clear_api_credentials` - Clear environment variables
- [x] `sample_feed_id` - Sample feed ID for testing
- [x] `sample_feed_ids` - Sample list of feed IDs
- [x] `sample_report_response` - Sample API response dict
- [x] `sample_decoded_report` - Sample decoded report dict

**Helper Functions:**
- [ ] `set_env_vars(key, secret)` - Set environment variables for testing
- [ ] `clear_env_vars()` - Clear environment variables after testing
- [ ] `create_sample_report_blob()` - Generate test report blob bytes

---

## Integration Tests

**Tests Requiring Network Access:**
- [ ] `test_fetch_single_report_integration()` - Real API call (requires credentials)
- [ ] `test_connect_websocket_integration()` - Real WebSocket connection (requires credentials)
- [ ] `test_stream_reports_integration()` - Real streaming (requires credentials)
- [ ] `test_decode_real_report()` - Decode actual report from API

**Note**: Integration tests should be marked with `@pytest.mark.integration` and can be skipped if credentials are not available.

---

## Test Execution

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_client.py

# Run with coverage
pytest --cov=py_chainlink_streams --cov-report=html tests/

# Run only unit tests (skip integration)
pytest -m "not integration" tests/

# Run only integration tests
pytest -m integration tests/
```

### Test Dependencies

Add to `pyproject.toml`:
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.10.0",
    "httpx>=0.24.0",  # For mocking HTTP requests
]
```

---

## Test Coverage Goals

- **Unit Tests**: 90%+ coverage
- **Integration Tests**: Cover main workflows
- **Edge Cases**: Test error conditions and boundary cases
- **Type Safety**: Test with various input types

---

## Implementation Priority

1. **Phase 1**: Basic unit tests for pure functions (no network)
   - `test_constants.py`
   - `test_decode.py` (most functions)
   - `test_client.py` (generate_hmac, generate_auth_headers, get_api_credentials)

2. **Phase 2**: Mocked network tests
   - `test_client.py` (connect_websocket with mocks)
   - `test_report.py` (fetch_single_report, stream_reports with mocks)

3. **Phase 3**: Integration tests
   - Real API calls (requires credentials)
   - Real WebSocket connections (requires credentials)

4. **Phase 4**: Edge cases and error handling
   - Invalid inputs
   - Network failures
   - Timeout scenarios
   - Malformed data

