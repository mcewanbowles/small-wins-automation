@echo on
setlocal
set "ROOT=D:\Seagate\small-wins-automation\Studioforge"
pushd "%ROOT%"

rem Run with a visible console to surface any errors
if exist "%ROOT%\backend\.venv311_x64\Scripts\python.exe" (
  "%ROOT%\backend\.venv311_x64\Scripts\python.exe" "WINDSURF_TOOL_LAUNCHER.py"
  goto :done
)
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 "WINDSURF_TOOL_LAUNCHER.py"
  goto :done
)

where python >nul 2>nul
if %errorlevel%==0 (
  python "WINDSURF_TOOL_LAUNCHER.py"
  goto :done
)

echo Could not find Python on PATH. Please install Python 3.x or add it to PATH.

:done
echo ExitCode=%errorlevel%
pause
