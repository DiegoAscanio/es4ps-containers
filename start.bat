@echo off
SETLOCAL

REM Read each line from .env file
for /F "tokens=1* delims==" %%i in (.env) do (
    REM Set environment variables
    set %%i=%%j
)

REM Build using docker-compose
docker-compose up

ENDLOCAL
