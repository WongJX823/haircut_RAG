@echo off
REM Runs the HaircutAI regression test suite.
REM Usage:  run_tests.bat            (quiet summary)
REM         run_tests.bat -v         (verbose, extra args are passed to pytest)

cd /d "%~dp0"
python -m pytest tests/ %*
if %errorlevel% equ 0 (
    echo.
    echo ================================
    echo   ALL TESTS PASSED - safe to proceed
    echo ================================
) else (
    echo.
    echo ================================
    echo   TESTS FAILED - fix before continuing
    echo ================================
)
REM Keep the window open when launched by double-click so results stay readable.
REM Double-click launches show this script's filename inside %cmdcmdline%;
REM an interactive terminal session does not.
set FINAL=%errorlevel%
echo %cmdcmdline% | findstr /i /c:"%~nx0" >nul && pause
exit /b %FINAL%
