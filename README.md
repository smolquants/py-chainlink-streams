# py-chainlink-streams

> **⚠️ Unofficial Client**: This is an **unofficial** Python SDK for Chainlink Data Streams API. It is not maintained or endorsed by Chainlink Labs or the Chainlink Foundation. Use at your own risk.

> **🤖 AI Implementation**: This Python SDK, including all code, tests, and documentation, was implemented by **Cursor** using the **Auto** agent router. The implementation was generated through AI-assisted development using various language models and has not been manually written by human developers.

A lightweight Python SDK for Chainlink Data Streams API with support for both HTTP REST API and WebSocket connections, including report decoding.

## Features

- ✅ **HTTP REST API** - Fetch latest reports for any feed
- ✅ **WebSocket Streaming** - Real-time report streaming with automatic keepalive
- ✅ **Report Decoding** - Decode hex-encoded reports (v3 schema supported)
- ✅ **Price Conversion** - Convert fixed-point prices to human-readable decimals
- ✅ **Authentication** - HMAC-SHA256 signature generation
- ✅ **Mainnet & Testnet** - Support for both environments

## Installation

```bash
pip install py-chainlink-streams
```

Or with `uv`:

```bash
uv add py-chainlink-streams
```

## Setup

Set your Chainlink Data Streams API credentials as environment variables:

```bash
export CHAINLINK_STREAMS_API_KEY="your-api-key"
export CHAINLINK_STREAMS_API_SECRET="your-api-secret"
```

## Quick Start

### Fetch and Decode a Single Report

```python
from py_chainlink_streams import (
    fetch_single_report,
    decode_report_from_response,
    get_decoded_prices
)

# Fetch latest report for a feed (e.g., BTC/USD)
feed_id = "0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8"
report_response = fetch_single_report(feed_id)

# Decode the hex-encoded fullReport
decoded = decode_report_from_response(report_response['report'])

# Get human-readable prices
prices = get_decoded_prices(decoded)
print(f"BTC/USD Benchmark: ${prices['benchmarkPrice']:.2f}")
print(f"Bid: ${prices['bid']:.2f}, Ask: ${prices['ask']:.2f}")
```

### Stream Reports via WebSocket

```python
import asyncio
from py_chainlink_streams import stream_reports_with_keepalive

def process_report(report):
    from py_chainlink_streams import decode_report_from_response, get_decoded_prices
    
    decoded = decode_report_from_response(report['report'])
    prices = get_decoded_prices(decoded)
    print(f"Timestamp: {prices['observationsTimestamp']}  "
          f"Benchmark: ${prices['benchmarkPrice']:.2f}, "
          f"Bid: ${prices['bid']:.2f}, Ask: ${prices['ask']:.2f}")

feed_ids = ["0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8"]
asyncio.run(stream_reports_with_keepalive(feed_ids, process_report))
```

## Examples

### Fetch and Decode a Single Report (HTTP REST API)

```python
In [1]: from py_chainlink_streams import (
   ...:     fetch_single_report,
   ...:     decode_report_from_response,
   ...:     get_decoded_prices
   ...: )

In [2]: # Fetch latest report for a feed (e.g., BTC/USD)
In [3]: feed_id = "0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8"
In [4]: report_response = fetch_single_report(feed_id)
In [5]: report_response
Out[5]: 
{'report': {'feedID': '0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8',
  'validFromTimestamp': 1767208232,
  'observationsTimestamp': 1767208232,
  'fullReport': '0x00094baebfda9b87680d8e59aa20a3e565126640ee7caeab3cd965e5568b17ee...'}}

In [6]: # Decode the hex-encoded fullReport
In [7]: decoded = decode_report_from_response(report_response['report'])
In [8]: decoded['schemaVersion']
Out[8]: 3

In [9]: # Access decoded data fields
In [10]: decoded['data']
Out[10]: 
{'feedId': '0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8',
 'validFromTimestamp': 1767208232,
 'observationsTimestamp': 1767208232,
 'nativeFee': 7000000000000000,
 'linkFee': 5000000000000000000,
 'expiresAt': 1767216032,
 'benchmarkPrice': 87656352262094430000000,
 'bid': 87656309944707825000000,
 'ask': 87656862768468300000000}

In [11]: # Convert fixed-point prices to human-readable decimals
In [12]: prices = get_decoded_prices(decoded)
In [13]: prices
Out[13]: 
{'observationsTimestamp': 1767208232,
 'benchmarkPrice': 87656.35,
 'bid': 87656.31,
 'ask': 87656.86,
 'midPrice': 87656.59}

In [14]: print(f"BTC/USD Benchmark: ${prices['benchmarkPrice']:.2f}")
BTC/USD Benchmark: $87656.35

In [15]: print(f"Bid: ${prices['bid']:.2f}, Ask: ${prices['ask']:.2f}, Spread: ${prices['ask'] - prices['bid']:.2f}")
Bid: $87656.31, Ask: $87656.86, Spread: $0.55
```

### Stream Reports via WebSocket

```python
In [1]: import asyncio
In [2]: from py_chainlink_streams import stream_reports_with_keepalive

In [3]: # Define callback to process each report
In [4]: def process_report(report):
   ...:     print(f"Received report for Feed ID: {report.get('report', {}).get('feedID', 'unknown')}")
   ...:     # Decode and process the report
   ...:     from py_chainlink_streams import (
   ...:         decode_report_from_response,
   ...:         get_decoded_prices
   ...:     )
   ...:     try:
   ...:         decoded = decode_report_from_response(report['report'])
   ...:         prices = get_decoded_prices(decoded)
   ...:         print(f"Timestamp: {prices['observationsTimestamp']}  Benchmark: ${prices['benchmarkPrice']:.2f}, "
   ...:               f"Bid: ${prices['bid']:.2f}, Ask: ${prices['ask']:.2f}")
   ...:     except Exception as e:
   ...:         print(f"  Error decoding: {e}")

In [5]: # Subscribe to one or more feeds
In [6]: feed_ids = ["0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8"]

In [7]: # Stream reports (runs until interrupted with Ctrl+C)
In [8]: asyncio.run(stream_reports_with_keepalive(feed_ids, process_report))
WebSocket connection established for feeds: ['0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8']
Received report for Feed ID: 0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8
Timestamp: 1767208232  Benchmark: $87656.35, Bid: $87656.31, Ask: $87656.86
Received report for Feed ID: 0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8
Timestamp: 1767208292  Benchmark: $87657.12, Bid: $87656.98, Ask: $87657.45
...
^C
Interrupt signal received, closing connection...
```

### Advanced: Manual WebSocket Connection

```python
In [1]: import asyncio
In [2]: from py_chainlink_streams import (
   ...:     connect_websocket,
   ...:     stream_reports,
   ...:     decode_report_from_response,
   ...:     get_decoded_prices
   ...: )

In [3]: async def main():
   ...:     feed_ids = ["0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8"]
   ...:     
   ...:     # Connect to WebSocket
   ...:     websocket = await connect_websocket(feed_ids)
   ...:     print("Connected!")
   ...:     
   ...:     # Process reports
   ...:     async def handle_report(report):
   ...:         decoded = decode_report_from_response(report['report'])
   ...:         prices = get_decoded_prices(decoded)
   ...:         print(f"Price: ${prices['benchmarkPrice']:.2f}")
   ...:     
   ...:     # Stream for 10 seconds
   ...:     stop_event = asyncio.Event()
   ...:     asyncio.create_task(asyncio.sleep(10)).add_done_callback(lambda _: stop_event.set())
   ...:     await stream_reports(websocket, handle_report, stop_event)
   ...:     await websocket.close()

In [4]: asyncio.run(main())
Connected!
Price: $87656.35
Price: $87657.12
...
```

### Determine Schema Version from Feed ID

```python
In [1]: from py_chainlink_streams import get_schema_version

In [2]: # Feed IDs encode their schema version in the prefix
In [3]: feed_id = "0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8"
In [4]: schema_version = get_schema_version(feed_id)
In [5]: print(f"Feed {feed_id} uses schema version v{schema_version}")
Feed 0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8 uses schema version v3
```

## API Reference

### Client Functions

- `fetch_single_report(feed_id, host=None, timeout=30)` - Fetch latest report via HTTP
- `connect_websocket(feed_ids, host=None, ping_interval=30, pong_timeout=60)` - Connect to WebSocket
- `stream_reports(websocket, callback, stop_event=None)` - Stream reports from WebSocket
- `stream_reports_with_keepalive(feed_ids, callback, ...)` - High-level streaming with keepalive

### Decode Functions

- `decode_report(full_report_hex, feed_id=None, schema_version=None)` - Decode hex-encoded report
- `decode_report_from_response(report_response)` - Decode from API response format
- `get_decoded_prices(decoded_report, decimals=18)` - Convert prices to decimal format
- `get_schema_version(feed_id)` - Determine schema version from feed ID
- `convert_fixed_point_to_decimal(value, decimals=18)` - Convert fixed-point to decimal

### Constants

- `MAINNET_API_HOST` - Mainnet API host
- `MAINNET_WS_HOST` - Mainnet WebSocket host
- `TESTNET_API_HOST` - Testnet API host
- `TESTNET_WS_HOST` - Testnet WebSocket host

## Testing

The SDK includes comprehensive unit tests with **90%+ code coverage**.

### Test Coverage

- ✅ **123 unit tests** covering all core functionality
- ✅ **15+ integration tests** for real mainnet API verification
- ✅ **5 basic integration tests** for functionality verification
- ✅ All modules tested: `client.py`, `report.py`, `decode.py`, `constants.py`
- ✅ Mocked network tests for HTTP and WebSocket operations
- ✅ Real API integration tests with Chainlink mainnet
- ✅ Error handling and edge cases covered

### Running Tests

```bash
# Install test dependencies
uv sync --extra dev

# Run all tests (unit tests only, skips integration by default)
pytest tests/

# Run with coverage report
pytest --cov=py_chainlink_streams --cov-report=html tests/

# Run specific test file
pytest tests/test_client.py

# Run only unit tests (explicitly skip integration)
pytest -m "not integration" tests/
```

### Integration Tests

Integration tests verify the SDK works with the real Chainlink mainnet API. They require valid API credentials and network access.

**Prerequisites:**
- Valid Chainlink Data Streams API credentials (mainnet)
- Network access to Chainlink API endpoints

**Setup:**
```bash
# Set your API credentials
export CHAINLINK_STREAMS_API_KEY="your-api-key"
export CHAINLINK_STREAMS_API_SECRET="your-api-secret"
```

**Running Integration Tests:**
```bash
# Run all integration tests
pytest -m integration tests/test_integration.py -v

# Run all tests including integration tests
pytest tests/ -v

# Run specific integration test class
pytest -m integration tests/test_integration.py::TestFetchSingleReportMainnet -v

# Run specific integration test
pytest -m integration tests/test_integration.py::TestFetchSingleReportMainnet::test_fetch_single_report_mainnet -v
```

**Integration Test Coverage:**
- ✅ HTTP REST API calls to mainnet
- ✅ Real report fetching and validation
- ✅ Report decoding with real data
- ✅ WebSocket connections to mainnet
- ✅ Real-time report streaming
- ✅ End-to-end workflows (fetch → decode → get prices)
- ✅ Error handling with real API
- ✅ Performance and reliability tests

**Note:** Integration tests are automatically skipped if API credentials are not set. They are marked with `@pytest.mark.integration` and can be excluded from CI/CD pipelines if needed.

### Test Structure

```
tests/
├── test_constants.py      # 7 tests - Constants validation
├── test_client.py         # 35 tests - Authentication & WebSocket connection
├── test_decode.py         # 46 tests - Report decoding & price conversion
├── test_report.py         # 30 tests - HTTP fetching & WebSocket streaming
├── test_basic.py          # 5 tests - Basic integration tests
├── test_integration.py    # 15+ tests - Real mainnet API integration tests
└── conftest.py            # Shared fixtures and test utilities
```

See [`tests/TEST_OUTLINE.md`](tests/TEST_OUTLINE.md) for detailed test coverage documentation.

## Official SDKs

Chainlink provides official SDKs for:
- **Go**: [github.com/smartcontractkit/data-streams-sdk/go](https://github.com/smartcontractkit/data-streams-sdk/tree/main/go)
- **Rust**: [github.com/smartcontractkit/data-streams-sdk/rust](https://github.com/smartcontractkit/data-streams-sdk/tree/main/rust)
- **TypeScript**: [github.com/smartcontractkit/data-streams-sdk/ts](https://github.com/smartcontractkit/data-streams-sdk/tree/main/ts)

For production use, consider using the official SDKs which are maintained by Chainlink Labs.

## Documentation

For more details, see the [Chainlink Data Streams documentation](https://docs.chain.link/data-streams/reference/data-streams-api/authentication).

## Disclaimer

This is an **unofficial** Python client for Chainlink Data Streams API. It is:
- Not maintained or endorsed by Chainlink Labs or the Chainlink Foundation
- Provided "as-is" without warranties
- Not audited for security or correctness
- Subject to breaking changes without notice

For production applications, please use the official Chainlink SDKs or conduct your own security audit.

## License

MIT
