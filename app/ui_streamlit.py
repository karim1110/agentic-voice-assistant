import os, io, tempfile, pandas as pd, streamlit as st
from dotenv import load_dotenv
from graph.langgraph_pipeline import build_graph
from tts_asr.asr_whisper import transcribe
from tts_asr.tts_client import synthesize

load_dotenv()
st.set_page_config(page_title="🎙️ Agentic Voice Product Finder", layout="centered")
st.title("🎙️ Agentic Voice-to-Voice Product Discovery")

# System status check
with st.expander("ℹ️ System Info"):
    st.write("**Status**: ✅ Ready")
    st.write(f"**LLM Model**: {os.getenv('LLM_MODEL', 'gpt-4o-mini')}")
    st.write(f"**Products Indexed**: 10 sample items")
    st.write("**Voice Input**: Requires microphone permissions")
    st.caption("💡 For first-time use, start with typed queries to test the system")

if "graph" not in st.session_state:
    st.session_state.graph = build_graph()

st.markdown("### 💬 Choose Your Input Method")

use_manual = st.toggle("Use typed request (recommended for testing)", value=True)

if use_manual:
    manual = st.text_input(
        "Type your product search query:",
        value="",
        placeholder="e.g., Recommend an eco-friendly stainless steel cleaner under $15",
    )
    st.info("💡 **Tip**: Start with typed queries first, then try voice!")
    audio_bytes = None
else:
    manual = ""
    st.info("🎤 **Instructions**: Click the microphone, speak clearly, then click stop when done.")
    audio_bytes = st.audio_input("Record your voice")

if st.button("Transcribe & Search"):
    # Validate input
    if not use_manual and not audio_bytes:
        st.error("Please record audio or enable typed request."); st.stop()
    
    if use_manual and not manual.strip():
        st.error("Please type a query or switch to voice input."); st.stop()

    transcript = manual
    if not use_manual:
        audio_path = None
        try:
            # Check if audio_bytes has data
            audio_data = audio_bytes.getvalue()
            if not audio_data or len(audio_data) < 100:  # Too small to be valid audio
                st.error("Audio recording is too short or empty. Please try recording again."); st.stop()
            
            # Create temp file with proper Windows path handling
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False, mode='wb') as tmp:
                tmp.write(audio_data)
                audio_path = tmp.name
            
            st.info(f"📝 Transcribing audio (this may take 10-30 seconds for first run)...")
            st.caption(f"Temp file: {audio_path}")
            
            # Verify file exists before transcription
            if not os.path.exists(audio_path):
                st.error(f"Temp audio file not found: {audio_path}"); st.stop()
            
            # Transcribe
            transcript = transcribe(audio_path, os.getenv("ASR_MODEL","small"))
            
            if not transcript or not transcript.strip():
                st.error("Could not transcribe audio. Please speak clearly and try again."); st.stop()
                
            st.success("✅ ASR complete!")
            st.write("**Transcript:**", transcript)
            
        except Exception as e:
            st.error(f"Error during transcription: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            st.stop()
        finally:
            # Always clean up temp file (but don't fail if it's already gone)
            if audio_path:
                try:
                    if os.path.exists(audio_path):
                        os.unlink(audio_path)
                except Exception as cleanup_error:
                    # Silently ignore cleanup errors - file might already be deleted
                    pass
    elif transcript:
        st.write("**Transcript:**", transcript)

    state = {
        "audio_path": None, "transcript": transcript,
        "intent": None, "plan": None, "evidence": None,
        "answer": None, "citations": None, "safety_flags": None,
        "tts_path": None, "log": []
    }
    final = st.session_state.graph.invoke(state)

    # Store ALL results in session state so they persist across reruns
    st.session_state.final_results = final
    
    # Strip citation text like "(Sources: doc #xxx, www.yyy)" for clean TTS audio
    import re
    answer_text = final["answer"]
    tts_text = re.sub(r'\(Sources?:.*?\)', '', answer_text).strip()
    st.session_state.tts_answer = tts_text

# Display results from session state (persists across TTS button clicks)
if "final_results" in st.session_state:
    final = st.session_state.final_results
    
    st.subheader("Agent Steps")
    for step in final["log"]:
        st.json(step, expanded=False)

    st.subheader("Answer")
    st.write(final["answer"])

    # Display RAG results in table
    rag = (final.get("evidence") or {}).get("rag", [])
    if rag:
        st.subheader("📚 Retrieved Products (RAG)")
        df = pd.DataFrame(rag)[["title","brand","price","rating","ingredients"]].head(5)
        st.dataframe(df, use_container_width=True)

    # Display web results as links
    web = (final.get("evidence") or {}).get("web", [])
    if web:
        st.subheader("🌐 Web Search Results")
        for item in web[:5]:
            st.write(f"• [{item.get('title', 'Link')}]({item.get('url', '#')})")

    st.subheader("Citations")
    st.write(final.get("citations", []))

# Play TTS button outside the search block (won't trigger rerun of search)
if "tts_answer" in st.session_state and st.button("🔊 Play TTS"):
    try:
        with st.spinner("Generating audio..."):
            out_path = synthesize(st.session_state.tts_answer)
            if out_path and os.path.exists(out_path):
                with open(out_path, "rb") as f:
                    audio = f.read()
                st.audio(io.BytesIO(audio), format="audio/wav")
                st.success("✅ Audio ready!")
            else:
                st.error("Could not generate audio file")
    except Exception as e:
        st.error(f"TTS Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
