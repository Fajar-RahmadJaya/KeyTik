@echo off
:: Ensure the script is running as Administrator
set "downloadURL=https://github.com/oblitum/Interception/releases/download/v1.0.1/Interception.zip"
set "zipFile=Interception.zip"
set "extractFolder=Interception"
set "installerExe=install-interception.exe"

:: Check for Administrator Privileges
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo This script requires Administrator privileges. Please run as Administrator.
    pause
    exit /b
)

:: Step 1: Download the Interception.zip file
echo Downloading Interception.zip...
powershell -Command "Invoke-WebRequest -Uri %downloadURL% -OutFile %zipFile%"
if %errorLevel% NEQ 0 (
    echo Failed to download the file.
    pause
    exit /b
)

:: Step 2: Extract the downloaded zip file
echo Extracting Interception.zip...
powershell -Command "Expand-Archive -Path %zipFile% -DestinationPath . -Force"
if %errorLevel% NEQ 0 (
    echo Failed to extract the file.
    pause
    exit /b
)

:: Step 3: Find the installer folder dynamically
echo Locating installer folder...
set "installerPath="
for /d %%d in (%extractFolder%\*) do (
    if exist "%%d\%installerExe%" (
        set "installerPath=%%d"
    )
)

if "%installerPath%"=="" (
    echo Installer folder not found. Please check the extracted files.
    pause
    exit /b
)

:: Step 4: Install Interception
cd "%installerPath%"
echo Installing Interception driver...
"%installerExe%" /install
if %errorLevel% NEQ 0 (
    echo Failed to install the Interception driver.
    pause
    exit /b
)

:: Step 5: Clean up downloaded and extracted files
cd ../..
rmdir /s /q "%extractFolder%"
del /q %zipFile%

echo Installation completed successfully!
