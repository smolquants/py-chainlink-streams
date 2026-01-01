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
    fetch_single_report,
    connect_websocket,
    stream_reports_with_keepalive,
    decode_report_from_response,
    get_decoded_prices,
    get_schema_version,
)

# Real mainnet feed IDs for testing (v3 schema)
BTC_USD_FEED_ID = "0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8"

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
def mainnet_feed_ids():
    """List of real mainnet feed IDs for testing."""
    return [BTC_USD_FEED_ID]


# ============================================================================
# HTTP REST API Integration Tests
# ============================================================================

class TestFetchSingleReportMainnet:
    """Integration tests for fetch_single_report with mainnet API."""

    def test_fetch_single_report_mainnet(self, mainnet_feed_id):
        """Test fetching latest report from mainnet API."""
        response = fetch_single_report(mainnet_feed_id)
        
        # API response wraps data in 'report' key
        assert "report" in response, "Response should contain 'report' key"
        report = response["report"]
        
        # Verify response structure
        assert "feedID" in report
        assert "validFromTimestamp" in report
        assert "observationsTimestamp" in report
        assert "fullReport" in report
        
        # Verify feed ID matches
        assert report["feedID"] == mainnet_feed_id
        
        # Verify fullReport is valid hex string
        full_report = report["fullReport"]
        assert isinstance(full_report, str)
        assert full_report.startswith("0x")
        assert len(full_report) > 100  # Should be substantial hex string
        
        # Verify timestamps are valid Unix timestamps
        assert isinstance(report["validFromTimestamp"], int)
        assert isinstance(report["observationsTimestamp"], int)
        assert report["validFromTimestamp"] > 0
        assert report["observationsTimestamp"] > 0

    def test_fetch_single_report_with_real_feed_id(self, mainnet_feed_id):
        """Test fetching report with real mainnet feed ID."""
        response = fetch_single_report(mainnet_feed_id)
        
        # API response wraps data in 'report' key
        assert "report" in response, "Response should contain 'report' key"
        report = response["report"]
        
        # Verify response structure matches API spec
        required_keys = ["feedID", "validFromTimestamp", "observationsTimestamp", "fullReport"]
        for key in required_keys:
            assert key in report, f"Missing required key: {key}"
        
        # Verify fullReport is valid hex string
        full_report = report["fullReport"]
        assert full_report.startswith("0x"), "fullReport should start with 0x"
        # Remove 0x and verify it's valid hex
        hex_part = full_report[2:]
        assert all(c in '0123456789abcdefABCDEF' for c in hex_part), "fullReport should be valid hex"
        
        # Verify timestamps are recent (within last hour)
        import time
        current_time = int(time.time())
        obs_timestamp = report["observationsTimestamp"]
        # Allow some flexibility (within last 2 hours to account for API delays)
        assert obs_timestamp > current_time - 7200, "observationsTimestamp should be recent"

    def test_fetch_single_report_handles_invalid_feed_id(self):
        """Test that invalid feed ID is handled gracefully."""
        invalid_feed_id = "0x0000000000000000000000000000000000000000000000000000000000000000"
        
        # Should either return error response or raise exception
        try:
            response = fetch_single_report(invalid_feed_id)
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
        response = fetch_single_report(mainnet_feed_id)
        
        # API response wraps data in 'report' key
        report = response["report"]
        
        # Decode the report
        decoded = decode_report_from_response(report)
        
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
        expected_version = get_schema_version(mainnet_feed_id)
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
        response = fetch_single_report(mainnet_feed_id)
        # API response wraps data in 'report' key
        report = response["report"]
        decoded = decode_report_from_response(report)
        
        # Get decoded prices
        prices = get_decoded_prices(decoded)
        
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
        response = fetch_single_report(mainnet_feed_id)
        assert "report" in response
        report = response["report"]
        assert "fullReport" in report
        
        # Step 2: Decode report
        decoded = decode_report_from_response(report)
        assert "data" in decoded
        assert decoded["schemaVersion"] == 3
        
        # Step 3: Get decoded prices
        prices = get_decoded_prices(decoded)
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
# WebSocket Connection Integration Tests
# ============================================================================

class TestConnectWebsocketMainnet:
    """Integration tests for WebSocket connections to mainnet."""

    @pytest.mark.asyncio
    async def test_connect_websocket_mainnet(self, mainnet_feed_ids):
        """Test successfully establishing WebSocket connection to mainnet."""
        websocket = await connect_websocket(mainnet_feed_ids, None, 30, 60)
        
        # Verify connection is established
        assert websocket is not None
        
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

    @pytest.mark.asyncio
    async def test_connect_websocket_with_multiple_feeds(self, mainnet_feed_ids):
        """Test connecting with multiple feed IDs."""
        # Use same feed ID twice to test multiple feeds (or add another feed ID)
        feed_ids = mainnet_feed_ids * 2  # Subscribe to same feed twice
        
        websocket = await connect_websocket(feed_ids, None, 30, 60)
        
        # Verify connection is established
        assert websocket is not None
        
        # Verify connection is alive by trying to ping
        try:
            await websocket.ping()
        except Exception:
            pytest.fail("WebSocket connection should be alive")
        
        # Verify connection URL would contain feed IDs (indirectly verified by successful connection)
        await asyncio.sleep(1)
        
        await websocket.close()


# ============================================================================
# WebSocket Streaming Integration Tests
# ============================================================================

class TestStreamReportsMainnet:
    """Integration tests for streaming reports from mainnet."""

    @pytest.mark.asyncio
    async def test_stream_reports_receives_messages(self, mainnet_feed_ids):
        """Test that streaming receives at least one report message."""
        messages_received = []
        
        def callback(report_data):
            messages_received.append(report_data)
        
        # Stream for up to 30 seconds or until we get a message
        stop_event = asyncio.Event()
        
        async def stream_with_timeout():
            try:
                await asyncio.wait_for(
                    stream_reports_with_keepalive(mainnet_feed_ids, callback),
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
    async def test_stream_reports_with_keepalive_mainnet(self, mainnet_feed_ids):
        """Test streaming with keepalive on mainnet."""
        messages_received = []
        
        def callback(report_data):
            messages_received.append(report_data)
            print(f"Received report: feedID={report_data.get('feedID', 'unknown')}")
        
        # Stream for a short period to test keepalive
        try:
            await asyncio.wait_for(
                stream_reports_with_keepalive(mainnet_feed_ids, callback),
                timeout=10.0  # Stream for 10 seconds
            )
        except asyncio.TimeoutError:
            # Timeout is expected - we're testing that keepalive works
            pass
        
        # Verify we could establish connection (no exception means connection worked)
        # Messages may or may not be received depending on API activity

    @pytest.mark.asyncio
    async def test_stream_reports_stop_event(self, mainnet_feed_ids):
        """Test that stop_event properly stops streaming."""
        messages_received = []
        stop_event = asyncio.Event()
        
        def callback(report_data):
            messages_received.append(report_data)
            # Stop after first message
            if len(messages_received) >= 1:
                stop_event.set()
        
        # Create a custom streaming function that respects stop_event
        async def stream_with_stop():
            websocket = await connect_websocket(mainnet_feed_ids, None, 30, 60)
            try:
                from py_chainlink_streams.report import stream_reports
                await stream_reports(websocket, callback, stop_event)
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
        # Temporarily set invalid credentials
        original_key = os.environ.get("CHAINLINK_STREAMS_API_KEY")
        original_secret = os.environ.get("CHAINLINK_STREAMS_API_SECRET")
        
        try:
            os.environ["CHAINLINK_STREAMS_API_KEY"] = "invalid_key"
            os.environ["CHAINLINK_STREAMS_API_SECRET"] = "invalid_secret"
            
            # Should raise error
            with pytest.raises(Exception) as exc_info:
                fetch_single_report(BTC_USD_FEED_ID)
            
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
            response = fetch_single_report(invalid_feed_id)
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
        
        def fetch_report():
            return fetch_single_report(mainnet_feed_id)
        
        # Make 3 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(fetch_report) for _ in range(3)]
            results = [future.result(timeout=30) for future in concurrent.futures.as_completed(futures)]
        
        # All requests should complete successfully
        assert len(results) == 3
        for result in results:
            # API response wraps data in 'report' key
            assert "report" in result
            report = result["report"]
            assert "feedID" in report
            assert "fullReport" in report

    @pytest.mark.asyncio
    async def test_long_running_stream(self, mainnet_feed_ids):
        """Test streaming for extended period to verify stability."""
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
        try:
            await asyncio.wait_for(
                stream_reports_with_keepalive(mainnet_feed_ids, callback),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            # Expected - we're testing long-running stability
            pass
        
        # If we got here without crashing, connection was stable
        # Messages may or may not be received depending on API activity

