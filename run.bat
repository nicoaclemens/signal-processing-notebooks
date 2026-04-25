@echo off
setlocal

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "PY=%ROOT%\venv\Scripts\python.exe"
set "KERNEL_NAME=signal-processing-notebooks"
set "KERNEL_DISPLAY=Python (Signal Processing Notebooks)"

if not exist "%PY%" (
  echo [ERROR] Python virtual environment not found at "%PY%".
  exit /b 1
)

echo [1/3] Installing dependencies from requirements.txt...
"%PY%" -m pip install -r "%ROOT%\requirements.txt" || exit /b 1

echo [2/3] Installing project...
"%PY%" -m pip install -e "%ROOT%" || exit /b 1
"%PY%" -m pip install ipykernel || exit /b 1

echo [3/3] Registering notebook kernel "%KERNEL_NAME%"...
"%PY%" -m ipykernel install --user --name "%KERNEL_NAME%" --display-name "%KERNEL_DISPLAY%" || exit /b 1

echo Starting Jupyter Lab in notebooks directory...
"%PY%" -m jupyter lab --notebook-dir="%ROOT%\notebooks"

endlocal
