@echo off

REM You can customize this script to run out agent using the script harness

set HARNESS="D:\PythonAgentSDK-1_0_3"\bin\script-harness.bat

%HARNESS% --properties="D:\dev\Foglight-Agent"\agent-properties.json --lib="D:\dev\Foglight-Agent"\library-dir --statedir="D:\dev\Foglight-Agent"\state "D:\dev\Foglight-Agent\scripts"\agent.py %*
