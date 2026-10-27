@echo off
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (
  py -m venv venv
)
call venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
pause
