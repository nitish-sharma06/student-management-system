# PowerShell Launcher for Student Management System
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " Starting Student Management System (Apex Academy SMS) " -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan

$pythonExe = "C:\Users\ayush\AppData\Local\Programs\Python\Python311\python.exe"

if (Test-Path $pythonExe) {
    & $pythonExe app.py
} else {
    python app.py
}
