cd /D "%~dp0"
pelican -s publishconf.py
wsl bash -c "./deploy.sh"