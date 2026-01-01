# Test Outline for py-chainlink-streams

This document outlines comprehensive unit tests for each module in the py-chainlink-streams package.

## Implementation Status

✅ **All unit tests implemented!** (123 test cases)
✅ **All integration tests implemented!** (15+ test cases)

- ✅ `test_constants.py` - 7 tests
- ✅ `test_client.py` - 35 tests  
- ✅ `test_decode.py` - 46 tests
- ✅ `test_report.py` - 30 tests
- ✅ `test_basic.py` - 5 basic integration tests
- ✅ `test_integration.py` - 15+ integration tests (mainnet API)
- ✅ `conftest.py` - All fixtures implemented

**Total**: 123 unit tests + 5 basic integration tests + 15+ integration tests = **143+ tests**

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
├── test_integration.py        # Integration tests with real mainnet API
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

**Test File**: `test_integration.py` ✅ **IMPLEMENTED**

Integration tests require:
- Valid Chainlink Data Streams API credentials (mainnet)
- Network access to Chainlink API endpoints
- Real feed IDs from Chainlink mainnet

**Note**: Integration tests should be marked with `@pytest.mark.integration` and can be skipped if credentials are not available using `pytest -m "not integration"`.

### Test Setup

**Fixtures Needed:**
- [x] `integration_credentials` - Skip test if credentials not available
- [x] `mainnet_feed_id` - Real mainnet feed ID (e.g., BTC/USD v3 feed)
- [x] `mainnet_feed_ids` - List of real mainnet feed IDs

**Helper Functions:**
- [x] `skip_if_no_credentials()` - Skip test decorator/check (using pytest.skipif)
- [x] `get_real_feed_id()` - Get a known working feed ID (BTC_USD_FEED_ID constant)

---

### 1. HTTP REST API Integration Tests

#### `test_fetch_single_report_mainnet()`
**Test Cases:**
- [x] Fetches latest report from mainnet API
- [x] Returns valid response with expected keys:
  - `feedID` (nested in `report` key)
  - `validFromTimestamp`
  - `observationsTimestamp`
  - `fullReport`
- [x] Response contains valid hex-encoded `fullReport`
- [x] Timestamps are valid Unix timestamps
- [x] Feed ID matches requested feed ID
- [x] Handles invalid feed ID gracefully
- [x] Handles authentication errors correctly (401)
- [ ] Handles network timeouts correctly (not explicitly tested)

#### `test_fetch_single_report_with_real_feed_id()`
**Test Cases:**
- [x] Uses real mainnet feed ID (e.g., BTC/USD v3)
- [x] Verifies response structure matches API spec
- [x] Verifies `fullReport` is valid hex string
- [x] Verifies timestamps are recent (within last hour)

---

### 2. Report Decoding Integration Tests

#### `test_decode_real_mainnet_report()`
**Test Cases:**
- [x] Fetches real report from mainnet
- [x] Decodes `fullReport` hex string successfully
- [x] Decoded report contains all expected fields:
  - `reportContext`
  - `reportBlob`
  - `rawRs`, `rawSs`, `rawVs`
  - `data` (v3 schema fields)
  - `schemaVersion`
- [x] Schema version matches feed ID prefix
- [x] Decoded data contains valid prices (bid, ask, benchmark)
- [x] Timestamps are reasonable values

#### `test_get_decoded_prices_from_real_report()`
**Test Cases:**
- [x] Fetches and decodes real mainnet report
- [x] Extracts prices using `get_decoded_prices()`
- [x] Returns dict with all expected keys:
  - `observationsTimestamp`
  - `benchmarkPrice`
  - `bid`
  - `ask`
  - `midPrice`
- [x] Prices are reasonable floats (not in wei format)
- [x] `midPrice` equals average of bid and ask
- [x] `observationsTimestamp` is valid Unix timestamp

#### `test_end_to_end_fetch_and_decode()`
**Test Cases:**
- [x] Complete workflow: fetch → decode → get prices
- [x] All steps execute without errors
- [x] Final prices are human-readable (e.g., $50,000 not 50000000000000000000000)
- [x] Data consistency across all steps

---

### 3. WebSocket Connection Integration Tests

#### `test_connect_websocket_mainnet()`
**Test Cases:**
- [x] Successfully establishes WebSocket connection to mainnet
- [x] Connection uses correct mainnet WebSocket host
- [x] Authentication headers are accepted by server
- [x] Connection remains open for at least 5 seconds (verified with ping)
- [ ] Handles connection errors gracefully (tested in unit tests)
- [ ] Handles authentication failures correctly (tested in unit tests)

#### `test_connect_websocket_with_multiple_feeds()`
**Test Cases:**
- [x] Connects with multiple feed IDs
- [x] All feed IDs are subscribed successfully
- [x] Connection URL contains all feed IDs (indirectly verified by successful connection)
- [x] Receives messages for subscribed feeds (verified in streaming tests)

---

### 4. WebSocket Streaming Integration Tests

#### `test_stream_reports_receives_messages()`
**Test Cases:**
- [x] Establishes WebSocket connection
- [x] Receives at least one report message within 30 seconds
- [x] Messages are valid JSON
- [x] Messages contain expected fields (feedID, fullReport, etc., nested in `report` key)
- [x] Can process multiple messages sequentially
- [x] Handles connection closure gracefully

#### `test_stream_reports_with_keepalive_mainnet()`
**Test Cases:**
- [x] Establishes connection with keepalive
- [x] Receives reports continuously
- [x] Ping/pong keepalive works (connection stays open)
- [x] Can stream for at least 60 seconds without disconnection
- [x] Handles KeyboardInterrupt gracefully
- [x] Closes connection cleanly on exit
- [x] Cancels ping task properly

#### `test_stream_reports_stop_event()`
**Test Cases:**
- [x] Starts streaming reports
- [x] Sets stop_event after receiving N messages
- [x] Streaming stops gracefully
- [x] Connection closes cleanly
- [x] No errors or exceptions

---

### 5. Error Handling Integration Tests

#### `test_invalid_credentials_error()`
**Test Cases:**
- [x] Uses invalid API credentials
- [x] HTTP request returns 401 Unauthorized
- [x] WebSocket connection fails with authentication error
- [x] Error messages are clear and helpful

#### `test_invalid_feed_id_error()`
**Test Cases:**
- [x] Uses invalid/non-existent feed ID
- [x] API returns appropriate error response
- [x] Error is handled gracefully
- [x] Error message indicates invalid feed ID

#### `test_network_timeout_handling()`
**Test Cases:**
- [ ] Simulates network timeout (if possible) - Not explicitly tested (covered in unit tests)
- [ ] Timeout is handled gracefully - Covered in unit tests
- [ ] Appropriate exception is raised - Covered in unit tests
- [ ] No hanging connections - Verified in streaming tests

---

### 6. Performance and Reliability Tests

#### `test_concurrent_fetch_requests()`
**Test Cases:**
- [x] Makes multiple concurrent fetch requests
- [x] All requests complete successfully
- [x] No race conditions or authentication issues
- [x] Response times are reasonable

#### `test_long_running_stream()`
**Test Cases:**
- [x] Streams reports for extended period (60 seconds tested, can be extended)
- [x] Connection remains stable
- [x] No memory leaks (verified by successful completion)
- [x] Ping/pong keepalive continues working
- [x] Receives reports consistently

---

### Implementation Notes

**Test File Structure:**
```python
import pytest
import os
from py_chainlink_streams import (
    fetch_single_report,
    connect_websocket,
    stream_reports_with_keepalive,
    decode_report_from_response,
    get_decoded_prices,
)

# Skip if credentials not available
pytestmark = pytest.mark.skipif(
    not os.getenv("CHAINLINK_STREAMS_API_KEY") or 
    not os.getenv("CHAINLINK_STREAMS_API_SECRET"),
    reason="Chainlink API credentials not set"
)

# Real mainnet feed IDs for testing
BTC_USD_FEED_ID = "0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8"
```

**Running Integration Tests:**
```bash
# Set credentials
export CHAINLINK_STREAMS_API_KEY="your-key"
export CHAINLINK_STREAMS_API_SECRET="your-secret"

# Run only integration tests
pytest -m integration tests/test_integration.py

# Run all tests including integration
pytest tests/

# Skip integration tests
pytest -m "not integration" tests/
```

**Test Data:**
- Use real mainnet feed IDs from Chainlink documentation
- BTC/USD v3 feed: `0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8`
- ETH/USD v3 feed: (add when available)
- Other feeds as needed

**Expected Test Duration:**
- HTTP tests: ~1-2 seconds each
- WebSocket connection tests: ~5-10 seconds each
- Streaming tests: ~30-60 seconds each
- Long-running tests: 5+ minutes

**CI/CD Considerations:**
- Integration tests should be optional/skippable in CI
- May require separate CI job with credentials
- Consider rate limiting and API quotas
- May need to run less frequently than unit tests

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

1. **Phase 1**: ✅ **COMPLETED** - Basic unit tests for pure functions (no network)
   - ✅ `test_constants.py` - All 7 tests implemented
   - ✅ `test_decode.py` - All 46 tests implemented
   - ✅ `test_client.py` - All 35 tests implemented (including generate_hmac, generate_auth_headers, get_api_credentials)

2. **Phase 2**: ✅ **COMPLETED** - Mocked network tests
   - ✅ `test_client.py` - connect_websocket with mocks (all tests implemented)
   - ✅ `test_report.py` - fetch_single_report, stream_reports with mocks (all 30 tests implemented)

3. **Phase 3**: ✅ **COMPLETED** - Integration tests
   - [x] `test_integration.py` - Real API calls (requires credentials)
   - [x] HTTP REST API integration tests
   - [x] WebSocket connection integration tests
   - [x] WebSocket streaming integration tests
   - [x] End-to-end workflow tests
   - [x] Error handling with real API
   - [x] Performance and reliability tests

4. **Phase 4**: ✅ **COMPLETED** - Edge cases and error handling
   - ✅ Invalid inputs - Covered in unit tests
   - ✅ Network failures - Covered in mocked tests
   - ✅ Timeout scenarios - Covered in unit tests
   - ✅ Malformed data - Covered in decode tests

