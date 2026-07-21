@echo off
setlocal
rem Repo root derived from this script's location (etc -> mcp -> network -> root),
rem so the retired C:\work\comfy checkout can never be picked up by accident.
cd /d "%~dp0..\..\.."
set PYTHONPATH=%CD%\network\mcp
C:\work\commandcenter\fleet-worker-node\.venv-omen\Scripts\python.exe -m comfy_gateway.kernel.gateway --callers network\mcp\comfy_gateway\etc\callers.json --providers comfy_gateway.toolsurface.valheim,comfy_gateway.toolsurface.inference >> network\mcp\var\gateway-task.log 2>&1

