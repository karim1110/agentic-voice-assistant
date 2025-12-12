# 🎯 Prompt Disclosure - Complete Transparency

**Project**: Agentic Voice-to-Voice Product Discovery Assistant  
**Course**: Applied Generative AI Agents and Multimodal Intelligence  
**Institution**: University of Chicago  
**Date**: December 2025

---

## 📋 Overview

This document provides **complete transparency** for all prompts, system messages, tool instructions, and few-shot examples used throughout the multi-agent pipeline. All prompts are disclosed in the `prompts/` directory with full context on how they map to agents and implementation.

**Total Lines Disclosed**: 560+ lines across 6 files

---

## 🗂️ Prompt Inventory

| File | Agent/Component | Lines | LLM Used | Purpose |
|------|----------------|-------|----------|---------|
| `system_router.md` | Router Agent | 117 | ✅ OpenAI/Claude | Intent extraction, constraint parsing, safety screening |
| `system_planner.md` | Planner Agent | 127 | ✅ OpenAI/Claude | Source selection, filter design, ranking strategy |
| `system_answerer.md` | Answerer Agent | 137 | ✅ OpenAI/Claude | Grounded response synthesis, citation formatting |
| `system_critic.md` | Critic Agent | 179 | ❌ Rule-based | Validation logic documentation (rule-based implementation) |
| `tool_call_instructions.md` | All Agents | 253 | ✅ OpenAI/Claude | MCP tool schemas, best practices, reconciliation rules |
| `few_shots.jsonl` | Router/Planner | 6 examples | ✅ OpenAI/Claude | End-to-end query examples with outputs |

**Total**: 819+ lines of disclosed prompts and documentation

---

## 🔄 Agent-to-Prompt Mapping

### 1. Router Agent (`graph/nodes/router.py`)

**Prompt Used**: `prompts/system_router.md`

**Implementation**:
```python
def route(state):
    system_prompt = load_prompt("system_router.md")
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"User query: {text}\n\nExtract the intent as JSON."}
    ]
    response = llm.chat_json(messages, temperature=0.2, max_tokens=500)
```

**Prompt Structure**:
- **Lines 1-4**: Role definition
- **Lines 6-13**: Task categorization (product_recommendation, comparison, information, out_of_scope)
- **Lines 15-35**: Constraint extraction rules (budget, material, brand, category, special requirements)
- **Lines 37-42**: Live data detection logic
- **Lines 44-57**: Safety screening criteria
- **Lines 59-73**: JSON output schema
- **Lines 75-117**: 3 complete examples with edge cases

**Key Techniques**:
- Structured JSON output format
- Clear safety denial criteria
- Regex-like extraction rules for LLM to follow
- Fallback to regex if LLM fails (lines 42-62 in router.py)

**Temperature**: 0.2 (low variability for consistent parsing)

---

### 2. Planner Agent (`graph/nodes/planner.py`)

**Prompt Used**: `prompts/system_planner.md`

**Implementation**:
```python
def plan(state):
    system_prompt = load_prompt("system_planner.md")
    context = f"""
User query: {transcript}
Router analysis:
- Task: {intent.get('task')}
- Budget: {constraints.get('budget')}
...
Design an execution plan as JSON.
"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": context}
    ]
    response = llm.chat_json(messages, temperature=0.2, max_tokens=500)
```

**Prompt Structure**:
- **Lines 1-4**: Role definition
- **Lines 8-27**: Source selection decision tree (when to use RAG vs web vs both)
- **Lines 29-49**: Filter construction guidelines (price, material, category)
- **Lines 51-61**: Field selection logic
- **Lines 63-69**: Ranking strategy rules (price_asc, rating_desc, relevance, price_per_oz)
- **Lines 71-84**: Output JSON schema
- **Lines 86-127**: 2 detailed examples with different strategies

**Key Techniques**:
- Decision tree for source selection
- Explicit filter validation rules
- Comparison strategy framework
- Rule-based fallback (lines 52-71 in planner.py)

**Temperature**: 0.2 (consistent planning strategy)

---

### 3. Retriever Agent (`graph/nodes/retriever.py`)

**Prompt Used**: `prompts/tool_call_instructions.md` (reference)

**Implementation**: ❌ **No LLM used** (pure HTTP calls to MCP server)

```python
def retrieve(state):
    # No LLM - direct HTTP calls
    payload = {"query": plan.get("query_text"), "top_k": 5, "filters": filters}
    results = call_tool(f"{base}/rag.search", payload)
```

**Tool Instructions Used**:
- Lines 1-67: `rag.search` schema and examples
- Lines 69-123: `web.search` schema and examples
- Lines 125-175: Reconciliation and error handling rules

**Key Implementation Details**:
- Strips category filters to avoid ChromaDB path matching issues (line 37-38)
- Implements timeout and retry logic (lines 8-18)
- Logs all tool calls with duration metrics (lines 74-78)

---

### 4. Answerer Agent (`graph/nodes/answerer.py`)

**Prompt Used**: `prompts/system_answerer.md`

**Implementation**:
```python
def answer(state):
    system_prompt = load_prompt("system_answerer.md")
    
    # Build evidence summary showing BOTH RAG and web separately
    evidence_text = "## Evidence Retrieved:\n\n"
    # ... (lines 79-104: format evidence)
    
    context = f"""
User query: {transcript}
{evidence_text}
Synthesize a concise voice response (≤15 seconds / ~50 words) with proper citations.
"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": context}
    ]
    response = llm.chat(messages, temperature=0.4, max_tokens=300)
```

**Prompt Structure**:
- **Lines 1-4**: Role definition
- **Lines 8-13**: Grounding principles (NEVER invent, ONLY use evidence, ALWAYS cite)
- **Lines 15-18**: Conciseness guidelines (≤15 sec, ~40-50 words)
- **Lines 20-24**: Citation format rules (user-friendly, not cryptic doc IDs)
- **Lines 26-53**: Comparison logic for RAG + web (relevance check, price reconciliation, conflict resolution)
- **Lines 55-71**: Response structure template (opening, top pick, alternatives, closing)
- **Lines 73-93**: 2 complete example responses
- **Lines 95-120**: Safety integration, missing data handling, TTS formatting
- **Lines 122-137**: Citation requirements (CRITICAL for grading)

**Key Techniques**:
- **Relevance filtering**: Instructs LLM to ignore off-topic RAG results (lines 29-36)
- **Fuzzy price matching**: Reconciliation with ±10% threshold (lines 38-41)
- **Natural TTS formatting**: Spell out prices ("twelve forty-nine" vs "$12.49")
- **Template fallback**: If LLM fails, use structured template (lines 147-169)

**Temperature**: 0.4 (allows natural variation in phrasing while staying grounded)

---

### 5. Critic Agent (`graph/nodes/critic.py`)

**Prompt Used**: `prompts/system_critic.md` (documentation only)

**Implementation**: ❌ **No LLM used** (rule-based validation)

```python
def critique(state):
    # Rule-based checks (no LLM)
    # 1. Safety check
    if safety_flags:
        state["answer"] = "I can help with product recommendations, but..."
    
    # 2. Empty evidence check
    if not any(evidence.values()):
        state["answer"] = "I couldn't find any products..."
    
    # 3. Citation check
    if evidence.get("rag") and not has_private_citation:
        # Auto-add citations from evidence
    
    # 4. Grounding check (price validation)
    # 5. Coherence check (length)
    # 6. Citation format check
```

**Why Rule-Based**:
- Faster execution (no LLM latency)
- Deterministic validation (no variability)
- Lower cost
- Easier to debug

**Validation Logic** (documented in `system_critic.md`):
- **Safety**: Override answer if safety_flags present (lines 24-28 in code)
- **Evidence**: Ensure answer acknowledges empty results (lines 38-45)
- **Citations**: Auto-add missing citations from evidence (lines 48-76)
- **Grounding**: Validate prices against evidence (lines 79-108)
- **Coherence**: Check length constraints 20-500 chars (lines 111-118)
- **Format**: Append citation text if missing (lines 122-136)

---

## 🛠️ Tool Schema Disclosure

### MCP Server Tools

Both tools are fully documented in `prompts/tool_call_instructions.md`:

#### `rag.search` (Private Catalog)

**Endpoint**: `POST http://127.0.0.1:8000/rag.search`

**Schema** (lines 16-28):
```json
{
  "query": "string (required)",
  "top_k": "integer (optional, default: 5)",
  "filters": {
    "category": "string (optional)",
    "price": {
      "$lte": "float (optional)",
      "$gte": "float (optional)"
    }
  }
}
```

**Response** (lines 30-48):
```json
{
  "tool": "rag.search",
  "timestamp": 1234567890.0,
  "results": [
    {
      "doc_id": "A001",
      "sku": "12345",
      "title": "Product name...",
      "price": 12.49,
      "rating": 0.0,
      "brand": "",
      "ingredients": "",
      "category": "Household Cleaning"
    }
  ]
}
```

**Implementation**: `mcp_server/tools/rag_tool.py`
- Vector search with ChromaDB (lines 32-38)
- Metadata filtering with normalization (lines 14-30)
- Returns top-k results with embeddings

---

#### `web.search` (Live Web Data)

**Endpoint**: `POST http://127.0.0.1:8000/web.search`

**Schema** (lines 80-86):
```json
{
  "query": "string (required)",
  "top_k": "integer (optional, default: 5)"
}
```

**Response** (lines 88-105):
```json
{
  "tool": "web.search",
  "timestamp": 1234567890.0,
  "results": [
    {
      "title": "Product title from web",
      "url": "https://example.com/product",
      "snippet": "Description...",
      "profile": "website name",
      "price": null,
      "availability": null
    }
  ]
}
```

**Implementation**: `mcp_server/tools/web_tool.py`
- Brave Search API integration
- Caching with 60-300s TTL
- Rate limiting and error handling

---

## 📚 Few-Shot Examples

**File**: `prompts/few_shots.jsonl`

Contains 6 complete end-to-end examples covering:

1. **Standard budget query**: "eco-friendly stainless cleaner under $15"
   - Tests: Budget filter, material constraint, eco-friendly keyword
   - Shows: RAG-only search, price sorting

2. **Live data query**: "What's the current price of Lysol spray in stock?"
   - Tests: needs_live flag, price comparison
   - Shows: Hybrid RAG + web search, conflict handling

3. **Quality-focused query**: "best glass cleaner for bathroom mirrors"
   - Tests: Material matching, context understanding
   - Shows: Relevance-based ranking

4. **Safety rejection**: "Can I mix bleach and ammonia for tough stains?"
   - Tests: Safety screening
   - Shows: Safety flag → refusal path

5. **Value query**: "affordable kitchen sponges bulk pack under $10"
   - Tests: Multiple constraints (bulk, affordable, budget)
   - Shows: Category filtering, price sorting

6. **(Partial example)**: Additional query demonstrating edge case

**Usage**: These examples serve as:
- Reference for prompt engineering
- Test cases for validation
- Documentation for expected behavior

---

## 🎨 Prompt Engineering Strategies

### 1. Structured Output Enforcement

**Technique**: Explicit JSON schema in system prompt + LLM response_format

```python
# Router example
response = llm.chat_json(messages, temperature=0.2)
# OpenAI uses response_format={"type": "json_object"} internally
```

**Benefits**:
- Reliable parsing
- Type safety
- Easy validation

---

### 2. Grounding Through Evidence Framing

**Technique**: Present evidence explicitly in user message

```python
# Answerer example (lines 78-104)
evidence_text = "## Evidence Retrieved:\n\n"
evidence_text += "### Private Catalog (RAG) - Top 5:\n"
for item in rag[:5]:
    evidence_text += f"- Title: {item['title']}\n"
    evidence_text += f"- Price: ${item['price']}\n"
```

**Benefits**:
- LLM sees full context
- Reduces hallucination
- Enables citation verification

---

### 3. Safety Through Multiple Checkpoints

**Technique**: Validate at both routing and critic stages

```python
# Router (lines 60-61 in router.py)
safety_flags = [f for f in SAFE_DENY if f in text.lower()]

# Critic (lines 24-32 in critic.py)
if safety_flags:
    state["answer"] = "I cannot provide advice on {safety_flags}..."
```

**Benefits**:
- Defense in depth
- Catches edge cases
- Auditable decisions

---

### 4. Fallback Mechanisms

**Technique**: Rule-based extraction if LLM fails

```python
# Router fallback (lines 42-62 in router.py)
except Exception as e:
    import re
    budget = None
    m = re.search(r'under\s*\$?(\d+(\.\d{1,2})?)', text, re.I)
    if m:
        budget = float(m.group(1))
```

**Benefits**:
- Resilience to LLM errors
- Graceful degradation
- Always returns valid output

---

### 5. Temperature Tuning by Agent

**Strategy**: Different temperatures for different agents

| Agent | Temperature | Rationale |
|-------|-------------|-----------|
| Router | 0.2 | Consistent intent parsing |
| Planner | 0.2 | Deterministic strategy |
| Answerer | 0.4 | Natural variation in phrasing |

---

## 🔍 Prompt Modification Guide

### To Adjust Safety Rules:

**File**: `prompts/system_router.md` (lines 44-57)

```markdown
**DENY** (set safety_flags):
- Mixing chemicals (e.g., "can I mix bleach and ammonia")
- Medical advice (e.g., "will this cure my rash")
- Unsafe usage (e.g., "can I use this on skin")
- Ingestion queries (e.g., "is this safe to eat")
+ YOUR NEW RULE HERE
```

**Also update**: `graph/nodes/router.py` (line 60) fallback list

---

### To Change Response Length:

**File**: `prompts/system_answerer.md` (lines 15-18)

```markdown
### 2. Conciseness
- Target **≤15 seconds of speech** (~40-50 words)  # ADJUST THIS
- Focus on top 2-3 most relevant products            # OR THIS
```

**Also update**: `graph/nodes/answerer.py` (line 123) max_tokens parameter

---

### To Add New Tool:

1. **Add schema**: `prompts/tool_call_instructions.md`
2. **Update planner**: `prompts/system_planner.md` (source selection logic)
3. **Implement**: `mcp_server/tools/new_tool.py`
4. **Register**: `mcp_server/server.py` (add endpoint)
5. **Call**: `graph/nodes/retriever.py` (add to retrieve function)

---

## 📊 Prompt Statistics

### Token Usage (Approximate)

| Component | System Prompt Tokens | Avg User Prompt Tokens | Total per Call |
|-----------|---------------------|------------------------|----------------|
| Router | ~300 | ~50 | ~350 |
| Planner | ~250 | ~100 | ~350 |
| Answerer | ~400 | ~600 (with evidence) | ~1000 |
| **Total per Query** | | | **~1700 tokens** |

**Cost Estimate** (GPT-4o-mini):
- Input: ~1700 tokens × $0.15/1M = $0.000255
- Output: ~200 tokens × $0.60/1M = $0.00012
- **Total per query**: ~$0.000375

---

## ✅ Grading Requirement Compliance

**Requirement**: "Submit a prompts/ folder (or README section) containing the main system prompts, tool-call instructions, planner rubric, and any few-shot examples used by agents."

### ✅ Checklist:

- [x] **Main system prompts**: 
  - `system_router.md` (117 lines)
  - `system_planner.md` (127 lines)
  - `system_answerer.md` (137 lines)
  - `system_critic.md` (179 lines - validation logic)

- [x] **Tool-call instructions**: 
  - `tool_call_instructions.md` (253 lines)
  - Complete schemas for both MCP tools
  - Best practices and error handling

- [x] **Planner rubric**: 
  - Embedded in `system_planner.md` (lines 8-69)
  - Decision tree for source selection
  - Filter construction rules
  - Ranking strategies

- [x] **Few-shot examples**: 
  - `few_shots.jsonl` (6 complete examples)
  - Cover standard, hybrid, safety, and edge cases

- [x] **Mapping to implementation**: 
  - This document (PROMPT_DISCLOSURE.md)
  - Shows exact code usage
  - Line-by-line breakdown

---

## 🎓 Academic Integrity Statement

All prompts were developed specifically for this project. No proprietary or third-party prompts were used without attribution. All LLM interactions are logged and auditable through the agent step logs visible in the UI.

---

## 📖 Additional Resources

- **Full codebase**: See `graph/nodes/` for agent implementations
- **UI transparency**: Agent logs show all LLM decisions in real-time
- **Reproducibility**: All prompts are version-controlled and can be modified via env vars

---

**Last Updated**: December 2025  
**Contact**: See README.md for project details  
**License**: MIT

---

## 🔗 Quick Links

- [Main README](README.md)
- [Prompts Folder](prompts/)
- [Architecture Documentation](README.md#architecture)
- [Agent Implementations](graph/nodes/)
- [MCP Server](mcp_server/)

---

**END OF PROMPT DISCLOSURE DOCUMENT**

*This document provides complete transparency for all prompts used in the agentic voice-to-voice product discovery assistant. All 560+ lines of prompts are disclosed in the `prompts/` directory.*

