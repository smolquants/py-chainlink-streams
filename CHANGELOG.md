# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-XX-XX

### Breaking Changes

- **Removed all backward-compatibility functions**: The function-based API has been completely removed. All functionality is now available through the `ChainlinkClient` class.
- **Removed `from_env()` method**: Use `os.getenv()` directly when creating `ChainlinkConfig`.
- **Removed standalone `connect_websocket()` function**: WebSocket connections are now handled internally by `ChainlinkClient.stream()` and `ChainlinkClient.stream_with_status_callback()`.

### Added

- **Class-based API**: New `ChainlinkClient` class for object-oriented usage
- **Configuration management**: `ChainlinkConfig` dataclass for centralized configuration
- **All HTTP API methods**: 
  - `get_feeds()` - List all available feeds
  - `get_reports(feed_ids, timestamp)` - Get reports at a specific timestamp
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

If you're upgrading from v0.1.0, here's how to migrate your code:

#### HTTP API Methods

```python
# Old (v0.1.0)
from py_chainlink_streams import fetch_single_report, get_feeds, get_reports, get_report_page

report = fetch_single_report(feed_id)
feeds = get_feeds()
reports = get_reports(feed_ids, timestamp)
page = get_report_page(feed_id, start_timestamp)

# New (v0.2.0)
from py_chainlink_streams import ChainlinkClient, ChainlinkConfig
import os

config = ChainlinkConfig(
    api_key=os.getenv("CHAINLINK_STREAMS_API_KEY"),
    api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET")
)
client = ChainlinkClient(config)

report = client.get_latest_report(feed_id)
feeds = client.get_feeds()
reports = client.get_reports(feed_ids, timestamp)
page = client.get_report_page(feed_id, start_timestamp)
```

#### Report Decoding

```python
# Old (v0.1.0)
from py_chainlink_streams import decode_report_from_response, get_decoded_prices, get_schema_version

decoded = decode_report_from_response(report_response)
prices = get_decoded_prices(decoded)
schema = get_schema_version(feed_id)

# New (v0.2.0)
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

# New (v0.2.0)
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

# New (v0.2.0)
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

