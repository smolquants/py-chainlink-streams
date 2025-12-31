# Testing py-chainlink-streams

## Quick Test

After installing dependencies, run:

```bash
uv sync
python3 test_client.py
```

Or test manually:

```python
# Test imports
from py_chainlink_streams import (
    fetch_single_report,
    connect_websocket,
    get_schema_version,
    decode_report_from_response,
    get_decoded_prices,
    convert_fixed_point_to_decimal,
    MAINNET_API_HOST,
    TESTNET_API_HOST,
)

# Test schema version detection
feed_id = '0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8'
version = get_schema_version(feed_id)
assert version == 3

# Test fixed point conversion
price = 87656352262094430000000
decimal_price = convert_fixed_point_to_decimal(price)
assert abs(decimal_price - 87656.35) < 0.01

# Test constants
assert MAINNET_API_HOST == "api.dataengine.chain.link"
assert TESTNET_API_HOST == "api.testnet-dataengine.chain.link"
```

## Package Structure Verification

✅ **Package files:**
- `src/py_chainlink_streams/__init__.py` - Package exports
- `src/py_chainlink_streams/constants.py` - API hosts and defaults
- `src/py_chainlink_streams/client.py` - HTTP & WebSocket client
- `src/py_chainlink_streams/decode.py` - Report decoding

✅ **Dependencies:**
- `eth-abi>=4.0.0` - For ABI decoding
- `eth-utils>=2.0.0` - For hex utilities
- `requests>=2.31.0` - For HTTP requests
- `websockets>=12.0` - For WebSocket connections

✅ **Code structure:**
- All imports are correct
- Module structure is clean
- Functions are properly exported in `__init__.py`

## Manual Testing Checklist

### Basic Functionality (No API credentials needed)
- [x] Package imports successfully
- [x] Constants are accessible
- [x] `get_schema_version()` works
- [x] `convert_fixed_point_to_decimal()` works
- [x] `generate_hmac()` works
- [x] `generate_auth_headers()` works

### With API Credentials (Requires CHAINLINK_STREAMS_API_KEY and CHAINLINK_STREAMS_API_SECRET)
- [ ] `fetch_single_report()` works
- [ ] `connect_websocket()` works
- [ ] `stream_reports_with_keepalive()` works
- [ ] `decode_report_from_response()` works
- [ ] `get_decoded_prices()` works

## Known Issues

- Linter warnings about `requests` and `websockets` imports are expected until dependencies are installed
- Terminal output may not show in some environments - use the test script for verification

