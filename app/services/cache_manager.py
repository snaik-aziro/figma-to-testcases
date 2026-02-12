"""Cache management for Figma data to prevent API rate limiting."""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any


class CacheManager:
    """Manages caching of Figma file data."""

    def __init__(self, cache_dir: str = ".cache/figma"):
        """Initialize cache manager.
        
        Args:
            cache_dir: Directory to store cached files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, file_id: str) -> Path:
        """Get cache file path for a Figma file ID.
        
        Args:
            file_id: Figma file ID
            
        Returns:
            Path to cache file
        """
        # Sanitize file ID for safe filename
        safe_filename = file_id.replace("/", "_").replace(":", "_")
        return self.cache_dir / f"{safe_filename}.json"

    def _get_metadata_path(self, file_id: str) -> Path:
        """Get metadata file path for a Figma file ID.
        
        Args:
            file_id: Figma file ID
            
        Returns:
            Path to metadata file
        """
        safe_filename = file_id.replace("/", "_").replace(":", "_")
        return self.cache_dir / f"{safe_filename}_meta.json"

    def save(self, file_id: str, data: Dict[str, Any], file_name: str = "") -> str:
        """Save Figma file data to cache.
        
        Args:
            file_id: Figma file ID
            data: Figma file data (screens, components, etc.)
            file_name: Human-readable file name for metadata
            
        Returns:
            Path to cached file
        """
        cache_path = self._get_cache_path(file_id)
        
        # Save data
        try:
            with open(cache_path, "w") as f:
                json.dump(data, f, indent=2)
        except TypeError as e:
            print(f"Error serializing data for cache: {e}")
            # Fallback for non-serializable data: convert to string representation
            with open(cache_path, "w") as f:
                json.dump(json.loads(json.dumps(data, default=str)), f, indent=2)

        # Save metadata
        metadata = {
            "file_id": file_id,
            "file_name": file_name,
            "cached_at": datetime.now().isoformat(),
        }
        
        # Safely calculate data size
        try:
            data_size = len(json.dumps(data))
        except TypeError:
            data_size = -1 # Indicate serialization issue
        
        metadata["data_size"] = data_size
        metadata["screens_count"] = len(data.get("screens", [])) if isinstance(data, dict) else 0
        
        meta_path = self._get_metadata_path(file_id)
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)

        return str(cache_path)

    def load(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Load Figma file data from cache.
        
        Args:
            file_id: Figma file ID
            
        Returns:
            Cached data or None if not found
        """
        cache_path = self._get_cache_path(file_id)
        
        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading cache: {e}")
            return None

    def exists(self, file_id: str) -> bool:
        """Check if a cached file exists for a Figma file ID."""
        return self._get_cache_path(file_id).exists()

    def is_stale(self, file_id: str, ttl_minutes: int = 1440) -> bool:
        """Check if cache for a Figma file is stale.
        
        Args:
            file_id: Figma file ID
            ttl_minutes: Time-to-live in minutes (default 24 hours)
            
        Returns:
            True if cache is stale or doesn't exist, False otherwise
        """
        meta_path = self._get_metadata_path(file_id)
        if not meta_path.exists():
            return True

        try:
            with open(meta_path, "r") as f:
                metadata = json.load(f)
            
            cached_at = datetime.fromisoformat(metadata["cached_at"])
            age = datetime.now() - cached_at
            
            return age.total_seconds() > ttl_minutes * 60
        except (json.JSONDecodeError, KeyError, IOError):
            return True

    def clear(self, file_id: str = None):
        """Clear cache for a specific file or the entire cache.
        
        Args:
            file_id: If provided, clear cache for this file ID only.
                     Otherwise, clear the entire cache directory.
        """
        if file_id:
            # Clear specific file and its metadata
            cache_path = self._get_cache_path(file_id)
            meta_path = self._get_metadata_path(file_id)
            if cache_path.exists():
                os.remove(cache_path)
            if meta_path.exists():
                os.remove(meta_path)
        else:
            # Clear entire cache directory
            for item in self.cache_dir.iterdir():
                os.remove(item)
    
    def list_cached_files(self) -> List[Dict[str, Any]]:
        """List all cached files with their metadata.
        
        Returns:
            List of metadata dictionaries for cached files
        """
        cached_files = []
        for meta_file in self.cache_dir.glob("*_meta.json"):
            try:
                with open(meta_file, "r") as f:
                    metadata = json.load(f)
                    # Add file path for convenience
                    metadata["cache_path"] = str(self._get_cache_path(metadata["file_id"]))
                    cached_files.append(metadata)
            except (json.JSONDecodeError, KeyError, IOError):
                continue
                
        # Sort by cached date, newest first
        cached_files.sort(key=lambda x: x.get("cached_at", ""), reverse=True)
        return cached_files

    def delete(self, file_id: str) -> bool:
        """Delete cached file and its metadata.
        
        Args:
            file_id: Figma file ID
            
        Returns:
            True if deleted, False if not found
        """
        cache_path = self._get_cache_path(file_id)
        meta_path = self._get_metadata_path(file_id)

        deleted = False
        
        if cache_path.exists():
            cache_path.unlink()
            deleted = True

        if meta_path.exists():
            meta_path.unlink()

        return deleted

    def clear_all(self) -> int:
        """Clear all cached files.
        
        Returns:
            Number of files deleted
        """
        count = 0
        
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1

        return count

    def get_cache_size(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        total_size = 0
        file_count = 0

        for cache_file in self.cache_dir.glob("*.json"):
            if not cache_file.name.endswith("_meta.json"):
                total_size += cache_file.stat().st_size
                file_count += 1

        return {
            "total_files": file_count,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_dir": str(self.cache_dir),
        }
