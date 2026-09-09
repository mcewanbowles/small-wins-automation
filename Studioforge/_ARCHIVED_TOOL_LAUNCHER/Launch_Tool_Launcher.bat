@echo off
setlocal
set "ROOT=D:\Seagate\small-wins-automation\Studioforge"
pushd "%ROOT%"
rem Prefer pyw/pythonw to avoid console if available; fallback to py/python
rem Use bundled venv first if available
if exist "%ROOT%\backend\.venv311_x64\Scripts\pythonw.exe" (
  start "" "%ROOT%\backend\.venv311_x64\Scripts\pythonw.exe" "WINDSURF_TOOL_LAUNCHER.py"
  exit /b
)
if exist "%ROOT%\backend\.venv311_x64\Scripts\python.exe" (
  start "" "%ROOT%\backend\.venv311_x64\Scripts\python.exe" "WINDSURF_TOOL_LAUNCHER.py"
  exit /b
)
where pyw >nul 2>nul
if %errorlevel%==0 (
  start "" pyw -3 "WINDSURF_TOOL_LAUNCHER.py"
  exit /b
)
where py >nul 2>nul
if %errorlevel%==0 (
  start "" py -3 "WINDSURF_TOOL_LAUNCHER.py"
  exit /b
)
where pythonw >nul 2>nul
if %errorlevel%==0 (
  start "" pythonw "WINDSURF_TOOL_LAUNCHER.py"
  exit /b
)
start "" python "WINDSURF_TOOL_LAUNCHER.py"
