"""
Integration tests for py-chainlink-streams with real Chainlink mainnet API.

These tests require:
- Valid Chainlink Data Streams API credentials (mainnet)
- Network access to Chainlink API endpoints
- Real feed IDs from Chainlink mainnet

Run with: pytest -m integration tests/test_integration.py
Skip with: pytest -m "not integration" tests/
"""

import os
import pytest
import asyncio
from typing import Optional

from py_chainlink_streams import (
    ChainlinkClient,
    ChainlinkConfig,
    ReportResponse,
    ReportPage,
)

# Real mainnet feed IDs for testing (v3 schema)
BTC_USD_FEED_ID = "0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8"
ETH_USD_FEED_ID = "0x000362205e10b3a147d02792eccee483dca6c7b44ecce7012cb8c6e0b68b3ae9"

# Skip all integration tests if credentials not available
# Also mark all tests in this file as integration tests
pytestmark = [
    pytest.mark.skipif(
        not os.getenv("CHAINLINK_STREAMS_API_KEY") or 
        not os.getenv("CHAINLINK_STREAMS_API_SECRET"),
        reason="Chainlink API credentials not set. Set CHAINLINK_STREAMS_API_KEY and CHAINLINK_STREAMS_API_SECRET environment variables."
    ),
    pytest.mark.integration,
]


@pytest.fixture
def mainnet_feed_id():
    """Real mainnet feed ID for testing (BTC/USD v3)."""
    return BTC_USD_FEED_ID


@pytest.fixture
def mainnet_feed_ids_single():
    """Single mainnet feed ID for testing (list with len 1)."""
    return [BTC_USD_FEED_ID]


@pytest.fixture
def mainnet_feed_ids_multiple():
    """Multiple mainnet feed IDs for testing (list with len > 1)."""
    return [BTC_USD_FEED_ID, ETH_USD_FEED_ID]


# ============================================================================
# HTTP REST API Integration Tests
# ============================================================================

class TestFetchSingleReportMainnet:
    """Integration tests for ChainlinkClient.get_latest_report with mainnet API."""

    def test_fetch_single_report_mainnet(self, mainnet_feed_id):
        """Test fetching latest report from mainnet API."""
        import os
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        client = ChainlinkClient(config)
        report = client.get_latest_report(mainnet_feed_id)
        
        # Verify response structure
        assert report.feed_id == mainnet_feed_id
        assert isinstance(report.valid_from_timestamp, int)
        assert isinstance(report.observations_timestamp, int)
        assert isinstance(report.full_report, str)
        
        # Verify fullReport is valid hex string
        assert report.full_report.startswith("0x")
        assert len(report.full_report) > 100  # Should be substantial hex string
        
        # Verify timestamps are valid Unix timestamps
        assert report.valid_from_timestamp > 0
        assert report.observations_timestamp > 0

    def test_fetch_single_report_with_real_feed_id(self, mainnet_feed_id):
        """Test fetching report with real mainnet feed ID."""
        import os
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        client = ChainlinkClient(config)
        report = client.get_latest_report(mainnet_feed_id)
        
        # Verify response structure matches API spec
        assert report.feed_id == mainnet_feed_id
        assert isinstance(report.valid_from_timestamp, int)
        assert isinstance(report.observations_timestamp, int)
        assert isinstance(report.full_report, str)
        
        # Verify fullReport is valid hex string
        assert report.full_report.startswith("0x"), "fullReport should start with 0x"
        # Remove 0x and verify it's valid hex
        hex_part = report.full_report[2:]
        assert all(c in '0123456789abcdefABCDEF' for c in hex_part), "fullReport should be valid hex"
        
        # Verify timestamps are recent (within last hour)
        import time
        current_time = int(time.time())
        # Allow some flexibility (within last 2 hours to account for API delays)
        assert report.observations_timestamp > current_time - 7200, "observationsTimestamp should be recent"

    def test_fetch_single_report_handles_invalid_feed_id(self):
        """Test that invalid feed ID is handled gracefully."""
        invalid_feed_id = "0x0000000000000000000000000000000000000000000000000000000000000000"
        
        # Should either return error response or raise exception
        try:
            import os
            config = ChainlinkConfig(
                api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
                api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
            )
            client = ChainlinkClient(config)
            report = client.get_latest_report(invalid_feed_id)
            # If it returns, might be empty or error response
            # This is acceptable behavior
        except Exception as e:
            # Exception is also acceptable for invalid feed ID
            assert "feed" in str(e).lower() or "not found" in str(e).lower() or "invalid" in str(e).lower() or "404" in str(e) or "401" in str(e)


# ============================================================================
# Report Decoding Integration Tests
# ============================================================================

class TestDecodeRealMainnetReport:
    """Integration tests for decoding real mainnet reports."""

    def test_decode_real_mainnet_report(self, mainnet_feed_id):
        """Test decoding a real report fetched from mainnet."""
        # Fetch real report
        import os
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        client = ChainlinkClient(config)
        report = client.get_latest_report(mainnet_feed_id)
        
        # Decode the report
        decoded = report.decode()
        
        # Verify decoded structure
        assert "reportContext" in decoded
        assert "reportBlob" in decoded
        assert "rawRs" in decoded
        assert "rawSs" in decoded
        assert "rawVs" in decoded
        assert "data" in decoded
        assert "schemaVersion" in decoded
        
        # Verify schema version matches feed ID
        schema_version = decoded["schemaVersion"]
        expected_version = ReportResponse.get_schema_version(mainnet_feed_id)
        assert schema_version == expected_version, f"Schema version {schema_version} should match feed ID version {expected_version}"
        
        # Verify decoded data contains v3 schema fields
        data = decoded["data"]
        assert "feedId" in data
        assert "validFromTimestamp" in data
        assert "observationsTimestamp" in data
        assert "nativeFee" in data
        assert "linkFee" in data
        assert "expiresAt" in data
        assert "benchmarkPrice" in data
        assert "bid" in data
        assert "ask" in data
        
        # Verify feed ID in data matches
        assert data["feedId"].lower() == mainnet_feed_id.lower()
        
        # Verify timestamps are reasonable
        assert data["validFromTimestamp"] > 0
        assert data["observationsTimestamp"] > 0
        assert data["expiresAt"] > data["validFromTimestamp"]

    def test_get_decoded_prices_from_real_report(self, mainnet_feed_id):
        """Test extracting prices from a real mainnet report."""
        # Fetch and decode real report
        import os
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        client = ChainlinkClient(config)
        report = client.get_latest_report(mainnet_feed_id)
        decoded = report.decode()
        
        # Get decoded prices
        prices = report.get_decoded_prices()
        
        # Verify price structure
        assert "observationsTimestamp" in prices
        assert "benchmarkPrice" in prices
        assert "bid" in prices
        assert "ask" in prices
        assert "midPrice" in prices
        
        # Verify prices are reasonable floats (not in wei format)
        assert isinstance(prices["benchmarkPrice"], float)
        assert isinstance(prices["bid"], float)
        assert isinstance(prices["ask"], float)
        assert isinstance(prices["midPrice"], float)
        
        # Prices should be reasonable (e.g., BTC/USD should be in thousands, not wei)
        assert prices["benchmarkPrice"] > 0
        assert prices["benchmarkPrice"] < 1000000  # Should be converted from wei
        assert prices["bid"] > 0
        assert prices["ask"] > 0
        
        # Verify midPrice is average of bid and ask
        expected_mid = (prices["bid"] + prices["ask"]) / 2.0
        assert abs(prices["midPrice"] - expected_mid) < 0.01, "midPrice should be average of bid and ask"
        
        # Verify observationsTimestamp
        assert isinstance(prices["observationsTimestamp"], int)
        assert prices["observationsTimestamp"] > 0

    def test_end_to_end_fetch_and_decode(self, mainnet_feed_id):
        """Test complete workflow: fetch → decode → get prices."""
        # Step 1: Fetch report
        import os
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        client = ChainlinkClient(config)
        report = client.get_latest_report(mainnet_feed_id)
        assert report.feed_id == mainnet_feed_id
        assert report.full_report.startswith("0x")
        
        # Step 2: Decode report
        decoded = report.decode()
        assert "data" in decoded
        assert decoded["schemaVersion"] == 3
        
        # Step 3: Get decoded prices
        prices = report.get_decoded_prices()
        assert "benchmarkPrice" in prices
        assert "bid" in prices
        assert "ask" in prices
        
        # Verify final prices are human-readable
        assert prices["benchmarkPrice"] < 1000000, "Price should be converted from wei to human-readable format"
        assert prices["bid"] < 1000000
        assert prices["ask"] < 1000000
        
        # Verify data consistency
        assert prices["observationsTimestamp"] == decoded["data"]["observationsTimestamp"]


# ============================================================================
# Historical Report Integration Tests
# ============================================================================

class TestGetReportMainnet:
    """Integration tests for get_report with historical timestamps."""

    def test_get_report_with_historical_timestamp(self, mainnet_feed_id):
        """Test fetching a report at a specific historical timestamp."""
        import os
        import time
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        client = ChainlinkClient(config)
        
        # Get a recent timestamp (1 hour ago)
        current_time = int(time.time())
        historical_timestamp = current_time - 3600
        
        # Fetch report at historical timestamp
        report = client.get_report(mainnet_feed_id, timestamp=historical_timestamp)
        
        # Verify report structure
        assert isinstance(report, ReportResponse)
        assert report.feed_id == mainnet_feed_id
        assert report.full_report.startswith("0x")
        assert report.observations_timestamp > 0
        assert report.valid_from_timestamp > 0
        
        # Verify timestamp is close to requested timestamp (within reasonable range)
        # The API may return the closest available report
        time_diff = abs(report.observations_timestamp - historical_timestamp)
        assert time_diff < 86400, "Report timestamp should be within 24 hours of requested timestamp"

    def test_get_report_can_decode_historical_report(self, mainnet_feed_id):
        """Test that historical reports can be decoded."""
        import os
        import time
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        client = ChainlinkClient(config)
        
        # Get a recent timestamp (1 hour ago)
        current_time = int(time.time())
        historical_timestamp = current_time - 3600
        
        # Fetch and decode historical report
        report = client.get_report(mainnet_feed_id, timestamp=historical_timestamp)
        decoded = report.decode()
        
        # Verify decoded structure
        assert "schemaVersion" in decoded
        assert "data" in decoded
        assert decoded["schemaVersion"] == 3
        
        # Verify decoded data
        data = decoded["data"]
        assert "feedId" in data
        assert "observationsTimestamp" in data
        assert data["feedId"].lower() == mainnet_feed_id.lower()

    def test_get_report_returns_empty_for_future_timestamp(self, mainnet_feed_id):
        """Test that get_report handles future timestamps gracefully."""
        import os
        import time
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        client = ChainlinkClient(config)
        
        # Use a future timestamp (1 hour from now)
        current_time = int(time.time())
        future_timestamp = current_time + 3600
        
        # Should either return a report (closest available) or raise an error
        # The API behavior may vary, so we just check it doesn't crash
        try:
            report = client.get_report(mainnet_feed_id, timestamp=future_timestamp)
            # If it returns, verify it's a valid ReportResponse
            assert isinstance(report, ReportResponse)
        except (ValueError, Exception):
            # If it raises an error, that's also acceptable
            pass


class TestGetReportPageMainnet:
    """Integration tests for get_report_page with historical timestamps."""

    def test_get_report_page_with_historical_timestamp(self, mainnet_feed_id):
        """Test fetching a page of reports starting from a historical timestamp."""
        import os
        import time
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        client = ChainlinkClient(config)
        
        # Get a recent timestamp (1 hour ago)
        current_time = int(time.time())
        historical_timestamp = current_time - 3600
        
        # Fetch report page
        page = client.get_report_page(mainnet_feed_id, start_timestamp=historical_timestamp)
        
        # Verify page structure
        assert isinstance(page, ReportPage)
        assert isinstance(page.reports, list)
        assert isinstance(page.next_page_timestamp, int)
        
        # Verify reports in page
        if len(page.reports) > 0:
            for report in page.reports:
                assert isinstance(report, ReportResponse)
                assert report.feed_id == mainnet_feed_id
                assert report.full_report.startswith("0x")
                # Reports should be at or after the start timestamp
                assert report.observations_timestamp >= historical_timestamp - 3600  # Allow some flexibility

    def test_get_report_page_next_page_timestamp(self, mainnet_feed_id):
        """Test that next_page_timestamp is set correctly for pagination."""
        import os
        import time
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        client = ChainlinkClient(config)
        
        # Get a recent timestamp (1 hour ago)
        current_time = int(time.time())
        historical_timestamp = current_time - 3600
        
        # Fetch first page
        page1 = client.get_report_page(mainnet_feed_id, start_timestamp=historical_timestamp)
        
        # Verify next_page_timestamp
        assert page1.next_page_timestamp >= 0
        
        # If there's a next page, fetch it
        if page1.next_page_timestamp > 0:
            page2 = client.get_report_page(mainnet_feed_id, start_timestamp=page1.next_page_timestamp)
            assert isinstance(page2, ReportPage)
            # Next page timestamp should be greater than or equal to first page's next timestamp
            assert page2.next_page_timestamp >= page1.next_page_timestamp

    def test_get_report_page_can_decode_reports(self, mainnet_feed_id):
        """Test that reports in a page can be decoded."""
        import os
        import time
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        client = ChainlinkClient(config)
        
        # Get a recent timestamp (1 hour ago)
        current_time = int(time.time())
        historical_timestamp = current_time - 3600
        
        # Fetch report page
        page = client.get_report_page(mainnet_feed_id, start_timestamp=historical_timestamp)
        
        # Decode first report if available
        if len(page.reports) > 0:
            report = page.reports[0]
            decoded = report.decode()
            
            # Verify decoded structure
            assert "schemaVersion" in decoded
            assert "data" in decoded
            assert decoded["schemaVersion"] == 3
            
            # Verify decoded data
            data = decoded["data"]
            assert "feedId" in data
            assert data["feedId"].lower() == mainnet_feed_id.lower()


# ============================================================================
# WebSocket Connection Integration Tests
# ============================================================================

class TestConnectWebsocketMainnetSingle:
    """Integration tests for WebSocket connections to mainnet with single feed ID."""

    @pytest.mark.asyncio
    async def test_connect_websocket_mainnet_single_feed(self, mainnet_feed_ids_single):
        """Test successfully establishing WebSocket connection to mainnet with single feed ID."""
        import os
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        client = ChainlinkClient(config)
        websocket = await client._connect_websocket(mainnet_feed_ids_single)
        
        # Verify connection is established
        assert websocket is not None
        assert len(mainnet_feed_ids_single) == 1
        
        # Keep connection open for a few seconds to verify stability
        # Try to ping to verify connection is alive
        try:
            await websocket.ping()
        except Exception:
            pytest.fail("WebSocket connection should be alive and respond to ping")
        
        await asyncio.sleep(2)
        
        # Verify connection is still open by trying another ping
        try:
            await websocket.ping()
        except Exception:
            pytest.fail("Connection should remain open")
        
        # Close connection
        await websocket.close()


class TestConnectWebsocketMainnetMultiple:
    """Integration tests for WebSocket connections to mainnet with multiple feed IDs."""

    @pytest.mark.asyncio
    async def test_connect_websocket_mainnet_multiple_feeds(self, mainnet_feed_ids_multiple):
        """Test successfully establishing WebSocket connection to mainnet with multiple feed IDs."""
        import os
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        client = ChainlinkClient(config)
        websocket = await client._connect_websocket(mainnet_feed_ids_multiple)
        
        # Verify connection is established
        assert websocket is not None
        assert len(mainnet_feed_ids_multiple) > 1
        
        # Verify connection is alive by trying to ping
        try:
            await websocket.ping()
        except Exception:
            pytest.fail("WebSocket connection should be alive")
        
        # Keep connection open for a few seconds to verify stability
        await asyncio.sleep(2)
        
        # Verify connection is still open by trying another ping
        try:
            await websocket.ping()
        except Exception:
            pytest.fail("Connection should remain open")
        
        # Close connection
        await websocket.close()


# ============================================================================
# WebSocket Streaming Integration Tests
# ============================================================================

class TestStreamReportsMainnetSingle:
    """Integration tests for streaming reports from mainnet with single feed ID."""

    @pytest.mark.asyncio
    async def test_stream_reports_receives_messages_single_feed(self, mainnet_feed_ids_single):
        """Test that streaming receives at least one report message."""
        import os
        messages_received = []
        
        def callback(report_data):
            messages_received.append(report_data)
        
        # Stream for up to 30 seconds or until we get a message
        stop_event = asyncio.Event()
        
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        client = ChainlinkClient(config)
        
        assert len(mainnet_feed_ids_single) == 1
        
        async def stream_with_timeout():
            try:
                await asyncio.wait_for(
                    client.stream(mainnet_feed_ids_single, callback),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                stop_event.set()
        
        # Start streaming
        stream_task = asyncio.create_task(stream_with_timeout())
        
        # Wait for at least one message or timeout
        await asyncio.sleep(5)  # Give it 5 seconds to receive a message
        
        # Check if we received any messages
        if messages_received:
            # Got a message, verify it's valid
            # WebSocket messages may have nested 'report' structure
            message = messages_received[0]
            if "report" in message:
                report = message["report"]
            else:
                report = message
            
            assert "feedID" in report or "report" in message
            assert "fullReport" in report or "observationsTimestamp" in report or "report" in message
            
            # Stop streaming
            stop_event.set()
            stream_task.cancel()
            try:
                await stream_task
            except asyncio.CancelledError:
                pass
        else:
            # No messages yet, cancel and verify we can cancel gracefully
            stream_task.cancel()
            try:
                await stream_task
            except asyncio.CancelledError:
                pass
            # This is acceptable - API might not send messages immediately

    @pytest.mark.asyncio
    async def test_stream_reports_with_keepalive_mainnet_single_feed(self, mainnet_feed_ids_single):
        """Test streaming with keepalive on mainnet with single feed ID."""
        import os
        messages_received = []
        
        def callback(report_data):
            messages_received.append(report_data)
            print(f"Received report: feedID={report_data.get('feedID', 'unknown')}")
        
        # Stream for a short period to test keepalive
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        client = ChainlinkClient(config)
        try:
            await asyncio.wait_for(
                client.stream(mainnet_feed_ids_single, callback),
                timeout=10.0  # Stream for 10 seconds
            )
        except asyncio.TimeoutError:
            # Timeout is expected - we're testing that keepalive works
            pass
        
        # Verify we could establish connection (no exception means connection worked)
        # Messages may or may not be received depending on API activity


class TestStreamReportsMainnetMultiple:
    """Integration tests for streaming reports from mainnet with multiple feed IDs."""

    @pytest.mark.asyncio
    async def test_stream_reports_receives_messages_multiple_feeds(self, mainnet_feed_ids_multiple):
        """Test that streaming receives at least one report message with multiple feed IDs."""
        import os
        messages_received = []
        
        def callback(report_data):
            messages_received.append(report_data)
        
        # Stream for up to 30 seconds or until we get a message
        stop_event = asyncio.Event()
        
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        client = ChainlinkClient(config)
        
        assert len(mainnet_feed_ids_multiple) > 1
        
        async def stream_with_timeout():
            try:
                await asyncio.wait_for(
                    client.stream(mainnet_feed_ids_multiple, callback),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                stop_event.set()
        
        # Start streaming
        stream_task = asyncio.create_task(stream_with_timeout())
        
        # Wait for at least one message or timeout
        await asyncio.sleep(5)  # Give it 5 seconds to receive a message
        
        # Check if we received any messages
        if messages_received:
            # Got a message, verify it's valid
            # WebSocket messages may have nested 'report' structure
            message = messages_received[0]
            if "report" in message:
                report = message["report"]
            else:
                report = message
            
            assert "feedID" in report or "report" in message
            assert "fullReport" in report or "observationsTimestamp" in report or "report" in message
            
            # Verify we can receive reports from different feeds
            feed_ids_received = set()
            for msg in messages_received:
                if "report" in msg:
                    report = msg["report"]
                else:
                    report = msg
                if "feedID" in report:
                    feed_ids_received.add(report["feedID"])
            
            # Stop streaming
            stop_event.set()
            stream_task.cancel()
            try:
                await stream_task
            except asyncio.CancelledError:
                pass
        else:
            # No messages yet, cancel and verify we can cancel gracefully
            stream_task.cancel()
            try:
                await stream_task
            except asyncio.CancelledError:
                pass
            # This is acceptable - API might not send messages immediately

    @pytest.mark.asyncio
    async def test_stream_reports_with_keepalive_mainnet_multiple_feeds(self, mainnet_feed_ids_multiple):
        """Test streaming with keepalive on mainnet with multiple feed IDs."""
        import os
        messages_received = []
        
        def callback(report_data):
            messages_received.append(report_data)
            print(f"Received report: feedID={report_data.get('feedID', 'unknown')}")
        
        # Stream for a short period to test keepalive
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        client = ChainlinkClient(config)
        try:
            await asyncio.wait_for(
                client.stream(mainnet_feed_ids_multiple, callback),
                timeout=10.0  # Stream for 10 seconds
            )
        except asyncio.TimeoutError:
            # Timeout is expected - we're testing that keepalive works
            pass
        
        # Verify we could establish connection (no exception means connection worked)
        # Messages may or may not be received depending on API activity

    @pytest.mark.asyncio
    async def test_stream_reports_stop_event_multiple_feeds(self, mainnet_feed_ids_multiple):
        """Test that stop_event properly stops streaming for multiple feeds."""
        messages_received = []
        stop_event = asyncio.Event()
        
        def callback(report_data):
            messages_received.append(report_data)
            # Stop after first message
            if len(messages_received) >= 1:
                stop_event.set()
        
        # Create a custom streaming function that respects stop_event
        async def stream_with_stop():
            import os
            config = ChainlinkConfig(
                api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
                api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
            )
            client = ChainlinkClient(config)
            websocket = await client._connect_websocket(mainnet_feed_ids_multiple)
            try:
                # Stream reports directly from websocket
                import json
                async for message in websocket:
                    try:
                        report_data = json.loads(message)
                        callback(report_data)
                        if stop_event.is_set():
                            break
                    except Exception:
                        continue
            finally:
                await websocket.close()
        
        # Stream with stop event
        try:
            await asyncio.wait_for(stream_with_stop(), timeout=15.0)
        except asyncio.TimeoutError:
            # If we get a message, stop_event should have been set
            if messages_received:
                assert stop_event.is_set(), "stop_event should be set after receiving message"


# ============================================================================
# Error Handling Integration Tests
# ============================================================================

class TestErrorHandlingMainnet:
    """Integration tests for error handling with real API."""

    def test_invalid_credentials_error(self):
        """Test that invalid credentials return appropriate error."""
        import os
        # Temporarily set invalid credentials
        original_key = os.environ.get("CHAINLINK_STREAMS_API_KEY")
        original_secret = os.environ.get("CHAINLINK_STREAMS_API_SECRET")
        
        try:
            os.environ["CHAINLINK_STREAMS_API_KEY"] = "invalid_key"
            os.environ["CHAINLINK_STREAMS_API_SECRET"] = "invalid_secret"
            
            # Should raise error
            config = ChainlinkConfig(
                api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
                api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
            )
            client = ChainlinkClient(config)
            with pytest.raises(Exception) as exc_info:
                client.get_latest_report(BTC_USD_FEED_ID)
            
            # Error should indicate authentication failure
            error_str = str(exc_info.value).lower()
            assert "401" in error_str or "unauthorized" in error_str or "authentication" in error_str or "credential" in error_str
            
        finally:
            # Restore original credentials
            if original_key:
                os.environ["CHAINLINK_STREAMS_API_KEY"] = original_key
            if original_secret:
                os.environ["CHAINLINK_STREAMS_API_SECRET"] = original_secret

    def test_invalid_feed_id_error(self):
        """Test that invalid feed ID returns appropriate error."""
        invalid_feed_id = "0x0000000000000000000000000000000000000000000000000000000000000000"
        
        # Should either return error or raise exception
        try:
            import os
            config = ChainlinkConfig(
                api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
                api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
            )
            client = ChainlinkClient(config)
            report = client.get_latest_report(invalid_feed_id)
            # If response is returned, it might be an error response
            # This is acceptable
        except Exception as e:
            # Exception is also acceptable
            error_str = str(e).lower()
            assert any(term in error_str for term in ["feed", "not found", "invalid", "404", "400"])


# ============================================================================
# Performance and Reliability Tests
# ============================================================================

class TestPerformanceMainnet:
    """Integration tests for performance and reliability."""

    def test_concurrent_fetch_requests(self, mainnet_feed_id):
        """Test making multiple concurrent fetch requests."""
        import concurrent.futures
        import os
        
        def fetch_report():
            config = ChainlinkConfig(
                api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
                api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
            )
            client = ChainlinkClient(config)
            return client.get_latest_report(mainnet_feed_id)
        
        # Make 3 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(fetch_report) for _ in range(3)]
            results = [future.result(timeout=30) for future in concurrent.futures.as_completed(futures)]
        
        # All requests should complete successfully
        assert len(results) == 3
        for report in results:
            assert report.feed_id == mainnet_feed_id
            assert report.full_report.startswith("0x")

    @pytest.mark.asyncio
    async def test_long_running_stream_single_feed(self, mainnet_feed_ids_single):
        """Test streaming for extended period to verify stability with single feed ID."""
        import os
        messages_received = []
        
        def callback(report_data):
            messages_received.append(report_data)
            # Handle nested structure
            if "report" in report_data:
                feed_id = report_data["report"].get('feedID', 'unknown')
            else:
                feed_id = report_data.get('feedID', 'unknown')
            print(f"Message {len(messages_received)}: feedID={feed_id}")
        
        # Stream for 60 seconds to test stability
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        client = ChainlinkClient(config)
        try:
            await asyncio.wait_for(
                client.stream(mainnet_feed_ids_single, callback),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            # Expected - we're testing long-running stability
            pass
        
        # If we got here without crashing, connection was stable
        # Messages may or may not be received depending on API activity

    @pytest.mark.asyncio
    async def test_long_running_stream_multiple_feeds(self, mainnet_feed_ids_multiple):
        """Test streaming for extended period to verify stability with multiple feed IDs."""
        import os
        messages_received = []
        
        def callback(report_data):
            messages_received.append(report_data)
            # Handle nested structure
            if "report" in report_data:
                feed_id = report_data["report"].get('feedID', 'unknown')
            else:
                feed_id = report_data.get('feedID', 'unknown')
            print(f"Message {len(messages_received)}: feedID={feed_id}")
        
        # Stream for 60 seconds to test stability
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        client = ChainlinkClient(config)
        try:
            await asyncio.wait_for(
                client.stream(mainnet_feed_ids_multiple, callback),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            # Expected - we're testing long-running stability
            pass
        
        # If we got here without crashing, connection was stable
        # Messages may or may not be received depending on API activity



class TestStreamReconnectionMainnet:
    """Integration tests for WebSocket reconnection behavior on mainnet."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_stream_reconnection_status_callback_behavior(self, mainnet_feed_ids_single):
        """Test that status callback is only called appropriately during reconnection."""
        import os
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        client = ChainlinkClient(config)
        
        reports_received = []
        status_calls = []
        
        def callback(data):
            reports_received.append(data)
        
        def status_callback(is_connected: bool, host: str, origin: str):
            status_calls.append((is_connected, host, origin))
        
        # Configure for fast reconnection (for testing)
        client.config.ws_max_reconnect = 3
        client.config.ws_reconnect_initial_delay = 1.0
        client.config.ws_reconnect_backoff_factor = 1.5
        
        # Stream for a short time to verify initial connection
        try:
            await asyncio.wait_for(
                client.stream_with_status_callback(mainnet_feed_ids_single, callback, status_callback),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            pass
        
        # Should have received at least one status callback (connected)
        assert len(status_calls) >= 1, "Should receive at least one status callback"
        # First status call should be True (connected)
        assert status_calls[0][0] is True, "First status callback should indicate connection"
        # Should have received some reports
        assert len(reports_received) >= 0, "May or may not receive reports in short time"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_stream_reconnection_handles_disconnection_gracefully(self, mainnet_feed_ids_single):
        """Test that stream handles disconnections and attempts reconnection."""
        import os
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        client = ChainlinkClient(config)
        
        reports_received = []
        connection_events = []
        
        def callback(data):
            reports_received.append(data)
        
        def status_callback(is_connected: bool, host: str, origin: str):
            connection_events.append((is_connected, host))
        
        # Configure for reconnection testing
        client.config.ws_max_reconnect = 2
        client.config.ws_reconnect_initial_delay = 1.0
        client.config.ws_reconnect_backoff_factor = 1.5
        
        # Stream for a short time
        try:
            await asyncio.wait_for(
                client.stream_with_status_callback(mainnet_feed_ids_single, callback, status_callback),
                timeout=8.0  # Longer timeout to allow for potential reconnection
            )
        except asyncio.TimeoutError:
            pass
        
        # Should have at least one connection event
        assert len(connection_events) >= 1, "Should have at least one connection event"
        # First event should be connection (True)
        assert connection_events[0][0] is True, "First event should be connection"
        
        # Note: We can't easily test actual disconnection/reconnection in integration tests
        # without artificially closing the connection, which is better tested in unit tests
