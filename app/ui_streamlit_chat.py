import os, io, tempfile, pandas as pd, streamlit as st
import time
from dotenv import load_dotenv
from graph.langgraph_pipeline import build_graph
from tts_asr.asr_whisper import transcribe
from tts_asr.tts_client import synthesize

load_dotenv()

# Page config
st.set_page_config(
    page_title="🎙️ Voice Product Assistant", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for chat interface
st.markdown("""
<style>
    /* Chat container */
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.8rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
        max-width: 85%;
    }
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        margin-left: auto;
        border: none;
        color: white;
    }
    .assistant-message {
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
        margin-right: auto;
        border: none;
        color: white;
    }
    .message-header {
        font-weight: 600;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .user-header {
        color: rgba(255, 255, 255, 0.95);
    }
    .assistant-header {
        color: rgba(255, 255, 255, 0.95);
    }
    .message-content {
        font-size: 1rem;
        line-height: 1.6;
        color: white;
    }
    .message-meta {
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.7);
        margin-top: 0.5rem;
    }
    
    /* Citation badges */
    .citation-badge {
        display: inline-block;
        background-color: rgba(255, 255, 255, 0.2);
        color: #ffd700;
        padding: 0.2rem 0.6rem;
        border-radius: 0.4rem;
        margin: 0.2rem;
        font-size: 0.8rem;
        border: 1px solid rgba(255, 255, 255, 0.3);
        backdrop-filter: blur(10px);
    }
    
    /* Product cards */
    .product-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    /* Streamlit overrides */
    .stButton button {
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "graph" not in st.session_state:
    st.session_state.graph = build_graph()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "audio_files" not in st.session_state:
    st.session_state.audio_files = {}

# Header
st.caption("ADSP 32028 IP01 Applied Generative AI: Agents and Multimodal Intelligence")
st.title("🎙️ Voice Product Discovery Assistant")
st.caption("Ask about products using text or voice • Get grounded recommendations with citations")

# Sidebar for system info
with st.sidebar:
    st.header("ℹ️ System Info")
    st.write(f"**Model**: {os.getenv('LLM_MODEL', 'gpt-4o-mini')}")
    st.write(f"**Products Indexed**: 10 items")
    st.write(f"**Voice**: {os.getenv('TTS_VOICE', 'alloy')}")
    
    st.divider()
    
    st.header("💡 Example Queries")
    examples = [
        "Find eco-friendly cleaners under $10",
        "Show me Lysol products",
        "What's the cheapest dish soap?",
        "Recommend stainless steel cleaners"
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{ex[:20]}", use_container_width=True):
            st.session_state.user_input = ex
            st.rerun()
    
    st.divider()
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.audio_files = {}
        st.rerun()

# Chat display area
chat_container = st.container()

with chat_container:
    if not st.session_state.messages:
        # Welcome message
        st.markdown("""
        <div class="chat-message assistant-message">
            <div class="message-header assistant-header">👋 Assistant</div>
            <div class="message-content">
                Hi! I'm your product discovery assistant. Ask me about cleaning products, 
                and I'll search our catalog and the web to find the best options for you.
                <br><br>
                Try: <i>"Find eco-friendly stainless steel cleaners under $15"</i>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Display chat history
    for idx, message in enumerate(st.session_state.messages):
        if message["role"] == "user":
            # User message
            st.markdown(f"""
            <div class="chat-message user-message">
                <div class="message-header user-header">👤 You</div>
                <div class="message-content">{message["content"]}</div>
                {f'<div class="message-meta">🎤 Voice input</div>' if message.get("is_voice") else ''}
            </div>
            """, unsafe_allow_html=True)
        
        else:
            # Assistant message
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <div class="message-header assistant-header">🤖 Assistant</div>
                <div class="message-content">{message["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Audio playback
            if message.get("audio_key") and message["audio_key"] in st.session_state.audio_files:
                audio_data = st.session_state.audio_files[message["audio_key"]]
                st.audio(audio_data, format="audio/wav")
            
            # Citations
            if message.get("citations"):
                citations_html = '<div style="margin-top: 0.5rem;">'
                for cite in message["citations"][:5]:
                    if cite.get("source") == "private":
                        citations_html += f'<span class="citation-badge">📚 Doc #{cite.get("doc_id", "?")}</span>'
                    elif cite.get("url"):
                        domain = cite["url"].split("/")[2] if "/" in cite["url"] else cite["url"]
                        citations_html += f'<span class="citation-badge">🌐 {domain}</span>'
                citations_html += '</div>'
                st.markdown(citations_html, unsafe_allow_html=True)
            
            # Product results (expandable)
            if message.get("products"):
                with st.expander(f"📦 View {len(message['products'])} Product(s)", expanded=False):
                    df = pd.DataFrame(message["products"])
                    # Select available columns
                    display_cols = []
                    for col in ["title", "brand", "price", "rating"]:
                        if col in df.columns:
                            display_cols.append(col)
                    if display_cols:
                        st.dataframe(df[display_cols], use_container_width=True)
            
            # Web results (expandable)
            if message.get("web_results"):
                with st.expander(f"🌐 View {len(message['web_results'])} Web Result(s)", expanded=False):
                    for item in message["web_results"]:
                        st.markdown(f"• [{item.get('title', 'Link')}]({item.get('url', '#')})")
            
            # Agent logs (expandable, for debugging)
            if message.get("agent_logs"):
                with st.expander("🔍 View Agent Decision Log", expanded=False):
                    for log in message["agent_logs"]:
                        st.json(log, expanded=False)

# Helper functions (must be defined BEFORE use)
def process_query(query_text, is_voice=False):
    """Process a text or voice query through the agent pipeline."""
    
    # Add user message to chat
    st.session_state.messages.append({
        "role": "user",
        "content": query_text,
        "is_voice": is_voice,
        "timestamp": time.time()
    })
    
    # Show processing message
    with st.spinner("🤔 Thinking..."):
        # Run agent pipeline
        state = {
            "audio_path": None,
            "transcript": query_text,
            "intent": None,
            "plan": None,
            "evidence": None,
            "answer": None,
            "citations": None,
            "safety_flags": None,
            "tts_path": None,
            "log": []
        }
        
        try:
            final = st.session_state.graph.invoke(state)
            
            # Extract results
            answer_text = final.get("answer", "I couldn't process that request.")
            citations = final.get("citations", [])
            rag_results = (final.get("evidence") or {}).get("rag", [])
            web_results = (final.get("evidence") or {}).get("web", [])
            agent_logs = final.get("log", [])
            
            # Generate TTS audio
            import re
            tts_text = re.sub(r'\(Sources?:.*?\)', '', answer_text).strip()
            audio_key = f"audio_{len(st.session_state.messages)}"
            
            try:
                with st.spinner("🔊 Generating audio..."):
                    audio_path = synthesize(tts_text)
                    with open(audio_path, "rb") as f:
                        audio_data = f.read()
                    st.session_state.audio_files[audio_key] = audio_data
            except Exception as e:
                st.warning(f"Could not generate audio: {str(e)}")
                audio_key = None
            
            # Add assistant response to chat
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer_text,
                "audio_key": audio_key,
                "citations": citations,
                "products": rag_results[:5] if rag_results else None,
                "web_results": web_results[:3] if web_results else None,
                "agent_logs": agent_logs,
                "timestamp": time.time()
            })
            
        except Exception as e:
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"❌ Error: {str(e)}",
                "timestamp": time.time()
            })

def process_voice_query(audio_bytes):
    """Process voice input: transcribe then query."""
    
    audio_path = None
    try:
        # Save audio to temp file
        audio_data = audio_bytes.getvalue()
        if not audio_data or len(audio_data) < 100:
            st.error("Audio recording is too short. Please try again.")
            return
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False, mode='wb') as tmp:
            tmp.write(audio_data)
            audio_path = tmp.name
        
        # Transcribe
        with st.spinner("🎤 Transcribing..."):
            transcript = transcribe(audio_path, os.getenv("ASR_MODEL", "small"))
        
        if not transcript or not transcript.strip():
            st.error("Could not transcribe audio. Please speak clearly and try again.")
            return
        
        # Process the transcribed query
        process_query(transcript, is_voice=True)
        
    except Exception as e:
        st.error(f"Voice processing error: {str(e)}")
    
    finally:
        # Cleanup temp file
        if audio_path and os.path.exists(audio_path):
            try:
                os.unlink(audio_path)
            except:
                pass

# Input area (flows after messages)
st.markdown("<br>", unsafe_allow_html=True)

# Input method selector
input_col1, input_col2 = st.columns([3, 1])

with input_col2:
    input_mode = st.radio(
        "Input method:",
        ["💬 Text", "🎤 Voice"],
        horizontal=True,
        label_visibility="collapsed"
    )

with input_col1:
    if input_mode == "💬 Text":
        # Text input
        user_input = st.text_input(
            "Your message:",
            value=st.session_state.get("user_input", ""),
            placeholder="Type your question here... (e.g., 'Find eco-friendly cleaners under $10')",
            key="text_input",
            label_visibility="collapsed"
        )
        
        col_send, col_clear = st.columns([1, 4])
        with col_send:
            send_button = st.button("📤 Send", use_container_width=True, type="primary")
        
        if send_button and user_input.strip():
            process_query(user_input, is_voice=False)
            st.session_state.user_input = ""
            st.rerun()
    
    else:
        # Voice input
        st.caption("🎤 Click the microphone below, speak clearly, then click Stop")
        audio_bytes = st.audio_input("Record your message", label_visibility="collapsed")
        
        col_transcribe, col_info = st.columns([1, 4])
        with col_transcribe:
            transcribe_button = st.button("🎙️ Transcribe & Send", use_container_width=True, type="primary")
        
        if transcribe_button:
            if not audio_bytes:
                st.error("Please record audio first!")
            else:
                process_voice_query(audio_bytes)
                st.rerun()

