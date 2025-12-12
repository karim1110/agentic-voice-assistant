# Quick Start Guide - Agentic Voice Assistant

## ✅ Setup Complete!

All configuration files have been created and the vector index has been built with 10 sample products.

**IMPORTANT**: Due to Windows DLL issues with PyTorch in the `.venv`, we're using **system Python (Anaconda)** instead. All required packages have been installed in the system Python.

## 🚀 Running the Application

### Option 1: Using Batch Files (Recommended)

1. **Start MCP Server** (Terminal 1):
   - Double-click `start_mcp_server.bat` OR
   - Run in terminal: `.\start_mcp_server.bat`
   - Wait until you see: `INFO: Uvicorn running on http://127.0.0.1:8000`

2. **Start Streamlit UI** (Terminal 2):
   - Double-click `start_streamlit_chat.bat` OR
   - Run in terminal: `.\start_streamlit_chat.bat`
   - Browser should open automatically at http://localhost:8501

### Option 2: Manual Commands

**Terminal 1 - MCP Server:**
```powershell
cd "D:\UCHICAGO\UChicago Courses\Applied Generative AI Agents and Multimodal Intelligence\FinalProject\agentic-web-rag-with-voice"
$env:PYTHONPATH = (Get-Location).Path
python -m uvicorn mcp_server.server:app --host 127.0.0.1 --port 8000
```

**Terminal 2 - Streamlit UI:**
```powershell
cd "D:\UCHICAGO\UChicago Courses\Applied Generative AI Agents and Multimodal Intelligence\FinalProject\agentic-web-rag-with-voice"
$env:PYTHONPATH = (Get-Location).Path
python -m streamlit run app\ui_streamlit_chat.py --server.port 8501
```

## 🎯 Using the Application

1. **Open Browser**: http://localhost:8501

2. **Choose Input Method**:
   - **Voice**: Click "Record your voice" button and speak
   - **Text**: Toggle "Use typed request instead of ASR" and type your query

3. **Example Queries**:
   ```
   ✅ "Recommend an eco-friendly stainless steel cleaner under $15"
   ✅ "Find Lysol disinfectant spray"
   ✅ "Show me cleaning supplies under $10"
   ✅ "What's a good dish soap?"
   ```

4. **View Results**:
   - Agent decision logs (Router → Planner → Retriever → Answerer → Critic)
   - Product table with details
   - Citations
   - Click "🔊 Play TTS" to hear the response

## 📊 Sample Dataset

The system is currently loaded with 10 sample products:
- EcoShine Steel Polish ($12.49)
- GreenClean Stainless Cleaner ($14.99)
- Lysol Disinfectant Spray ($8.99)
- Scotch-Brite Heavy Duty Scrub Sponges ($6.49)
- Method All-Purpose Cleaner ($4.99)
- Clorox Disinfecting Wipes ($7.99)
- Dawn Ultra Dish Soap ($3.49)
- Mrs. Meyer's Multi-Surface Cleaner ($5.99)
- Seventh Generation Disinfectant Spray ($6.99)
- OxiClean Versatile Stain Remover ($11.99)

## 🔧 Configuration

All settings are in `.env` file:
- **OpenAI API Key**: Configured ✅
- **Brave Search API Key**: Configured ✅ (for web search)
- **LLM Model**: gpt-4o-mini
- **Embedding Model**: all-MiniLM-L6-v2
- **TTS Voice**: alloy

## 🧪 Testing MCP Server

Test the RAG endpoint:
```powershell
curl -X POST http://127.0.0.1:8000/rag.search `
  -H "Content-Type: application/json" `
  -d '{"query":"cleaner","top_k":3}'
```

Expected response: JSON with 3 product results

## 📁 Project Structure

```
agentic-web-rag-with-voice/
├── .env                      # ✅ API credentials
├── start_mcp_server.bat      # ✅ MCP server launcher
├── start_streamlit_chat.bat  # ✅ UI launcher
├── data/
│   ├── processed/
│   │   └── products.csv      # ✅ 10 sample products
│   └── index/                # ✅ ChromaDB vector index
├── graph/                    # Multi-agent pipeline
├── mcp_server/               # MCP tool server
├── app/                      # Streamlit UI
└── prompts/                  # Agent prompts
```

## 🐛 Troubleshooting

### MCP Server won't start
- Check if port 8000 is already in use: `netstat -ano | findstr :8000`
- Kill process: `taskkill /PID <PID> /F`

### Streamlit UI won't start
- Check if port 8501 is already in use: `netstat -ano | findstr :8501`
- Kill process: `taskkill /PID <PID> /F`

### "Module not found" errors
- Ensure PYTHONPATH is set: `$env:PYTHONPATH = (Get-Location).Path`
- **SOLUTION APPLIED**: We're using system Python (Anaconda) which has all packages installed
- DO NOT use `.venv\Scripts\python.exe` - it has DLL loading issues on Windows

### Voice recording not working
- Ensure microphone permissions are granted
- Use typed input as fallback (toggle switch)

## 🎓 Architecture Overview

**5-Agent Pipeline (LangGraph)**:
1. **Router**: Extracts intent, constraints, safety flags
2. **Planner**: Designs execution strategy (RAG/web sources)
3. **Retriever**: Calls MCP tools (rag.search, web.search)
4. **Answerer**: Synthesizes grounded response with citations
5. **Critic**: Validates safety, grounding, citations

**Data Flow**:
```
Voice Input → Whisper ASR → Router → Planner → Retriever
                                                    ↓
                                            MCP Server
                                         (RAG + Web Search)
                                                    ↓
TTS ← Critic ← Answerer ← Evidence
```

## 📚 Next Steps

1. **Download Full Dataset** (optional):
   - 10,002 products from Kaggle
   - See `data/DATASET_SETUP.md` for instructions

2. **Explore Prompts**:
   - All agent prompts in `prompts/` directory
   - Modify to customize behavior

3. **Try Different Models**:
   - Edit `.env`: `LLM_MODEL=gpt-4o` or `claude-3-5-sonnet-20241022`

## 🎉 You're All Set!

The system is ready to use. Start both services and open http://localhost:8501 in your browser.

For detailed documentation, see:
- `README.md` - Full project overview
- `ARCHITECTURE.md` - System design
- `DEMO_GUIDE.md` - Demo instructions

