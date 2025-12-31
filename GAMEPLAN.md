# Production Readiness Gameplan for py-chainlink-streams

This document outlines the roadmap to make `py-chainlink-streams` a production-ready, lightweight Python SDK for Chainlink Data Streams.

## Current Status

✅ **Completed:**
- Basic HTTP REST API client (`fetch_single_report`)
- WebSocket streaming with keepalive
- V3 report decoding
- Price conversion utilities
- Authentication (HMAC-SHA256)
- Mainnet/Testnet support

## Phase 1: Core Improvements (High Priority)

### 1.1 Structured Error Handling
**Status:** ⚠️ Partial (uses generic exceptions)

**Tasks:**
- [ ] Create custom exception hierarchy:
  - `ChainlinkError` (base)
  - `AuthenticationError`
  - `InvalidFeedIDError`
  - `APIError` (with status_code)
  - `DecodeError`
  - `StreamClosedError`
- [ ] Update all functions to raise appropriate custom exceptions
- [ ] Add error documentation

**Estimated Effort:** 2-3 hours

### 1.2 Configuration Management
**Status:** ⚠️ Partial (env vars only)

**Tasks:**
- [ ] Create `ChainlinkConfig` dataclass:
  ```python
  @dataclass
  class ChainlinkConfig:
      api_key: str
      api_secret: str
      api_host: str = MAINNET_API_HOST
      ws_host: str = MAINNET_WS_HOST
      ping_interval: int = 30
      pong_timeout: int = 60
      timeout: int = 30
      logger: Optional[Callable] = None
  ```
- [ ] Create `ChainlinkClient` class that accepts config
- [ ] Maintain backward compatibility with function-based API
- [ ] Add config validation

**Estimated Effort:** 3-4 hours

### 1.3 Additional HTTP API Methods
**Status:** ❌ Missing

**Tasks:**
- [ ] `get_feeds()` - List all available feeds
  - Endpoint: `GET /api/v1/feeds`
- [ ] `get_reports(feed_ids, timestamp)` - Get reports at specific timestamp
  - Endpoint: `GET /api/v1/reports?feedIDs=...&timestamp=...`
- [ ] `get_report_page(feed_id, timestamp, limit, cursor)` - Paginate reports
  - Endpoint: `GET /api/v1/reports/page?feedID=...&timestamp=...&limit=...&cursor=...`

**Estimated Effort:** 4-5 hours

### 1.4 Logging Configuration
**Status:** ❌ Missing

**Tasks:**
- [ ] Replace `print()` statements with proper logging
- [ ] Add configurable logger (default: no-op or basic logger)
- [ ] Add log levels (DEBUG, INFO, WARNING, ERROR)
- [ ] Document logging usage

**Estimated Effort:** 2-3 hours

## Phase 2: Enhanced Features (Medium Priority)

### 2.1 WebSocket Status Callbacks
**Status:** ❌ Missing

**Tasks:**
- [ ] Add `stream_reports_with_status_callback()` function
- [ ] Support status callbacks for:
  - `connected`
  - `disconnected`
  - `reconnecting`
  - `error`
- [ ] Update `stream_reports_with_keepalive()` to support status callbacks

**Estimated Effort:** 3-4 hours

### 2.2 Connection Statistics
**Status:** ❌ Missing

**Tasks:**
- [ ] Create `StreamStats` dataclass:
  ```python
  @dataclass
  class StreamStats:
      messages_received: int
      connection_uptime: float
      errors_count: int
      last_message_time: Optional[float]
      reconnect_count: int
  ```
- [ ] Track statistics in streaming functions
- [ ] Add `get_stream_stats()` function

**Estimated Effort:** 2-3 hours

### 2.3 Additional Schema Versions
**Status:** ⚠️ Partial (v3 only)

**Tasks:**
- [ ] Research and implement v4 schema (RWA)
- [ ] Research and implement v6 schema (Multiple Price Values)
- [ ] Research and implement v10 schema (Tokenized Asset)
- [ ] Create schema registry/registry pattern for easy extension
- [ ] Update `decode_report()` to support multiple schemas

**Estimated Effort:** 8-12 hours (depends on schema complexity)

### 2.4 Retry Logic
**Status:** ❌ Missing

**Tasks:**
- [ ] Add exponential backoff retry for HTTP requests
- [ ] Add configurable retry settings (max_retries, backoff_factor)
- [ ] Add retry for WebSocket reconnection
- [ ] Document retry behavior

**Estimated Effort:** 3-4 hours

## Phase 3: Advanced Features (Lower Priority)

### 3.1 High Availability (HA) Mode
**Status:** ❌ Missing

**Tasks:**
- [ ] Design HA architecture:
  - Multiple simultaneous WebSocket connections
  - Automatic failover
  - Report deduplication
  - Per-connection health monitoring
- [ ] Implement `HAStreamManager` class
- [ ] Add connection pooling
- [ ] Add load balancing logic

**Estimated Effort:** 12-16 hours (complex feature)

### 3.2 Onchain Verification
**Status:** ❌ Missing

**Tasks:**
- [ ] Add `verify_report_onchain()` function
- [ ] Integrate with web3.py for EVM chain verification
- [ ] Verify report signatures
- [ ] Verify report context
- [ ] Add example usage

**Estimated Effort:** 6-8 hours

### 3.3 Type Stubs
**Status:** ❌ Missing

**Tasks:**
- [ ] Generate `.pyi` type stub files
- [ ] Add comprehensive type hints
- [ ] Ensure IDE support (VS Code, PyCharm)

**Estimated Effort:** 3-4 hours

## Phase 4: Developer Experience

### 4.1 Documentation
**Status:** ⚠️ Partial (basic README)

**Tasks:**
- [ ] Expand README with:
  - Architecture overview
  - Error handling guide
  - Best practices
  - Troubleshooting
- [ ] Add docstrings to all public functions
- [ ] Create API reference documentation
- [ ] Add migration guide from Go SDK

**Estimated Effort:** 4-6 hours

### 4.2 Testing
**Status:** ❌ Missing

**Tasks:**
- [ ] Set up pytest
- [ ] Unit tests for:
  - Authentication functions
  - Decoding functions
  - Error handling
- [ ] Integration tests (with mock server):
  - HTTP API calls
  - WebSocket connections
- [ ] Test coverage target: 80%+
- [ ] CI/CD setup (GitHub Actions)

**Estimated Effort:** 8-12 hours

### 4.3 Examples and Tutorials
**Status:** ⚠️ Partial (basic examples)

**Tasks:**
- [ ] Create example scripts:
  - Price monitoring script
  - Historical data collection
  - Multi-feed streaming
- [ ] Add Jupyter notebook tutorials
- [ ] Create comparison examples (vs Go SDK)

**Estimated Effort:** 4-6 hours

### 4.4 Package Distribution
**Status:** ⚠️ Partial (local package)

**Tasks:**
- [ ] Publish to PyPI
- [ ] Set up automated releases
- [ ] Add versioning strategy (semantic versioning)
- [ ] Create changelog
- [ ] Add license file

**Estimated Effort:** 2-3 hours

## Phase 5: Performance & Reliability

### 5.1 Performance Optimization
**Status:** ⚠️ Not optimized

**Tasks:**
- [ ] Profile code for bottlenecks
- [ ] Optimize decoding functions
- [ ] Add connection pooling for HTTP
- [ ] Optimize WebSocket message handling
- [ ] Add benchmarks

**Estimated Effort:** 4-6 hours

### 5.2 Reliability Improvements
**Status:** ⚠️ Basic

**Tasks:**
- [ ] Add connection health checks
- [ ] Improve error recovery
- [ ] Add circuit breaker pattern
- [ ] Add timeout handling improvements
- [ ] Add graceful degradation

**Estimated Effort:** 6-8 hours

## Recommended Implementation Order

### Sprint 1 (Week 1): Foundation
1. Structured error handling (1.1)
2. Logging configuration (1.4)
3. Basic testing setup (4.2)

### Sprint 2 (Week 2): Core Features
1. Configuration management (1.2)
2. Additional HTTP API methods (1.3)
3. Documentation improvements (4.1)

### Sprint 3 (Week 3): Enhanced Features
1. WebSocket status callbacks (2.1)
2. Connection statistics (2.2)
3. Retry logic (2.4)

### Sprint 4 (Week 4): Polish
1. Additional schema versions (2.3) - start with v4
2. Examples and tutorials (4.3)
3. Package distribution (4.4)

### Future Sprints: Advanced Features
- HA Mode (3.1)
- Onchain verification (3.2)
- Performance optimization (5.1)
- Reliability improvements (5.2)

## Success Criteria

### Minimum Viable Product (MVP)
- ✅ All current functionality working
- [ ] Structured error handling
- [ ] Configuration management
- [ ] `get_feeds()` and `get_reports()` methods
- [ ] Basic logging
- [ ] 80%+ test coverage
- [ ] Published to PyPI

### Production Ready
- [ ] All MVP features
- [ ] WebSocket status callbacks
- [ ] Connection statistics
- [ ] Retry logic
- [ ] Comprehensive documentation
- [ ] Performance benchmarks
- [ ] HA mode (optional, but valuable)

## Notes

- Keep the SDK lightweight - avoid heavy dependencies
- Maintain backward compatibility where possible
- Follow Python best practices (PEP 8, type hints, etc.)
- Consider async/await patterns for better performance
- Document all breaking changes clearly

## Dependencies to Consider

- `web3.py` - For onchain verification (optional dependency)
- `pytest` - For testing
- `pytest-asyncio` - For async tests
- `pytest-mock` - For mocking
- `httpx` - Alternative to requests (async support, but adds dependency)

## Questions to Resolve

1. Should we support both sync and async APIs, or async-only?
2. Do we want to maintain backward compatibility with function-based API when adding Client class?
3. Should HA mode be a separate package or included?
4. What's the minimum Python version? (Currently 3.9+)

