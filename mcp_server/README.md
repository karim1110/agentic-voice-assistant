# MCP Server Documentation

## Overview

This is a Model Context Protocol (MCP) server providing two tools for the agentic voice assistant:

1. **rag.search** - Query private product catalog (Amazon 2020 dataset)
2. **web.search** - Live web search via Brave Search API

The server exposes these tools via a FastAPI REST interface, enabling the agent pipeline to retrieve grounded evidence from both private and live data sources.

---

## Architecture

```
┌─────────────────────────────────────┐
│      LangGraph Agent Pipeline       │
│  (Router → Planner → Retriever)     │
└──────────────┬──────────────────────┘
               │ HTTP POST
               ↓
┌─────────────────────────────────────┐
│         MCP Server (FastAPI)        │
│  http://127.0.0.1:8000              │
├─────────────────────────────────────┤
│  POST /rag.search                   │
│  POST /web.search                   │
└──────────────┬──────────────────────┘
               │
        ┌──────┴──────┐
        ↓             ↓
┌──────────────┐ ┌──────────────┐
│   ChromaDB   │ │ Brave Search │
│  Vector DB   │ │     API      │
└──────────────┘ └──────────────┘
```

---

## Tool Schemas

### 1. rag.search

**Description**: Search the private product catalog using vector similarity and metadata filters.

**Endpoint**: `POST /rag.search`

**Request Schema**:
```json
{
  "query": "string (required) - Search query text",
  "top_k": "integer (optional, default: 5) - Number of results to return",
  "filters": "object (optional) - Metadata filters for refinement"
}
```

**Response Schema**:
```json
{
  "tool": "rag.search",
  "timestamp": 1234567890.123,
  "results": [
    {
      "doc_id": "string - Document ID for citation",
      "sku": "string - Product SKU",
      "title": "string - Product title (truncated to 220 chars)",
      "price": "float - Product price in USD",
      "rating": "float - Average rating (0-5)",
      "brand": "string - Brand name",
      "ingredients": "string - Product ingredients/composition"
    }
  ]
}
```

**Example Request**:
```bash
curl -X POST http://127.0.0.1:8000/rag.search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "eco-friendly stainless steel cleaner",
    "top_k": 3,
    "filters": {"price": {"$lte": 15}}
  }'
```

**Example Response**:
```json
{
  "tool": "rag.search",
  "timestamp": 1702166400.0,
  "results": [
    {
      "doc_id": "P001",
      "sku": "P001",
      "title": "EcoShine Steel Polish Plant-based formula for stainless steel...",
      "price": 12.49,
      "rating": 0.0,
      "brand": "",
      "ingredients": ""
    }
  ]
}
```

**Filters Supported**:
- `price`: `{"$lte": 15}` (less than or equal)
- `brand`: `{"$eq": "Lysol"}` (exact match)
- Multiple filters combined with `$and`

---

### 2. web.search

**Description**: Search the web via Brave Search API for live product information, prices, and availability.

**Endpoint**: `POST /web.search`

**Request Schema**:
```json
{
  "query": "string (required) - Search query text",
  "top_k": "integer (optional, default: 5) - Number of results to return (max: 5)"
}
```

**Response Schema**:
```json
{
  "tool": "web.search",
  "timestamp": 1234567890.123,
  "results": [
    {
      "title": "string - Result title",
      "url": "string - Source URL",
      "snippet": "string - Text snippet",
      "profile": "string|null - Source profile name",
      "price": "null - Price (if extractable)",
      "availability": "null - Availability (if extractable)"
    }
  ]
}
```

**Example Request**:
```bash
curl -X POST http://127.0.0.1:8000/web.search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Lysol disinfectant spray current price",
    "top_k": 3
  }'
```

**Example Response**:
```json
{
  "tool": "web.search",
  "timestamp": 1702166400.0,
  "results": [
    {
      "title": "Lysol Disinfectant Spray 19 oz - Amazon",
      "url": "https://www.amazon.com/...",
      "snippet": "Buy Lysol Disinfectant Spray 19 oz for $10.49...",
      "profile": "Amazon",
      "price": null,
      "availability": null
    }
  ]
}
```

**Rate Limiting**: 
- Currently no rate limiting implemented
- Recommended: 10 requests/minute for production

**Caching**:
- Currently no caching implemented
- Recommended: TTL 300s (5 minutes) for production

---

## API Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...           # For embeddings in rag.search
SEARCH_API_KEY=your-brave-key   # For web.search
SEARCH_PROVIDER=brave           # Web search provider

# Optional
INDEX_PATH=./data/index         # ChromaDB storage path
EMBED_MODEL=all-MiniLM-L6-v2   # Embedding model
MCP_PORT=8000                   # Server port
```

---

## Running the Server

### Start Server:
```bash
# Using batch file (Windows)
.\start_mcp_server.bat

# Using uvicorn directly
python -m uvicorn mcp_server.server:app --host 127.0.0.1 --port 8000

# With auto-reload (development)
python -m uvicorn mcp_server.server:app --reload --port 8000
```

### Verify Server:
```bash
# Check if server is running
curl http://127.0.0.1:8000/docs

# Test rag.search
curl -X POST http://127.0.0.1:8000/rag.search \
  -H "Content-Type: application/json" \
  -d '{"query":"cleaner","top_k":3}'

# Test web.search
curl -X POST http://127.0.0.1:8000/web.search \
  -H "Content-Type: application/json" \
  -d '{"query":"lysol spray price","top_k":3}'
```

---

## MCP Protocol Compliance

### Current Implementation:
- ✅ Two tools exposed via HTTP POST
- ✅ JSON request/response format
- ✅ Timestamp logging
- ✅ Error handling with HTTP status codes

### Not Yet Implemented:
- ❌ Tool discovery endpoint (GET /tools)
- ❌ stdio transport (HTTP only)
- ❌ Server-Sent Events (SSE) streaming
- ❌ Request/response caching with TTL
- ❌ Rate limiting

### Future Enhancements:

**Discovery Endpoint**:
```python
@app.get("/tools")
def list_tools():
    return {
        "tools": [
            {
                "name": "rag.search",
                "description": "Search private product catalog",
                "input_schema": {...},
                "output_schema": {...}
            },
            {
                "name": "web.search",
                "description": "Search web for live data",
                "input_schema": {...},
                "output_schema": {...}
            }
        ]
    }
```

**Caching Strategy**:
```python
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def cached_web_search(query, timestamp_bucket):
    # Cache for 5-minute buckets
    return web_search(query)

def web_endpoint(q: WebQuery):
    bucket = int(time.time() // 300)  # 5-min TTL
    return cached_web_search(q.query, bucket)
```

---

## Safety & Compliance

### Web Search:
- **API Used**: Brave Search API (https://api.search.brave.com)
- **ToS Compliance**: Respects Brave Search Terms of Service
- **Rate Limits**: No enforcement (should add in production)
- **robots.txt**: Not checked (web API handles this)

### Data Privacy:
- No user queries logged permanently
- Temporary logs for debugging only
- API keys stored in environment variables (not committed)

### Security:
- No authentication on MCP server (internal use only)
- Should add API key authentication for production
- HTTPS recommended for production deployment

---

## Error Handling

### Common Errors:

**rag.search**:
- `500 Internal Server Error` - ChromaDB connection failed
- `400 Bad Request` - Invalid filter syntax
- `200 OK` with `results: []` - No matches found

**web.search**:
- `500 Internal Server Error` - Brave API failed or key invalid
- `200 OK` with `results: []` - No web results (API key not set)

### Debugging:
```bash
# Check server logs
# Look for error messages in terminal

# Test ChromaDB connection
python -c "import chromadb; client = chromadb.PersistentClient(path='./data/index'); print('OK')"

# Test Brave API
curl -X GET "https://api.search.brave.com/res/v1/web/search?q=test" \
  -H "X-Subscription-Token: YOUR_KEY"
```

---

## Performance

### Typical Response Times:
- **rag.search**: 50-200ms (vector search + retrieval)
- **web.search**: 500-1500ms (external API call)

### Optimization Tips:
1. Use metadata filters to reduce search space
2. Limit `top_k` to 5 or fewer
3. Cache web.search results (not implemented)
4. Use connection pooling for ChromaDB

---

## Development

### File Structure:
```
mcp_server/
├── __init__.py          # Package init
├── server.py            # FastAPI app
├── tools/
│   ├── __init__.py      # Tools package init
│   ├── rag_tool.py      # RAG search implementation
│   └── web_tool.py      # Web search implementation
└── README.md            # This file
```

### Adding a New Tool:

1. Create tool file in `tools/`:
```python
# mcp_server/tools/my_tool.py
def my_tool_search(query, param):
    # Implementation
    return results
```

2. Add endpoint in `server.py`:
```python
from mcp_server.tools.my_tool import my_tool_search

@app.post("/my.tool")
def my_tool_endpoint(q: MyQuery):
    results = my_tool_search(q.query, q.param)
    return {"tool": "my.tool", "timestamp": time.time(), "results": results}
```

3. Update this README with schema

---

## Testing

### Unit Tests (Not Implemented):
```python
# tests/test_mcp.py
import pytest
from mcp_server.tools.rag_tool import rag_search

def test_rag_search():
    results = rag_search("cleaner", top_k=3)
    assert len(results) <= 3
    assert all("title" in r for r in results)
```

### Integration Test:
```bash
# Start server
python -m uvicorn mcp_server.server:app --port 8000 &

# Test both endpoints
curl -X POST http://127.0.0.1:8000/rag.search -d '{"query":"test","top_k":1}'
curl -X POST http://127.0.0.1:8000/web.search -d '{"query":"test","top_k":1}'
```

---

## References

- **MCP Specification**: (Link to MCP protocol docs if available)
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **ChromaDB Docs**: https://docs.trychroma.com/
- **Brave Search API**: https://api.search.brave.com/

---

**Version**: 1.0  
**Last Updated**: December 2025  
**Maintainer**: UChicago Applied Gen AI Final Project

