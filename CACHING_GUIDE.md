# Figma Data Caching Feature

## Overview

The QA Test Generator now includes an intelligent caching system that prevents unnecessary Figma API calls. This is essential for:

- **Rate Limit Protection**: Figma API has rate limits; caching prevents hitting them during testing/iteration
- **Faster Iteration**: Load previously fetched data instantly instead of waiting for API calls
- **Offline Testing**: Work with cached data when API is unavailable
- **Cost Optimization**: Reduce API request overhead in production deployments

## How It Works

### Data Source Selection (Streamlit UI)

The sidebar now has two options for loading Figma design data:

1. **Fetch from Figma API** (Default)
   - Connects to your Figma account using personal access token
   - Fetches latest design data from your Figma file
   - Automatically caches the data for future use
   - Shows progress indicators during fetch

2. **Load from Cache** (Available when cache exists)
   - Lists all previously cached Figma files
   - Shows cache date and screen count
   - Loads data instantly without API call
   - Allows deletion of individual cached files

### Cache Storage

- **Location**: `.cache/figma_data/` directory
- **File Structure**:
  ```
  .cache/figma_data/
  ├── file_id_abc123.json          # Cached Figma data
  ├── file_id_abc123_meta.json     # Metadata (date, name, count)
  ├── file_id_def456.json
  └── file_id_def456_meta.json
  ```

### Cache Metadata

Each cached file includes metadata:
```json
{
  "file_id": "abc123xyz",
  "file_name": "Login Screen Designs",
  "cached_at": "2026-02-03T14:30:45.123456",
  "data_size": 156789,
  "screens_count": 12
}
```

## Usage Examples

### Example 1: First-Time Fetch and Cache

```
1. Select "Fetch from Figma API"
2. Enter Figma URL and token
3. Click "Load & Analyze"
4. Data is fetched and automatically cached
5. Success message shows cache status
```

### Example 2: Use Cached Data

```
1. Select "Load from Cache"
2. Choose cached file from dropdown (shows date cached)
3. Click "Load & Analyze"
4. Data loads instantly, no API call made
```

### Example 3: Manage Cache

```
1. Select "Load from Cache"
2. Choose file to delete
3. Click "Delete Cache" button
4. Cache is removed, file re-added after next fetch
```

## Cache Statistics

The UI displays cache information:

```
Cache Info (2 files)
├── Cache Size: 0.23 MB
├── Location: .cache/figma_data
└── Files: 2 cached Figma designs
```

## API Rate Limiting

### Figma Rate Limits
- **Standard**: 1000 requests/minute per file
- **Enterprise**: Higher limits

### Caching Strategy
With caching enabled:
- First call: ~1 API request
- Subsequent calls: 0 API requests (instant)
- Multiple iterations: ~1 API request total per file
- Team sharing: Share cached files, no additional API calls

## Configuration

### Environment Variables

```bash
# Enable/disable caching
ENABLE_CACHING=true

# Cache directory
CACHE_DIR=.cache/figma_data

# Cache expiration (optional, future feature)
# CACHE_EXPIRY_DAYS=7
```

### Runtime Configuration

In `config.py`:
```python
cache_dir = ".cache/figma_data"  # Customize as needed
```

## API Reference

### CacheManager Class

```python
from app.services.cache_manager import CacheManager

# Initialize
cache = CacheManager(cache_dir=".cache/figma_data")

# Save data
cache.save(file_id="abc123", data={...}, file_name="My Design")

# Load data
data = cache.load(file_id="abc123")

# Check if exists
exists = cache.exists(file_id="abc123")

# Get all cached files
files = cache.get_all_cached_files()

# Delete specific cache
cache.delete(file_id="abc123")

# Clear all caches
count = cache.clear_all()

# Get cache statistics
stats = cache.get_cache_size()
# Returns: {"total_files": 2, "total_size_mb": 0.23, "cache_dir": "..."}
```

## Best Practices

### 1. Fresh Data When Needed
```
If you update designs in Figma:
1. Select "Fetch from Figma API" to get latest
2. Previous cache will be overwritten with new data
```

### 2. Cache Management
```
Periodically clean up old caches:
1. Go to cache info expander
2. Delete unused cached files
3. Keep only active project caches
```

### 3. Team Sharing
```
Share cached files with team:
1. Commit .cache/figma_data/ to version control (optional)
2. Team members can load from cache without API tokens
3. Reduces per-person API quotas
```

### 4. CI/CD Pipeline
```
In automated testing:
1. Cache Figma data at build time
2. Use cached data in test runs
3. Update cache only on schedule (e.g., daily)
4. Saves API calls and improves pipeline speed
```

## Troubleshooting

### Cache File Not Appearing

**Problem**: Cached file doesn't appear in dropdown

**Solutions**:
1. Refresh Streamlit (`R` key)
2. Check that file was cached successfully (look for success message)
3. Check `.cache/figma_data/` directory exists
4. Verify `.env` file `ENABLE_CACHING=true`

### Cannot Load Cached Data

**Problem**: "Failed to load cache" error

**Solutions**:
1. Clear cache and re-fetch: `cache.clear_all()`
2. Check file permissions in `.cache/figma_data/`
3. Verify JSON file isn't corrupted: `validate_integration.py`

### Cache Taking Up Space

**Problem**: `.cache/` directory too large

**Solutions**:
1. Delete individual caches via UI
2. Run: `cache.clear_all()` to remove all
3. Set up automated cleanup (future feature)
4. Use `.gitignore`: Add `.cache/` to prevent version control bloat

## Future Enhancements

- [ ] Cache expiration (TTL-based automatic cleanup)
- [ ] Compression (reduce cache size)
- [ ] Encryption (secure sensitive data)
- [ ] Cloud sync (share caches across devices)
- [ ] Incremental updates (only fetch changed components)
- [ ] Cache versioning (track design iterations)

## Performance Impact

### Load Time Comparison

| Operation | Without Cache | With Cache |
|-----------|---------------|-----------|
| First load | 5-15 sec (API) | 5-15 sec (API) |
| Reload | 5-15 sec (API) | 1-2 sec (cache) |
| Multiple iterations | 30-60 sec (4-5 calls) | 5-15 sec (1 API call) |

### File Size Impact

- Typical Figma file: 100-500 KB cached
- Large design system: 500 KB - 2 MB
- Minimal impact on repository size (add to `.gitignore`)

## See Also

- [CacheManager Source](../app/services/cache_manager.py)
- [Streamlit UI](../demo_ui.py)
- [Integration Notes](INTEGRATION_NOTES.md)
