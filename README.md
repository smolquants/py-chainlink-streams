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
from py_chainlink_streams import ChainlinkClient, ChainlinkConfig

# Create client
import os
config = ChainlinkConfig(
    api_key=os.getenv("CHAINLINK_STREAMS_API_KEY"),
    api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET")
)
client = ChainlinkClient(config)

# Fetch latest report for a feed (e.g., BTC/USD)
feed_id = "0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8"
report = client.get_latest_report(feed_id)

# Decode the hex-encoded fullReport
decoded = report.decode()

# Get human-readable prices
prices = report.get_decoded_prices()
print(f"BTC/USD Benchmark: ${prices['benchmarkPrice']:.2f}")
print(f"Bid: ${prices['bid']:.2f}, Ask: ${prices['ask']:.2f}")
print(f"Timestamp: {prices['observationsTimestamp']}")
```

### Stream Reports via WebSocket

```python
import asyncio
from py_chainlink_streams import ChainlinkClient, ChainlinkConfig

async def process_report(report_data):
    # report_data is a dict from WebSocket
    # Create ReportResponse from it and decode
    from py_chainlink_streams import ReportResponse
    
    report = ReportResponse.from_dict(report_data)
    prices = report.get_decoded_prices()
    print(f"Timestamp: {prices['observationsTimestamp']}  "
          f"Benchmark: ${prices['benchmarkPrice']:.2f}, "
          f"Bid: ${prices['bid']:.2f}, Ask: ${prices['ask']:.2f}")

# Create client and stream
import os
config = ChainlinkConfig(
    api_key=os.getenv("CHAINLINK_STREAMS_API_KEY"),
    api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET")
)
client = ChainlinkClient(config)

feed_ids = ["0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8"]
asyncio.run(client.stream(feed_ids, process_report))
```

## Client API (Recommended)

For a more object-oriented approach similar to the Go SDK, use the `ChainlinkClient` class:

```python
import os
from py_chainlink_streams import ChainlinkClient, ChainlinkConfig

# Create config from environment variables
config = ChainlinkConfig(
    api_key=os.getenv("CHAINLINK_STREAMS_API_KEY"),
    api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET")
)

# Or create config explicitly
config = ChainlinkConfig(
    api_key="your-api-key",
    api_secret="your-api-secret",
    api_host="api.dataengine.chain.link",  # Optional, defaults to mainnet
    ws_host="ws.dataengine.chain.link",     # Optional, defaults to mainnet
    timeout=30,                              # Optional, HTTP timeout
    ping_interval=30,                       # Optional, WebSocket ping interval
    pong_timeout=60                          # Optional, WebSocket pong timeout
)

# Create client
client = ChainlinkClient(config)

# Get all available feeds
feeds = client.get_feeds()
print(f"Available feeds: {len(feeds)}")
for feed in feeds:
    print(f"  - {feed.id}: {feed.name}")

# Get latest report
report = client.get_latest_report("0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8")
print(f"Latest report timestamp: {report.observations_timestamp}")

# Get reports for multiple feeds at a specific timestamp
import time
timestamp = int(time.time()) - 3600  # 1 hour ago
reports = client.get_reports(
    feed_ids=["0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8"],
    timestamp=timestamp
)
print(f"Found {len(reports)} reports at timestamp {timestamp}")

# Paginate through reports
page = client.get_report_page(
    feed_id="0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8",
    start_timestamp=timestamp
)
print(f"Page contains {len(page.reports)} reports")
print(f"Next page timestamp: {page.next_page_timestamp}")

# Stream reports with status callbacks
async def on_status(is_connected: bool, host: str, origin: str):
    if is_connected:
        print(f"Connected to {host}")
    else:
        print(f"Disconnected from {host}")

async def process_report(report_data):
    print(f"Received report: {report_data}")

await client.stream_with_status_callback(
    feed_ids=["0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8"],
    callback=process_report,
    status_callback=on_status
)
```

## Examples

### Fetch and Decode a Single Report (HTTP REST API)

```python
In [1]: from py_chainlink_streams import ChainlinkClient, ChainlinkConfig, ReportResponse

In [2]: # Create client
In [3]: import os
In [4]: config = ChainlinkConfig(
   ...:     api_key=os.getenv("CHAINLINK_STREAMS_API_KEY"),
   ...:     api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET")
   ...: )
In [5]: client = ChainlinkClient(config)

In [5]: # Fetch latest report for a feed (e.g., BTC/USD)
In [6]: feed_id = "0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8"
In [7]: report = client.get_latest_report(feed_id)
In [8]: report
Out[8]: <ReportResponse feed_id='0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8' ...>

In [9]: # Access report attributes
In [10]: report.feed_id
Out[10]: '0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8'

In [11]: report.observations_timestamp
Out[11]: 1767208232

In [12]: # Decode the hex-encoded fullReport
In [13]: decoded = report.decode()
In [14]: decoded['schemaVersion']
Out[14]: 3

In [15]: # Access decoded data fields
In [16]: decoded['data']
Out[16]: 
{'feedId': '0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8',
 'validFromTimestamp': 1767208232,
 'observationsTimestamp': 1767208232,
 'nativeFee': 7000000000000000,
 'linkFee': 5000000000000000000,
 'expiresAt': 1767216032,
 'benchmarkPrice': 87656352262094430000000,
 'bid': 87656309944707825000000,
 'ask': 87656862768468300000000}

In [17]: # Convert fixed-point prices to human-readable decimals
In [18]: prices = report.get_decoded_prices()
In [19]: prices
Out[19]: 
{'observationsTimestamp': 1767208232,
 'benchmarkPrice': 87656.35,
 'bid': 87656.31,
 'ask': 87656.86,
 'midPrice': 87656.59}

In [20]: print(f"BTC/USD Benchmark: ${prices['benchmarkPrice']:.2f}")
BTC/USD Benchmark: $87656.35

In [21]: print(f"Bid: ${prices['bid']:.2f}, Ask: ${prices['ask']:.2f}, Spread: ${prices['ask'] - prices['bid']:.2f}")
Bid: $87656.31, Ask: $87656.86, Spread: $0.55
```

### Stream Reports via WebSocket

```python
In [1]: import asyncio
In [2]: from py_chainlink_streams import ChainlinkClient, ChainlinkConfig, ReportResponse

In [3]: # Create client
In [4]: import os
In [5]: config = ChainlinkConfig(
   ...:     api_key=os.getenv("CHAINLINK_STREAMS_API_KEY"),
   ...:     api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET")
   ...: )
In [6]: client = ChainlinkClient(config)

In [6]: # Define callback to process each report
In [7]: async def process_report(report_data):
   ...:     # report_data is a dict from WebSocket
   ...:     report = ReportResponse.from_dict(report_data)
   ...:     prices = report.get_decoded_prices()
   ...:     print(f"Feed ID: {report.feed_id}")
   ...:     print(f"Timestamp: {prices['observationsTimestamp']}  Benchmark: ${prices['benchmarkPrice']:.2f}, "
   ...:           f"Bid: ${prices['bid']:.2f}, Ask: ${prices['ask']:.2f}")

In [8]: # Subscribe to one or more feeds
In [9]: feed_ids = ["0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8"]

In [10]: # Stream reports (runs until interrupted with Ctrl+C)
In [11]: asyncio.run(client.stream(feed_ids, process_report))
Feed ID: 0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8
Timestamp: 1767208232  Benchmark: $87656.35, Bid: $87656.31, Ask: $87656.86
Feed ID: 0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8
Timestamp: 1767208292  Benchmark: $87657.12, Bid: $87656.98, Ask: $87657.45
...
^C
Interrupt signal received, closing connection...
```

### Determine Schema Version from Feed ID

```python
In [1]: from py_chainlink_streams import ReportResponse, Feed

In [2]: # Feed IDs encode their schema version in the prefix
In [3]: feed_id = "0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8"

In [4]: # Using ReportResponse static method
In [5]: schema_version = ReportResponse.get_schema_version(feed_id)
In [6]: print(f"Feed {feed_id} uses schema version v{schema_version}")
Feed 0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8 uses schema version v3

In [7]: # Or using Feed instance method
In [8]: from py_chainlink_streams import ChainlinkClient, ChainlinkConfig
In [9]: import os
In [10]: config = ChainlinkConfig(
   ...:     api_key=os.getenv("CHAINLINK_STREAMS_API_KEY"),
   ...:     api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET")
   ...: )
In [11]: client = ChainlinkClient(config)
In [11]: feeds = client.get_feeds()
In [12]: if feeds:
   ...:     feed = feeds[0]
   ...:     print(f"Feed {feed.id} uses schema version v{feed.schema_version()}")
```

## API Reference

### Client Class (Recommended)

#### `ChainlinkConfig`
Configuration dataclass for ChainlinkClient.

**Attributes:**
- `api_key` (str): Chainlink Data Streams API key (required)
- `api_secret` (str): Chainlink Data Streams API secret (required)
- `api_host` (str): REST API host (default: mainnet)
- `ws_host` (str): WebSocket host (default: mainnet)
- `ping_interval` (int): WebSocket ping interval in seconds (default: 30)
- `pong_timeout` (int): WebSocket pong timeout in seconds (default: 60)
- `timeout` (int): HTTP request timeout in seconds (default: 30)
- `logger` (Optional[Callable]): Optional logging function
- `ws_ha` (bool): Enable WebSocket high availability mode (default: False)
- `ws_max_reconnect` (int): Maximum WebSocket reconnection attempts (default: 10)
- `insecure_skip_verify` (bool): Skip TLS certificate verification (default: False)


#### `ChainlinkClient`
Main client class for Chainlink Data Streams API (similar to Go SDK's Client interface).

**Methods:**
- `get_feeds()` → `List[Feed]`: List all available feeds
- `get_latest_report(feed_id: str)` → `ReportResponse`: Get latest report for a feed
- `get_reports(feed_ids: List[str], timestamp: int)` → `List[ReportResponse]`: Get reports at a timestamp
- `get_report_page(feed_id: str, start_timestamp: int)` → `ReportPage`: Paginate through reports
- `stream(feed_ids: List[str], callback: Callable)` → `None`: Stream reports (async)
- `stream_with_status_callback(feed_ids: List[str], callback: Callable, status_callback: Optional[Callable])` → `None`: Stream with status callbacks (async)

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
- ✅ All modules tested: `client.py`, `report.py`, `feed.py`, `auth.py`, `config.py`, `constants.py`
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

All tests are documented and organized by module in the test files.

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

## Future TODOs

This section outlines potential future improvements to the SDK. The current implementation is fully functional and production-ready for basic use cases.

### High Priority

#### Structured Error Handling
- [ ] Create custom exception hierarchy:
  - `ChainlinkError` (base)
  - `AuthenticationError`
  - `InvalidFeedIDError`
  - `APIError` (with status_code)
  - `DecodeError`
  - `StreamClosedError`
- [ ] Update all functions to raise appropriate custom exceptions

#### Configuration Management
- [ ] Create `ChainlinkConfig` dataclass for centralized configuration
- [ ] Create `ChainlinkClient` class that accepts config
- [ ] Maintain backward compatibility with function-based API

#### Additional HTTP API Methods
- [ ] `get_feeds()` - List all available feeds
- [ ] `get_reports(feed_ids, timestamp)` - Get reports at specific timestamp
- [ ] `get_report_page()` - Paginate reports

#### Logging Configuration
- [ ] Replace `print()` statements with proper logging
- [ ] Add configurable logger with log levels
- [ ] Document logging usage

### Medium Priority

#### WebSocket Enhancements
- [ ] Add status callbacks (connected, disconnected, reconnecting, error)
- [ ] Connection statistics tracking (messages received, uptime, errors)
- [ ] Retry logic with exponential backoff

#### Additional Schema Versions
- [ ] Research and implement v4 schema (RWA)
- [ ] Research and implement v6 schema (Multiple Price Values)
- [ ] Research and implement v10 schema (Tokenized Asset)
- [ ] Create schema registry pattern for easy extension

### Lower Priority

#### Advanced Features
- [ ] High Availability (HA) mode with multiple connections and failover
- [ ] Onchain verification with web3.py integration
- [ ] Type stubs (`.pyi` files) for better IDE support

#### Developer Experience
- [ ] Architecture overview documentation
- [ ] Error handling guide
- [ ] Best practices section
- [ ] Troubleshooting guide
- [ ] Migration guide from Go SDK
- [ ] Additional example scripts and Jupyter notebooks

#### Package Distribution
- [ ] Publish to PyPI
- [ ] Set up automated releases
- [ ] Create changelog
- [ ] CI/CD setup (GitHub Actions)

#### Performance & Reliability
- [ ] Performance profiling and optimization
- [ ] Connection pooling for HTTP
- [ ] Circuit breaker pattern
- [ ] Graceful degradation

**Note:** These are potential future enhancements. The current SDK is fully functional and suitable for production use. Priority should be based on user feedback and actual needs.

## License

MIT
