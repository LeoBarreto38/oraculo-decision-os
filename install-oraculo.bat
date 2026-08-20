@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul

set "PROJECT_DIR=%~dp0"
set "BACKEND_DIR=%PROJECT_DIR%backend"
set "FRONTEND_DIR=%PROJECT_DIR%frontend"
set "VENV_DIR=%BACKEND_DIR%\.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "LOCAL_ENV=%PROJECT_DIR%.env.local"
set "LEGACY_PARENT_ENV=%PROJECT_DIR%..\.env.local"
set "CODEX_RUNTIME_DEPS=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies"
set "BUNDLED_PYTHON=%CODEX_RUNTIME_DEPS%\python\python.exe"
set "BUNDLED_NODE_DIR=%CODEX_RUNTIME_DEPS%\node\bin"
set "BUNDLED_NODE=%BUNDLED_NODE_DIR%\node.exe"
set "BUNDLED_PNPM=%CODEX_RUNTIME_DEPS%\bin\fallback\pnpm.cmd"

echo.
echo ============================================================
echo   ORACULO v0 - instalacao local para Windows 11
echo ============================================================
echo.

if not exist "%BACKEND_DIR%\requirements.txt" goto missing_backend
if not exist "%FRONTEND_DIR%\package.json" goto missing_frontend

echo [1/6] Procurando Python 3.12...
set "PYTHON_EXE="
where py >nul 2>&1
if errorlevel 1 goto try_python_command
for /f "delims=" %%P in ('py -3.12 -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%P"
if defined PYTHON_EXE goto python_found

:try_python_command
where python >nul 2>&1
if errorlevel 1 goto try_python3_command
python -c "import sys; assert sys.version_info.major == 3 and sys.version_info.minor >= 12" >nul 2>&1
if errorlevel 1 goto try_python3_command
set "PYTHON_EXE=python"
goto python_found

:try_python3_command
where python3 >nul 2>&1
if errorlevel 1 goto try_bundled_python
python3 -c "import sys; assert sys.version_info.major == 3 and sys.version_info.minor >= 12" >nul 2>&1
if errorlevel 1 goto try_bundled_python
set "PYTHON_EXE=python3"
goto python_found

:try_bundled_python
if not exist "%BUNDLED_PYTHON%" goto python_missing
set "PYTHON_EXE=%BUNDLED_PYTHON%"

:python_found
"%PYTHON_EXE%" -c "import sys; assert sys.version_info.major == 3 and sys.version_info.minor >= 12" >nul 2>&1
if errorlevel 1 goto python_missing
"%PYTHON_EXE%" --version

echo [2/6] Procurando Node.js e npm...
set "NODE_EXE="
where node >nul 2>&1
if errorlevel 1 goto try_bundled_node
set "NODE_EXE=node"
goto node_found

:try_bundled_node
if not exist "%BUNDLED_NODE%" goto node_missing
set "NODE_EXE=%BUNDLED_NODE%"
set "PATH=%BUNDLED_NODE_DIR%;%PATH%"

:node_found
"%NODE_EXE%" -e "process.exit(Number(process.versions.node.split('.')[0]) >= 20 ? 0 : 1)" >nul 2>&1
if errorlevel 1 goto node_old
"%NODE_EXE%" --version

set "PACKAGE_MANAGER="
set "PACKAGE_MANAGER_KIND="
where npm >nul 2>&1
if errorlevel 1 goto try_bundled_pnpm
set "PACKAGE_MANAGER=npm"
set "PACKAGE_MANAGER_KIND=npm"
goto package_manager_found

:try_bundled_pnpm
if not exist "%BUNDLED_PNPM%" goto npm_missing
set "PACKAGE_MANAGER=%BUNDLED_PNPM%"
set "PACKAGE_MANAGER_KIND=pnpm"

:package_manager_found
echo       Gerenciador: %PACKAGE_MANAGER_KIND%

echo [3/6] Preparando ambiente virtual do backend...
if exist "%VENV_PYTHON%" goto validate_venv
"%PYTHON_EXE%" -m venv "%VENV_DIR%"
if errorlevel 1 goto venv_failed
goto install_backend

:validate_venv
"%VENV_PYTHON%" -c "import sys; assert sys.version_info.major == 3 and sys.version_info.minor >= 12" >nul 2>&1
if errorlevel 1 goto venv_incompatible
echo       Ambiente existente sera reutilizado.

:install_backend
echo [4/6] Instalando dependencias do backend...
"%VENV_PYTHON%" -m pip install --disable-pip-version-check --upgrade pip
if errorlevel 1 goto pip_failed
"%VENV_PYTHON%" -m pip install --disable-pip-version-check -r "%BACKEND_DIR%\requirements.txt"
if errorlevel 1 goto pip_failed

echo [5/6] Instalando dependencias do frontend...
pushd "%FRONTEND_DIR%"
if errorlevel 1 goto frontend_dir_failed
if "%PACKAGE_MANAGER_KIND%"=="pnpm" goto pnpm_install
if exist "package-lock.json" goto npm_clean_install
call "%PACKAGE_MANAGER%" install
set "NPM_RESULT=%ERRORLEVEL%"
goto npm_install_done

:npm_clean_install
call "%PACKAGE_MANAGER%" ci
set "NPM_RESULT=%ERRORLEVEL%"
goto npm_install_done

:pnpm_install
if exist "pnpm-lock.yaml" goto pnpm_frozen_install
call "%PACKAGE_MANAGER%" install
set "NPM_RESULT=%ERRORLEVEL%"
goto npm_install_done

:pnpm_frozen_install
call "%PACKAGE_MANAGER%" install --frozen-lockfile
set "NPM_RESULT=%ERRORLEVEL%"

:npm_install_done
if not "%NPM_RESULT%"=="0" goto npm_install_failed
echo       Gerando build otimizado para execucao local...
call "%PACKAGE_MANAGER%" run build
set "BUILD_RESULT=%ERRORLEVEL%"
popd
if not "%BUILD_RESULT%"=="0" goto frontend_build_failed

echo [6/6] Inicializando banco SQLite e Estado Zero...
if not defined ORACULO_ENV_FILE if exist "%LOCAL_ENV%" set "ORACULO_ENV_FILE=%LOCAL_ENV%"
if not defined ORACULO_ENV_FILE if exist "%LEGACY_PARENT_ENV%" set "ORACULO_ENV_FILE=%LEGACY_PARENT_ENV%"
pushd "%BACKEND_DIR%"
if errorlevel 1 goto backend_dir_failed
"%VENV_PYTHON%" -m app.cli init-db
set "INIT_RESULT=%ERRORLEVEL%"
popd
if not "%INIT_RESULT%"=="0" goto init_failed

echo.
echo ============================================================
echo   Instalacao concluida.
echo ============================================================
if defined ORACULO_ENV_FILE echo Ambiente local detectado.
if not defined ORACULO_ENV_FILE echo AVISO: nenhum .env.local foi encontrado. A interface abrira, mas analises por IA exigem OPENAI_API_KEY.
echo.
echo Para iniciar: start-oraculo.bat
echo Aplicacao: http://127.0.0.1:8000
echo.
exit /b 0

:missing_backend
echo ERRO: backend\requirements.txt nao foi encontrado.
goto failed

:missing_frontend
echo ERRO: frontend\package.json nao foi encontrado.
goto failed

:python_missing
echo ERRO: Python 3.12 ou superior nao foi encontrado.
echo Instale Python 3.12 para Windows e marque a opcao de adicionar ao PATH.
goto failed

:node_missing
echo ERRO: Node.js nao foi encontrado.
echo Instale Node.js 20 LTS ou disponibilize o runtime local do Codex.
goto failed

:node_old
echo ERRO: a versao do Node.js e anterior a 20.
echo Instale Node.js 20 LTS ou superior.
goto failed

:npm_missing
echo ERRO: nenhum gerenciador de pacotes foi encontrado.
echo Instale npm com Node.js ou disponibilize o pnpm do runtime local do Codex.
goto failed

:venv_failed
echo ERRO: nao foi possivel criar backend\.venv.
goto failed

:venv_incompatible
echo ERRO: backend\.venv existe, mas usa um Python incompativel.
echo Renomeie essa pasta e execute o instalador novamente.
goto failed

:pip_failed
echo ERRO: falha ao instalar dependencias Python.
echo Verifique a internet, espaco em disco e proxy/antivirus.
goto failed

:frontend_dir_failed
echo ERRO: nao foi possivel acessar a pasta frontend.
goto failed

:backend_dir_failed
echo ERRO: nao foi possivel acessar a pasta backend.
goto failed

:npm_install_failed
popd
echo ERRO: falha ao instalar dependencias do frontend.
echo Verifique a internet, espaco em disco e configuracao do gerenciador de pacotes.
goto failed

:frontend_build_failed
echo ERRO: dependencias foram instaladas, mas o build do frontend falhou.
echo Execute pnpm run typecheck e pnpm run build na pasta frontend para diagnosticar.
goto failed

:init_failed
echo ERRO: dependencias foram instaladas, mas o banco/seed nao foi inicializado.
echo Execute backend\.venv\Scripts\python.exe -m app.cli init-db na pasta backend para ver o diagnostico.
goto failed

:failed
echo.
echo Instalacao interrompida. Consulte README.md e docs\OPERACAO.md.
echo.
exit /b 1
