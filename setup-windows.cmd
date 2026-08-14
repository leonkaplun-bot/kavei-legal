@echo off
setlocal enabledelayedexpansion
title Council setup - connect Grok and Codex to Claude Code

rem One-shot Windows setup for the Grok + Codex advisory council.
rem Safe to run repeatedly: every step checks before it acts.
rem Runs as a plain .cmd so the PowerShell execution policy never applies.

set "REPO=%USERPROFILE%\kavei-legal"
set "BRANCH=claude/grok-codex-integration-ezmmc9"
set "GITURL=https://github.com/leonkaplun-bot/kavei-legal"

rem Places these tools install into that are not always on PATH.
set "PATH=%APPDATA%\npm;%USERPROFILE%\.grok\bin;%USERPROFILE%\.codex\bin;%PATH%"

echo.
echo ==========================================================
echo   Council setup: Grok + Codex for Claude Code
echo ==========================================================
echo.

echo [1/5] Checking Node.js and git...
where node >nul 2>&1
if errorlevel 1 (
  echo    ERROR: Node.js not found.
  echo    Install the LTS build from https://nodejs.org then run this file again.
  goto :fail
)
for /f "delims=" %%v in ('node --version 2^>nul') do echo    Node %%v
where git >nul 2>&1
if errorlevel 1 (
  echo    ERROR: git not found.
  echo    Install it from https://git-scm.com/download/win then run this file again.
  goto :fail
)
echo    git found
echo.

echo [2/5] Preparing the repository at %REPO% ...
if exist "%REPO%\.git" (
  echo    Already present, updating...
  pushd "%REPO%"
  git fetch origin %BRANCH% >nul 2>&1
  git checkout %BRANCH% >nul 2>&1
  git pull origin %BRANCH%
  if errorlevel 1 echo    WARNING: pull failed, continuing with the local copy.
  popd
) else (
  git clone -b %BRANCH% "%GITURL%" "%REPO%"
  if errorlevel 1 (
    echo    ERROR: clone failed. Check the network connection.
    goto :fail
  )
)
echo    Repository ready.
echo.

echo [3/5] Checking Claude Code...
where claude >nul 2>&1
if errorlevel 1 (
  echo    Not installed, installing now. This takes a minute...
  call npm.cmd install -g @anthropic-ai/claude-code
  if errorlevel 1 (
    echo    ERROR: install failed. Try running this file as Administrator.
    goto :fail
  )
  set "PATH=%APPDATA%\npm;!PATH!"
) else (
  echo    Already installed.
)
echo.

echo [4/5] Looking for the Grok and Codex CLIs...
set "GROKPATH="
set "CODEXPATH="
for /f "delims=" %%P in ('where grok 2^>nul') do if not defined GROKPATH set "GROKPATH=%%P"
for /f "delims=" %%P in ('where codex 2^>nul') do if not defined CODEXPATH set "CODEXPATH=%%P"
if defined GROKPATH (echo    grok  : !GROKPATH!) else (echo    grok  : NOT FOUND)
if defined CODEXPATH (echo    codex : !CODEXPATH!) else (echo    codex : NOT FOUND)
if not defined CODEXPATH (
  echo.
  echo    Codex is missing. Installing it now so both advisors are available...
  call npm.cmd install -g @openai/codex
  if errorlevel 1 (
    echo    Could not install Codex automatically - continuing with Grok alone.
  ) else (
    set "PATH=%APPDATA%\npm;!PATH!"
    echo    Codex installed.
  )
)
if not defined GROKPATH if not defined CODEXPATH (
  echo.
  echo    Neither CLI was found. The council needs at least one of them
  echo    installed on this machine to work without API keys.
)
echo.

echo [5/5] Testing the connection...
pushd "%REPO%"
node tools\council\bin\council.js status
popd
echo.

echo ==========================================================
echo   Setup finished.
echo ==========================================================
echo.
echo Starting Claude Code in %REPO%.
echo When it asks to enable the MCP server named "council", say yes.
echo Then type:  check council
echo.
pause
cd /d "%REPO%"
call claude
goto :end

:fail
echo.
echo Setup stopped. Nothing was broken - fix the item above and run this file again.
echo.
pause
exit /b 1

:end
endlocal
