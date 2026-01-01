# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2025-XX-XX

### Added

- **PyPI publication readiness**: Added comprehensive PyPI metadata including:
  - Python version classifiers (3.9, 3.10, 3.11, 3.12, 3.13)
  - Keywords for discoverability
  - Project URLs (homepage, repository, issues, documentation)
  - Development status and topic classifiers
- **Code coverage tooling**: Added `coverage>=7.0.0` as a dev dependency
- **Coverage configuration**: Added comprehensive `[tool.coverage]` configuration in `pyproject.toml`
- **Professional badges**: Added badges to README for Python version support, license, PyPI version, and test coverage
- **Python version support documentation**: Added explicit section documenting supported Python versions (3.9+)
- **Enhanced testing documentation**: Added detailed code coverage reporting instructions

### Changed

- **README improvements**: Enhanced testing section with Python version support and code coverage details
- **Project metadata**: Professionalized `pyproject.toml` with proper PyPI classifiers and metadata

## [0.3.0] - 2025-XX-XX

### Breaking Changes

- **Changed `get_reports()` to `get_report()`**: The method signature changed from accepting multiple `feed_ids: List[str]` to a single `feed_id: str`, and now returns a single `ReportResponse` instead of a list. This aligns with the API's behavior for single feed queries and simplifies the interface.
  - **Before**: `client.get_reports(feed_ids: List[str], timestamp: int) -> List[ReportResponse]`
  - **After**: `client.get_report(feed_id: str, timestamp: int) -> ReportResponse`

### Added

- **Enhanced integration tests**: Added comprehensive integration tests for both single and multiple feed ID scenarios
  - Tests for WebSocket connections with single feed ID (BTC/USD)
  - Tests for WebSocket connections with multiple feed IDs (BTC/USD and ETH/USD)
  - Tests for streaming with single and multiple feed IDs
  - Long-running stream tests for both scenarios
- **ETH/USD feed support**: Added ETH/USD feed ID (`0x000362205e10b3a147d02792eccee483dca6c7b44ecce7012cb8c6e0b68b3ae9`) to integration tests

### Changed

- **Test suite refactoring**: Reorganized tests into class-based structure matching the SDK architecture:
  - `test_auth.py` - All authentication function tests (27 tests)
  - `test_feed.py` - Feed class tests (9 tests)
  - `test_report.py` - ReportResponse and ReportPage class tests including all decode functionality (59 tests)
  - `test_client.py` - ChainlinkClient method tests (22 tests)
  - Removed `test_decode.py` (merged into `test_report.py`)
- **Code organization**: Inlined WebSocket streaming logic (`stream_reports` and `_ping_loop`) directly into `ChainlinkClient.stream_with_status_callback()` method
- **Test coverage**: Increased from 123 to 141+ unit tests and 15+ to 25+ integration tests

### Fixed

- Fixed `get_report_page` to use `nextPageTimestamp` from API response when available
- Fixed test expectations to match actual API behavior for `get_latest_report` endpoint
- Fixed integration test imports for `ReportPage` class

## [0.2.0] - 2025-XX-XX

### Breaking Changes

- **Removed all backward-compatibility functions**: The function-based API has been completely removed. All functionality is now available through the `ChainlinkClient` class.
- **Removed `from_env()` method**: Use `os.getenv()` directly when creating `ChainlinkConfig`.
- **Removed standalone `connect_websocket()` function**: WebSocket connections are now handled internally by `ChainlinkClient.stream()` and `ChainlinkClient.stream_with_status_callback()`.

**Note**: The `get_reports()` → `get_report()` breaking change was moved to v0.3.0 for better semantic versioning clarity.

### Added

- **Class-based API**: New `ChainlinkClient` class for object-oriented usage
- **Configuration management**: `ChainlinkConfig` dataclass for centralized configuration
- **All HTTP API methods**: 
  - `get_feeds()` - List all available feeds
  - `get_report(feed_id, timestamp)` - Get a report for a feed at a specific timestamp
  - `get_report_page(feed_id, start_timestamp)` - Paginate through reports
- **WebSocket status callbacks**: `stream_with_status_callback()` method with support for connection status tracking
- **Class methods for decoding**: All decode functionality moved to `ReportResponse` and `Feed` classes:
  - `ReportResponse.decode()` - Decode hex-encoded report
  - `ReportResponse.get_decoded_prices()` - Convert prices to decimal format
  - `ReportResponse.get_schema_version()` - Static method to determine schema version
  - `Feed.get_schema_version()` - Instance method to get schema version
  - `Feed.schema_version()` - Alias for `get_schema_version()`

### Changed

- All decode methods are now instance or class methods on `ReportResponse` and `Feed` classes
- WebSocket connections are managed internally by the client
- Configuration is now done through `ChainlinkConfig` dataclass

### Migration Guide

If you're upgrading from v0.1.0 or v0.2.0, here's how to migrate your code:

#### HTTP API Methods

```python
# Old (v0.1.0)
from py_chainlink_streams import fetch_single_report, get_feeds, get_reports, get_report_page

report = fetch_single_report(feed_id)
feeds = get_feeds()
reports = get_reports(feed_ids, timestamp)
page = get_report_page(feed_id, start_timestamp)

# New (v0.3.0)
from py_chainlink_streams import ChainlinkClient, ChainlinkConfig
import os

config = ChainlinkConfig(
    api_key=os.getenv("CHAINLINK_STREAMS_API_KEY"),
    api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET")
)
client = ChainlinkClient(config)

report = client.get_latest_report(feed_id)
feeds = client.get_feeds()
# ⚠️ BREAKING in v0.3.0: get_reports() changed to get_report() with single feed_id
report = client.get_report(feed_id, timestamp)  # Single feed_id, returns single ReportResponse (was: feed_ids list → ReportResponse list)
page = client.get_report_page(feed_id, start_timestamp)
```

#### Report Decoding

```python
# Old (v0.1.0)
from py_chainlink_streams import decode_report_from_response, get_decoded_prices, get_schema_version

decoded = decode_report_from_response(report_response)
prices = get_decoded_prices(decoded)
schema = get_schema_version(feed_id)

# New (v0.3.0)
decoded = report.decode()
prices = report.get_decoded_prices()
schema = ReportResponse.get_schema_version(feed_id)  # or Feed.get_schema_version(feed_id)
```

#### WebSocket Streaming

```python
# Old (v0.1.0)
from py_chainlink_streams import stream_reports_with_keepalive

async def callback(report):
    print(report)

await stream_reports_with_keepalive(feed_ids, callback)

# New (v0.3.0)
from py_chainlink_streams import ChainlinkClient, ChainlinkConfig
import os

config = ChainlinkConfig(
    api_key=os.getenv("CHAINLINK_STREAMS_API_KEY"),
    api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET")
)
client = ChainlinkClient(config)

async def callback(report):
    print(report)

await client.stream(feed_ids, callback)

# Or with status callbacks
async def status_callback(status, host=None, origin=None):
    print(f"Status: {status}")

await client.stream_with_status_callback(feed_ids, callback, status_callback)
```

#### Configuration

```python
# Old (v0.1.0)
from py_chainlink_streams import ChainlinkConfig

config = ChainlinkConfig.from_env()

# New (v0.3.0)
from py_chainlink_streams import ChainlinkConfig
import os

config = ChainlinkConfig(
    api_key=os.getenv("CHAINLINK_STREAMS_API_KEY"),
    api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET")
)
```

## [0.1.0] - 2025-XX-XX

### Added

- Initial release with function-based API
- HTTP REST API client for fetching reports
- WebSocket streaming with keepalive
- V3 report decoding
- Price conversion utilities
- Authentication (HMAC-SHA256)
- Mainnet and Testnet support

