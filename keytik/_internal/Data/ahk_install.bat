@echo off
setlocal

set "AHK_URL=https://www.autohotkey.com/download/ahk-v2.exe"
set "AHK_EXE=%TEMP%\ahk-v2_%RANDOM%.exe"

echo Downloading AutoHotkey v2 from %AHK_URL% ...
powershell -Command "try { Invoke-WebRequest -Uri '%AHK_URL%' -OutFile '%AHK_EXE%' -UseBasicParsing; Write-Host 'Download completed.' } catch { Write-Host 'Download failed.'; exit 1 }"

if not exist "%AHK_EXE%" (
    echo Download failed!
    pause
    exit /b 1
)

echo Running AutoHotkey installer: %AHK_EXE%
start /wait "" "%AHK_EXE%"

echo.
del /f /q "%AHK_EXE%"

echo Done.
pause

endlocal
