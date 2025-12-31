#!/usr/bin/env python3
"""Basic integration tests for py-chainlink-streams client."""

import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    try:
        from py_chainlink_streams import (
            fetch_single_report,
            connect_websocket,
            stream_reports,
            stream_reports_with_keepalive,
            get_schema_version,
            decode_report_from_response,
            get_decoded_prices,
            convert_fixed_point_to_decimal,
            MAINNET_API_HOST,
            TESTNET_API_HOST,
            generate_hmac,
            generate_auth_headers,
        )
        print("✓ All imports successful!")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_schema_version():
    """Test schema version detection."""
    print("\nTesting schema version detection...")
    try:
        from py_chainlink_streams import get_schema_version
        feed_id = '0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8'
        version = get_schema_version(feed_id)
        assert version == 3, f"Expected version 3, got {version}"
        print(f"✓ Schema version detection: v{version}")
        return True
    except Exception as e:
        print(f"✗ Schema version error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fixed_point_conversion():
    """Test fixed point to decimal conversion."""
    print("\nTesting fixed point conversion...")
    try:
        from py_chainlink_streams import convert_fixed_point_to_decimal
        price = 87656352262094430000000
        decimal_price = convert_fixed_point_to_decimal(price)
        expected = 87656.35
        assert abs(decimal_price - expected) < 0.01, f"Expected ~{expected}, got {decimal_price}"
        print(f"✓ Fixed point conversion: {price} -> ${decimal_price:.2f}")
        return True
    except Exception as e:
        print(f"✗ Fixed point conversion error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hmac_generation():
    """Test HMAC and auth header generation."""
    print("\nTesting HMAC generation...")
    try:
        from py_chainlink_streams import generate_hmac, generate_auth_headers
        api_key = 'test-key'
        api_secret = 'test-secret'
        method = 'GET'
        path = '/api/v1/reports/latest?feedID=0x123'
        body = b''
        
        signature, timestamp = generate_hmac(method, path, body, api_key, api_secret)
        assert len(signature) == 64, f"Expected 64-char hex signature, got {len(signature)}"
        assert isinstance(timestamp, int), f"Expected int timestamp, got {type(timestamp)}"
        print(f"✓ HMAC generation: signature={signature[:20]}..., timestamp={timestamp}")
        
        headers = generate_auth_headers(method, path, api_key, api_secret, body)
        assert 'Authorization' in headers
        assert 'X-Authorization-Timestamp' in headers
        assert 'X-Authorization-Signature-SHA256' in headers
        print(f"✓ Auth headers: {list(headers.keys())}")
        return True
    except Exception as e:
        print(f"✗ HMAC/auth error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_constants():
    """Test constants are accessible."""
    print("\nTesting constants...")
    try:
        from py_chainlink_streams import (
            MAINNET_API_HOST,
            MAINNET_WS_HOST,
            TESTNET_API_HOST,
            TESTNET_WS_HOST,
            DEFAULT_PING_INTERVAL,
            DEFAULT_PONG_TIMEOUT,
        )
        print(f"✓ Constants loaded:")
        print(f"  MAINNET_API_HOST: {MAINNET_API_HOST}")
        print(f"  MAINNET_WS_HOST: {MAINNET_WS_HOST}")
        print(f"  TESTNET_API_HOST: {TESTNET_API_HOST}")
        print(f"  TESTNET_WS_HOST: {TESTNET_WS_HOST}")
        print(f"  DEFAULT_PING_INTERVAL: {DEFAULT_PING_INTERVAL}s")
        print(f"  DEFAULT_PONG_TIMEOUT: {DEFAULT_PONG_TIMEOUT}s")
        return True
    except Exception as e:
        print(f"✗ Constants error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing py-chainlink-streams client")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_schema_version,
        test_fixed_point_conversion,
        test_hmac_generation,
        test_constants,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())

