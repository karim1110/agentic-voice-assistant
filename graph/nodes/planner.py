import json
from graph.llm_client import get_llm_client, load_prompt


def plan(state):
    """
    Planner Agent: Design execution strategy using LLM.
    """
    intent = state.get("intent") or {}
    constraints = intent.get("constraints") or {}
    transcript = state.get("transcript", "")
    
    # Load system prompt
    system_prompt = load_prompt("system_planner.md")
    
    # Prepare context
    context = f"""
User query: {transcript}

Router analysis:
- Task: {intent.get('task')}
- Budget: {constraints.get('budget')}
- Material: {constraints.get('material')}
- Brand: {constraints.get('brand')}
- Category: {constraints.get('category')}
- Needs live data: {intent.get('needs_live')}

Design an execution plan as JSON.
"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": context}
    ]
    
    # Call LLM
    try:
        llm = get_llm_client()
        response = llm.chat_json(messages, temperature=0.2, max_tokens=500)
        
        plan = {
            "sources": response.get("sources", ["rag.search"]),
            "filters": response.get("filters", {}),
            "query_text": response.get("query_text", transcript),
            "fields": response.get("fields", ["sku", "title", "price"]),
            "ranking": response.get("ranking", "relevance"),
            "top_k": response.get("top_k", 5),
            "comparison_strategy": response.get("comparison_strategy", "none")
        }
        
    except Exception as e:
        # Fallback to rule-based planning
        filters = {}
        
        # Infer category
        if any(k in transcript.lower() for k in ["clean", "cleaner", "disinfect"]):
            filters["category"] = "Household Cleaning"
        
        # Add budget filter
        if constraints.get("budget"):
            filters["price"] = {"$lte": constraints["budget"]}
        
        plan = {
            "sources": ["rag.search"] + (["web.search"] if intent.get("needs_live") else []),
            "filters": filters,
            "query_text": transcript,
            "fields": ["sku", "title", "price", "rating", "brand", "ingredients"],
            "ranking": "price_asc" if constraints.get("budget") else "relevance",
            "top_k": 5,
            "comparison_strategy": "price_check" if intent.get("needs_live") else "none"
        }
        
        state.setdefault("log", []).append({
            "node": "planner",
            "warning": "llm_fallback",
            "error": str(e)
        })
    
    # Update state
    state.update(plan=plan)
    state.setdefault("log", []).append({"node": "planner", "plan": plan})
    
    return state
