@echo off
:begin
echo Starting dream_watcher.py ...
cd /D "%~dp0"
python dream_watcher.py

echo dream_watcher.py exited. Restarting in 5 seconds...
timeout /t 5 > nul

goto begin