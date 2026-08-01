@echo off
setlocal
rem Repo root derived from this script's location (etc -> mcp -> network -> root),
rem so the retired C:\work\comfy checkout can never be picked up by accident.
cd /d "%~dp0..\..\.."
set PYTHONPATH=%CD%\network\mcp
set COMFY_MCP_ROOT=%CD%\network\mcp
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
if not defined COMFY_MCP_PORT set "COMFY_MCP_PORT=8721"
if not defined COMFY_MCP_PROFILE set "COMFY_MCP_PROFILE=Dev"
for /f "delims=" %%R in ('git rev-parse HEAD 2^>nul') do if not defined COMFY_MCP_SOURCE_REVISION set "COMFY_MCP_SOURCE_REVISION=%%R"
if not defined COMFY_MCP_SOURCE_REVISION set "COMFY_MCP_SOURCE_REVISION=unknown"
for /f "delims=" %%D in ('git status --porcelain 2^>nul') do set "COMFY_MCP_SOURCE_DIRTY=true"
if not defined COMFY_MCP_SOURCE_DIRTY set "COMFY_MCP_SOURCE_DIRTY=false"
if not defined COMFY_MCP_IMAGE set "COMFY_MCP_IMAGE=native-baseline:%COMFY_MCP_SOURCE_REVISION%"
"%COMFY_GATEWAY_PYTHON_EXE%" -m comfy_gateway.kernel.gateway --host 127.0.0.1 --port "%COMFY_MCP_PORT%" --callers network\mcp\comfy_gateway\etc\callers.json --providers comfy_gateway.toolsurface.valheim,comfy_gateway.toolsurface.inference >> network\mcp\var\gateway-task.log 2>&1

