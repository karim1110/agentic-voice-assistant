import json
from graph.llm_client import get_llm_client, load_prompt


def route(state):
    """
    Router Agent: Extract intent, constraints, and safety flags using LLM.
    """
    text = (state.get("transcript") or "").strip()
    
    if not text:
        state.update(
            intent={"task": "out_of_scope", "constraints": {}, "needs_live": False},
            safety_flags=[]
        )
        state.setdefault("log", []).append({"node": "router", "error": "empty_transcript"})
        return state
    
    # Load system prompt
    system_prompt = load_prompt("system_router.md")
    
    # Prepare messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"User query: {text}\n\nExtract the intent as JSON."}
    ]
    
    # Call LLM
    try:
        llm = get_llm_client()
        response = llm.chat_json(messages, temperature=0.2, max_tokens=500)
        
        # Parse response
        intent = {
            "task": response.get("task", "product_recommendation"),
            "constraints": response.get("constraints", {}),
            "needs_live": response.get("needs_live", False)
        }
        safety_flags = response.get("safety_flags", [])
        
    except Exception as e:
        # Fallback to regex-based extraction if LLM fails
        import re
        budget = None
        m = re.search(r'under\s*\$?(\d+(\.\d{1,2})?)', text, re.I)
        if m:
            budget = float(m.group(1))
        
        intent = {
            "task": "product_recommendation",
            "constraints": {
                "budget": budget,
                "material": "stainless steel" if "stainless" in text.lower() else None,
                "brand": None,
                "category": "cleaning supplies" if "clean" in text.lower() else None
            },
            "needs_live": any(k in text.lower() for k in ["now", "today", "in stock", "availability", "current price", "latest"])
        }
        
        SAFE_DENY = ["mixing chemicals", "medical claims", "mix bleach", "mix ammonia"]
        safety_flags = [f for f in SAFE_DENY if f in text.lower()]
        
        state.setdefault("log", []).append({
            "node": "router",
            "warning": "llm_fallback",
            "error": str(e)
        })
    
    # Update state
    state.update(intent=intent, safety_flags=safety_flags)
    state.setdefault("log", []).append({
        "node": "router",
        "intent": intent,
        "safety_flags": safety_flags
    })
    
    return state
