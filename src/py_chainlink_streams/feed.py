"""
Feed information classes for Chainlink Data Streams API.
"""

from typing import Dict, Any


class Feed:
    """
    Feed information from Chainlink Data Streams API.
    
    Attributes:
        id: Feed identifier (hex string)
        name: Feed name (optional)
        other fields as returned by API
    """
    
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id", data.get("feedID", ""))
        self.name = data.get("name", "")
        self._data = data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return self._data
    
    @staticmethod
    def get_schema_version(feed_id: str) -> int:
        """
        Determine the report schema version from the feed ID prefix.
        
        Schema versions are determined by the first 4 hex characters after '0x':
        - 0x0001 = v1
        - 0x0002 = v2
        - 0x0003 = v3 (Crypto Streams)
        - 0x0004 = v4
        - etc.
        
        Args:
            feed_id: Feed ID hex string (e.g., "0x000359843a543ee2...")
            
        Returns:
            Schema version number (e.g., 3 for v3)
        """
        if not feed_id.startswith('0x'):
            raise ValueError(f"Invalid feed ID format: {feed_id}")
        
        # Extract first 4 hex chars (2 bytes) after '0x'
        prefix = feed_id[2:6]
        try:
            version = int(prefix, 16)
            return version
        except ValueError:
            raise ValueError(f"Could not determine schema version from feed ID: {feed_id}")
    
    def schema_version(self) -> int:
        """
        Get the schema version for this feed.
        
        Returns:
            Schema version number (e.g., 3 for v3)
        """
        return self.get_schema_version(self.id)

