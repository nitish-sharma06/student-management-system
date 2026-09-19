@echo off
title Student Management System
echo ========================================================
echo Starting Student Management System (SMS)...
echo ========================================================
echo.

set PYTHON_EXE="C:\Users\ayush\AppData\Local\Programs\Python\Python311\python.exe"

if exist %PYTHON_EXE% (
    %PYTHON_EXE% app.py
) else (
    python app.py
)

pause
