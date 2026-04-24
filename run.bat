@echo off
cd /d "%~dp0"
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Starting Campus SkillSwap server...
echo Open your browser at http://127.0.0.1:8000/
echo Press Ctrl+C to stop.
py manage.py runserver
pause
