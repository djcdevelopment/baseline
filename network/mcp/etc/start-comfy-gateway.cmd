@echo off
setlocal
rem Repo root derived from this script's location (etc -> mcp -> network -> root),
rem so the retired C:\work\comfy checkout can never be picked up by accident.
cd /d "%~dp0..\..\.."
set PYTHONPATH=%CD%\network\mcp
rem Interpreter precedence: COMFY_GATEWAY_PYTHON when explicitly set, otherwise
rem whatever `python` the caller's PATH resolves — normally an activated
rem project-local venv. Deliberately no machine-specific fallback: this gateway
rem is project-owned and must run from the repo and its Docker image alone.
rem See README.md for the venv + requirements.txt setup.
if defined COMFY_GATEWAY_PYTHON (
    set "COMFY_GATEWAY_PYTHON_EXE=%COMFY_GATEWAY_PYTHON%"
) else (
    set "COMFY_GATEWAY_PYTHON_EXE=python"
)
"%COMFY_GATEWAY_PYTHON_EXE%" -m comfy_gateway.kernel.gateway --callers network\mcp\comfy_gateway\etc\callers.json --providers comfy_gateway.toolsurface.valheim,comfy_gateway.toolsurface.inference >> network\mcp\var\gateway-task.log 2>&1

