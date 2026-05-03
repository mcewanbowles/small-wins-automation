@echo off
setlocal
pushd "%~dp0"
set PYTHON=python
if exist ".venv\Scripts\python.exe" set PYTHON=.venv\Scripts\python.exe
%PYTHON% -m streamlit run studioforge_app.py --server.port 8501
popd
