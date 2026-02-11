@echo off
echo =============================================
echo Cleaning old build and dist folders...
echo =============================================

if exist EXE\build rmdir /s /q EXE\build
if exist EXE\dist rmdir /s /q EXE\dist
if exist SaMPH.spec del SaMPH.spec

echo.
echo =============================================
echo Running PyInstaller...
echo =============================================

REM =====================================================
REM PyInstaller Build Configuration
REM =====================================================
REM 
REM IMPORTANT: Resource Handling
REM -----------------------------------------
REM 1. Images: Code expects resources at _MEIPASS/SaMPH/SaMPH_Images
REM    So we map: src/SaMPH_Images -> SaMPH/SaMPH_Images
REM 
REM 2. Entry Point: src/Main.py
REM    This is the main entry point defined in the project
REM 
REM 3. User Data: 
REM    The application expects 'usr' folder next to the EXE.
REM    We do NOT bundle 'usr' inside the EXE strictly, 
REM    but we copy it to the dist folder after build.
REM 
REM =====================================================

pyinstaller ^
  --clean ^
  --onefile ^
  --windowed ^
  --name "SaMPH-Hull" ^
  --workpath "EXE/build" ^
  --distpath "EXE/dist" ^
  --paths "src" ^
  --add-data "src/SaMPH_Images;SaMPH/SaMPH_Images" ^
  --hidden-import "matplotlib" ^
  --hidden-import "matplotlib.pyplot" ^
  --hidden-import "matplotlib.backends.backend_agg" ^
  --hidden-import "latex2mathml" ^
  --hidden-import "latex2mathml.converter" ^
  --hidden-import "scipy.special.cython_special" ^
  --collect-data "matplotlib" ^
  --collect-data "latex2mathml" ^
  --collect-data "reportlab" ^
  --exclude-module "tkinter" ^
  --exclude-module "IPython" ^
  --exclude-module "pandas" ^
  --exclude-module "setuptools" ^
  --icon "src/SaMPH_Images/planing-hull-app-logo.ico" ^
  src/Main.py

echo.
echo =============================================
echo Copying external resources to dist folder...
echo =============================================

REM Copy usr directory (for settings/history)
if not exist "EXE\dist\usr" mkdir "EXE\dist\usr"
xcopy "usr" "EXE\dist\usr" /E /I /Y

REM Copy Examples directory
if not exist "EXE\dist\Examples" mkdir "EXE\dist\Examples"
xcopy "Examples" "EXE\dist\Examples" /E /I /Y

echo.
echo =============================================
echo Build finished.
echo EXE located at: %CD%\EXE\dist\SaMPH-Hull.exe
echo =============================================

pause
