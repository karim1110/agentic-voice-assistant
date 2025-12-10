@echo off
cd /d "%~dp0"
set PYTHONPATH=%CD%

REM Add ffmpeg to PATH for any audio processing
set PATH=C:\Users\afiniti\anaconda3\Lib\site-packages\imageio_ffmpeg\binaries;%PATH%

echo Starting MCP Server on http://127.0.0.1:8000
echo.
echo NOTE: Using system Python (Anaconda) to avoid DLL issues
echo Deactivating any virtual environments...
call deactivate 2>nul
C:\Users\afiniti\anaconda3\python.exe -m uvicorn mcp_server.server:app --host 127.0.0.1 --port 8000
pause

