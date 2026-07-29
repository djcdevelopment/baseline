@echo off
setlocal
rem Repo root derived from this script's location (etc -> mcp -> network -> root),
rem so the retired C:\work\comfy checkout can never be picked up by accident.
cd /d "%~dp0..\..\.."
set PYTHONPATH=%CD%\network\mcp
rem Interpreter precedence: COMFY_GATEWAY_PYTHON env var, then the historical
rem hardcoded OMEN venv if it still exists on this machine, then plain python.
set "COMFY_GATEWAY_PYTHON_FALLBACK=C:\work\commandcenter\fleet-worker-node\.venv-omen\Scripts\python.exe"
if defined COMFY_GATEWAY_PYTHON (
    set "COMFY_GATEWAY_PYTHON_EXE=%COMFY_GATEWAY_PYTHON%"
) else if exist "%COMFY_GATEWAY_PYTHON_FALLBACK%" (
    set "COMFY_GATEWAY_PYTHON_EXE=%COMFY_GATEWAY_PYTHON_FALLBACK%"
) else (
    set "COMFY_GATEWAY_PYTHON_EXE=python"
)
"%COMFY_GATEWAY_PYTHON_EXE%" -m comfy_gateway.kernel.gateway --callers network\mcp\comfy_gateway\etc\callers.json --providers comfy_gateway.toolsurface.valheim,comfy_gateway.toolsurface.inference >> network\mcp\var\gateway-task.log 2>&1

