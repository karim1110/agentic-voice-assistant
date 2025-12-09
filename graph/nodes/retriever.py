import os
import httpx
import time


def call_tool(path, payload):
    """Call MCP tool endpoint with error handling."""
    try:
        with httpx.Client(timeout=20) as c:
            r = c.post(path, json=payload)
            r.raise_for_status()
            return r.json().get("results", [])
    except httpx.HTTPError as e:
        print(f"[retriever] HTTP error calling {path}: {e}")
        return []
    except Exception as e:
        print(f"[retriever] Unexpected error: {e}")
        return []


def retrieve(state):
    """
    Retriever Agent: Execute tool calls based on plan.
    """
    base = os.getenv("MCP_BASE", "http://127.0.0.1:8000")
    plan = state.get("plan") or {}
    sources = plan.get("sources", ["rag.search"])
    
    evidence = {}
    tool_calls = []
    
    # Call RAG tool
    if "rag.search" in sources:
        start = time.time()
        # ENFORCE: never send category filters (they don't match hierarchical paths)
        filters = plan.get("filters", {})
        filters.pop("category", None)  # strip category if present
        payload = {
            "query": plan.get("query_text", state.get("transcript", "")),
            "top_k": plan.get("top_k", 5),
            "filters": filters
        }
        
        results = call_tool(f"{base}/rag.search", payload)
        evidence["rag"] = results
        
        tool_calls.append({
            "tool": "rag.search",
            "payload": payload,
            "results_count": len(results),
            "duration_ms": int((time.time() - start) * 1000)
        })
    
    # Call Web tool
    if "web.search" in sources:
        start = time.time()
        payload = {
            "query": plan.get("query_text", state.get("transcript", "")),
            "top_k": min(plan.get("top_k", 5), 5)  # Limit web to 5 max
        }
        
        results = call_tool(f"{base}/web.search", payload)
        evidence["web"] = results
        
        tool_calls.append({
            "tool": "web.search",
            "payload": payload,
            "results_count": len(results),
            "duration_ms": int((time.time() - start) * 1000)
        })
    
    # Update state
    state.update(evidence=evidence)
    state.setdefault("log", []).append({
        "node": "retriever",
        "tool_calls": tool_calls,
        "total_results": {k: len(v) for k, v in evidence.items()}
    })
    
    return state
