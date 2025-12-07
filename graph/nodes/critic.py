import re
from datetime import datetime


def critique(state):
    """
    Critic Agent: Verify safety, grounding, citations, and answer quality.
    """
    log_entry = {
        "node": "critic",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    answer = state.get("answer", "")
    citations = state.get("citations") or []
    safety_flags = state.get("safety_flags") or []
    evidence = state.get("evidence") or {}
    
    status = "pass"
    issues = []
    
    # 1. Safety Check
    if safety_flags:
        state["answer"] = (
            "I can help with product recommendations, but I cannot provide advice on "
            f"{', '.join(safety_flags)}. Please consult manufacturer instructions or a qualified professional."
        )
        status = "fail"
        log_entry["checks"]["safety"] = "fail"
        log_entry["safety_flags"] = safety_flags
        state.setdefault("log", []).append(log_entry)
        return state
    else:
        log_entry["checks"]["safety"] = "pass"
    
    # 2. Empty Evidence Check
    if not any(evidence.values()):
        if "couldn't find" not in answer.lower() and "no products" not in answer.lower():
            state["answer"] = "I couldn't find any products matching those criteria. Try broadening your search."
            status = "fail"
            issues.append("empty_evidence_not_acknowledged")
        log_entry["checks"]["evidence"] = "warn" if not any(evidence.values()) else "pass"
    else:
        log_entry["checks"]["evidence"] = "pass"
    
    # 3. Citation Check
    has_private_citation = any(c.get("source") == "private" for c in citations)
    has_web_citation = any(c.get("source") == "web" for c in citations)
    
    if evidence.get("rag") and not has_private_citation:
        issues.append("missing_private_citations")
        log_entry["checks"]["citations"] = "fail"
        
        # Try to add citations from evidence
        for item in evidence.get("rag", [])[:3]:
            doc_id = item.get("doc_id") or item.get("sku")
            if doc_id and not any(c.get("doc_id") == doc_id for c in citations):
                citations.append({"doc_id": doc_id, "source": "private"})
        
        state["citations"] = citations
        log_entry["checks"]["citations"] = "fixed"
    elif has_private_citation:
        log_entry["checks"]["citations"] = "pass"
    else:
        log_entry["checks"]["citations"] = "warn"
    
    # Check if web search was done but no web citations
    if evidence.get("web") and not has_web_citation:
        issues.append("missing_web_citations")
        # Try to add from evidence
        for item in evidence.get("web", [])[:2]:
            url = item.get("url")
            if url and not any(c.get("url") == url for c in citations):
                citations.append({"url": url, "source": "web"})
        state["citations"] = citations
    
    # 4. Grounding Check - Look for specific claims
    # Check if answer mentions prices/ratings not in evidence
    price_pattern = r'\$\d+\.?\d*'
    prices_in_answer = re.findall(price_pattern, answer)
    
    if prices_in_answer:
        evidence_prices = []
        for source in evidence.values():
            for item in source:
                if item.get("price"):
                    evidence_prices.append(f"${item['price']}")
        
        # Basic check - not exhaustive but catches obvious hallucinations
        ungrounded_prices = []
        for price in prices_in_answer:
            # Remove $ and compare as floats
            try:
                price_val = float(price.replace("$", ""))
                if not any(abs(price_val - float(ep.replace("$", ""))) < 0.01 
                          for ep in evidence_prices):
                    ungrounded_prices.append(price)
            except:
                pass
        
        if ungrounded_prices:
            issues.append(f"potentially_ungrounded_prices: {ungrounded_prices}")
            log_entry["checks"]["grounding"] = "warn"
        else:
            log_entry["checks"]["grounding"] = "pass"
    else:
        log_entry["checks"]["grounding"] = "pass"
    
    # 5. Coherence Check
    if len(answer) < 20:
        issues.append("answer_too_short")
        log_entry["checks"]["coherence"] = "warn"
    elif len(answer) > 500:
        issues.append("answer_too_long")
        log_entry["checks"]["coherence"] = "warn"
    else:
        log_entry["checks"]["coherence"] = "pass"
    
    # 6. Citation Format Check in Answer
    # Ensure answer mentions sources
    if citations and "(source" not in answer.lower() and "doc #" not in answer.lower():
        # Append citation list to answer
        cite_text = "\n\n(Sources: "
        cite_parts = []
        for c in citations[:5]:  # Limit to top 5
            if c.get("doc_id"):
                cite_parts.append(f"doc #{c['doc_id']}")
            elif c.get("url"):
                domain = c["url"].split("/")[2] if "/" in c["url"] else c["url"]
                cite_parts.append(domain)
        cite_text += ", ".join(cite_parts) + ")"
        state["answer"] = answer + cite_text
        log_entry["checks"]["citation_format"] = "fixed"
    else:
        log_entry["checks"]["citation_format"] = "pass"
    
    # Final status
    if "fail" in [v for v in log_entry["checks"].values() if isinstance(v, str)]:
        status = "fail"
    elif "warn" in [v for v in log_entry["checks"].values() if isinstance(v, str)]:
        status = "warn"
    
    log_entry["status"] = status
    log_entry["issues"] = issues
    
    state.setdefault("log", []).append(log_entry)
    
    return state
