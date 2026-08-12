@echo off
call "D:\DevTools\start_postgres.bat"
echo Starting Django server...
"D:\DigitalGpPython\venv\Scripts\python.exe" "D:\DigitalGpPython\manage.py" runserver
pause
