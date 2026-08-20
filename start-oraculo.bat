@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul

set "PROJECT_DIR=%~dp0"
set "BACKEND_DIR=%PROJECT_DIR%backend"
set "FRONTEND_DIR=%PROJECT_DIR%frontend"
set "VENV_PYTHON=%BACKEND_DIR%\.venv\Scripts\python.exe"
set "LOCAL_ENV=%PROJECT_DIR%.env.local"
set "LEGACY_PARENT_ENV=%PROJECT_DIR%..\.env.local"
set "API_URL=http://127.0.0.1:8000"
set "HEALTH_URL=http://127.0.0.1:8000/api/health"
set "APP_URL=http://127.0.0.1:8000"
set "DEV_APP_URL=http://127.0.0.1:5173"
set "USE_DEV_FRONTEND=0"
set "CODEX_RUNTIME_DEPS=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies"
set "BUNDLED_NODE_DIR=%CODEX_RUNTIME_DEPS%\node\bin"
set "BUNDLED_NODE=%BUNDLED_NODE_DIR%\node.exe"
set "BUNDLED_PNPM=%CODEX_RUNTIME_DEPS%\bin\fallback\pnpm.cmd"
set "FRONTEND_RUNNER="

echo.
echo ============================================================
echo   ORACULO v0 - inicializacao local
echo ============================================================
echo.

if not exist "%VENV_PYTHON%" goto not_installed
if not exist "%FRONTEND_DIR%\package.json" goto not_installed
if exist "%FRONTEND_DIR%\dist\index.html" goto runtime_ready
set "USE_DEV_FRONTEND=1"
set "APP_URL=%DEV_APP_URL%"
echo AVISO: frontend\dist nao foi encontrado; usando Vite em modo de desenvolvimento.
where node >nul 2>&1
if not errorlevel 1 goto fallback_node_ready
if not exist "%BUNDLED_NODE%" goto build_missing
set "PATH=%BUNDLED_NODE_DIR%;%PATH%"

:fallback_node_ready
where npm >nul 2>&1
if errorlevel 1 goto fallback_try_pnpm
set "FRONTEND_RUNNER=npm"
goto runtime_ready

:fallback_try_pnpm
if not exist "%BUNDLED_PNPM%" goto build_missing
set "FRONTEND_RUNNER=%BUNDLED_PNPM%"

:runtime_ready

if not defined ORACULO_ENV_FILE if exist "%LOCAL_ENV%" set "ORACULO_ENV_FILE=%LOCAL_ENV%"
if not defined ORACULO_ENV_FILE if exist "%LEGACY_PARENT_ENV%" set "ORACULO_ENV_FILE=%LEGACY_PARENT_ENV%"
if defined ORACULO_ENV_FILE goto env_ready
echo AVISO: nenhum .env.local foi encontrado. Recursos locais abrirao, mas a IA ficara indisponivel.
echo Consulte a secao Configuracao segura do README.md.
echo.

:env_ready
call :probe_url "%HEALTH_URL%"
if not errorlevel 1 goto api_already_running
echo Iniciando API em %API_URL% ...
start "Oraculo" /D "%BACKEND_DIR%" cmd.exe /k ""%VENV_PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
goto api_started

:api_already_running
echo API ja esta ativa em %API_URL%.

:api_started
if "%USE_DEV_FRONTEND%"=="0" goto services_started
call :probe_url "%APP_URL%"
if not errorlevel 1 goto frontend_already_running
echo Iniciando interface em %APP_URL% ...
start "Oraculo - Interface" /D "%FRONTEND_DIR%" cmd.exe /k call "%FRONTEND_RUNNER%" run dev
goto services_started

:frontend_already_running
echo Interface ja esta ativa em %APP_URL%.

:services_started
echo Aguardando a aplicacao responder...
call :wait_url "%HEALTH_URL%" 45
if errorlevel 1 goto api_timeout
call :wait_url "%APP_URL%" 45
if errorlevel 1 goto frontend_timeout

echo.
echo Oraculo pronto: %APP_URL%
if "%USE_DEV_FRONTEND%"=="0" echo Mantenha a janela "Oraculo" aberta. Para encerrar, pressione Ctrl+C nela.
if "%USE_DEV_FRONTEND%"=="1" echo Mantenha as janelas API e Interface abertas. Para encerrar, pressione Ctrl+C em cada uma.
start "" "%APP_URL%"
exit /b 0

:probe_url
powershell.exe -NoProfile -Command "try { $response = Invoke-WebRequest -UseBasicParsing -Uri '%~1' -TimeoutSec 2; if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) { exit 0 } } catch {}; exit 1" >nul 2>&1
exit /b %ERRORLEVEL%

:wait_url
powershell.exe -NoProfile -Command "$deadline = (Get-Date).AddSeconds([int]'%~2'); do { try { $response = Invoke-WebRequest -UseBasicParsing -Uri '%~1' -TimeoutSec 2; if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) { exit 0 } } catch {}; Start-Sleep -Milliseconds 750 } while ((Get-Date) -lt $deadline); exit 1" >nul 2>&1
exit /b %ERRORLEVEL%

:not_installed
echo ERRO: a instalacao local nao foi encontrada.
echo Execute install-oraculo.bat primeiro.
goto failed

:build_missing
echo ERRO: o build frontend nao existe e Node.js/npm nao esta disponivel para o fallback.
echo Execute install-oraculo.bat para gerar frontend\dist.
goto failed

:api_timeout
echo.
echo ERRO: a API nao respondeu em ate 45 segundos.
echo Verifique a janela "Oraculo". Causas comuns: porta 8000 ocupada, ambiente invalido ou banco sem permissao.
goto failed

:frontend_timeout
echo.
echo ERRO: a interface nao respondeu em ate 45 segundos.
if "%USE_DEV_FRONTEND%"=="0" echo Verifique se frontend\dist existe e se a janela "Oraculo" mostra erro ao montar os arquivos estaticos.
if "%USE_DEV_FRONTEND%"=="1" echo Verifique a janela "Oraculo - Interface". Causas comuns: porta 5173 ocupada ou dependencias ausentes.
goto failed

:failed
echo Consulte README.md e docs\OPERACAO.md.
echo.
exit /b 1
