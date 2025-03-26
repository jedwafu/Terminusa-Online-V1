@echo off
setlocal enabledelayedexpansion

echo Uninstalling Visual Studio Code and removing leftover files...
echo.

REM Initialize progress bar
set "bar="
set "fill="
set "total=20"

REM Uninstall VSCode
echo Uninstalling Visual Studio Code...
wmic product where "name like 'Microsoft Visual Studio Code%%'" call uninstall /nointeractive >nul 2>&1
call :progress 10

REM Remove leftover files
echo Removing leftover files...
rmdir /s /q "C:\Users\PC\AppData\Roaming\Code" >nul 2>&1
call :progress 15
rmdir /s /q "C:\Users\PC\.vscode" >nul 2>&1
call :progress 20

echo.
echo Visual Studio Code has been uninstalled and leftover files have been removed.
pause
exit /b

:progress
set /a "filled=(%1*total)/20"
set "bar="
for /l %%i in (1,1,%filled%) do set "bar=!bar!█"
for /l %%i in (%filled%,1,%total%) do set "bar=!bar!░"
echo Progress: [!bar!] %1/20
exit /b