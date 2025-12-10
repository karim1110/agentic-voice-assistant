@echo off
cd /d "%~dp0"
set PYTHONPATH=%CD%

REM Add ffmpeg to PATH for Whisper ASR
set PATH=C:\Users\afiniti\anaconda3\Lib\site-packages\imageio_ffmpeg\binaries;%PATH%

echo Starting Chat-Based Streamlit UI on http://localhost:8501
echo The browser will open automatically...
echo.
echo NOTE: Using NEW chat interface with conversation history
echo Deactivating any virtual environments...
call deactivate 2>nul
C:\Users\afiniti\anaconda3\python.exe -m streamlit run app\ui_streamlit_chat.py --server.port 8501
pause

