@echo off
REM Windows twin of run.sh — what Task Scheduler calls. Runs one pass, logging
REM to data\jobradar.log. Any args are passed through to run.py, e.g.:
REM   scripts\run.bat --config profiles\payments.yaml
setlocal
cd /d "%~dp0.."
if not exist data mkdir data
".venv\Scripts\python.exe" run.py -v %* >> data\jobradar.log 2>&1
