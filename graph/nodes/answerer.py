import json
from rapidfuzz import fuzz
from graph.llm_client import get_llm_client, load_prompt


def reconcile(rag_items, web_items):
    """Match RAG results with web results using fuzzy matching."""
    out = []
    for r in rag_items:
        match = None
        score_best = 0
        for w in (web_items or []):
            s = fuzz.token_set_ratio(r.get("title", ""), w.get("title", ""))
            if s > score_best:
                score_best, match = s, w
        
        # Check for price conflict
        conflict = None
        if match and r.get("price") and match.get("price"):
            try:
                rag_price = float(r["price"])
                web_price = float(match["price"])
                diff_pct = abs(rag_price - web_price) / rag_price * 100
                if diff_pct > 10:
                    conflict = f"price_diff_{diff_pct:.1f}%"
            except (ValueError, TypeError):
                pass
        
        out.append({
            "primary": r,
            "web_match": match if score_best > 80 else None,
            "score": score_best,
            "conflict": conflict
        })
    return out


def answer(state):
    """
    Answerer Agent: Synthesize grounded response using LLM.
    """
    rag = (state.get("evidence") or {}).get("rag", [])
    web = (state.get("evidence") or {}).get("web", [])
    plan = state.get("plan") or {}
    transcript = state.get("transcript", "")
    
    # Check for empty evidence
    if not rag and not web:
        state.update(
            answer="I couldn't find any products matching those criteria. Try broadening your search or adjusting filters.",
            citations=[]
        )
        state.setdefault("log", []).append({"node": "answerer", "status": "no_results"})
        return state
    
    # Reconcile sources
    reconciled = reconcile(rag, web)
    
    # Sort by ranking strategy
    ranking = plan.get("ranking", "relevance")
    if ranking == "price_asc":
        reconciled = sorted(reconciled, key=lambda x: x["primary"].get("price") or 1e9)
    elif ranking == "rating_desc":
        reconciled = sorted(reconciled, key=lambda x: -(x["primary"].get("rating") or 0))
    elif ranking == "price_per_oz_asc":
        reconciled = sorted(reconciled, key=lambda x: x["primary"].get("price_per_oz") or 1e9)
    
    # Take top 3
    top = reconciled[:3]
    
    # Load system prompt
    system_prompt = load_prompt("system_answerer.md")
    
    # Prepare evidence summary
    evidence_text = "## Evidence Retrieved:\n\n"
    for i, item in enumerate(top, 1):
        p = item["primary"]
        evidence_text += f"{i}. **{p.get('title', 'Unknown')}**\n"
        evidence_text += f"   - Doc ID: {p.get('doc_id') or p.get('sku')}\n"
        evidence_text += f"   - Price: ${p.get('price', 'N/A')}\n"
        evidence_text += f"   - Rating: {p.get('rating', 'N/A')}\n"
        evidence_text += f"   - Brand: {p.get('brand') or 'N/A'}\n"
        evidence_text += f"   - Category: {p.get('category', 'N/A')}\n"
        
        if item["web_match"]:
            w = item["web_match"]
            evidence_text += f"   - Web Match (score {item['score']}):\n"
            evidence_text += f"     - URL: {w.get('url')}\n"
            evidence_text += f"     - Snippet: {w.get('snippet', 'N/A')[:100]}\n"
            if item["conflict"]:
                evidence_text += f"     - **CONFLICT**: {item['conflict']}\n"
        
        evidence_text += "\n"
    
    # Prepare messages
    context = f"""
User query: {transcript}

{evidence_text}

Synthesize a concise voice response (≤15 seconds / ~50 words) with proper citations.
"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": context}
    ]
    
    # Call LLM
    try:
        llm = get_llm_client()
        response = llm.chat(messages, temperature=0.4, max_tokens=300)
        
        # Extract citations from evidence
        citations = []
        for item in top:
            p = item["primary"]
            citations.append({
                "doc_id": p.get("doc_id") or p.get("sku"),
                "source": "private",
                "title": p.get("title", "")[:100]
            })
            if item["web_match"] and item["web_match"].get("url"):
                citations.append({
                    "url": item["web_match"]["url"],
                    "source": "web",
                    "title": item["web_match"].get("title", "")[:100]
                })
        
        answer_text = response.strip()
        
    except Exception as e:
        # Fallback to template-based answer
        lines = []
        citations = []
        
        for i, item in enumerate(top, 1):
            p = item["primary"]
            price = f"${p.get('price')}" if p.get('price') else "price N/A"
            title = p.get('title', 'Product')[:60]
            lines.append(f"{i}. {title} — {price}")
            citations.append({
                "doc_id": p.get("doc_id") or p.get("sku"),
                "source": "private"
            })
            if item["web_match"] and item["web_match"].get("url"):
                citations.append({"url": item["web_match"]["url"], "source": "web"})
        
        answer_text = "Here are options that fit your request. " + " ".join(lines) + " See details on your screen."
        
        state.setdefault("log", []).append({
            "node": "answerer",
            "warning": "llm_fallback",
            "error": str(e)
        })
    
    # Update state
    state.update(answer=answer_text, citations=citations)
    state.setdefault("log", []).append({
        "node": "answerer",
        "top_k": len(top),
        "citations_count": len(citations)
    })
    
    return state
