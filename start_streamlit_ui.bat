@echo off
cd /d "%~dp0"
set PYTHONPATH=%CD%

REM Add ffmpeg to PATH for Whisper ASR
set PATH=C:\Users\afiniti\anaconda3\Lib\site-packages\imageio_ffmpeg\binaries;%PATH%

echo Starting Streamlit UI on http://localhost:8501
echo The browser will open automatically...
echo.
echo NOTE: Using system Python (Anaconda) to avoid DLL issues
echo Deactivating any virtual environments...
call deactivate 2>nul
C:\Users\afiniti\anaconda3\python.exe -m streamlit run app\ui_streamlit.py --server.port 8501
pause

